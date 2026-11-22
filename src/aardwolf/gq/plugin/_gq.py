"""Aardwolf gq plugin: follow the global quests of the character and raise them as events."""

import copy
import logging
import time
from collections.abc import Callable
from typing import Any

from bastproxy.libs.logger import get_logger, log_to
from bastproxy.libs.persistentdict import PersistentDict
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.events import RegisterToEvent

from aardwolf.libs import aardu

from ..libs import (
    CMD,
    CMD_REGEX,
    CMDTYPE,
    EVENT_AVAILABLE,
    EVENT_CANCELLED,
    EVENT_CHAR_ACTIVE,
    EVENT_COMPLETED,
    EVENT_DECLARED,
    EVENT_DISCONNECT,
    EVENT_DONE,
    EVENT_JOINED,
    EVENT_MOBK_KILL,
    EVENT_MOBSLEFT,
    EVENT_NOTAVAILABLE,
    EVENT_STARTED,
    EVENT_WON,
    EVENTS,
    GROUP_CHECK,
    GROUP_IN,
    GROUP_REW,
    TRIGGERS,
    WATCH_NAME,
    WATCH_REGEX,
    TriggerSpec,
    count_down,
    new_mob,
    new_state,
    reward_key,
)

_ALL_GROUPS = (GROUP_CHECK, GROUP_IN, GROUP_REW)
_NOT_JOINED = -1


