"""Aardwolf itemid plugin: identify an item with invdetails and identify, and show it."""

import copy
import functools
import logging
from collections.abc import Callable
from typing import Any

from bastproxy.libs.api import AddAPI
from bastproxy.libs.logger import get_logger, log_to
from bastproxy.libs.records import NetworkData, NetworkDataLine, SendDataDirectlyToClient
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.commands import AddArgument, AddCommand, AddParser, CommandResult
from bastproxy.plugins.core.events import RegisterToEvent

from ..libs import (
    API_EQ_IDENTIFY_ADD,
    API_EQ_ITEM_FETCH,
    API_EQ_ITEM_GET,
    API_EQ_ITEM_PUT,
    API_EQDB_ITEM_GET,
    API_EQDB_ITEM_SAVE,
    API_SKILL_GET,
    EVENT_DISCONNECT,
    EVENT_EQ_INVENTORY_REMOVED,
    EVENT_EQ_PUT,
    EVENT_EQ_WORN,
    EVENT_IDENTIFIED,
    EVENTS,
    GROUP_IDENTIFY,
    GROUP_INVDETAILS,
    HIDE_MAX,
    INVENTORY,
    TIMEOUT_EVENT,
    TRIGGERS,
    TYPE_IDENTIFY,
    TYPE_INVDETAILS,
    TYPES,
    WORN,
    IdentifyReader,
    InvdetailsReader,
    TriggerSpec,
    TypeSpec,
    build_item,
    format_item,
    to_int,
)

_CALLBACKS = {
    "itemid_invdetails_start": "_trigger_invdetails_start",
    "itemid_invdetails_line": "_trigger_invdetails_line",
    "itemid_invdetails_end": "_trigger_invdetails_end",
    "itemid_identify_line": "_trigger_identify_line",
}


def _serial(value: object) -> int | None:
    """Return a serial as an int, or None when it is not one."""
    try:
        number = to_int(value)
    except ValueError:
        return None
    return number if number > 0 else None


