"""Aardwolf daily plugin: raise an event when the daily blessing is available."""

import logging
import time
from collections.abc import Callable

from bastproxy.libs.logger import get_logger, log_to
from bastproxy.libs.records import NetworkData, SendDataDirectlyToMud
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.commands import AddCommand, AddParser, CommandResult
from bastproxy.plugins.core.events import RegisterToEvent

from aardwolf._libs.eventu import own_event, own_events
from aardwolf._libs.validate import time_format_error

from ..libs import (
    BLESSING_WAIT,
    DAILY_CMD,
    EVENTS,
    SETTING_TIME_FORMAT,
    SUFFIX_AVAILABLE,
    TIME_FORMAT,
    TIMER_NAME,
    TRIGGER_READY,
    TRIGGER_TOOK,
    TRIGGER_WAIT,
    TRIGGERS,
    is_active_state,
    next_message,
    parse_wait,
)

EVENT_CHAR_ACTIVE = "ev_libs.api_character_active"
STATE_PATH = "char.status.state"


class DailyPlugin(BasePlugin):
    """Raise an event when the daily blessing can be received, and show when it is."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Start with nothing known about the daily."""
        self._next_time: float | None = None
        self._available = False

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the setting, event and triggers, and check the daily when the character is active."""
        self.api("plugins.core.settings:setting.add")(
            self.plugin_id,
            SETTING_TIME_FORMAT,
            TIME_FORMAT,
            str,
            "the strftime pattern of the time the next command shows",
            nocolor=True,
            validator=time_format_error,
        )
        add_event = self.api("plugins.core.events:event.add")
        for event_name, info in own_events(self.plugin_id, EVENTS).items():
            add_event(
                event_name,
                self.plugin_id,
                description=info["description"],
                arg_descriptions=info["arg_descriptions"],
            )
        callbacks: dict[str, Callable[[], None]] = {
            TRIGGER_WAIT: self._trigger_wait,
            TRIGGER_READY: self._trigger_ready,
            TRIGGER_TOOK: self._trigger_took,
        }
        for spec in TRIGGERS:
            result = self.api("plugins.core.triggers:trigger.add")(spec.name, spec.regex)
            if not result.success:
                get_logger(self.plugin_id).error("could not add the %s trigger", spec.name)
                continue
            self.api("plugins.core.triggers:trigger.register")(
                result.trigger.trigger_id, callbacks[spec.name]
            )
        if self.api("libs.api:character.is.active")():
            self._check()

    # scheduling

    def _schedule(self, seconds: int) -> None:
        """Remember when the daily is next available and arm the timer for it."""
        self._remove_timer()
        if seconds < 1:
            self._set_available()
            return
        self._available = False
        self._next_time = time.time() + seconds
        self.api("plugins.core.timers:timer.add")(
            TIMER_NAME, self._timer_available, seconds, onetime=True
        )
        log_to(self.plugin_id, logging.DEBUG, "daily blessing timer set for %d seconds", seconds)

    def _remove_timer(self) -> None:
        """Remove the timer when there is one (timer.remove logs an error for a missing one)."""
        if self.api("plugins.core.timers:timer.exists")(TIMER_NAME):
            self.api("plugins.core.timers:timer.remove")(TIMER_NAME)

    def _set_available(self) -> None:
        """The daily can be received: forget the next time and raise the event."""
        self._remove_timer()
        self._next_time = None
        self._available = True
        self.api("plugins.core.events:event.raise")(own_event(self.plugin_id, SUFFIX_AVAILABLE))

    def _timer_available(self) -> None:
        """The timer fired."""
        self._set_available()

    # triggers

    def _trigger_wait(self) -> None:
        """A line says how long until the next daily."""
        record = self.api("plugins.core.events:event.current.record.get")() or {}
        seconds = parse_wait((record.get("matches") or {}).get("wait"))
        if seconds is None:
            log_to(self.plugin_id, logging.DEBUG, "daily wait line could not be read")
            return
        self._schedule(seconds)

    def _trigger_ready(self) -> None:
        """A line says the daily can be received now."""
        self._set_available()

    def _trigger_took(self) -> None:
        """The daily was received: the next one is after the blessing wait."""
        self._schedule(BLESSING_WAIT)

    # active character

    @RegisterToEvent(event_name=EVENT_CHAR_ACTIVE)
    def _eventcb_character_active(self) -> None:
        """The character is first active: check the daily."""
        record = self.api("plugins.core.events:event.current.record.get")() or {}
        if record.get("is_character_active"):
            self._check()

    def _check(self) -> None:
        """Send daily when the character is active, nothing is known and it is not available."""
        if self._next_time is not None or self._available:
            return
        state = self.api("libs.net.protocols:gmcp.value.get")(STATE_PATH)
        if is_active_state(state):
            self._send_to_mud(DAILY_CMD)

    def _send_to_mud(self, line: str) -> None:
        """Send a line straight to the mud."""
        SendDataDirectlyToMud(NetworkData([line], owner_id=f"{self.plugin_id}:_send_to_mud"))()

    # commands

    @AddCommand()
    @AddParser(description="show when the next daily is")
    def _command_next(self) -> CommandResult:
        """Show when the next daily is."""
        time_format = str(
            self.api("plugins.core.settings:setting.get")(self.plugin_id, SETTING_TIME_FORMAT)
        )
        return CommandResult(True, [next_message(self._next_time, self._available, time_format)])