class GqPlugin(BasePlugin):
    """Follow a global quest from the MUD output and raise its mobs and its end as events."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Load the saved global quest and the mobs left."""
        directory = self.plugin_info.data_directory
        self.gqinfo = PersistentDict(self.plugin_id, directory / "gq.txt", "c")
        self.track = PersistentDict(self.plugin_id, directory / "gqmobsleft.txt", "c")
        # the declared and started gquests are global MUD state: kept in memory only
        self._declared: set[int] = set()
        self._started: set[int] = set()
        self._groups_ready: set[str] = set()
        # True after a gquest mob died, until the mobk kill event for it arrives
        self._await_kill = False

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the events, settings, watch, command type and triggers."""
        add_event = self.api("plugins.core.events:event.add")
        for event_name, info in EVENTS.items():
            add_event(
                event_name,
                self.plugin_id,
                description=info["description"],
                arg_descriptions=info["arg_descriptions"],
            )
        add_setting = self.api("plugins.core.settings:setting.add")
        add_setting(self.plugin_id, "joined", _NOT_JOINED, int, "the gq number joined")
        add_setting(self.plugin_id, "maxkills", False, bool, "no qp because of maxkills")
        self.api("plugins.core.mudcmds:type.add")(
            CMDTYPE, CMD, CMD_REGEX, beforef=self._check_before, afterf=self._check_after
        )
        self.api("plugins.core.watch:watch.add")(WATCH_NAME, WATCH_REGEX)
        self.api("plugins.core.events:event.register")(f"watch_{WATCH_NAME}", self._watch_check)
        callbacks = self._trigger_callbacks()
        for spec in TRIGGERS:
            self._add_trigger(spec, callbacks.get(spec.name))
        self._check_if_joined()

    def _trigger_callbacks(self) -> dict[str, Callable[[], None]]:
        """Return the callback of each trigger, by trigger name."""
        return {
            "gq_declared": self._trigger_declared,
            "gq_joined": self._trigger_joined,
            "gq_started": self._trigger_started,
            "gq_cancelled": self._trigger_cancelled,
            "gq_quit": self._trigger_quit,
            "gq_note": self._trigger_note,
            "gq_maxkills": self._trigger_maxkills,
            "gq_none": self._trigger_none,
            "gq_item": self._trigger_item,
            "gq_notstarted": self._trigger_notstarted,
            "gq_wins": self._trigger_wins,
            "gq_mobdead": self._trigger_mobdead,
            "gq_extended": self._trigger_extended,
            "gq_won": self._trigger_won,
            "gq_extfin": self._trigger_extfin,
            "gq_wonannounce": self._trigger_wonannounce,
            "gq_reward": self._trigger_reward,
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

    def _toggle_all_groups(self, flag: bool) -> None:
        """Turn every trigger group on or off."""
        for suffix in _ALL_GROUPS:
            self._toggle_group(suffix, flag)

    def _queue_check(self) -> None:
        """Queue a ``gq check``."""
        self.api("plugins.core.mudcmds:command.queue")(CMDTYPE)

    def _check_if_joined(self) -> None:
        """Queue a check when a gquest is joined and the character is active."""
        if self._joined() != _NOT_JOINED and self.api("libs.api:character.is.active")():
            self._queue_check()

    @staticmethod
    def _now() -> float:
        """Return the current time."""
        return time.time()

    def _joined(self) -> int:
        """Return the number of the gquest joined, or -1."""
        return int(self.api("plugins.core.settings:setting.get")(self.plugin_id, "joined"))

    def _maxkills(self) -> bool:
        """Return True when the kills no longer earn quest points."""
        return bool(self.api("plugins.core.settings:setting.get")(self.plugin_id, "maxkills"))

    def _set(self, name: str, value: object) -> None:
        """Change a setting of the plugin."""
        self.api("plugins.core.settings:setting.set")(self.plugin_id, name, value)

    def _gmcp_value(self, path: str) -> object:
        """Return the cached GMCP value at a dotted path, or None."""
        return self.api("libs.net.protocols:gmcp.value.get")(path)

    def _record(self) -> dict[str, Any]:
        """Return the record of the current event."""
        return dict(self.api("plugins.core.events:event.current.record.get")() or {})

    def _matches(self) -> dict[str, Any]:
        """Return the groups the current trigger matched."""
        return dict(self._record().get("matches") or {})

    def _sync(self) -> None:
        """Write the state and the mobs left."""
        self.gqinfo.sync()
        self.track.sync()

    def _raise(self, name: str, payload: dict[str, Any] | None = None) -> None:
        """Raise an event with a payload that is a copy, so no one changes the state."""
        self._sync()
        if payload:
            self.api("plugins.core.events:event.raise")(name, event_args=copy.deepcopy(payload))
        else:
            self.api("plugins.core.events:event.raise")(name)

    def _state_payload(self) -> dict[str, Any]:
        """Return a copy of the state."""
        return copy.deepcopy(dict(self.gqinfo))

    def _mobsleft(self) -> list[dict[str, Any]]:
        """Return the mobs left, not a copy."""
        return list(self.track.get("mobsleft", []))

    def _mobsleft_payload(self) -> dict[str, Any]:
        """Return the payload of the mobsleft event."""
        return {"mobsleft": copy.deepcopy(self._mobsleft())}

    # the gq check command

    def _watch_check(self) -> None:
        """A client typed ``gq check``: forget the mobs left and read the output."""
        self.track["mobsleft"] = []
        self._toggle_group(GROUP_CHECK, True)

    def _check_before(self) -> None:
        """Before ``gq check`` is sent: forget the mobs left and read the output."""
        self._watch_check()
        self.api("plugins.core.mudcmds:command.start")(CMDTYPE)

    def _check_after(self) -> None:
        """After ``gq check`` finished: stop reading the check."""
        self._toggle_group(GROUP_CHECK, False)

    # state

    def _gq_new(self) -> None:
        """Start a new state and forget the mobs left."""
        level = aardu.actual_level_from_gmcp(self._gmcp_value)
        self.gqinfo.clear()
        self.gqinfo.update(new_state(level))
        self.track["mobsleft"] = []
        self._set("maxkills", False)
        self._sync()

    def _forget(self, gqnum: int) -> None:
        """Take a gquest off the declared and the started ones."""
        self._declared.discard(gqnum)
        self._started.discard(gqnum)

    def _reset_quietly(self) -> None:
        """Leave the gquest: new state, nothing joined, every group off, no events."""
        self._gq_new()
        self._set("joined", _NOT_JOINED)
        self._toggle_all_groups(False)
        self._await_kill = False

    def _gq_reset(self, gqnum: int) -> None:
        """Leave the gquest and take it off the declared ones."""
        self._reset_quietly()
        self._forget(gqnum)
        self._check_available()

    def _check_available(self) -> None:
        """Raise whether a gquest is declared."""
        self._raise(EVENT_AVAILABLE if self._declared else EVENT_NOTAVAILABLE)

    def _finish_done(self) -> None:
        """Raise done when gquest mobs were killed."""
        if self.gqinfo.get("qpmobs", 0) > 0:
            self.gqinfo["finishtime"] = self._now()
            self._raise(EVENT_DONE, self._state_payload())

    def _start(self, gqnum: int) -> None:
        """A gquest started: raise it once, and follow it when it is the one joined."""
        if gqnum not in self._started:
            self._started.add(gqnum)
            self._raise(EVENT_STARTED, {"gqnum": gqnum})
            self._check_available()
        if self._joined() == gqnum:
            self.gqinfo["starttime"] = self._now()
            self._toggle_group(GROUP_IN, True)
            self._queue_check()

    # triggers

    def _trigger_declared(self) -> None:
        """A gquest was declared."""
        matches = self._matches()
        gqnum = int(matches["gqnum"])
        self._declared.add(gqnum)
        self._raise(
            EVENT_DECLARED,
            {
                "gqnum": gqnum,
                "lowlev": matches.get("lowlev"),
                "highlev": matches.get("highlev"),
            },
        )
        self._check_available()

    def _trigger_joined(self) -> None:
        """The character joined a gquest."""
        gqnum = int(self._matches()["gqnum"])
        self._gq_new()
        self._set("joined", gqnum)
        if gqnum in self._started:
            self._start(gqnum)
        elif gqnum not in self._declared:
            self._declared.add(gqnum)
            self._start(gqnum)
        self._raise(EVENT_JOINED, {"gqnum": gqnum})

    def _trigger_started(self) -> None:
        """A gquest started."""
        self._start(int(self._matches()["gqnum"]))

    def _trigger_cancelled(self) -> None:
        """A gquest was cancelled."""
        gqnum = int(self._matches()["gqnum"])
        self._raise(EVENT_CANCELLED, {"gqnum": gqnum})
        if gqnum == self._joined():
            self._finish_done()
            self._gq_reset(gqnum)
        else:
            self._forget(gqnum)
            self._check_available()

    def _trigger_quit(self) -> None:
        """The character quit the gquest."""
        self._finish_done()
        self._gq_reset(int(self._matches()["gqnum"]))

    def _trigger_note(self) -> None:
        """The note of a finished gquest was posted."""
        gqnum = int(self._matches()["gqnum"])
        if gqnum == self._joined():
            self._finish_done()
            self._gq_reset(gqnum)
        else:
            self._forget(gqnum)
            self._check_available()

    def _trigger_maxkills(self) -> None:
        """The kills no longer earn quest points."""
        self._set("maxkills", True)

    def _trigger_item(self) -> None:
        """A target mob, in the check output."""
        matches = self._matches()
        name = str(matches.get("mob") or "")
        location = str(matches.get("location") or "")
        num = int(matches.get("num") or 0)
        if not name or not location or not num:
            log_to([self.plugin_id], logging.DEBUG, "error parsing the mob line: %s", matches)
            return
        mobsleft = self._mobsleft()
        mobsleft.append(new_mob(name, location, num))
        self.track["mobsleft"] = mobsleft

    def _trigger_none(self) -> None:
        """The character is not in a gquest."""
        joined = self._joined()
        self._trigger_notstarted()
        if joined != _NOT_JOINED:
            # the gquest ended while the proxy did not see it
            self._forget(joined)
            self._reset_quietly()

    def _trigger_notstarted(self) -> None:
        """The end of a check of a gquest that is not on."""
        # finish first: the after function of the check turns the check group off
        self.api("plugins.core.mudcmds:command.finish")(CMDTYPE)
        self._toggle_group(GROUP_CHECK, False)
        self._toggle_group(GROUP_IN, False)

    def _trigger_wins(self) -> None:
        """The end of the check output: raise the mobs left and finish the command."""
        if not self.gqinfo.get("mobs"):
            self.gqinfo["mobs"] = copy.deepcopy(self._mobsleft())
        self._raise(EVENT_MOBSLEFT, self._mobsleft_payload())
        self.api("plugins.core.mudcmds:command.finish")(CMDTYPE)
        self._toggle_group(GROUP_CHECK, False)
        if self._joined() != _NOT_JOINED:
            self._toggle_group(GROUP_IN, True)

    def _trigger_mobdead(self) -> None:
        """A gquest mob died: the next mobk kill is its kill."""
        if not self._maxkills():
            self.gqinfo["qpmobs"] = self.gqinfo.get("qpmobs", 0) + 3
            self.gqinfo.sync()
        self._await_kill = True

    def _trigger_extended(self) -> None:
        """The gquest went into extended time."""
        if int(self._matches()["gqnum"]) == self._joined():
            self.gqinfo["extended"] = 1
            self.gqinfo.sync()

    def _trigger_won(self) -> None:
        """The character was the first to complete the gquest: read the rewards."""
        self.gqinfo["won"] = 1
        self.gqinfo["finishtime"] = self._now()
        self.gqinfo.sync()
        self._toggle_group(GROUP_REW, True)

    def _trigger_wonannounce(self) -> None:
        """The MUD announced who won the gquest."""
        matches = self._matches()
        if self._gmcp_value("char.base.name") == matches.get("winner"):
            self._raise(EVENT_WON, self._state_payload())
            self._gq_reset(int(matches["gqnum"]))

    def _trigger_reward(self) -> None:
        """A reward of the gquest."""
        matches = self._matches()
        rtype = str(matches.get("type", ""))
        key = reward_key(rtype)
        if key is None:
            log_to([self.plugin_id], logging.DEBUG, "unknown reward type: %s", rtype)
            return
        self.gqinfo[key] = int(matches.get("amount", 0))
        self.gqinfo.sync()

    def _trigger_extfin(self) -> None:
        """The character finished the gquest in extended time."""
        if self.gqinfo.get("qpmobs", 0) > 0:
            gqnum = self._joined()
            self.gqinfo["completed"] = 1
            self.gqinfo["finishtime"] = self._now()
            self._raise(EVENT_COMPLETED, self._state_payload())
            self._gq_reset(gqnum)

    # events

    @RegisterToEvent(event_name=EVENT_MOBK_KILL)
    def _eventcb_mobk_kill(self) -> None:
        """A mob was killed: when it was a gquest mob, count it down in the mobs left."""
        if not self._await_kill:
            return
        self._await_kill = False
        name = str(self._record().get("name", ""))
        mobsleft = copy.deepcopy(self._mobsleft())
        if count_down(mobsleft, name):
            self.track["mobsleft"] = mobsleft
            self._raise(EVENT_MOBSLEFT, self._mobsleft_payload())
        else:
            log_to([self.plugin_id], logging.DEBUG, "could not find the mob: %s", name)
            self._queue_check()

    @RegisterToEvent(event_name=EVENT_CHAR_ACTIVE)
    def _eventcb_character_active(self) -> None:
        """The character is active: check the gquest when one is joined."""
        if self._record().get("is_character_active") and self._joined() != _NOT_JOINED:
            self._queue_check()

    @RegisterToEvent(event_name=EVENT_DISCONNECT)
    def _eventcb_disconnect(self) -> None:
        """Turn the groups off and forget that a gquest mob died."""
        self._await_kill = False
        self._toggle_all_groups(False)

    @RegisterPluginHook("save")
    def _phook_save(self) -> None:
        """Save the gquest and the mobs left."""
        self._sync()
