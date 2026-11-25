"""Aardwolf scanh plugin: highlight the cp, gq and quest mobs in the scan output."""

import logging
from collections.abc import Callable
from typing import Any

from bastproxy.libs.logger import get_logger, log_to
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.events import RegisterToEvent

from ..libs import (
    API_A102_TAG_TOGGLE,
    CP_MOBS_API,
    CP_ONCP_API,
    EVENT_CP_COMP,
    EVENT_CP_FAILED,
    EVENT_CP_MOBSLEFT,
    EVENT_DISCONNECT,
    EVENT_GQ_CANCELLED,
    EVENT_GQ_COMPLETED,
    EVENT_GQ_DONE,
    EVENT_GQ_MOBSLEFT,
    EVENT_GQ_WON,
    EVENT_QUEST_COMP,
    EVENT_QUEST_FAILED,
    EVENT_QUEST_KILLED,
    EVENT_QUEST_RESET,
    EVENT_QUEST_START,
    GROUP_SCAN,
    SCAN_END_REGEX,
    SCAN_LINE_REGEX,
    SCAN_START_REGEX,
    SCAN_TAG,
    SETTINGS,
    TRIGGER_END,
    TRIGGER_LINE,
    TRIGGER_START,
    highlight,
    matching_sources,
    mob_names,
)


