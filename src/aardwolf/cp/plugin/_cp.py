"""Aardwolf cp plugin: follow the campaigns of the character and raise them as events."""

import copy
import logging
import time
from collections.abc import Callable
from typing import Any

from bastproxy.libs.api import AddAPI
from bastproxy.libs.logger import get_logger, log_to
from bastproxy.libs.persistentdict import PersistentDict
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.commands import AddCommand, AddParser, CommandResult
from bastproxy.plugins.core.events import RegisterToEvent

from aardwolf._libs import aardu
from aardwolf._libs.eventu import own_event, own_events

from ..libs import (
    ALL_LINES_ID,
    API_QUESTMASTERS_GET,
    CHECK_HIDE_START,
    CMD,
    CMD_INFO,
    CMD_INFO_REGEX,
    CMD_REGEX,
    CMDTYPE,
    CMDTYPE_INFO,
    EVENT_CHAR_ACTIVE,
    EVENT_DISCONNECT,
    EVENT_MOBK_KILL,
    EVENT_QUESTMASTERS_CHANGED,
    EVENTS,
    GROUP_CHECK,
    GROUP_DONE,
    GROUP_IN,
    GROUP_INFO,
    GROUP_REW,
    HIDE_MAX_LINES,
    INFO_HIDE_START,
    NEW_TRIGGER,
    SUFFIX_COMP,
    SUFFIX_FAILED,
    SUFFIX_MOBSLEFT,
    SUFFIX_MOBSORIG,
    TRIGGERS,
    TriggerSpec,
    bonus_qp,
    info_mobs,
    info_starttime,
    is_count_line,
    new_campaign_regex,
    new_mob,
    new_state,
    parse_time_left,
    remove_mob,
    reward_key,
)

_ALL_GROUPS = (GROUP_CHECK, GROUP_IN, GROUP_REW, GROUP_DONE, GROUP_INFO)


