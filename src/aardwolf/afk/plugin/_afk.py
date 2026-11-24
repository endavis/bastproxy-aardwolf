"""Aardwolf afk plugin: set a title and keep the tells while no client is playing."""

import time
from typing import Any

from bastproxy.libs.logger import get_logger
from bastproxy.libs.persistentdict import PersistentDict
from bastproxy.libs.records import NetworkData, NetworkDataLine, SendDataDirectlyToClient
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.commands import AddCommand, AddParser, CommandResult
from bastproxy.plugins.core.events import RegisterToEvent

from ..libs import (
    DEFAULT_AFK_TITLE,
    EVENT_CLIENT_DISCONNECTED,
    EVENT_CLIENT_LOGGED_IN,
    EVENT_DISCONNECT,
    EVENT_GMCP_COMM,
    GMCP_MODULES,
    GROUP_REPLY,
    HIDE_MAX,
    QUEUE_KEY,
    TIMEOUT_EVENT,
    TITLE_CMD,
    TITLE_REGEX,
    TITLE_SET_REGEX,
    TRIGGERS,
    TYPE_TITLE,
    WATCH_NAME,
    WATCH_TITLE_REGEX,
    TriggerSpec,
    count_active,
    format_tells,
    queue_notice,
    remember_title,
    tell_entry,
    title_to_send,
)


