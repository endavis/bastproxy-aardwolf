"""The Aardwolf statmn plugin: the stats report and a message when an event completes."""

import logging
import sqlite3
import time
from typing import Any

from bastproxy.libs.logger import log_to
from bastproxy.libs.records import NetworkData, NetworkDataLine, SendDataDirectlyToClient
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.commands import AddArgument, AddCommand, AddParser, CommandResult
from bastproxy.plugins.core.events import RegisterToEvent

from aardwolf._libs.validate import int_validator

from ..libs import (
    CALLBACK_PRIORITY,
    DEFAULT_EXPPERMIN,
    DEFAULT_INFOCOLOR,
    DEFAULT_REPORTMINUTES,
    DEFAULT_SHOW,
    DEFAULT_STATCOLOR,
    EMPTYLINE_EVENT,
    EMPTYLINE_ID,
    EVENT_CP_COMP,
    EVENT_DISCONNECT,
    EVENT_GQ_COMPLETED,
    EVENT_GQ_DONE,
    EVENT_GQ_WON,
    EVENT_LEVEL_GAIN,
    EVENT_QUEST_COMP,
    LINE_LENGTH,
    NO_DB,
    SELECT_API,
    SETTING_LINE_LENGTH,
    Colors,
    Formatters,
    Rows,
    cp_message,
    gq_message,
    level_kills,
    level_message,
    level_window,
    quest_average,
    quest_message,
    report_lines,
    window_stats,
)