class ItemIdPlugin(BasePlugin):
    """Read invdetails and identify for an item, keep the result and show it."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Create the empty state."""
        # serial to the identified item, in eqdb's shape; cleared on disconnect
        self._cache: dict[int, dict[str, Any]] = {}
        # the serials queued, in the order the commands were queued; the head is the one read now
        self._pending: list[int] = []
        # serial to the container the item was fetched from
        self._fetched: dict[int, str] = {}
        # serial to the container the item is being put back into, and what to raise
        self._waits: dict[int, tuple[str, dict[str, Any] | None]] = {}
        # serials to show once they are identified
        self._show: set[int] = set()
        self._details = InvdetailsReader()
        self._details_result: dict[str, Any] | None = None
        # True between {invdetails} and {/invdetails}; other tagged lines (an {invmon} from a
        # fetch) can arrive while the group is on and before the block starts
        self._in_details = False
        self._identify = IdentifyReader()
        self._groups_ready = False

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the event, the command types, the triggers and the timeout handlers."""
        for event_name, info in EVENTS.items():
            self.api("plugins.core.events:event.add")(
                event_name,
                self.plugin_id,
                description=info["description"],
                arg_descriptions=info["arg_descriptions"],
            )
        for spec in TYPES:
            self._add_type(spec)
        for trigger in TRIGGERS:
            self._add_trigger(trigger)
        register = self.api("plugins.core.events:event.register")
        register(TIMEOUT_EVENT.format(TYPE_INVDETAILS), self._eventcb_invdetails_timeout)
        register(TIMEOUT_EVENT.format(TYPE_IDENTIFY), self._eventcb_identify_timeout)

    # setup helpers

    def _add_type(self, spec: TypeSpec) -> None:
        """Add a command type that hides its output when it is queued."""
        self.api("plugins.core.mudcmds:type.add")(
            spec.cmdtype,
            spec.cmd,
            spec.regex,
            # beforef runs only for a queued command, so a typed one is shown and not parsed
            beforef=functools.partial(self._command_started, spec.cmdtype),
            hide_output=True,
            hide_start=spec.hide_start,
            hide_max=HIDE_MAX + 2,
        )

    def _add_trigger(self, spec: TriggerSpec) -> None:
        """Add a trigger, off, in its group, and register its callback."""
        result = self.api("plugins.core.triggers:trigger.add")(
            spec.name, spec.regex, enabled=False, group=self._group(spec.group)
        )
        if not result.success:
            get_logger(self.plugin_id).error("could not add the %s trigger", spec.name)
            return
        callback: Callable[[], None] = getattr(self, _CALLBACKS[spec.name])
        self.api("plugins.core.triggers:trigger.register")(result.trigger.trigger_id, callback)
        self._groups_ready = True

    def _group(self, suffix: str) -> str:
        """Return the trigger group name; group names are global, so it carries the plugin id."""
        return f"{self.plugin_id}.{suffix}"

    def _toggle(self, suffix: str, flag: bool) -> None:
        """Turn a trigger group on or off, when the triggers exist."""
        if self._groups_ready:
            self.api("plugins.core.triggers:group.toggle.enable")(self._group(suffix), flag)

    def _record(self) -> dict[str, Any]:
        """Return the record of the current event."""
        return dict(self.api("plugins.core.events:event.current.record.get")() or {})

    def _matches(self) -> dict[str, Any]:
        """Return the groups the current trigger matched."""
        return dict(self._record().get("matches") or {})

    def _args(self) -> dict[str, Any]:
        """Return the arguments of the running command."""
        args = self.api("plugins.core.commands:command.current.args.get")()
        return dict(args) if args else {}

    def _exists(self, api_name: str) -> bool:
        """Return True when an API is registered."""
        return bool(self.api("libs.api:api.exists")(api_name))

    def _strip(self, text: str) -> str:
        """Remove the colour codes of the text."""
        return str(self.api("plugins.core.colors:colorcode.strip")(text))

    def _client(self, lines: list[str]) -> None:
        """Send lines to the client, without the preamble."""
        data = NetworkData(
            [NetworkDataLine(line, preamble=False) for line in lines],
            owner_id=f"{self.plugin_id}:show",
        )
        SendDataDirectlyToClient(data)()

    def _eq_item(self, serial: int) -> dict[str, Any] | None:
        """Return eq's copy of an item, or None."""
        found = self.api(API_EQ_ITEM_GET)(serial)
        return dict(found) if found else None

    # the queued commands

    def _command_started(self, cmdtype: str) -> None:
        """The queue is sending one of our commands: start its timing and read its reply."""
        self.api("plugins.core.mudcmds:command.start")(cmdtype)
        if cmdtype == TYPE_INVDETAILS:
            self._details.start()
            self._details_result = None
            self._in_details = False
            self._toggle(GROUP_INVDETAILS, True)
        else:
            self._identify.reset()
            self._toggle(GROUP_IDENTIFY, True)

    def _head(self) -> int | None:
        """Return the serial being read, or None."""
        return self._pending[0] if self._pending else None

    def _trigger_invdetails_start(self) -> None:
        """The opening tag: begin a new item."""
        self._details.start()
        self._in_details = True

    def _trigger_invdetails_line(self) -> None:
        """A tagged line inside the block: add it to the item."""
        if not self._in_details:
            return
        matches = self._matches()
        header = str(matches.get("header", ""))
        data = str(matches.get("data", ""))
        try:
            self._details.line(header, data)
        except ValueError as err:
            log_to(
                [self.plugin_id], logging.WARNING, "invdetails line {%s}%s: %s", header, data, err
            )

    def _trigger_invdetails_end(self) -> None:
        """The closing tag: keep the item when it is the one asked for, and finish the command."""
        self._in_details = False
        self._toggle(GROUP_INVDETAILS, False)
        result = self._details.result()
        head = self._head()
        self._details_result = None
        if not self._details.has_header:
            log_to([self.plugin_id], logging.WARNING, "invdetails for %s had no invheader", head)
        elif result.get("serial") != head:
            log_to(
                [self.plugin_id],
                logging.WARNING,
                "invdetails is for %s, expected %s: dropped",
                result.get("serial"),
                head,
            )
        else:
            self._details_result = result
        self.api("plugins.core.mudcmds:command.finish")(TYPE_INVDETAILS)

    def _trigger_identify_line(self) -> None:
        """A line of the identify reply: read it, and finish at the end."""
        if not self._identify.feed(str(self._matches().get("line", ""))):
            return
        self._toggle(GROUP_IDENTIFY, False)
        self._finish_identify()
        self.api("plugins.core.mudcmds:command.finish")(TYPE_IDENTIFY)

    def _finish_identify(self) -> None:
        """Join the two replies, hand the item to eq, and put the item back."""
        serial = self._pending.pop(0) if self._pending else None
        details, self._details_result = self._details_result, None
        if serial is None:
            log_to([self.plugin_id], logging.WARNING, "an identify finished with none queued")
            return
        for label in self._identify.unknown:
            log_to([self.plugin_id], logging.DEBUG, "unknown identify label %r", label)
        item: dict[str, Any] | None = None
        if details is None:
            log_to([self.plugin_id], logging.WARNING, "no invdetails for %s: not saved", serial)
        else:
            item = build_item(details, self._identify.result())
            known = self._eq_item(serial) or {}
            for key in ("cname", "name"):
                if key in known:
                    item[key] = known[key]
            self._cache[serial] = item
            self._save(serial, item)
        self._put_back(serial, item)

    def _save(self, serial: int, item: dict[str, Any]) -> None:
        """Give the item to eq, and to eqdb when eq does not know it."""
        # eqdb has no table for the temporary mods
        attributes = {key: value for key, value in copy.deepcopy(item).items() if key != "tempmod"}
        if self.api(API_EQ_IDENTIFY_ADD)(serial, attributes):
            return
        if self._exists(API_EQDB_ITEM_SAVE):
            self.api(API_EQDB_ITEM_SAVE)(attributes)

    def _eventcb_invdetails_timeout(self) -> None:
        """The invdetails reply never ended: drop what was read. The identify still follows."""
        self._details.start()
        self._details_result = None
        self._in_details = False
        self._toggle(GROUP_INVDETAILS, False)

    def _eventcb_identify_timeout(self) -> None:
        """The identify reply never ended: drop it, and put the item back."""
        self._identify.reset()
        self._toggle(GROUP_IDENTIFY, False)
        self._details_result = None
        serial = self._pending.pop(0) if self._pending else None
        if serial is not None:
            self._put_back(serial, None)

    # putting an item back

    def _put_back(self, serial: int, item: dict[str, Any] | None) -> None:
        """Put a fetched item back, and release the item when it is there."""
        fetched = self._fetched.pop(serial, None)
        if fetched is None:
            self._release(serial, item)
            return
        target = self.api(API_EQ_ITEM_PUT)(serial, fetched)
        now = self._eq_item(serial)
        if target is None or (now is not None and str(now.get("container")) == fetched):
            self._release(serial, item)
            return
        self._waits[serial] = (fetched, item)

    def _release(self, serial: int, item: dict[str, Any] | None) -> None:
        """The item is where it was: raise the event, and show it when asked."""
        self._waits.pop(serial, None)
        wanted = serial in self._show
        self._show.discard(serial)
        if item is None:
            if wanted:
                self._client([f"Could not identify {serial}"])
            return
        payload = {"serial": serial, "item": copy.deepcopy(item)}
        self.api("plugins.core.events:event.raise")(EVENT_IDENTIFIED, event_args=payload)
        if wanted:
            self._client(self._box(item))

    def _release_wait(self, serial: object) -> None:
        """Release a waiting item by serial."""
        number = _serial(serial)
        if number is not None and number in self._waits:
            self._release(number, self._waits[number][1])

    @RegisterToEvent(event_name=EVENT_EQ_PUT)
    def _eventcb_eq_put(self) -> None:
        """An item was put somewhere: release the item waiting for that container."""
        record = self._record()
        number = _serial(record.get("serial"))
        wait = self._waits.get(number) if number is not None else None
        if wait is not None and wait[0] != WORN and str(record.get("container")) == wait[0]:
            self._release_wait(number)

    @RegisterToEvent(event_name=EVENT_EQ_WORN)
    def _eventcb_eq_worn(self) -> None:
        """An item was worn: release the item waiting to be worn again."""
        number = _serial((self._record().get("item") or {}).get("serial"))
        wait = self._waits.get(number) if number is not None else None
        if wait is not None and wait[0] == WORN:
            self._release_wait(number)

    @RegisterToEvent(event_name=EVENT_EQ_INVENTORY_REMOVED)
    def _eventcb_eq_inventory_removed(self) -> None:
        """An item left the inventory: stop waiting for it."""
        self._release_wait((self._record().get("item") or {}).get("serial"))

    @RegisterToEvent(event_name=EVENT_DISCONNECT)
    def _eventcb_disconnect(self) -> None:
        """Forget the items and everything in progress."""
        self._cache.clear()
        self._pending.clear()
        self._fetched.clear()
        self._waits.clear()
        self._show.clear()
        self._details.start()
        self._details_result = None
        self._in_details = False
        self._identify.reset()
        self._toggle(GROUP_INVDETAILS, False)
        self._toggle(GROUP_IDENTIFY, False)

    # APIs

    @AddAPI(
        "item.identify",
        description="identify an item; return a copy when it is known, or None after queueing",
    )
    def _api_item_identify(self, serial: int | str, force: bool = False) -> dict[str, Any] | None:
        """Return the identified item, or queue invdetails and identify and return None.

        An item that is not in the inventory is fetched first and put back afterwards, and
        ``ev_plugins.aardwolf.itemid_identified`` is raised when that is done.
        """
        number = _serial(serial)
        if number is None:
            return None
        if number in self._cache and not force:
            return copy.deepcopy(self._cache[number])
        if number in self._pending:
            return None
        self._pending.append(number)
        known = self._eq_item(number)
        place = known.get("container") if known else None
        if place not in (None, INVENTORY) and self.api(API_EQ_ITEM_FETCH)(number):
            self._fetched[number] = str(place)
        queue = self.api("plugins.core.mudcmds:command.queue")
        queue(TYPE_INVDETAILS, str(number))
        queue(TYPE_IDENTIFY, str(number))
        return None

    def _skill_name(self, sn: int | str) -> str | None:
        """Return the name of a skill by sn, or None."""
        if not self._exists(API_SKILL_GET):
            return None
        skill = self.api(API_SKILL_GET)(sn)
        return str(skill["name"]) if skill and skill.get("name") else None

    def _box(self, item: dict[str, Any]) -> list[str]:
        """Return the lines of the item box, with where the item is now."""
        known = self._eq_item(_serial(item.get("serial")) or 0) or {}
        slot = known.get("wearslot")
        location = known.get("container")
        return format_item(
            item,
            str(location) if location else None,
            slot if isinstance(slot, int) else None,
            self._skill_name,
            self._strip,
        )

    @AddAPI("item.format", description="return the lines of the item box for an item dict")
    def _api_item_format(self, item: dict[str, Any], location: str | None = None) -> list[str]:
        """Return the lines of the item box; ``location`` defaults to where eq has the item."""
        if location is None:
            return self._box(item)
        return format_item(item, location, None, self._skill_name, self._strip)

    @AddAPI("item.show", description="show an item to the client, identifying it when needed")
    def _api_item_show(self, serial: int | str, database: bool = False) -> None:
        """Show the item box; identify first when the item is not cached."""
        lines = self._do_show(serial, database, False)
        if lines:
            self._client(lines)

    def _do_show(self, serial: int | str, database: bool, force: bool) -> list[str]:
        """Show an item, or start identifying it; return the messages for the user."""
        number = _serial(serial)
        if number is None:
            return [f"{serial} is not a serial number"]
        if database:
            if not self._exists(API_EQDB_ITEM_GET):
                return ["The eqdb plugin is not loaded, so there is no database to read"]
            item = self.api(API_EQDB_ITEM_GET)(number)
            if not item:
                return [f"{number} is not in the database"]
            self._client(self._box(dict(item)))
            return []
        if number in self._cache and not force:
            self._client(self._box(self._cache[number]))
            return []
        if self._eq_item(number) is None and number not in self._cache:
            return [f"Could not find {number}"]
        self._show.add(number)
        self._api_item_identify(number, force=force)
        return []

    # commands

    @AddCommand(format=False, preamble=False)
    @AddParser(description="identify an item and show it")
    @AddArgument("serial", help="the serial of the item", nargs="?", default="")
    @AddArgument("-f", "--force", help="identify the item again", action="store_true")
    @AddArgument("-d", "--database", help="show the item from the database", action="store_true")
    def _command_id(self) -> CommandResult:
        """Show an item, identifying it first when needed."""
        args = self._args()
        if not args.get("serial"):
            return CommandResult(True, ["Please supply a serial #"])
        return CommandResult(
            True,
            self._do_show(args["serial"], bool(args.get("database")), bool(args.get("force"))),
        )
