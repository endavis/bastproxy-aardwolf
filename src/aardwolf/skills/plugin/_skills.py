"""Aardwolf skills plugin: keep the skills, spells and recoveries up to date from slist."""

import copy
import functools
import logging
import time
from collections.abc import Callable
from typing import Any

from bastproxy.libs.api import AddAPI
from bastproxy.libs.logger import get_logger, log_to
from bastproxy.libs.records import NetworkData, SendDataDirectlyToMud
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.commands import AddArgument, AddCommand, AddParser, CommandResult
from bastproxy.plugins.core.events import RegisterToEvent

from ..libs import (
    A102_OPTIONS,
    API_A102_TOGGLE,
    ARGS_FULL,
    ARGS_SPELLUP,
    CMD,
    CMD_REGEX,
    CMD_SPELLUP_REGEX,
    CMDTYPE,
    CMDTYPE_SPELLUP,
    EVENT_AFFECTED_UPDATE,
    EVENT_AFFOFF,
    EVENT_AFFON,
    EVENT_DISCONNECT,
    EVENT_FAIL,
    EVENT_GAIN,
    EVENT_LEVEL_REMORT,
    EVENT_LEVEL_TIER,
    EVENT_RECOFF,
    EVENT_RECON,
    EVENT_UPTODATE,
    EVENTS,
    GROUP_RECOVERIES,
    GROUP_SLIST,
    GROUP_SPELLS,
    HIDE_END_FULL,
    HIDE_END_SPELLUP,
    HIDE_MAX_LINES,
    HIDE_START_FULL,
    HIDE_START_SPELLUP,
    TRIGGERS,
    SkillTable,
    TriggerSpec,
    fail_payload,
)

_ALL_GROUPS = (GROUP_SLIST, GROUP_SPELLS, GROUP_RECOVERIES)
# the slist kinds whose output ends at the end of the spell headers, with no recoveries
_SHORT_KINDS = ("learned", "spellup")


