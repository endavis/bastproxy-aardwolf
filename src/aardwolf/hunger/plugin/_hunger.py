"""Aardwolf hunger plugin: drink from a container when the character is hungry or thirsty."""

import time
from collections.abc import Callable
from typing import Any

from bastproxy.libs.logger import get_logger
from bastproxy.libs.records import (
    NetworkData,
    NetworkDataLine,
    SendDataDirectlyToClient,
    SendDataDirectlyToMud,
)
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.commands import AddArgument, AddCommand, AddParser, CommandResult
from bastproxy.plugins.core.events import RegisterToEvent

from aardwolf._libs.validate import int_validator

from ..libs import (
    API_EXISTS,
    API_ITEM_FETCH,
    API_ITEM_FIND,
    API_ITEM_GET,
    API_ITEM_PUT,
    API_ROOM_GET,
    API_WALK_GET,
    API_WALK_START,
    COOLDOWN,
    EVENT_DISCONNECT,
    EVENT_EQ_INVENTORY_ADDED,
    EVENT_EQ_PUT,
    EVENT_EQ_TAKEN,
    EVENT_MOVE_ROOM,
    EVENT_WALK_DONE,
    EVENT_WALK_FAILED,
    EVENT_WALK_STARTED,
    GMCP_ROOM_NUM,
    GROUP,
    GROUP_REPLY,
    GULP_CMD,
    INVENTORY,
    PENDING_TIMEOUT,
    REPLY_TRIGGERS,
    SETTING_CONTAINER,
    SETTING_COOLDOWN,
    SETTING_DRINK,
    SETTING_FILLOBJECT,
    SETTING_FILLROOM,
    STAGE_TRIGGERS,
    TIMER_FETCH,
    TIMER_REPLY,
    TRIGGER_DRANK,
    TRIGGER_EMPTY,
    TRIGGER_FILLED,
    TRIGGER_FULL,
    TRIGGER_NOSOURCE,
    WALK_BUSY_STATES,
    TriggerSpec,
    choose_item,
    cooldown_ok,
    fill_command,
    parse_item_setting,
    room_num,
    should_autofill,
)

KIND_DRINK = "drink"
KIND_FILL = "fill"