class StatmnPlugin(BasePlugin):
    """Show a report of the recent stats, and a message for each completed event."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Create the empty message queue."""
        self._msgs: list[str] = []
        # True while _flush is registered on the empty line trigger
        self._waiting = False

    @property
    def _report_timer(self) -> str:
        """The name of the report timer; timer names are global, so it carries the plugin id."""
        return f"{self.plugin_id}_report"

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the settings and start the report timer."""
        add = self.api("plugins.core.settings:setting.add")
        add(self.plugin_id, "statcolor", DEFAULT_STATCOLOR, "color", "the stat color")
        add(self.plugin_id, "infocolor", DEFAULT_INFOCOLOR, "color", "the info color")
        add(self.plugin_id, "show", DEFAULT_SHOW, "timelength", "show the report every x time")
        add(
            self.plugin_id,
            "reportminutes",
            DEFAULT_REPORTMINUTES,
            "timelength",
            "the length of time the report covers",
        )
        add(
            self.plugin_id,
            "exppermin",
            DEFAULT_EXPPERMIN,
            int,
            "the threshold for showing exp per minute",
        )
        add(
            self.plugin_id,
            SETTING_LINE_LENGTH,
            LINE_LENGTH,
            int,
            "the width of the report",
            validator=int_validator(1, 500),
        )
        self._schedule_report()

    @RegisterPluginHook("uninitialize", priority=10)
    def _phook_uninitialize(self) -> None:
        """Stop waiting for an empty line."""
        self._unregister_flush()

    # helpers

    def _setting(self, name: str) -> object:
        """Return the value of one of this plugin's settings."""
        return self.api("plugins.core.settings:setting.get")(self.plugin_id, name)

    def _colors(self) -> Colors:
        """Return the colours from the settings."""
        return Colors(str(self._setting("infocolor")), str(self._setting("statcolor")))

    def _formatters(self) -> Formatters:
        """Return the bastproxy helpers the text needs."""
        return Formatters(
            format_time=lambda seconds, nosec: self.api("plugins.core.utils:timelength.format")(
                seconds, nosec=nosec
            ),
            center=self.api("plugins.core.utils:string.center.colored"),
        )

    def _record(self) -> dict[str, Any]:
        """Return a copy of the current event's data."""
        return dict(self.api("plugins.core.events:event.current.record.get")() or {})

    def _client(self, lines: list[str]) -> None:
        """Send lines to the clients, without the preamble."""
        data = NetworkData(
            [NetworkDataLine(line, preamble=False) for line in lines],
            owner_id=f"{self.plugin_id}:notice",
        )
        SendDataDirectlyToClient(data)()

    def _select(self, sql: str, params: tuple[Any, ...]) -> Rows | None:
        """Run a select against statdb; None when its API is missing or the select failed."""
        if not self.api("libs.api:api.exists")(SELECT_API):
            return None
        try:
            return self.api(SELECT_API)(sql, params)  # type: ignore[no-any-return]
        except sqlite3.Error:
            log_to(self.plugin_id, logging.ERROR, "could not read the stats", exc_info=True)
            return None

    # the report

    def _report(self, window: float) -> list[str] | None:
        """Return the report for the last ``window`` seconds, or None when statdb has no data."""
        rows = window_stats(self._select, time.time() - window)
        if rows is None:
            return None
        line_length = int(str(self._setting(SETTING_LINE_LENGTH)))
        return report_lines(rows, window, self._colors(), self._formatters(), line_length)

    def _schedule_report(self) -> None:
        """Replace the report timer: it repeats every ``show`` seconds, and is off at 0."""
        if self.api("plugins.core.timers:timer.exists")(self._report_timer):
            self.api("plugins.core.timers:timer.remove")(self._report_timer)
        interval = self._setting("show")
        if isinstance(interval, int) and interval >= 1:
            self.api("plugins.core.timers:timer.add")(
                self._report_timer, self._timer_report, interval
            )

    def _timer_report(self) -> None:
        """Show the report to the clients while the MUD is connected."""
        if not self.api("plugins.core.proxy:mud.is.connected")():
            return
        window = self._setting("reportminutes")
        if not isinstance(window, int) or window < 1:
            return
        lines = self._report(window)
        if lines is not None:
            self._client(lines)

    @RegisterToEvent(event_name="ev_{plugin_id}_var_show_modified")
    def _eventcb_show_modified(self) -> None:
        """The report interval changed: start the timer again, or turn it off."""
        self._schedule_report()
        interval = self._setting("show")
        if not isinstance(interval, int) or interval < 1:
            self._client(["Turning off the statmon report"])

    @AddCommand(format=False, preamble=False)
    @AddParser(description="show the report")
    @AddArgument(
        "minutes",
        help="the length of time the report covers, ex. 30m; default is the reportminutes setting",
        default="",
        nargs="?",
    )
    def _command_rep(self) -> CommandResult:
        """Show the report."""
        args = self.api("plugins.core.commands:command.current.args.get")() or {}
        text = str(args.get("minutes") or "")
        window: object = self._setting("reportminutes")
        if text:
            try:
                window = self.api("plugins.core.utils:value.verify")(text, "timelength")
            except ValueError as exc:
                return CommandResult(False, [f"{text!r} is not a length of time: {exc}"])
        if not isinstance(window, int) or window < 1:
            return CommandResult(False, ["The report needs a length of time of 1 second or more"])
        lines = self._report(window)
        if lines is None:
            return CommandResult(True, [NO_DB])
        return CommandResult(True, lines)

    # the completion messages

    def _in_empty_line(self) -> bool:
        """Return True while the core is raising the empty-line event."""
        return EMPTYLINE_EVENT in self.api("plugins.core.events:event.stack.get")()

    def _queue(self, message: str) -> None:
        """Hold a message until the next empty line, or show it now during an empty line."""
        self._msgs.append(message)
        if self._waiting:
            return
        if self._in_empty_line():
            # registering on the event while it is running would run _flush out of order
            # in the same pass (#162), so show the message at this empty line directly
            self._flush()
            return
        registered = self.api("plugins.core.triggers:trigger.register")(EMPTYLINE_ID, self._flush)
        self._waiting = bool(registered)
        if not self._waiting:
            # without the trigger nothing would show the message
            self._flush()

    def _unregister_flush(self) -> None:
        """Stop waiting for an empty line, when waiting."""
        if self._waiting:
            self.api("plugins.core.triggers:trigger.unregister")(EMPTYLINE_ID, self._flush)
            self._waiting = False

    def _flush(self) -> None:
        """Show the held messages to the clients."""
        self._unregister_flush()
        messages, self._msgs = self._msgs, []
        if messages:
            self._client(messages)

    @RegisterToEvent(event_name=EVENT_DISCONNECT)
    def _eventcb_disconnect(self) -> None:
        """The MUD link closed: show what is held, as no empty line may follow."""
        self._flush()

    @RegisterToEvent(event_name=EVENT_QUEST_COMP, priority=CALLBACK_PRIORITY)
    def _eventcb_quest_comp(self) -> None:
        """Queue the message for a finished quest."""
        self._queue(
            quest_message(
                self._record(),
                self._colors(),
                self._formatters(),
                quest_average(self._select),
            )
        )

    @RegisterToEvent(event_name=EVENT_CP_COMP, priority=CALLBACK_PRIORITY)
    def _eventcb_cp_comp(self) -> None:
        """Queue the message for a finished campaign."""
        self._queue(cp_message(self._record(), self._colors(), self._formatters()))

    @RegisterToEvent(event_name=EVENT_GQ_WON, priority=CALLBACK_PRIORITY)
    @RegisterToEvent(event_name=EVENT_GQ_COMPLETED, priority=CALLBACK_PRIORITY)
    @RegisterToEvent(event_name=EVENT_GQ_DONE, priority=CALLBACK_PRIORITY)
    def _eventcb_gq(self) -> None:
        """Queue the message for a finished global quest."""
        self._queue(gq_message(self._record(), self._colors(), self._formatters()))

    @RegisterToEvent(event_name=EVENT_LEVEL_GAIN, priority=CALLBACK_PRIORITY)
    def _eventcb_level_gain(self) -> None:
        """Queue the message for a level or a pup, with the mobs killed during it."""
        record = self._record()
        start = record.get("starttime")
        window = (
            level_window(self._select, float(start)) if isinstance(start, int | float) else None
        )
        kills = None
        if window is not None and isinstance(start, int | float):
            kills = level_kills(self._select, start - window, float(start))
        perlevel = self.api("libs.net.protocols:gmcp.value.get")("char.base.perlevel")
        exppermin = self._setting("exppermin")
        self._queue(
            level_message(
                record,
                self._colors(),
                self._formatters(),
                window,
                kills,
                perlevel,
                exppermin if isinstance(exppermin, int) else DEFAULT_EXPPERMIN,
            )
        )