class ScanhPlugin(BasePlugin):
    """Rewrite the scan lines that end with a cp, gq or quest mob."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Start with no targets."""
        self.targets: dict[str, list[str]] = {}
        self._group_ready = False
        self._scan_tag_on = False
        self.attributes_to_save_on_reload = ["_scan_tag_on"]

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the settings and the triggers, and read the campaign when it is there."""
        for name, default, help_text in SETTINGS:
            self.api("plugins.core.settings:setting.add")(
                self.plugin_id, name, default, "color", help_text
            )
        self._add_trigger(TRIGGER_START, SCAN_START_REGEX, self._trigger_start, False, omit=True)
        self._add_trigger(TRIGGER_END, SCAN_END_REGEX, self._trigger_end, True, omit=True)
        self._add_trigger(TRIGGER_LINE, SCAN_LINE_REGEX, self._trigger_line, True)
        self._load_cp_targets()
        if not self._scan_tag_on:
            self._scan_tag_on = bool(self.api(API_A102_TAG_TOGGLE)(SCAN_TAG, True))

    # Runs before the base uninitialize hook (priority 100).
    @RegisterPluginHook("uninitialize", priority=10)
    def _phook_uninitialize(self) -> None:
        """On a real unload, release the SCAN tag; a reload keeps it, to not resend commands."""
        if self.is_reloading_f or not self._scan_tag_on:
            return
        self._scan_tag_on = False
        self.api(API_A102_TAG_TOGGLE)(SCAN_TAG, False)

    def _group(self) -> str:
        """Return the trigger group name; group names are global, so it carries the plugin id."""
        return f"{self.plugin_id}.{GROUP_SCAN}"

    def _add_trigger(
        self, name: str, regex: str, func: Callable[[], None], grouped: bool, omit: bool = False
    ) -> None:
        """Add a trigger and register its callback; the grouped ones start disabled."""
        kwargs: dict[str, Any] = {}
        if omit:
            kwargs["omit"] = True
        if grouped:
            kwargs["enabled"] = False
            kwargs["group"] = self._group()
        result = self.api("plugins.core.triggers:trigger.add")(name, regex, **kwargs)
        if not result.success:
            get_logger(self.plugin_id).error("could not add the %s trigger", name)
            return
        self.api("plugins.core.triggers:trigger.register")(result.trigger.trigger_id, func)
        if grouped:
            self._group_ready = True

    def _toggle_group(self, flag: bool) -> None:
        """Turn the scan trigger group on or off, when it exists."""
        if self._group_ready:
            self.api("plugins.core.triggers:group.toggle.enable")(self._group(), flag)

    def _load_cp_targets(self) -> None:
        """Read the mobs left of a campaign that started before the plugin loaded."""
        if self.api("libs.api:api.exists")(CP_MOBS_API) and self._on_campaign():
            self.targets["cp"] = mob_names(self.api(CP_MOBS_API)())

    def _on_campaign(self) -> bool:
        """Return True when the cp plugin is loaded and says the character is on a campaign."""
        if not self.api("libs.api:api.exists")(CP_ONCP_API):
            return False
        return bool(self.api(CP_ONCP_API)())

    def _record(self) -> dict[str, Any]:
        """Return the record of the current event."""
        return dict(self.api("plugins.core.events:event.current.record.get")() or {})

    def _setting(self, name: str) -> str:
        """Return the value of a setting of the plugin."""
        return str(self.api("plugins.core.settings:setting.get")(self.plugin_id, name))

    def _trigger_start(self) -> None:
        """The scan starts: look at its lines."""
        if not self._on_campaign():
            self._clear("cp")
        log_to([self.plugin_id], logging.DEBUG, "found {scan}")
        self._toggle_group(True)

    def _trigger_end(self) -> None:
        """The scan ends: stop looking at lines."""
        log_to([self.plugin_id], logging.DEBUG, "found {/scan}")
        self._toggle_group(False)

    def _trigger_line(self) -> None:
        """Rewrite a scan line that ends with a target."""
        if not any(self.targets.values()):
            return
        line = self._record().get("line")
        if line is None or not isinstance(line.line, str) or line.mxp_mode is not None:
            return
        text = str(line.noansi)
        sources = matching_sources(text, self.targets)
        if not sources:
            return
        first = sources[0]
        escaped = str(self.api("plugins.core.colors:colorcode.escape")(text))
        coloured = highlight(
            escaped, sources, self._setting(first.textsetting), self._setting(first.backsetting)
        )
        line.line = self.api("plugins.core.colors:colorcode.to.ansicode")(coloured)
        log_to([self.plugin_id], logging.DEBUG, "highlighted %s", [s.tag for s in sources])

    def _set(self, key: str, names: list[str]) -> None:
        """Set the targets of a source."""
        self.targets[key] = names

    def _clear(self, key: str) -> None:
        """Forget the targets of a source."""
        log_to([self.plugin_id], logging.DEBUG, "clearing the %s mobs", key)
        self.targets.pop(key, None)

    @RegisterToEvent(event_name=EVENT_CP_MOBSLEFT)
    def _eventcb_cp_mobsleft(self) -> None:
        """The campaign mobs left changed."""
        self._set("cp", mob_names(self._record().get("mobsleft")))

    @RegisterToEvent(event_name=EVENT_GQ_MOBSLEFT)
    def _eventcb_gq_mobsleft(self) -> None:
        """The global quest mobs left changed."""
        self._set("gq", mob_names(self._record().get("mobsleft")))

    @RegisterToEvent(event_name=EVENT_QUEST_START)
    def _eventcb_quest_start(self) -> None:
        """A quest started: its mob is the target."""
        self._set("quest", mob_names([{"name": self._record().get("mobname")}]))

    @RegisterToEvent(event_name=EVENT_CP_COMP)
    def _eventcb_cp_comp(self) -> None:
        """The campaign is complete."""
        self._clear("cp")

    @RegisterToEvent(event_name=EVENT_CP_FAILED)
    def _eventcb_cp_failed(self) -> None:
        """The campaign failed."""
        self._clear("cp")

    @RegisterToEvent(event_name=EVENT_GQ_DONE)
    def _eventcb_gq_done(self) -> None:
        """The global quest is done."""
        self._clear("gq")

    @RegisterToEvent(event_name=EVENT_GQ_WON)
    def _eventcb_gq_won(self) -> None:
        """The global quest was won."""
        self._clear("gq")

    @RegisterToEvent(event_name=EVENT_GQ_COMPLETED)
    def _eventcb_gq_completed(self) -> None:
        """The global quest is completed."""
        self._clear("gq")

    @RegisterToEvent(event_name=EVENT_GQ_CANCELLED)
    def _eventcb_gq_cancelled(self) -> None:
        """The global quest was cancelled."""
        self._clear("gq")

    @RegisterToEvent(event_name=EVENT_QUEST_KILLED)
    def _eventcb_quest_killed(self) -> None:
        """The quest mob was killed."""
        self._clear("quest")

    @RegisterToEvent(event_name=EVENT_QUEST_COMP)
    def _eventcb_quest_comp(self) -> None:
        """The quest is complete."""
        self._clear("quest")

    @RegisterToEvent(event_name=EVENT_QUEST_FAILED)
    def _eventcb_quest_failed(self) -> None:
        """The quest failed or timed out."""
        self._clear("quest")

    @RegisterToEvent(event_name=EVENT_QUEST_RESET)
    def _eventcb_quest_reset(self) -> None:
        """The quest was reset."""
        self._clear("quest")

    @RegisterToEvent(event_name=EVENT_DISCONNECT)
    def _eventcb_disconnect(self) -> None:
        """The mud disconnected: a scan cut short must not leave the group on."""
        self._toggle_group(False)
