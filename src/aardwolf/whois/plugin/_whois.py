"""Aardwolf whois plugin: parse the whois command output and raise it as an event."""

import copy
import logging
from collections.abc import Callable
from typing import Any

from bastproxy.libs.logger import get_logger, log_to
from bastproxy.libs.persistentdict import PersistentDict
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.events import RegisterToEvent

from ..libs import (
    CLASSES_REGEX,
    END_REGEX,
    HEADER_REGEX,
    POWERUP_REGEX,
    STAT1_REGEX,
    STAT2_REGEX,
    STAT3_REGEX,
    WHOIS_COMMAND_REGEX,
    header_values,
    multiclass_classes,
    single_class,
    stat_values,
    total_levels,
)

EVENT_WHOIS = "ev_plugins.aardwolf.whois_received"
EVENT_WATCH = "watch_whois"
EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"
EVENT_CHAR_ACTIVE = "ev_libs.api_character_active"
WHOIS_NAME = "whois"
END_TRIGGER = "whoisend"

EVENT_ARGS = {
    "name": "the name of the character",
    "level": "the level within the remort",
    "tiers": "the tiers",
    "redos": "the redos",
    "race": "the race, in lower case",
    "sex": "the sex, in lower case",
    "subclass": "the subclass, in lower case",
    "remorts": "the number of remorts",
    "classes": "a list of the classes, each with a remort and a class abbreviation",
    "powerupsall": "the powerups of all kinds",
    "powerupsmort": "the powerups of the mortal kind",
    "totallevels": "the total level",
    "stats": "one key per stat line, named for the stat in lower case without spaces",
}


class WhoisPlugin(BasePlugin):
    """Parse the output of the whois command into a saved state and raise it as an event."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Load the saved whois state."""
        self.whois = PersistentDict(
            self.plugin_id, self.plugin_info.data_directory / "whois.txt", "c"
        )
        self._group_ready = False
        self._end_ready = False

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the event, the watch, the command type and the triggers."""
        self.api("plugins.core.events:event.add")(
            EVENT_WHOIS,
            self.plugin_id,
            description=["raised with the parsed whois data after the whois output ends"],
            arg_descriptions=EVENT_ARGS,
        )
        self.api("plugins.core.watch:watch.add")(WHOIS_NAME, WHOIS_COMMAND_REGEX)
        self.api("plugins.core.events:event.register")(EVENT_WATCH, self._eventcb_whois_sent)
        self.api("plugins.core.mudcmds:type.add")(
            WHOIS_NAME, WHOIS_NAME, WHOIS_COMMAND_REGEX, beforef=self._start_whois
        )

        self._add_trigger("whoisheader", HEADER_REGEX, self._trigger_header, grouped=True)
        self._add_trigger("whoisclasses", CLASSES_REGEX, self._trigger_classes, grouped=True)
        self._add_trigger("whois1", STAT1_REGEX, self._trigger_stats, grouped=True)
        self._add_trigger("whois2", STAT2_REGEX, self._trigger_stats, grouped=True)
        self._add_trigger("whois3", STAT3_REGEX, self._trigger_stats, grouped=True)
        self._add_trigger("whoispowerup", POWERUP_REGEX, self._trigger_stats, grouped=True)
        # not in the group: it is turned on at the header, so the dashed line above it cannot end
        self._add_trigger(END_TRIGGER, END_REGEX, self._trigger_end, grouped=False)
        if self.api("libs.api:character.is.active")():
            self._queue_whois()

    def _queue_whois(self) -> None:
        """Queue a whois for the MUD."""
        self.api("plugins.core.mudcmds:command.queue")(WHOIS_NAME)

    @RegisterToEvent(event_name=EVENT_CHAR_ACTIVE)
    def _eventcb_character_active(self) -> None:
        """The character is first active: queue a whois."""
        record = self.api("plugins.core.events:event.current.record.get")() or {}
        if record.get("is_character_active"):
            self._queue_whois()

    def _add_trigger(self, name: str, regex: str, func: Callable[[], None], grouped: bool) -> None:
        """Add a disabled trigger and register its callback."""
        kwargs: dict[str, Any] = {"enabled": False}
        if grouped:
            kwargs["group"] = self.plugin_id
        result = self.api("plugins.core.triggers:trigger.add")(name, regex, **kwargs)
        if not result.success:
            get_logger(self.plugin_id).error("could not add the %s trigger", name)
            return
        self.api("plugins.core.triggers:trigger.register")(result.trigger.trigger_id, func)
        if grouped:
            self._group_ready = True
        else:
            self._end_ready = True

    def _toggle_triggers(self, flag: bool, end: bool | None = None) -> None:
        """Turn the group on or off, and the end trigger when end is given."""
        if self._group_ready:
            self.api("plugins.core.triggers:group.toggle.enable")(self.plugin_id, flag)
        if end is not None and self._end_ready:
            self.api("plugins.core.triggers:trigger.toggle.enable")(END_TRIGGER, end)

    def _start_whois(self) -> None:
        """Clear the state and turn the group on for the whois that is about to arrive."""
        self.whois.clear()
        self._toggle_triggers(True)

    def _eventcb_whois_sent(self) -> None:
        """A client typed whois."""
        self._start_whois()

    @RegisterToEvent(event_name=EVENT_DISCONNECT)
    def _eventcb_disconnect(self) -> None:
        """Turn the triggers off so a whois cut off by a disconnect does not leave them on."""
        self._toggle_triggers(False, end=False)

    def _gmcp_value(self, path: str) -> object:
        """Return the cached GMCP value at a dotted path, or None."""
        return self.api("libs.net.protocols:gmcp.value.get")(path)

    def _matches(self) -> dict[str, Any]:
        """Return the groups the current trigger matched."""
        record = self.api("plugins.core.events:event.current.record.get")()
        return dict(record.get("matches") or {})

    def _trigger_header(self) -> None:
        """Set the state from GMCP and turn the end trigger on."""
        sex = self._matches().get("sex") or ""
        self.whois.update(header_values(self._gmcp_value, str(sex)))
        if self.whois["remorts"] == 1:
            self.whois["classes"] = single_class(self._gmcp_value("char.base.class"))
        self._toggle_triggers(True, end=True)

    def _trigger_classes(self) -> None:
        """Set the classes of a multiclass character."""
        classes = multiclass_classes(str(self._matches().get("classes") or ""))
        self.whois["classes"] = classes
        self.whois["remorts"] = len(classes)

    def _trigger_stats(self) -> None:
        """Add the stats of a stat line."""
        self.whois.update(stat_values(self._matches()))

    def _trigger_end(self) -> None:
        """Finish the whois: save the state, turn the triggers off and raise the event."""
        self.whois["totallevels"] = total_levels(self.whois)
        self.whois.sync()
        self._toggle_triggers(False, end=False)
        self.api("plugins.core.events:event.raise")(
            EVENT_WHOIS, event_args=copy.deepcopy(dict(self.whois))
        )
        self.api("plugins.core.mudcmds:command.finish")(WHOIS_NAME)
        log_to(self.plugin_id, logging.DEBUG, "whois: %s", dict(self.whois))

    @RegisterPluginHook("save")
    def _phook_save(self) -> None:
        """Save the whois state."""
        self.whois.sync()
