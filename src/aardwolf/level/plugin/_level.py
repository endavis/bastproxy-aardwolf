"""Aardwolf level plugin: detect levels, powerups, remorts and tiers and raise them as events."""

import copy
import logging
import time
from collections.abc import Callable
from typing import Any

from bastproxy.libs.logger import get_logger, log_to
from bastproxy.libs.persistentdict import PersistentDict
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.events import RegisterToEvent

from aardwolf._libs import aardu

from ..libs import (
    EMPTYLINE_ID,
    EVENT_DISCONNECT,
    EVENT_GAIN,
    EVENT_GMCP_BASE,
    EVENT_GMCP_STATUS,
    EVENT_HERO,
    EVENT_PREREMORT,
    EVENT_REMORT,
    EVENT_SUPERHERO,
    EVENT_TIER,
    EVENTS,
    GROUP_LINFO,
    GROUP_SUPERHERO,
    TRIGGERS,
    WATCHES,
    TriggerSpec,
    bonus_stat_key,
    new_record,
    should_finish,
    to_int,
)

_SETTINGS = {
    "preremort": "flag for pre remort",
    "remortcomp": "flag for remort completion",
    "tiering": "flag for tiering",
    "seen2": "we saw a state 2 after tiering",
}


class LevelPlugin(BasePlugin):
    """Collect the gains of a level or powerup and raise events when it finishes."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Load the saved level record."""
        self.levelinfo = PersistentDict(
            self.plugin_id, self.plugin_info.data_directory / "level.txt", "c"
        )
        # True while _finish is registered on the empty line trigger
        self._collecting = False
        # the GMCP event the tier callback is registered on: "status", "base" or None
        self._gmcp_cb: str | None = None
        self._groups_ready: set[str] = set()

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the events, settings, watches and triggers."""
        add_event = self.api("plugins.core.events:event.add")
        for event_name, info in EVENTS.items():
            add_event(
                event_name,
                self.plugin_id,
                description=info["description"],
                arg_descriptions=info["arg_descriptions"],
            )
        for name, help_text in _SETTINGS.items():
            self.api("plugins.core.settings:setting.add")(
                self.plugin_id, name, False, bool, help_text
            )
        for watch_name, regex in WATCHES.items():
            self.api("plugins.core.watch:watch.add")(watch_name, regex)
            self.api("plugins.core.events:event.register")(
                f"watch_{watch_name}", self._watch_superhero
            )
        callbacks = self._trigger_callbacks()
        for spec in TRIGGERS:
            self._add_trigger(spec, callbacks.get(spec.name))
        self._rearm_tier()

    def _trigger_callbacks(self) -> dict[str, Callable[[], None]]:
        """Return the callback of each trigger that has one, by trigger name."""
        return {
            "lvlpup": self._trigger_pup,
            "lvlpupbless": self._trigger_pup,
            "lvllevel": self._trigger_level,
            "lvlbless": self._trigger_level,
            "lvlshloud": self._trigger_superhero_loud,
            "lvlgains": self._trigger_gains,
            "lvlpupgains": self._trigger_pup_gains,
            "lvlblesstrain": self._trigger_blessing_trains,
            "lvlbonustrains": self._trigger_bonus_trains,
            "lvlbattlelearntrains": self._trigger_battlelearn_trains,
            "lvlbonusstat": self._trigger_bonus_stat,
            "lvlshbadstar": self._trigger_superhero_bad,
            "lvlshbad": self._trigger_superhero_bad,
            "lvlshnogold": self._trigger_superhero_bad,
            "lvlshnoqp": self._trigger_superhero_bad,
            "lvlshnodbl": self._trigger_superhero_bad,
            "lvlshnot200": self._trigger_superhero_bad,
            "lvlpreremort": self._trigger_preremort,
            "lvlremortcomp": self._trigger_remort_complete,
            "lvltier": self._trigger_tier,
        }

    def _group(self, suffix: str) -> str:
        """Return the trigger group name; group names are global, so it carries the plugin id."""
        return f"{self.plugin_id}.{suffix}"

    def _add_trigger(self, spec: TriggerSpec, func: Callable[[], None] | None) -> None:
        """Add a trigger and register its callback, noting which groups are usable."""
        kwargs: dict[str, Any] = {"enabled": spec.enabled}
        if spec.group:
            kwargs["group"] = self._group(spec.group)
        if spec.argtypes:
            kwargs["argtypes"] = spec.argtypes
        result = self.api("plugins.core.triggers:trigger.add")(spec.name, spec.regex, **kwargs)
        if not result.success:
            get_logger(self.plugin_id).error("could not add the %s trigger", spec.name)
            return
        if func is not None:
            self.api("plugins.core.triggers:trigger.register")(result.trigger.trigger_id, func)
        if spec.group:
            self._groups_ready.add(spec.group)

    def _toggle_group(self, suffix: str, flag: bool) -> None:
        """Turn a trigger group on or off, when it exists."""
        if suffix in self._groups_ready:
            self.api("plugins.core.triggers:group.toggle.enable")(self._group(suffix), flag)

    def _toggle_collecting_groups(self, flag: bool) -> None:
        """Turn the groups that only matter while a level is collected on or off."""
        self._toggle_group(GROUP_LINFO, flag)
        self._toggle_group(GROUP_SUPERHERO, flag)

    def _register_finish(self) -> None:
        """Run _finish on empty lines, once."""
        if self._collecting:
            return
        registered = self.api("plugins.core.triggers:trigger.register")(EMPTYLINE_ID, self._finish)
        self._collecting = bool(registered)

    def _unregister_finish(self) -> None:
        """Stop running _finish on empty lines, when it is registered."""
        if not self._collecting:
            return
        self.api("plugins.core.triggers:trigger.unregister")(EMPTYLINE_ID, self._finish)
        self._collecting = False

    @staticmethod
    def _now() -> float:
        """Return the current time."""
        return time.time()

    def _setting(self, name: str) -> bool:
        """Return a boolean setting of the plugin."""
        return bool(self.api("plugins.core.settings:setting.get")(self.plugin_id, name))

    def _set(self, name: str, value: bool) -> None:
        """Change a setting of the plugin."""
        self.api("plugins.core.settings:setting.set")(self.plugin_id, name, value)

    def _gmcp_value(self, path: str) -> object:
        """Return the cached GMCP value at a dotted path, or None."""
        return self.api("libs.net.protocols:gmcp.value.get")(path)

    def _matches(self) -> dict[str, Any]:
        """Return the groups the current trigger matched."""
        record = self.api("plugins.core.events:event.current.record.get")()
        return dict(record.get("matches") or {})

    def _raise(self, event_name: str, payload: dict[str, Any] | None = None) -> None:
        """Raise an event of the plugin."""
        self.api("plugins.core.events:event.raise")(event_name, event_args=payload or {})

    def _start(self, kind: str, level: int | None = None) -> None:
        """Start a new record and collect its gains until the next empty line.

        A powerup passes no level: it comes from GMCP, like the total level.
        """
        if level is None:
            level = to_int(self._gmcp_value("char.status.level"))
            total = aardu.actual_level_from_gmcp(self._gmcp_value)
        else:
            total = aardu.actual_level_from_gmcp(self._gmcp_value, level)
        starttime = self._now()
        self.levelinfo.clear()
        self.levelinfo.update(new_record(kind, level, total, starttime))
        self._toggle_group(GROUP_LINFO, True)
        self._register_finish()
        log_to(self.plugin_id, logging.DEBUG, "started a %s record at level %s", kind, level)

    # triggers that start a record

    def _trigger_level(self) -> None:
        """A level was raised."""
        self._start("level", to_int(self._matches().get("level")))

    def _trigger_pup(self) -> None:
        """A powerup was gained."""
        self._start("pup")

    # triggers that add gains to the record

    def _trigger_gains(self) -> None:
        """The gains line of a level."""
        matches = self._matches()
        self.levelinfo["hp"] = to_int(matches.get("hp"))
        self.levelinfo["mp"] = to_int(matches.get("mp"))
        self.levelinfo["mv"] = to_int(matches.get("mv"))
        self.levelinfo["pracs"] = to_int(matches.get("pr"))
        self.levelinfo["trains"] = to_int(matches.get("tr"))

    def _trigger_pup_gains(self) -> None:
        """The trains line of a powerup."""
        self.levelinfo["trains"] = to_int(self._matches().get("tr"))

    def _trigger_blessing_trains(self) -> None:
        """The trains of the daily blessing."""
        self.levelinfo["blessingtrains"] = to_int(self._matches().get("tr"))

    def _trigger_bonus_trains(self) -> None:
        """The bonus trains."""
        self.levelinfo["bonustrains"] = to_int(self._matches().get("tr"))

    def _trigger_battlelearn_trains(self) -> None:
        """The trains of enhanced battle learning."""
        self.levelinfo["battlelearntrains"] = to_int(self._matches().get("tr"))

    def _trigger_bonus_stat(self) -> None:
        """A bonus stat point."""
        key = bonus_stat_key(str(self._matches().get("stat") or ""))
        if key is not None:
            self.levelinfo[key] = 1

    def _trigger_superhero_loud(self) -> None:
        """The superhero loud line: the trains of the level 201 record being collected."""
        if self._collecting and self.levelinfo.get("level") == 201:
            self.levelinfo["trains"] = to_int(self._matches().get("trains"))

    # superhero

    def _watch_superhero(self) -> None:
        """A client typed a superhero command: watch for the result and start a record."""
        log_to(self.plugin_id, logging.DEBUG, "superhero was typed")
        self._toggle_group(GROUP_SUPERHERO, True)
        self._start("level", 201)

    def _trigger_superhero_bad(self) -> None:
        """The superhero command did not work: undo what the command started."""
        log_to(self.plugin_id, logging.DEBUG, "no superhero after all")
        self._toggle_collecting_groups(False)
        self._unregister_finish()

    # remort and tier

    def _trigger_preremort(self) -> None:
        """The character is flagged as remorting."""
        self._set("preremort", True)
        self._raise(EVENT_PREREMORT)

    def _trigger_remort_complete(self) -> None:
        """A remort is complete: the record at level 1 ends at the next empty line."""
        self._set("preremort", False)
        self._set("remortcomp", True)
        self._start("level", 1)

    def _trigger_tier(self) -> None:
        """A tier is about to happen: watch the GMCP status for the end of it."""
        self._set("tiering", True)
        log_to(self.plugin_id, logging.DEBUG, "tiering")
        self._register_gmcp("status")

    def _register_gmcp(self, which: str | None) -> None:
        """Register the tier callback on the GMCP status or base event, or on none."""
        self._unregister_gmcp()
        if which == "status":
            self.api("plugins.core.events:event.register")(EVENT_GMCP_STATUS, self._gmcp_status)
        elif which == "base":
            self.api("plugins.core.events:event.register")(EVENT_GMCP_BASE, self._gmcp_base)
        self._gmcp_cb = which

    def _unregister_gmcp(self) -> None:
        """Unregister the tier callback from the event it is registered on, if any."""
        if self._gmcp_cb == "status":
            self.api("plugins.core.events:event.unregister")(EVENT_GMCP_STATUS, self._gmcp_status)
        elif self._gmcp_cb == "base":
            self.api("plugins.core.events:event.unregister")(EVENT_GMCP_BASE, self._gmcp_base)
        self._gmcp_cb = None

    def _rearm_tier(self) -> None:
        """After a restart in the middle of a tier, register the matching GMCP callback again."""
        if self._setting("tiering"):
            self._register_gmcp("base" if self._setting("seen2") else "status")

    def _gmcp_status(self) -> None:
        """Wait for state 2 of the GMCP status, then for the new base."""
        if to_int(self._gmcp_value("char.status.state")) == 2:
            log_to(self.plugin_id, logging.DEBUG, "seen state 2 while tiering")
            self._set("seen2", True)
            self._register_gmcp("base")

    def _gmcp_base(self) -> None:
        """A new base after state 3 of a tier: start the level 1 record, once."""
        state = to_int(self._gmcp_value("char.status.state"))
        if self._setting("tiering") and self._setting("seen2") and state == 3:
            log_to(self.plugin_id, logging.DEBUG, "new base after the tier")
            self._register_gmcp(None)
            self._start("level", 1)

    # finish

    def _finish(self) -> None:
        """An empty line: finish the record when it has its gains, and raise the events."""
        info = self.levelinfo
        if not should_finish(
            to_int(info.get("trains")), self._setting("remortcomp"), self._setting("tiering")
        ):
            return
        info["finishtime"] = self._now()
        info.sync()
        self._toggle_collecting_groups(False)
        self._unregister_finish()
        self._raise(EVENT_GAIN, copy.deepcopy(dict(info)))
        level = info.get("level")
        kind = info.get("type")
        if level == 200 and kind == "level":
            self._raise(EVENT_HERO)
        elif level == 201 and kind == "level":
            self._raise(EVENT_SUPERHERO)
        elif level == 1:
            if self._setting("tiering"):
                self._set("tiering", False)
                self._set("seen2", False)
                self._raise(EVENT_TIER)
            else:
                self._set("remortcomp", False)
                self._raise(EVENT_REMORT)

    @RegisterToEvent(event_name=EVENT_DISCONNECT)
    def _eventcb_disconnect(self) -> None:
        """Turn the collecting off so a level cut off by a disconnect does not leave it on."""
        self._toggle_collecting_groups(False)
        self._unregister_finish()

    @RegisterPluginHook("save")
    def _phook_save(self) -> None:
        """Save the level record."""
        self.levelinfo.sync()