class HungerPlugin(BasePlugin):
    """Drink from the configured container when a hunger or thirst line arrives."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Create the empty state."""
        # the action waiting for eq to take the container out: (command, serial, kind)
        self._pending: tuple[str, int, str] | None = None
        # the kind of the drink or fill sent and not answered yet
        self._awaiting: str | None = None
        self._auto_fill = False
        # the monotonic time of the last drink attempt
        self._last: float | None = None
        # why nothing is done now; the client is told once, when it is first set
        self._blocked: str | None = None
        self._empty = False
        # the room uid of a fill walk started by the fill command
        self._fill_walk: str | None = None
        self._groups_ready = False

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the settings and the triggers; the reply triggers start off."""
        add = self.api("plugins.core.settings:setting.add")
        add(self.plugin_id, SETTING_DRINK, False, bool, "drink when hungry or thirsty")
        add(
            self.plugin_id,
            SETTING_CONTAINER,
            "",
            str,
            "the container to drink from: its serial, or a piece of its name",
            nocolor=True,
        )
        add(
            self.plugin_id,
            SETTING_COOLDOWN,
            COOLDOWN,
            int,
            "seconds to wait after a drink before another one is tried",
            validator=int_validator(1, 3600),
        )
        add(
            self.plugin_id,
            SETTING_FILLROOM,
            "",
            str,
            "the room uid of the liquid source that fills the container",
            nocolor=True,
        )
        add(
            self.plugin_id,
            SETTING_FILLOBJECT,
            "",
            str,
            "the object of the liquid source, empty to let the mud find it",
            nocolor=True,
        )
        for spec in STAGE_TRIGGERS:
            self._add_trigger(spec, self._needs_drink, reply=False)
        callbacks = {
            TRIGGER_DRANK: self._trigger_drank,
            TRIGGER_EMPTY: self._trigger_empty,
            TRIGGER_FILLED: self._trigger_filled,
            TRIGGER_FULL: self._trigger_full,
            TRIGGER_NOSOURCE: self._trigger_nosource,
        }
        for spec in REPLY_TRIGGERS:
            self._add_trigger(spec, callbacks[spec.name], reply=True)

    @RegisterPluginHook("uninitialize", priority=10)
    def _phook_uninitialize(self) -> None:
        """Remove the timers."""
        self._remove_timer(TIMER_FETCH)
        self._remove_timer(TIMER_REPLY)

    # helpers

    def _add_trigger(self, spec: TriggerSpec, func: Callable[[], None], reply: bool) -> None:
        """Add a trigger and register its callback; a reply trigger is off, in its group."""
        kwargs: dict[str, Any] = {}
        if reply:
            kwargs = {"enabled": False, "group": self._group()}
        result = self.api("plugins.core.triggers:trigger.add")(spec.name, spec.regex, **kwargs)
        if not result.success:
            get_logger(self.plugin_id).error("could not add the %s trigger", spec.name)
            return
        self.api("plugins.core.triggers:trigger.register")(result.trigger.trigger_id, func)
        if reply:
            self._groups_ready = True

    def _group(self) -> str:
        """Return the reply trigger group name; group names are global."""
        return f"{self.plugin_id}.{GROUP_REPLY}"

    def _toggle_reply(self, flag: bool) -> None:
        """Turn the reply triggers on or off, when they exist."""
        if self._groups_ready:
            self.api("plugins.core.triggers:group.toggle.enable")(self._group(), flag)

    def _record(self) -> dict[str, Any]:
        """Return the record of the current event."""
        return dict(self.api("plugins.core.events:event.current.record.get")() or {})

    def _args(self) -> dict[str, Any]:
        """Return the arguments of the running command."""
        args = self.api("plugins.core.commands:command.current.args.get")()
        return dict(args) if args else {}

    def _setting(self, name: str) -> object:
        """Return a setting of the plugin."""
        return self.api("plugins.core.settings:setting.get")(self.plugin_id, name)

    def _gmcp(self, path: str) -> object:
        """Return a GMCP value."""
        return self.api("libs.net.protocols:gmcp.value.get")(path)

    def _room(self) -> str | None:
        """Return the uid of the room the character is in, or None when it is not known."""
        return room_num(self._gmcp(GMCP_ROOM_NUM))

    def _client(self, lines: list[str]) -> None:
        """Send lines to the clients."""
        data = NetworkData(
            [NetworkDataLine(line, preamble=False) for line in lines],
            owner_id=f"{self.plugin_id}:notice",
        )
        SendDataDirectlyToClient(data)()

    def _send(self, line: str) -> None:
        """Send a line straight to the mud."""
        SendDataDirectlyToMud(NetworkData([line], owner_id=f"{self.plugin_id}:send"))()

    def _busy(self) -> bool:
        """Return True while a drink or fill waits for eq or for the mud."""
        return self._pending is not None or self._awaiting is not None

    def _remove_timer(self, name: str) -> None:
        """Remove a timer when there is one (timer.remove logs an error otherwise)."""
        if self.api("plugins.core.timers:timer.exists")(name):
            self.api("plugins.core.timers:timer.remove")(name)

    def _start_timer(self, name: str, func: Callable[[], None]) -> None:
        """Start a one shot timer of PENDING_TIMEOUT seconds, replacing one of the same name."""
        self._remove_timer(name)
        self.api("plugins.core.timers:timer.add")(name, func, PENDING_TIMEOUT, onetime=True)

    def _block(self, reason: str) -> None:
        """Stop acting until something changes, telling the client once."""
        first = self._blocked is None
        self._blocked = reason
        if first:
            self._client([f"@BHunger - not acting: {reason}"])

    def _unblock(self) -> None:
        """Act again."""
        self._blocked = None
        self._empty = False

    def _clear_all(self) -> None:
        """Forget the action under way."""
        self._pending = None
        self._awaiting = None
        self._auto_fill = False
        self._remove_timer(TIMER_FETCH)
        self._remove_timer(TIMER_REPLY)
        self._toggle_reply(False)

    def _resolve(self) -> int | None:
        """Return the serial of the container the setting names, or None when eq has none."""
        wanted = parse_item_setting(self._setting(SETTING_CONTAINER))
        if wanted is None:
            return None
        if isinstance(wanted, int):
            return wanted if self.api(API_ITEM_GET)(wanted) else None
        return choose_item(self.api(API_ITEM_FIND)(wanted))

    # acting

    def _act(self, command: str, serial: int, kind: str) -> None:
        """Take the container out when it is in a bag, send the command, and put it back.

        Eq moves the item only when the mud's reply arrives, so the command waits for eq_taken.
        """
        item = self.api(API_ITEM_GET)(serial) or {}
        place = item.get("container")
        if place in (None, INVENTORY):
            self._send_command(command, kind)
            return
        self._pending = (command, serial, kind)
        self.api(API_ITEM_FETCH)(serial)
        self._start_timer(TIMER_FETCH, self._timer_fetch)

    def _send_command(self, command: str, kind: str, put_back: int | None = None) -> None:
        """Send the drink or fill, put the container back, and wait for the reply."""
        self._send(command)
        if put_back is not None:
            self.api(API_ITEM_PUT)(put_back)
        self._awaiting = kind
        self._toggle_reply(True)
        self._start_timer(TIMER_REPLY, self._timer_reply)

    def _timer_fetch(self) -> None:
        """eq never took the container out: drop the action."""
        if self._pending is None:
            return
        self._pending = None
        self._auto_fill = False
        self._client(["@BHunger - the container did not come out, giving up"])

    def _timer_reply(self) -> None:
        """The mud did not answer: stop reading replies."""
        self._awaiting = None
        self._auto_fill = False
        self._toggle_reply(False)

    def _finish_reply(self) -> str | None:
        """The mud answered: stop waiting, and return the kind of the action answered."""
        kind = self._awaiting
        self._awaiting = None
        self._remove_timer(TIMER_REPLY)
        self._toggle_reply(False)
        return kind

    def _needs_drink(self) -> None:
        """A hunger or thirst line: drink, unless off, blocked, busy or inside the cooldown."""
        if not self._setting(SETTING_DRINK) or self._blocked is not None or self._busy():
            return
        now = time.monotonic()
        if not cooldown_ok(self._last, now, float(str(self._setting(SETTING_COOLDOWN)))):
            return
        serial = self._resolve()
        if serial is None:
            self._block("the drink container was not found")
            return
        self._last = now
        self._act(GULP_CMD.format(item=serial), serial, KIND_DRINK)

    def _do_fill(self, auto: bool) -> bool:
        """Fill the container where the character is; return False when nothing was sent."""
        if self._busy():
            self._client(["@BHunger - a drink or fill is already under way"])
            return False
        serial = self._resolve()
        if serial is None:
            self._block("the drink container was not found")
            return False
        self._auto_fill = auto
        source = str(self._setting(SETTING_FILLOBJECT))
        self._act(fill_command(serial, source), serial, KIND_FILL)
        return True

    def _start_fill_walk(self, room: str) -> str | None:
        """Walk to the fill room; return why it was not started, or None when it was.

        The only place that calls walk.start, and only the fill command calls this.
        """
        if not self.api(API_EXISTS)(API_WALK_START):
            return "the mapper is not loaded"
        if self.api(API_ROOM_GET)(room) is None:
            return f"room {room} is not mapped"
        if self.api(API_WALK_GET)().get("state") in WALK_BUSY_STATES:
            return "a walk is already under way"
        if not self.api(API_WALK_START)(room):
            return f"the walk to room {room} could not start"
        self._fill_walk = room
        return None

    # triggers

    def _trigger_drank(self) -> None:
        """The drink worked."""
        self._finish_reply()

    def _trigger_empty(self) -> None:
        """The container is empty: drink no more until it is filled."""
        self._finish_reply()
        self._empty = True
        name = self._record().get("matches", {}).get("container", "the container")
        self._block(f"{name} is empty")

    def _trigger_filled(self) -> None:
        """The container was filled."""
        self._finish_reply()
        self._unblock()

    def _trigger_full(self) -> None:
        """The container was already full: it has liquid, so the fill is done."""
        self._finish_reply()
        self._unblock()

    def _trigger_nosource(self) -> None:
        """There was nothing to fill from: keep the empty state."""
        auto = self._auto_fill
        self._finish_reply()
        self._auto_fill = False
        if auto:
            self._client(["@BHunger - the stored fill room has no liquid source"])
        else:
            self._client(["@BHunger - there is no liquid source here"])

    # events

    @RegisterToEvent(event_name=EVENT_EQ_TAKEN)
    def _eventcb_taken(self) -> None:
        """An item was taken out: when it is the waited container, drink or fill now."""
        serial = self._record().get("serial")
        if self._pending is not None and serial == self._pending[1]:
            command, wanted, kind = self._pending
            self._pending = None
            self._remove_timer(TIMER_FETCH)
            self._send_command(command, kind, put_back=wanted)
        self._maybe_unblock()

    @RegisterToEvent(event_name=EVENT_EQ_PUT)
    def _eventcb_put(self) -> None:
        """An item was put away."""
        self._maybe_unblock()

    @RegisterToEvent(event_name=EVENT_EQ_INVENTORY_ADDED)
    def _eventcb_inventory_added(self) -> None:
        """An item reached the inventory."""
        self._maybe_unblock()

    def _maybe_unblock(self) -> None:
        """Act again when the container was missing and eq knows it now."""
        if self._blocked is not None and not self._empty and self._resolve() is not None:
            self._unblock()

    @RegisterToEvent(event_name="ev_{plugin_id}_var_container_modified")
    def _eventcb_container_modified(self) -> None:
        """A new container was set: forget why the old one stopped the plugin."""
        self._unblock()

    @RegisterToEvent(event_name=EVENT_MOVE_ROOM)
    def _eventcb_move_room(self) -> None:
        """The character moved: fill when it entered the fill room and the container is empty."""
        to = self._record().get("to")
        room = room_num(to.get("num")) if isinstance(to, dict) else None
        busy = self._fill_walk is not None or self._busy()
        if should_autofill(room, str(self._setting(SETTING_FILLROOM)), self._empty, busy):
            self._do_fill(True)

    @RegisterToEvent(event_name=EVENT_WALK_STARTED)
    def _eventcb_walk_started(self) -> None:
        """A walk started: one to another room means the player went elsewhere."""
        if self._fill_walk is not None and str(self._record().get("target")) != self._fill_walk:
            self._fill_walk = None

    @RegisterToEvent(event_name=EVENT_WALK_DONE)
    def _eventcb_walk_done(self) -> None:
        """A walk ended: when it is the fill walk, fill."""
        if self._fill_walk is None or str(self._record().get("target")) != self._fill_walk:
            return
        self._fill_walk = None
        self._do_fill(False)

    @RegisterToEvent(event_name=EVENT_WALK_FAILED)
    def _eventcb_walk_failed(self) -> None:
        """A walk failed: when it is the fill walk, say why."""
        record = self._record()
        if self._fill_walk is None or str(record.get("target")) != self._fill_walk:
            return
        self._fill_walk = None
        self._client([f"@BHunger - the walk to the fill room failed: {record.get('reason')}"])

    @RegisterToEvent(event_name=EVENT_DISCONNECT)
    def _eventcb_disconnect(self) -> None:
        """The connection dropped: forget the action under way."""
        self._clear_all()
        self._fill_walk = None
        self._last = None

    # commands

    @AddCommand(group=GROUP)
    @AddParser(description="record the room the character is in as the place to fill the container")
    @AddArgument("object", help="the liquid source object; none clears it", nargs="?", default="")
    @AddArgument("-s", "--show", help="show the stored fill source", action="store_true")
    def _command_fillsource(self) -> CommandResult:
        """Store the current room, and the object when given, as the fill source."""
        args = self._args()
        if not args.get("show"):
            room = self._room()
            if room is None:
                return CommandResult(False, ["The room the character is in is not known"])
            set_setting = self.api("plugins.core.settings:setting.set")
            set_setting(self.plugin_id, SETTING_FILLROOM, room)
            set_setting(self.plugin_id, SETTING_FILLOBJECT, str(args.get("object") or ""))
        room_text = str(self._setting(SETTING_FILLROOM)) or "not set"
        source = str(self._setting(SETTING_FILLOBJECT)) or "none"
        return CommandResult(True, [f"Fill room: {room_text}", f"Fill object: {source}"])

    @AddCommand(group=GROUP)
    @AddParser(description="fill the drink container, walking to the fill room first if needed")
    def _command_fill(self) -> CommandResult:
        """Fill the container here, or walk to the fill room and fill on arrival."""
        fillroom = str(self._setting(SETTING_FILLROOM))
        if parse_item_setting(self._setting(SETTING_CONTAINER)) is None:
            return CommandResult(False, ["No drink container is set"])
        if not fillroom:
            return CommandResult(False, ["No fill room is set; use fillsource in the room"])
        if self._room() == fillroom:
            if self._do_fill(False):
                return CommandResult(True, ["Filling the container"])
            return CommandResult(False, ["Could not fill the container"])
        error = self._start_fill_walk(fillroom)
        if error:
            return CommandResult(False, [f"Not walking to the fill room: {error}"])
        return CommandResult(True, [f"Walking to room {fillroom} to fill the container"])

    @AddCommand(group=GROUP)
    @AddParser(description="show what the hunger plugin is doing")
    def _command_status(self) -> CommandResult:
        """Show the state."""
        return CommandResult(
            True,
            [
                f"Drinking: {'on' if self._setting(SETTING_DRINK) else 'off'}",
                f"Container: {self._setting(SETTING_CONTAINER) or 'not set'}"
                f" (serial {self._resolve()})",
                f"Not acting: {self._blocked or 'no'}",
                f"Empty: {'yes' if self._empty else 'no'}",
                f"Waiting: {'yes' if self._busy() else 'no'}",
                f"Fill walk: {self._fill_walk or 'none'}",
            ],
        )