class SkillsPlugin(BasePlugin):
    """Follow slist and the skill tags, and raise the changes as events."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Create the empty skill table and the state of the slist reader."""
        self.table = SkillTable()
        self._groups_ready: set[str] = set()
        # the kind of the slist being read: None for a full one, else affected, learned, spellup
        self._current: str | None = None
        # True from the start tag of a block until its end
        self._started = False
        # the command type of the slist being read
        self._cmdtype: str = CMDTYPE
        # True while the a102 tag options are requested by this plugin
        self._tags_on = False

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the events, the command type and the triggers, and ask for the tags."""
        add_event = self.api("plugins.core.events:event.add")
        for event_name, info in EVENTS.items():
            add_event(
                event_name,
                self.plugin_id,
                description=info["description"],
                arg_descriptions=info["arg_descriptions"],
            )
        for cmdtype, regex, hide_start, hide_end in (
            (CMDTYPE, CMD_REGEX, HIDE_START_FULL, HIDE_END_FULL),
            (CMDTYPE_SPELLUP, CMD_SPELLUP_REGEX, HIDE_START_SPELLUP, HIDE_END_SPELLUP),
        ):
            self.api("plugins.core.mudcmds:type.add")(
                cmdtype,
                CMD,
                regex,
                beforef=functools.partial(self._slist_before, cmdtype),
                afterf=self._slist_after,
                hide_output=True,
                hide_start=hide_start,
                hide_end=hide_end,
                hide_max=HIDE_MAX_LINES + 1,
            )
        callbacks = self._trigger_callbacks()
        for spec in TRIGGERS:
            self._add_trigger(spec, callbacks.get(spec.name))
        for option in A102_OPTIONS:
            self.api(API_A102_TOGGLE)(option, True)
        self._tags_on = True

    @RegisterPluginHook("uninitialize", priority=10)
    def _phook_uninitialize(self) -> None:
        """Take back the tag requests, on reload and on unload, so the counts stay balanced."""
        if not self._tags_on:
            return
        self._tags_on = False
        for option in A102_OPTIONS:
            self.api(API_A102_TOGGLE)(option, False)

    @RegisterPluginHook("character_active")
    def _phook_character_active(self) -> None:
        """The character is active: read the skills when they are not known yet."""
        if self.table.count() == 0 or not self.table.uptodate:
            self._refresh()

    def _trigger_callbacks(self) -> dict[str, Callable[[], None]]:
        """Return the callback of each trigger, by trigger name."""
        return {
            "skills_affon": self._trigger_affon,
            "skills_affoff": self._trigger_affoff,
            "skills_recon": self._trigger_recon,
            "skills_recoff": self._trigger_recoff,
            "skills_skillgain": self._trigger_skillgain,
            "skills_sfail": self._trigger_sfail,
            "skills_start": self._trigger_start,
            "skills_spellheaders_end": self._trigger_spellheaders_end,
            "skills_recov_start": self._trigger_recov_start,
            "skills_recoveries_end": self._trigger_recoveries_end,
            "skills_spell_line": self._trigger_spell_line,
            "skills_recov_line": self._trigger_recov_line,
        }

    def _group(self, suffix: str) -> str:
        """Return the trigger group name; group names are global, so it carries the plugin id."""
        return f"{self.plugin_id}.{suffix}"

    def _add_trigger(self, spec: TriggerSpec, func: Callable[[], None] | None) -> None:
        """Add a trigger and register its callback, noting which groups are usable."""
        kwargs: dict[str, Any] = {"enabled": spec.enabled}
        if spec.group:
            kwargs["group"] = self._group(spec.group)
        if spec.omit:
            kwargs["omit"] = True
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

    def _toggle_all_groups(self, flag: bool) -> None:
        """Turn every trigger group on or off."""
        for suffix in _ALL_GROUPS:
            self._toggle_group(suffix, flag)

    @staticmethod
    def _now() -> float:
        """Return the current time."""
        return time.time()

    def _record(self) -> dict[str, Any]:
        """Return the record of the current event."""
        return dict(self.api("plugins.core.events:event.current.record.get")() or {})

    def _matches(self) -> dict[str, Any]:
        """Return the groups the current trigger matched."""
        return dict(self._record().get("matches") or {})

    def _raise(self, name: str, payload: dict[str, Any]) -> None:
        """Raise an event with a payload that is a copy, so no one changes the state."""
        self.api("plugins.core.events:event.raise")(name, event_args=copy.deepcopy(payload))

    def _args(self) -> dict[str, Any]:
        """Return the arguments of the running command."""
        args = self.api("plugins.core.commands:command.current.args.get")()
        return dict(args) if args else {}

    # the slist command

    def _refresh(self) -> None:
        """Queue the full slist and the spellup slist."""
        self.api("plugins.core.mudcmds:command.queue")(CMDTYPE, ARGS_FULL)
        self.api("plugins.core.mudcmds:command.queue")(CMDTYPE_SPELLUP, ARGS_SPELLUP)

    def _slist_before(self, cmdtype: str) -> None:
        """Before an slist is sent: read its output."""
        self._cmdtype = cmdtype
        self._toggle_group(GROUP_SLIST, True)
        self._toggle_group(GROUP_SPELLS, True)
        self.api("plugins.core.mudcmds:command.start")(cmdtype)

    def _slist_after(self) -> None:
        """After an slist finished: raise what it made known."""
        if self._current == "spellup":
            if not self.table.uptodate:
                self.table.uptodate = True
                self._raise(EVENT_UPTODATE, {})
        elif self._current in (None, "affected"):
            self._raise(EVENT_AFFECTED_UPDATE, {})
        self._current = None

    def _end_block(self) -> None:
        """The block is over: stop reading, and finish the command, which ends its hide window."""
        self._toggle_all_groups(False)
        self._started = False
        self.api("plugins.core.mudcmds:command.finish")(self._cmdtype)

    # slist triggers

    def _trigger_start(self) -> None:
        """The start tag of a block: note its kind and clear what it will set again."""
        kind = self._matches().get("type") or None
        self._current = kind
        self._started = True
        if kind is None:
            self.table.reset()
        elif kind == "affected":
            self.table.reset_affected()

    def _trigger_spell_line(self) -> None:
        """A line of the spell section."""
        if not self._started:
            return
        matches = self._matches()
        sn = int(matches["sn"])
        now = self._now()
        if self._current == "affected":
            known = self.table.set_duration(sn, matches["duration"], now)
        elif self._current == "learned":
            known = self.table.set_percent(sn, matches["pct"])
        elif self._current == "spellup":
            known = self.table.flag_spellup(sn)
        else:
            self.table.add_skill(matches, now)
            known = True
        if not known:
            log_to([self.plugin_id], logging.DEBUG, "slist line for an unknown sn %d", sn)

    def _trigger_recov_start(self) -> None:
        """The start of the recoveries section: read recovery lines instead of spell lines."""
        self._toggle_group(GROUP_SPELLS, False)
        self._toggle_group(GROUP_RECOVERIES, True)

    def _trigger_recov_line(self) -> None:
        """A line of the recoveries section."""
        if not self._started:
            return
        matches = self._matches()
        sn = int(matches["sn"])
        if self._current == "affected":
            if not self.table.set_recovery_duration(sn, matches["duration"], self._now()):
                log_to([self.plugin_id], logging.DEBUG, "recovery line for an unknown sn %d", sn)
        elif self._current in _SHORT_KINDS:
            log_to(
                [self.plugin_id],
                logging.DEBUG,
                "recovery line in a %s slist, which should not have any",
                self._current,
            )
        else:
            self.table.add_recovery(matches, self._now())

    def _trigger_spellheaders_end(self) -> None:
        """The end of the spell headers: the end of the block for learned and spellup."""
        if self._started and self._current in _SHORT_KINDS:
            self._end_block()

    def _trigger_recoveries_end(self) -> None:
        """The end of the recoveries: the end of the block for a full or affected slist."""
        if self._started and self._current not in _SHORT_KINDS:
            self._end_block()

    # tag triggers

    def _trigger_affon(self) -> None:
        """An affect started: store when it ends."""
        matches = self._matches()
        sn = matches["sn"]
        if not self.table.set_duration(sn, matches["duration"], self._now()):
            log_to([self.plugin_id], logging.DEBUG, "affon for an unknown sn %d", sn)
            return
        skill = self.table.get_skill(sn)
        duration = skill["duration"] if skill else 0
        self._raise(EVENT_AFFON, {"sn": sn, "duration": duration})

    def _trigger_affoff(self) -> None:
        """An affect ended."""
        sn = self._matches()["sn"]
        if not self.table.set_duration(sn, 0, self._now()):
            log_to([self.plugin_id], logging.DEBUG, "affoff for an unknown sn %d", sn)
            return
        self._raise(EVENT_AFFOFF, {"sn": sn})

    def _trigger_recon(self) -> None:
        """A recovery started: store when it ends."""
        matches = self._matches()
        sn = matches["sn"]
        if not self.table.set_recovery_duration(sn, matches["duration"], self._now()):
            log_to([self.plugin_id], logging.DEBUG, "recon for an unknown sn %d", sn)
            return
        recovery = self.table.get_recovery(sn)
        duration = recovery["duration"] if recovery else 0
        self._raise(EVENT_RECON, {"sn": sn, "duration": duration})

    def _trigger_recoff(self) -> None:
        """A recovery ended."""
        sn = self._matches()["sn"]
        if not self.table.set_recovery_duration(sn, 0, self._now()):
            log_to([self.plugin_id], logging.DEBUG, "recoff for an unknown sn %d", sn)
            return
        self._raise(EVENT_RECOFF, {"sn": sn})

    def _trigger_skillgain(self) -> None:
        """The percent of a skill changed."""
        matches = self._matches()
        sn = matches["sn"]
        if not self.table.set_percent(sn, matches["percent"]):
            log_to([self.plugin_id], logging.DEBUG, "skillgain for an unknown sn %d", sn)
            return
        self._raise(EVENT_GAIN, {"sn": sn, "percent": matches["percent"]})

    def _trigger_sfail(self) -> None:
        """A skill or spell failed: raise why, and refresh when a known skill says unknown."""
        matches = self._matches()
        payload = fail_payload(
            matches["sn"], matches["target"], matches["reason"], matches["recovery"]
        )
        skill = self.table.get_skill(matches["sn"])
        if payload["reason"] == "dontknow" and skill and skill["percent"] > 0:
            log_to([self.plugin_id], logging.DEBUG, "refreshing because of an unlearned spell")
            self._refresh()
        self._raise(EVENT_FAIL, payload)

    # events

    @RegisterToEvent(event_name=EVENT_LEVEL_REMORT)
    def _eventcb_level_remort(self) -> None:
        """The character remorted: the skills changed."""
        self._refresh()

    @RegisterToEvent(event_name=EVENT_LEVEL_TIER)
    def _eventcb_level_tier(self) -> None:
        """The character tiered: the skills changed."""
        self._refresh()

    @RegisterToEvent(event_name=EVENT_DISCONNECT)
    def _eventcb_disconnect(self) -> None:
        """Forget the skills, and abandon a block in progress."""
        self.table.reset()
        self._current = None
        self._started = False
        self._toggle_all_groups(False)

    # APIs

    @AddAPI("skill.get", description="return a copy of a skill or spell by sn or name, or None")
    def _api_skill_get(self, key: int | str) -> dict[str, Any] | None:
        """Return a copy of a skill with its recovery resolved, or None."""
        return self.table.get_skill(key)

    @AddAPI("recovery.get", description="return a copy of a recovery by sn or name, or None")
    def _api_recovery_get(self, key: int | str) -> dict[str, Any] | None:
        """Return a copy of a recovery, or None."""
        return self.table.get_recovery(key)

    @AddAPI("skill.is.affected", description="return True when the skill has an affect running")
    def _api_skill_is_affected(self, key: int | str) -> bool:
        """Return True when the skill has an affect running."""
        return self.table.is_affected(key)

    @AddAPI(
        "skill.is.blocked.by.recovery",
        description="return True when a recovery blocks the skill",
    )
    def _api_skill_is_blocked_by_recovery(self, key: int | str) -> bool:
        """Return True when a recovery that blocks the skill is running."""
        return self.table.is_blocked_by_recovery(key)

    @AddAPI("skill.is.practiced", description="return True when more than 10 percent is learned")
    def _api_skill_is_practiced(self, key: int | str) -> bool:
        """Return True when more than 10 percent is learned."""
        return self.table.is_practiced(key)

    @AddAPI("skill.can.use", description="return True when the skill can be used now")
    def _api_skill_can_use(self, key: int | str) -> bool:
        """Return True when the skill is practiced, not affected and not blocked."""
        return self.table.can_use(key)

    @AddAPI("skill.is.spellup", description="return True when the skill is a spellup")
    def _api_skill_is_spellup(self, key: int | str) -> bool:
        """Return True when the skill is a spellup."""
        return self.table.is_spellup(key)

    @AddAPI("skill.is.bad", description="return True for an attack or special skill")
    def _api_skill_is_bad(self, key: int | str) -> bool:
        """Return True for an attack or special skill that is not a spellup."""
        return self.table.is_bad(key)

    @AddAPI("spellups.get", description="return copies of the spellups")
    def _api_spellups_get(self) -> list[dict[str, Any]]:
        """Return copies of the spellups."""
        return self.table.spellups()

    @AddAPI("is.up.to.date", description="return True when the skills and spellups are known")
    def _api_is_up_to_date(self) -> bool:
        """Return True once a spellup slist was read since the last reset."""
        return self.table.uptodate

    @AddAPI("skill.send", description="send the command that uses a skill or spell")
    def _api_skill_send(self, key: int | str) -> bool:
        """Send ``cast <sn>`` for a spell or the first word of the name for a skill."""
        skill = self.table.get_skill(key)
        if not skill:
            return False
        if skill["type"] == "spell":
            command = f"cast {skill['sn']}"
        else:
            command = str(skill["name"]).split()[0]
        SendDataDirectlyToMud(NetworkData([command], owner_id=f"{self.plugin_id}:skill.send"))()
        return True

    # commands

    @AddCommand()
    @AddParser(description="refresh the skills and spells")
    def _command_refresh(self) -> CommandResult:
        """Read the skills again."""
        self._refresh()
        return CommandResult(True, ["Refreshing spells and skills"])

    @AddCommand()
    @AddParser(description="look up a skill or spell by name or sn")
    @AddArgument("skill", help="the skill to look up", nargs="?", default="")
    def _command_lu(self) -> CommandResult:
        """Show what is known about a skill."""
        name = self._args().get("skill", "")
        skill = self.table.get_skill(name) if name else None
        if not skill:
            return CommandResult(True, [f"Could not find: {name}"])
        now = self._now()
        lines = [
            f"{'SN':<8} : {skill['sn']}",
            f"{'Name':<8} : {skill['name']}",
            f"{'Percent':<8} : {skill['percent']}",
        ]
        if skill["duration"] > 0:
            lines.append(f"{'Duration':<8} : {self._elapsed(now, skill['duration'])}")
        lines.append(f"{'Target':<8} : {skill['target']}")
        lines.append(f"{'Spellup':<8} : {skill['spellup']}")
        lines.append(f"{'Type':<8} : {skill['type']}")
        recovery = skill["recovery"]
        if recovery:
            if recovery["duration"] > 0:
                left = self._elapsed(now, recovery["duration"])
                lines.append(f"{'Recovery':<8} : {recovery['name']} ({left})")
            else:
                lines.append(f"{'Recovery':<8} : {recovery['name']}")
        return CommandResult(True, lines)

    def _elapsed(self, start: float, end: float) -> str:
        """Return the time from start to end as text."""
        return str(self.api("plugins.core.utils:timedelta.to.string")(start, end))