class AfkPlugin(BasePlugin):
    """Turn AFK on when the last client that can play leaves and off when one logs in."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Load the kept tells and create the empty state."""
        self.tells = PersistentDict(
            self.plugin_id, self.plugin_info.data_directory / "tells.txt", "c"
        )
        # True while a queued title is in flight, so its reply finishes the command
        self._queued_title = False
        # the title a client typed and the MUD has not answered yet
        self._pending_title: str | None = None
        self._groups_ready = False

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the settings, the command type, the watch, the reply trigger and the handlers."""
        add = self.api("plugins.core.settings:setting.add")
        add(self.plugin_id, "afktitle", DEFAULT_AFK_TITLE, str, "the title when afk mode is on")
        add(self.plugin_id, "lasttitle", "", str, "the title before afk mode was turned on")
        add(self.plugin_id, "isafk", False, bool, "AFK flag", readonly=True)
        self.api("libs.net.protocols:gmcp.modules.add")(GMCP_MODULES)
        self._add_type()
        for trigger in TRIGGERS:
            self._add_trigger(trigger)
        self.api("plugins.core.watch:watch.add")(WATCH_NAME, WATCH_TITLE_REGEX)
        register = self.api("plugins.core.events:event.register")
        register(f"watch_{WATCH_NAME}", self._watch_title)
        register(TIMEOUT_EVENT.format(TYPE_TITLE), self._eventcb_title_timeout)
        # the plugin may load after the clients; no title is sent for what is already so
        self._store_afk(self._active_count() == 0)

    @RegisterPluginHook("character_active")
    def _phook_character_active(self) -> None:
        """The character is active: send the title that fits the AFK state."""
        self._send_title()

    @RegisterPluginHook("save")
    def _phook_save(self) -> None:
        """Save the kept tells."""
        self.tells.sync()

    # setup helpers

    def _add_type(self) -> None:
        """Add the title command type, which hides its output when it is queued."""
        self.api("plugins.core.mudcmds:type.add")(
            TYPE_TITLE,
            TITLE_CMD,
            TITLE_REGEX,
            # beforef runs only for a queued command, so a typed title is shown
            beforef=self._command_started,
            hide_output=True,
            hide_start=TITLE_SET_REGEX,
            hide_max=HIDE_MAX,
        )

    def _add_trigger(self, spec: TriggerSpec) -> None:
        """Add a trigger, off, in its group, and register its callback."""
        result = self.api("plugins.core.triggers:trigger.add")(
            spec.name, spec.regex, enabled=False, group=self._group(spec.group)
        )
        if not result.success:
            get_logger(self.plugin_id).error("could not add the %s trigger", spec.name)
            return
        self.api("plugins.core.triggers:trigger.register")(
            result.trigger.trigger_id, self._trigger_reply
        )
        self._groups_ready = True

    def _group(self, suffix: str) -> str:
        """Return the trigger group name; group names are global, so it carries the plugin id."""
        return f"{self.plugin_id}.{suffix}"

    def _toggle(self, flag: bool) -> None:
        """Turn the reply trigger group on or off, when the triggers exist."""
        if self._groups_ready:
            self.api("plugins.core.triggers:group.toggle.enable")(self._group(GROUP_REPLY), flag)

    def _record(self) -> dict[str, Any]:
        """Return the record of the current event."""
        return dict(self.api("plugins.core.events:event.current.record.get")() or {})

    def _setting(self, name: str) -> object:
        """Return a setting of the plugin."""
        return self.api("plugins.core.settings:setting.get")(self.plugin_id, name)

    def _client(self, lines: list[str]) -> None:
        """Send lines to the clients, without the preamble."""
        data = NetworkData(
            [NetworkDataLine(line, preamble=False) for line in lines],
            owner_id=f"{self.plugin_id}:notice",
        )
        SendDataDirectlyToClient(data)()

    # the clients

    def _active_count(self) -> int:
        """Return how many clients are logged in and can play."""
        uuids = self.api("plugins.core.clients:client.list")(uuid_only=True)
        logged_in = self.api("plugins.core.clients:client.is.logged.in")
        view_only = self.api("plugins.core.clients:client.is.view.client")
        return count_active((bool(logged_in(uuid)), bool(view_only(uuid))) for uuid in uuids)

    def _store_afk(self, flag: bool) -> None:
        """Store the AFK flag when it changes, without sending a title."""
        if bool(self._setting("isafk")) != flag:
            self.api("plugins.core.settings:setting.set")(self.plugin_id, "isafk", flag)

    def _set_afk(self, flag: bool) -> bool:
        """Turn AFK on or off; nothing happens when it is already so. Return True on a change."""
        if bool(self._setting("isafk")) == flag:
            return False
        self.api("plugins.core.settings:setting.set")(self.plugin_id, "isafk", flag)
        get_logger(self.plugin_id).debug("afk is now %s", flag)
        self._send_title()
        if not flag and (notice := queue_notice(len(self._entries()))):
            self._client(notice)
        return True

    def _send_title(self) -> None:
        """Queue the title that fits the AFK state, when the MUD is connected and there is one."""
        if not self.api("plugins.core.proxy:mud.is.connected")():
            return
        title = title_to_send(
            bool(self._setting("isafk")),
            str(self._setting("afktitle")),
            str(self._setting("lasttitle")),
        )
        if title is not None:
            self.api("plugins.core.mudcmds:command.queue")(TYPE_TITLE, title)

    @RegisterToEvent(event_name=EVENT_CLIENT_DISCONNECTED)
    def _eventcb_client_disconnected(self) -> None:
        """A client left: when none that can play is left, turn AFK on."""
        if self._active_count() == 0:
            self._set_afk(True)

    @RegisterToEvent(event_name=EVENT_CLIENT_LOGGED_IN)
    def _eventcb_client_logged_in(self) -> None:
        """A client that can play logged in: turn AFK off. A view client raises another event."""
        self._set_afk(False)

    # the title

    def _command_started(self) -> None:
        """The queue is sending a title: start its timing and read its reply."""
        self.api("plugins.core.mudcmds:command.start")(TYPE_TITLE)
        self._queued_title = True
        # a typed title that was never answered must not be taken for this one
        self._pending_title = None
        self._toggle(True)

    def _watch_title(self) -> None:
        """A client typed a title: remember it and read the reply."""
        title = self._record().get("matched", {}).get("title")
        self._pending_title = str(title) if title is not None else None
        self._toggle(True)

    def _trigger_reply(self) -> None:
        """The MUD confirmed a title: finish the queued one, else remember the typed one."""
        self._toggle(False)
        if self._queued_title:
            self._queued_title = False
            self.api("plugins.core.mudcmds:command.finish")(TYPE_TITLE)
            return
        typed, self._pending_title = self._pending_title, None
        keep = remember_title(typed, str(self._setting("afktitle")))
        if keep is not None:
            self.api("plugins.core.settings:setting.set")(self.plugin_id, "lasttitle", keep)

    def _eventcb_title_timeout(self) -> None:
        """No reply matched: the queue is freed by the timeout, so stop reading."""
        get_logger(self.plugin_id).debug("no reply to a title matched, timed out")
        self._queued_title = False
        self._toggle(False)

    @RegisterToEvent(event_name=EVENT_DISCONNECT)
    def _eventcb_disconnect(self) -> None:
        """The MUD link closed: forget the title in flight and stop reading a reply."""
        self._queued_title = False
        self._pending_title = None
        self._toggle(False)

    # the tells

    def _entries(self) -> list[Any]:
        """Return the kept tells."""
        entries = self.tells.get(QUEUE_KEY)
        return entries if isinstance(entries, list) else []

    @RegisterToEvent(event_name=EVENT_GMCP_COMM)
    def _eventcb_comm(self) -> None:
        """A GMCP comm.channel message: keep it when it is a tell and AFK is on."""
        if not self._setting("isafk"):
            return
        entry = tell_entry(self._record().get("data"), time.time())
        if entry is None:
            return
        entries = self._entries()
        entries.append(entry)
        self.tells[QUEUE_KEY] = entries
        self.tells.sync()

    # commands

    @AddCommand()
    @AddParser(description="show the tells received while afk")
    def _command_show(self) -> CommandResult:
        """Show the kept tells."""
        return CommandResult(True, format_tells(self._entries()))

    @AddCommand()
    @AddParser(description="clear the tells received while afk")
    def _command_clear(self) -> CommandResult:
        """Forget the kept tells."""
        self.tells[QUEUE_KEY] = []
        self.tells.sync()
        return CommandResult(True, ["AFK tell queue cleared"])

    @AddCommand()
    @AddParser(description="toggle afk mode")
    def _command_toggle(self) -> CommandResult:
        """Turn AFK on or off by hand."""
        flag = not self._setting("isafk")
        self._set_afk(flag)
        return CommandResult(True, [f"AFK is now {'on' if flag else 'off'}"])