class CpPlugin(BasePlugin):
    """Follow a campaign from the MUD output and raise its mobs and its end as events."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Load the saved campaign."""
        self.cp = PersistentDict(self.plugin_id, self.plugin_info.data_directory / "cp.txt", "c")
        self._groups_ready: set[str] = set()
        # True after a campaign mob died, until the mobk kill event for it arrives
        self._await_kill = False
        # True while _after_done is registered on the every-line trigger
        self._waiting_done = False
        # the values of the campaign info output, until its last line applies them
        self._info: dict[str, Any] = {}
        # True while _after_info_none is registered on the every-line trigger
        self._waiting_info = False

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the events, the command type and the triggers."""
        add_event = self.api("plugins.core.events:event.add")
        for event_name, info in own_events(self.plugin_id, EVENTS).items():
            add_event(
                event_name,
                self.plugin_id,
                description=info["description"],
                arg_descriptions=info["arg_descriptions"],
            )
        self.api("plugins.core.mudcmds:type.add")(
            CMDTYPE,
            CMD,
            CMD_REGEX,
            beforef=self._check_before,
            afterf=self._check_after,
            hide_output=True,
            hide_start=CHECK_HIDE_START,
            hide_max=HIDE_MAX_LINES + 1,
        )
        self.api("plugins.core.mudcmds:type.add")(
            CMDTYPE_INFO,
            CMD_INFO,
            CMD_INFO_REGEX,
            beforef=self._info_before,
            afterf=self._info_after,
            hide_output=True,
            hide_start=INFO_HIDE_START,
            hide_max=HIDE_MAX_LINES + 1,
        )
        callbacks = self._trigger_callbacks()
        for spec in TRIGGERS:
            if spec.name == NEW_TRIGGER:
                spec = spec._replace(regex=new_campaign_regex(self._questmasters()))
            self._add_trigger(spec, callbacks.get(spec.name))
        if self.api("libs.api:character.is.active")():
            self._queue_info()
            self._queue_check()

    def _questmasters(self) -> list[str]:
        """Return the questmaster names from the config plugin."""
        return list(self.api(API_QUESTMASTERS_GET)())

    def _trigger_callbacks(self) -> dict[str, Callable[[], None]]:
        """Return the callback of each trigger, by trigger name."""
        return {
            "cp_new": self._trigger_new,
            "cp_none": self._trigger_none,
            "cp_time": self._trigger_time,
            "cp_mob": self._trigger_mob,
            "cp_needtolevel": self._trigger_needtolevel,
            "cp_cantake": self._trigger_cantake,
            "cp_shnext": self._trigger_shnext,
            "cp_mobdead": self._trigger_mobdead,
            "cp_complete": self._trigger_complete,
            "cp_clear": self._trigger_clear,
            "cp_reward": self._trigger_reward,
            "cp_compdone": self._trigger_compdone,
            "cp_info_completeby": self._trigger_info_completeby,
            "cp_info_timeleft": self._trigger_info_timeleft,
            "cp_info_level": self._trigger_info_level,
            "cp_info_mob": self._trigger_info_mob,
            "cp_info_end": self._trigger_info_end,
            "cp_info_none": self._trigger_info_none,
            "cp_info_cantake": self._trigger_info_cantake,
            "cp_info_needtolevel": self._trigger_info_needtolevel,
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

    def _queue_check(self) -> None:
        """Queue a ``campaign check``."""
        self.api("plugins.core.mudcmds:command.queue")(CMDTYPE)

    def _queue_info(self) -> None:
        """Queue a ``campaign info``."""
        self.api("plugins.core.mudcmds:command.queue")(CMDTYPE_INFO)

    @staticmethod
    def _now() -> float:
        """Return the current time."""
        return time.time()

    def _gmcp_value(self, path: str) -> object:
        """Return the cached GMCP value at a dotted path, or None."""
        return self.api("libs.net.protocols:gmcp.value.get")(path)

    def _record(self) -> dict[str, Any]:
        """Return the record of the current event."""
        return dict(self.api("plugins.core.events:event.current.record.get")() or {})

    def _matches(self) -> dict[str, Any]:
        """Return the groups the current trigger matched."""
        return dict(self._record().get("matches") or {})

    def _raise(self, suffix: str, payload: dict[str, Any]) -> None:
        """Raise one of this plugin's events with a payload that is a copy."""
        self.api("plugins.core.events:event.raise")(
            own_event(self.plugin_id, suffix), event_args=copy.deepcopy(payload)
        )

    def _mobsleft_payload(self) -> dict[str, Any]:
        """Return the payload of the mobs events."""
        return {"mobsleft": copy.deepcopy(list(self.cp.get("mobsleft", [])))}

    # the campaign check command

    def _check_before(self) -> None:
        """Before ``campaign check`` is sent: forget the mobs left and read the output."""
        self.cp["mobsleft"] = []
        self._toggle_group(GROUP_CHECK, True)
        self.api("plugins.core.mudcmds:command.start")(CMDTYPE)

    def _check_after(self) -> None:
        """After ``campaign check`` finished: follow the campaign, stop reading the check."""
        self._toggle_group(GROUP_IN, True)
        self._toggle_group(GROUP_CHECK, False)

    # the campaign info command

    def _info_before(self) -> None:
        """Before ``campaign info`` is sent: forget the last values and read the output."""
        self._info = {"mobs": []}
        self._toggle_group(GROUP_INFO, True)
        self.api("plugins.core.mudcmds:command.start")(CMDTYPE_INFO)

    def _info_after(self) -> None:
        """After ``campaign info`` finished: stop reading the info and the prompt."""
        self._toggle_group(GROUP_INFO, False)
        self._stop_waiting_info()

    def _stop_waiting_info(self) -> None:
        """Unregister the prompt watcher of the not-on-a-campaign reply."""
        if self._waiting_info:
            self.api("plugins.core.triggers:trigger.unregister")(
                ALL_LINES_ID, self._after_info_none
            )
            self._waiting_info = False

    def _finish_info(self) -> None:
        """The ``campaign info`` output is over."""
        self.api("plugins.core.mudcmds:command.finish")(CMDTYPE_INFO)

    def _apply_info(self) -> None:
        """Start a campaign from the info values, unless it is the one already tracked."""
        completeby = str(self._info.get("completeby") or "")
        mobs: list[dict[str, Any]] = list(self._info.get("mobs", []))
        if not completeby or not mobs:
            log_to([self.plugin_id], logging.DEBUG, "campaign info has no Complete By or targets")
            return
        if self.cp.get("oncp") and self.cp.get("completeby") == completeby:
            return
        level = aardu.actual_level_from_gmcp(self._gmcp_value, level=self._info.get("level"))
        state = new_state(self._now(), level)
        state["starttime"] = info_starttime(self._now(), self._info.get("timeleft"))
        state["completeby"] = completeby
        state["mobs"] = copy.deepcopy(mobs)
        state["mobsleft"] = copy.deepcopy(mobs)
        self.cp.clear()
        self.cp.update(state)
        self.cp.sync()
        self._raise(SUFFIX_MOBSORIG, {"mobsleft": copy.deepcopy(mobs)})
        self._queue_check()

    # triggers

    def _trigger_new(self) -> None:
        """A new campaign tell: ask the server, which is the only thing that starts a campaign."""
        self._queue_info()

    def _trigger_info_completeby(self) -> None:
        """The Complete By line of the info output."""
        self._info["completeby"] = str(self._matches().get("completeby") or "")

    def _trigger_info_timeleft(self) -> None:
        """The Time Left line of the info output."""
        self._info["timeleft"] = parse_time_left(str(self._matches().get("timeleft") or ""))

    def _trigger_info_level(self) -> None:
        """The Level Taken line of the info output."""
        self._info["level"] = self._matches().get("level")

    def _trigger_info_mob(self) -> None:
        """A target of the info output; a count of n is n mobs."""
        matches = self._matches()
        name = str(matches.get("mob") or "")
        location = str(matches.get("location") or "")
        if not name or not location:
            log_to([self.plugin_id], logging.DEBUG, "error parsing the info mob line: %s", matches)
            return
        self._info.setdefault("mobs", []).extend(
            info_mobs(int(matches.get("count") or 1), name, location)
        )

    def _trigger_info_end(self) -> None:
        """The last line of the info output: apply it and finish the command."""
        self._apply_info()
        self._finish_info()

    def _trigger_info_none(self) -> None:
        """Not on a campaign, in the info output: wait for the limit lines or the prompt."""
        self.cp["oncp"] = False
        self.cp.sync()
        for suffix in (GROUP_IN, GROUP_REW, GROUP_DONE):
            self._toggle_group(suffix, False)
        if self._waiting_info:
            return
        registered = self.api("plugins.core.triggers:trigger.register")(
            ALL_LINES_ID, self._after_info_none
        )
        self._waiting_info = bool(registered)

    def _after_info_none(self) -> None:
        """The first prompt after the not-on-a-campaign line ends the info output."""
        line = self._record().get("line")
        if getattr(line, "is_prompt", False):
            self._finish_info()

    def _trigger_info_cantake(self) -> None:
        """The info output says a campaign may be taken."""
        self.cp["cantake"] = True
        self.cp.sync()
        self._finish_info()

    def _trigger_info_needtolevel(self) -> None:
        """The info output says the character has to level first."""
        self.cp["cantake"] = False
        self.cp.sync()
        self._finish_info()

    def _trigger_none(self) -> None:
        """The character is not on a campaign."""
        self.cp["oncp"] = False
        self.cp.sync()
        # finish first: the after function of the check turns the in group on
        self.api("plugins.core.mudcmds:command.finish")(CMDTYPE)
        self._toggle_all_groups(False)

    def _trigger_time(self) -> None:
        """The end of the check output: raise the mobs and finish the command."""
        if not self.cp.get("mobs"):
            self.cp["mobs"] = copy.deepcopy(list(self.cp.get("mobsleft", [])))
            self.cp.sync()
            self._raise(SUFFIX_MOBSORIG, self._mobsleft_payload())
        self.cp.sync()
        self._raise(SUFFIX_MOBSLEFT, self._mobsleft_payload())
        self.api("plugins.core.mudcmds:command.finish")(CMDTYPE)

    def _trigger_mob(self) -> None:
        """A mob of the campaign, in the check output."""
        matches = self._matches()
        name = str(matches.get("mob") or "")
        location = str(matches.get("location") or "")
        if not name or not location:
            log_to([self.plugin_id], logging.DEBUG, "error parsing the mob line: %s", matches)
            return
        mobsleft = list(self.cp.get("mobsleft", []))
        mobsleft.append(new_mob(name, location, matches.get("dead")))
        self.cp["mobsleft"] = mobsleft

    def _trigger_needtolevel(self) -> None:
        """The character has to level before the next campaign."""
        self.cp["cantake"] = False
        self.cp.sync()

    def _trigger_cantake(self) -> None:
        """The character may take a campaign."""
        self.cp["cantake"] = True
        self.cp.sync()

    def _trigger_shnext(self) -> None:
        """The time until the next campaign can be taken."""
        self.cp["shtime"] = self._matches().get("time")
        self.cp.sync()

    def _trigger_mobdead(self) -> None:
        """A campaign mob died: the next kill is its kill, or ask for the campaign."""
        if self.cp.get("oncp"):
            self._await_kill = True
        else:
            self._queue_info()

    def _trigger_complete(self) -> None:
        """The campaign is complete: read the rewards."""
        self._toggle_group(GROUP_REW, True)
        self.cp["finishtime"] = self._now()
        self.cp["oncp"] = False
        self.cp.sync()

    def _trigger_reward(self) -> None:
        """A reward of the campaign."""
        matches = self._matches()
        rtype = str(matches.get("type", ""))
        key = reward_key(rtype)
        if key is None:
            log_to([self.plugin_id], logging.DEBUG, "unknown reward type: %s", rtype)
            return
        self.cp[key] = int(matches.get("amount", 0))
        self.cp.sync()
        self._toggle_group(GROUP_DONE, True)

    def _trigger_compdone(self) -> None:
        """The line under the rewards: wait for the bonus line or the end of the output."""
        if self._waiting_done:
            return
        registered = self.api("plugins.core.triggers:trigger.register")(
            ALL_LINES_ID, self._after_done
        )
        self._waiting_done = bool(registered)

    def _trigger_clear(self) -> None:
        """The campaign was cleared."""
        self.cp["failed"] = 1
        self._raise(SUFFIX_FAILED, dict(self.cp))
        self._trigger_none()

    def _after_done(self) -> None:
        """Look at each line after the rewards for the bonus line, the count or the prompt."""
        line = self._record().get("line")
        text = str(getattr(line, "noansi", line)) if line is not None else ""
        bonus = bonus_qp(text)
        if bonus is not None:
            self.cp["bonusqp"] = bonus
            self._finish_comp()
        elif is_count_line(text) or getattr(line, "is_prompt", False):
            self._finish_comp()

    def _finish_comp(self) -> None:
        """The campaign output is over: raise the campaign."""
        if self._waiting_done:
            self.api("plugins.core.triggers:trigger.unregister")(ALL_LINES_ID, self._after_done)
            self._waiting_done = False
        self._toggle_group(GROUP_REW, False)
        self._toggle_group(GROUP_DONE, False)
        self.cp.sync()
        self._raise(SUFFIX_COMP, dict(self.cp))

    # events

    @RegisterToEvent(event_name=EVENT_MOBK_KILL)
    def _eventcb_mobk_kill(self) -> None:
        """A mob was killed: when it was a campaign mob, take it off the mobs left."""
        if not self._await_kill:
            return
        self._await_kill = False
        name = str(self._record().get("name", ""))
        mobsleft = list(self.cp.get("mobsleft", []))
        if remove_mob(mobsleft, name):
            self.cp["mobsleft"] = mobsleft
            self.cp.sync()
            self._raise(SUFFIX_MOBSLEFT, self._mobsleft_payload())
        else:
            log_to([self.plugin_id], logging.DEBUG, "could not find the mob: %s", name)
            self._queue_check()

    @RegisterToEvent(event_name=EVENT_CHAR_ACTIVE)
    def _eventcb_character_active(self) -> None:
        """The character is active: check the campaign."""
        if self._record().get("is_character_active"):
            self._queue_info()
            self._queue_check()

    @RegisterToEvent(event_name=EVENT_DISCONNECT)
    def _eventcb_disconnect(self) -> None:
        """Turn the groups off, and do not lose a campaign that is waiting for its last line."""
        self._await_kill = False
        if self._waiting_done:
            self._finish_comp()
        self._stop_waiting_info()
        self._info = {}
        self._toggle_all_groups(False)

    @RegisterToEvent(event_name=EVENT_QUESTMASTERS_CHANGED)
    def _eventcb_questmasters_changed(self) -> None:
        """The questmasters changed: only they may start a campaign."""
        names = self._record().get("questmasters", [])
        self.api("plugins.core.triggers:trigger.update")(
            NEW_TRIGGER, {"regex": new_campaign_regex(names)}
        )

    # APIs

    @AddAPI("oncp", description="return True when the character is on a campaign")
    def _api_oncp(self) -> bool:
        """Return True when the character is on a campaign."""
        return bool(self.cp.get("oncp", False))

    @AddAPI("mobs.left.get", description="return a copy of the mobs left of the campaign")
    def _api_mobs_left_get(self) -> list[dict[str, Any]]:
        """Return a copy of the mobs left; each has name, nocolorname, location and mobdead."""
        return copy.deepcopy(list(self.cp.get("mobsleft", [])))

    # commands

    @AddCommand()
    @AddParser(description="show the mobs left of the campaign")
    def _command_show(self) -> CommandResult:
        """Show the mobs left."""
        if not self.cp.get("oncp"):
            return CommandResult(True, ["You are not on a cp"])
        lines = ["Mobs left:", f"{'Mob Name':<40} Area/Room", "@G" + "-" * 60]
        for mob in self.cp.get("mobsleft", []):
            color = "@R" if mob.get("mobdead") else "@w"
            lines.append(f"{color}{mob.get('name', ''):<40} {mob.get('location', '')}")
        return CommandResult(True, lines)

    @AddCommand()
    @AddParser(description="refresh the mobs left of the campaign")
    def _command_refresh(self) -> CommandResult:
        """Check the campaign again."""
        if not self.cp.get("oncp"):
            return CommandResult(True, ["You are not on a cp"])
        self._queue_check()
        return CommandResult(True, ["Refreshing cp mobs"])

    @RegisterPluginHook("save")
    def _phook_save(self) -> None:
        """Save the campaign."""
        self.cp.sync()
