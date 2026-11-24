"""Aardwolf iceage plugin: raise events for Ice Age and reboot countdown lines."""

import logging
from collections.abc import Callable
from typing import Any

from bastproxy.libs.logger import get_logger, log_to
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook

from ..libs import EVENT_ICEAGE, EVENT_REBOOT, EVENTS, TRIGGERS, minutes


class IceAgePlugin(BasePlugin):
    """Raise an event for each Ice Age and reboot countdown line, with the minutes left."""

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the events and the triggers."""
        add_event = self.api("plugins.core.events:event.add")
        for event_name, info in EVENTS.items():
            add_event(
                event_name,
                self.plugin_id,
                description=info["description"],
                arg_descriptions=info["arg_descriptions"],
            )
        callbacks: dict[str, Callable[[], None]] = {
            EVENT_ICEAGE: self._trigger_iceage,
            EVENT_REBOOT: self._trigger_reboot,
        }
        for spec in TRIGGERS:
            result = self.api("plugins.core.triggers:trigger.add")(
                spec.name, spec.regex, argtypes={"minutes": int}
            )
            if not result.success:
                get_logger(self.plugin_id).error("could not add the %s trigger", spec.name)
                continue
            self.api("plugins.core.triggers:trigger.register")(
                result.trigger.trigger_id, callbacks[spec.event]
            )

    def _matches(self) -> dict[str, Any]:
        """Return the groups the current trigger matched."""
        record = self.api("plugins.core.events:event.current.record.get")() or {}
        return dict(record.get("matches") or {})

    def _raise(self, event_name: str, what: str) -> None:
        """Raise an event with the minutes of the current match, when they are valid."""
        left = minutes(self._matches().get("minutes"))
        if left is None:
            log_to([self.plugin_id], logging.DEBUG, "%s line without valid minutes", what)
            return
        log_to([self.plugin_id], logging.DEBUG, "%s imminent: %d minutes", what, left)
        self.api("plugins.core.events:event.raise")(event_name, event_args={"minutes": left})

    def _trigger_iceage(self) -> None:
        """An Ice Age countdown line."""
        self._raise(EVENT_ICEAGE, "Ice Age")

    def _trigger_reboot(self) -> None:
        """A reboot countdown line."""
        self._raise(EVENT_REBOOT, "Reboot")
