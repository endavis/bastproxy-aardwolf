"""Tests for the Aardwolf gq plugin, with a stubbed API that drives its triggers."""

import logging
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from event_keys import assert_raised_described
from statdb_support import make_db

import aardwolf
from aardwolf.gq.libs import (
    CMDTYPE,
    EVENT_AVAILABLE,
    EVENT_CANCELLED,
    EVENT_COMPLETED,
    EVENT_DECLARED,
    EVENT_DONE,
    EVENT_JOINED,
    EVENT_MOBSLEFT,
    EVENT_NOTAVAILABLE,
    EVENT_STARTED,
    EVENT_WON,
    EVENTS,
    TRIGGERS,
)
from aardwolf.libs.aardu import actual_level

if TYPE_CHECKING:
    from aardwolf.gq.plugin._gq import GqPlugin

PLUGIN_ID = "plugins.aardwolf.gq"
NOW = 1000.0
GMCP: dict[str, Any] = {
    "char.status.level": 50,
    "char.base.remorts": 2,
    "char.base.tier": 1,
    "char.base.redos": 0,
    "char.base.name": "Bast",
}
WHOIS = {"name": "Bast", "level": 50, "totallevels": 50, "remorts": 1, "classes": []}
LEVEL = actual_level(50, 2, 1, 0)
ALWAYS_ON = {
    "gq_declared",
    "gq_joined",
    "gq_started",
    "gq_cancelled",
    "gq_quit",
    "gq_note",
    "gq_maxkills",
}
DECLARED = "Global Quest: Global quest # 12 has been declared for levels 10 to 60 - some."
JOINED = "You have now joined Global Quest # 12. Type gq info"
STARTED = "Global Quest: Global quest # 12 for levels 10 to 60 has now started."
CANCELLED = "Global Quest: Global quest # 12 has been cancelled due to lack of activity."
QUIT = "You are no longer part of Global Quest # 12 and will be unable to rejoin."
NOTE = "INFO: New post #5 in forum Gquest from Aardwolf Subj: Lvl 10 to 60 - Global quest # 12"
NONE = "You are not in a global quest."
NOTSTARTED = "Global Quest # 12 has not yet started."
RAT = "You still have to kill 2 * A rat (Sewers)"
BAT = "You still have to kill 1 * A bat (Cave)."
WINS = "You may win 2 more gquests at this level."
DEAD = "Congratulations, that was one of the GLOBAL QUEST mobs!"
MAXKILLS = "You have reached the maximum 20 kills for which you can earn quest points this level."
EXTENDED = "Global Quest: Global Quest # 12 will go into extended time for 3 more minutes."
WON = "You were the first to complete this quest!"
EXTFIN = "You have finished this global quest."
ANNOUNCE = "Global Quest: Global Quest #12 has been won by Bast - 1st win."
REWARDS = (
    "  Reward of 120 quest points added.",
    "  Reward of 300 gold pieces added.",
    "  Reward of 4 trivia points added.",
    "  Reward of 5 training sessions added.",
    "  Reward of 6 practice sessions added.",
)
GROUPS = ("gqcheck", "gqin", "gqrew")


class FakeApi:
    """A stand-in for the bastproxy API that records the calls and drives the triggers."""

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        self.gmcp: dict[str, Any] = dict(GMCP)
        self.settings: dict[str, Any] = {} if settings is None else settings
        self.setting_defaults: dict[str, Any] = {}
        self.events_added: dict[str, dict[str, Any]] = {}
        self.event_cbs: dict[str, list[Callable[..., Any]]] = {}
        self.watches: dict[str, str] = {}
        self.raised: list[tuple[str, dict[str, Any] | None]] = []
        self.triggers: dict[str, str] = {}
        self.kwargs: dict[str, dict[str, Any]] = {}
        self.trigger_cbs: dict[str, list[Callable[..., Any]]] = {}
        self.enabled: dict[str, bool] = {}
        self.toggles: list[tuple[str, bool]] = []
        self.add_ok = True
        self.record: dict[str, Any] = {}
        self.active = False
        self.types: dict[str, dict[str, Any]] = {}
        self.queued: list[str] = []
        self.started: list[str] = []
        self.finished: list[str] = []
        self.current: str | None = None
        self.table: dict[str, Callable[..., Any]] = {
            "plugins.core.events:event.add": self._event_add,
            "plugins.core.events:event.register": self._event_register,
            "plugins.core.events:event.raise": self._event_raise,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.watch:watch.add": self._watch_add,
            "plugins.core.settings:setting.add": self._setting_add,
            "plugins.core.settings:setting.get": lambda pid, name: self.settings[name],
            "plugins.core.settings:setting.set": self._setting_set,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
            "plugins.core.triggers:group.toggle.enable": self._group_toggle,
            "plugins.core.mudcmds:type.add": self._type_add,
            "plugins.core.mudcmds:command.queue": self._command_queue,
            "plugins.core.mudcmds:command.start": self.started.append,
            "plugins.core.mudcmds:command.finish": self._command_finish,
            "libs.net.protocols:gmcp.value.get": self.gmcp.get,
            "libs.api:character.is.active": lambda: self.active,
        }

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name; an unknown name is a KeyError."""
        return self.table[name]

    def _event_add(self, name: str, created_by: str, **kwargs: object) -> None:
        self.events_added[name] = kwargs

    def _event_register(self, name: str, func: Callable[..., Any]) -> None:
        self.event_cbs.setdefault(name, []).append(func)

    def _event_raise(self, name: str, event_args: dict[str, Any] | None = None) -> None:
        self.raised.append((name, event_args))

    def _watch_add(self, name: str, regex: str) -> bool:
        self.watches[name] = regex
        return True

    def _setting_add(
        self, pid: str, name: str, default: object, stype: object, help_text: str
    ) -> None:
        self.setting_defaults[name] = default
        self.settings.setdefault(name, default)

    def _setting_set(self, pid: str, name: str, value: object) -> bool:
        assert name in self.settings, f"unknown setting {name}"
        self.settings[name] = value
        return True

    def _trigger_add(self, name: str, regex: str, **kwargs: object) -> SimpleNamespace:
        self.triggers[name] = regex
        self.kwargs[name] = dict(kwargs)
        self.enabled[name] = bool(kwargs.get("enabled", True))
        self.trigger_cbs.setdefault(name, [])
        return SimpleNamespace(success=self.add_ok, trigger=SimpleNamespace(trigger_id=name))

    def _trigger_register(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        assert trigger_id in self.trigger_cbs, f"unknown trigger {trigger_id}"
        self.trigger_cbs[trigger_id].append(func)
        return True

    def _group_toggle(self, group: str, flag: bool) -> None:
        self.toggles.append((group, flag))
        for name, kwargs in self.kwargs.items():
            if kwargs.get("group") == group:
                self.enabled[name] = flag

    def _type_add(self, cmdtype: str, cmd: str, regex: str, **kwargs: object) -> None:
        self.types[cmdtype] = dict(kwargs)

    def _command_queue(self, cmdtype: str, arguments: str = "") -> None:
        self.queued.append(cmdtype)
        if self.current is None:
            self.current = cmdtype
            self.types[cmdtype]["beforef"]()

    def _command_finish(self, cmdtype: str) -> None:
        self.finished.append(cmdtype)
        if self.current == cmdtype:
            self.current = None
            self.types[cmdtype]["afterf"]()

    def group_on(self, suffix: str) -> bool:
        """Return True when every trigger of the group is on."""
        group = f"{PLUGIN_ID}.{suffix}"
        names = [n for n, k in self.kwargs.items() if k.get("group") == group]
        assert names
        return all(self.enabled[n] for n in names)

    def feed(self, *lines: str) -> None:
        """Run each line through the enabled triggers."""
        for line in lines:
            for name, regex in list(self.triggers.items()):
                match = re.match(regex, line)
                if not match or not self.enabled[name]:
                    continue
                groups = match.groupdict()
                for arg, argtype in (self.kwargs[name].get("argtypes") or {}).items():
                    groups[arg] = argtype(groups[arg])
                self.record = {"matches": groups}
                for func in list(self.trigger_cbs[name]):
                    func()

    def type_watch(self, command: str) -> None:
        """A client types a command: call what is registered on the watch it matches."""
        for name, regex in self.watches.items():
            if re.match(regex, command):
                for func in list(self.event_cbs.get(f"watch_{name}", [])):
                    func()

    def events(self, name: str) -> list[dict[str, Any]]:
        """The payloads raised for an event; an event raised without args has {}."""
        return [payload or {} for event, payload in self.raised if event == name]

    def names(self) -> list[str]:
        """The names of the raised events, without the prefix."""
        return [event.removeprefix("ev_plugins.aardwolf.gq_") for event, _ in self.raised]


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: "GqPlugin", fake: FakeApi, home: Path) -> None:
        self.plugin = plugin
        self.fake = fake
        self.home = home

    def kill(self, name: str) -> None:
        """The mobk plugin raises a kill."""
        self.fake.record = {"name": name}
        self.plugin._eventcb_mobk_kill()

    def join(self, *mobs: str) -> None:
        """Declare, join and start the gquest and read its check output."""
        self.fake.feed(DECLARED, JOINED, STARTED, *mobs, WINS)

    def win(self) -> None:
        """Win the gquest, read the rewards and the announce."""
        self.fake.feed(WON, *REWARDS, ANNOUNCE)


def build(home: Path, fake: FakeApi) -> "GqPlugin":
    """Build and load a plugin on a data directory."""
    from aardwolf.gq.plugin import _gq

    plugin = _gq.GqPlugin.__new__(_gq.GqPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.plugin_info = SimpleNamespace(data_directory=home)  # type: ignore[assignment]
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    plugin._phook_initialize()
    return plugin


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build a GqPlugin with a fake API and load it."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from aardwolf.gq.plugin import _gq

    monkeypatch.setattr(_gq.GqPlugin, "_now", staticmethod(lambda: NOW))
    fake = FakeApi()
    result = Env(build(tmp_path, fake), fake, tmp_path)
    yield result
    assert_raised_described(fake.raised, EVENTS)


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.gq" in {p["plugin_id"] for p in result.plugins}


def test_dependencies() -> None:
    """The plugin needs watch, mudcmds and settings, and not mobk."""
    from aardwolf import gq

    for needed in ("watch", "mudcmds", "settings", "events", "triggers"):
        assert f"plugins.core.{needed}" in gq.PLUGIN_DEPENDENCIES
    assert "plugins.aardwolf.connect" in gq.PLUGIN_DEPENDENCIES
    assert "plugins.aardwolf.mobk" not in gq.PLUGIN_DEPENDENCIES


def test_after_load_adds_everything(env: Env) -> None:
    """The events, triggers, groups, watch, command type and settings are added."""
    fake = env.fake
    assert set(fake.events_added) == set(EVENTS)
    assert all(kw["description"] for kw in fake.events_added.values())
    assert set(fake.triggers) == {spec.name for spec in TRIGGERS}
    assert {n for n, on in fake.enabled.items() if on} == ALWAYS_ON
    assert all(
        fake.kwargs[n]["group"].startswith(f"{PLUGIN_ID}.")
        for n in fake.kwargs
        if n not in ALWAYS_ON
    )
    assert not any("omit" in kw for kw in fake.kwargs.values())
    assert set(fake.types) == {CMDTYPE}
    assert "gq_check" in fake.watches
    assert fake.setting_defaults == {"joined": -1, "maxkills": False}


def test_declared(env: Env) -> None:
    """A declared gquest raises declared with its numbers, then available."""
    env.fake.feed(DECLARED)
    assert env.fake.events(EVENT_DECLARED) == [{"gqnum": 12, "lowlev": "10", "highlev": "60"}]
    assert env.fake.names() == ["declared", "available"]


def test_join_declared_not_started(env: Env) -> None:
    """Joining resets the state, sets joined and raises joined, not started."""
    env.plugin.gqinfo["qp"] = 99
    env.fake.feed(DECLARED, JOINED)
    assert env.fake.events(EVENT_JOINED) == [{"gqnum": 12}]
    assert env.fake.settings["joined"] == 12
    assert env.plugin.gqinfo["qp"] == 0
    assert env.plugin.gqinfo["level"] == LEVEL
    assert env.plugin.track["mobsleft"] == []
    assert env.fake.events(EVENT_STARTED) == []
    assert env.fake.queued == []


def test_start_of_the_joined_gquest(env: Env) -> None:
    """The start raises started, sets starttime, turns gqin on and queues a check."""
    env.fake.feed(DECLARED, JOINED, STARTED)
    assert env.fake.events(EVENT_STARTED) == [{"gqnum": 12}]
    assert env.plugin.gqinfo["starttime"] == NOW
    assert env.fake.group_on("gqin")
    assert env.fake.queued == [CMDTYPE]
    assert env.fake.started == [CMDTYPE]
    assert env.fake.group_on("gqcheck")


def test_start_twice_raises_started_once(env: Env) -> None:
    """A second start line does not raise started again."""
    env.fake.feed(DECLARED, STARTED, STARTED)
    assert len(env.fake.events(EVENT_STARTED)) == 1
    assert env.fake.queued == []


def test_join_of_an_undeclared_gquest(env: Env) -> None:
    """Joining a gquest never seen declared raises started and joined."""
    env.fake.feed(JOINED)
    assert env.fake.names() == ["started", "available", "joined"]
    assert env.fake.group_on("gqin")


def test_check_output_raises_the_mobs(env: Env) -> None:
    """The item lines and the wins line fill mobs once and raise mobsleft."""
    env.join(RAT, BAT)
    expected = [
        {"name": "A rat", "nocolorname": "A rat", "location": "Sewers", "num": 2},
        {"name": "A bat", "nocolorname": "A bat", "location": "Cave", "num": 1},
    ]
    assert env.fake.events(EVENT_MOBSLEFT) == [{"mobsleft": expected}]
    assert env.plugin.gqinfo["mobs"] == expected
    assert env.fake.finished == [CMDTYPE]
    assert not env.fake.group_on("gqcheck")
    assert env.fake.group_on("gqin")


def test_second_check_does_not_overwrite_the_mobs(env: Env) -> None:
    """The original mobs stay after a later check."""
    env.join(RAT)
    env.fake.queued.clear()
    env.plugin._queue_check()
    env.fake.feed(BAT, WINS)
    assert [m["name"] for m in env.plugin.gqinfo["mobs"]] == ["A rat"]
    assert [m["name"] for m in env.fake.events(EVENT_MOBSLEFT)[1]["mobsleft"]] == ["A bat"]


def test_item_line_with_no_mob_is_ignored(env: Env) -> None:
    """A target line that cannot be parsed adds nothing and is logged."""
    env.fake.feed(DECLARED, JOINED, STARTED)
    env.fake.record = {"matches": {"mob": "", "location": "Sewers", "num": 2}}
    env.plugin._trigger_item()
    assert env.plugin.track["mobsleft"] == []


@pytest.mark.parametrize("command", ["gq c", "gq check", "gquest check", "gqu che"])
def test_typed_check_clears_the_mobs_and_turns_the_group_on(env: Env, command: str) -> None:
    """A check the client types reads the output."""
    env.plugin.track["mobsleft"] = [{"name": "x"}]
    env.fake.feed(DECLARED, JOINED)
    env.fake.type_watch(command)
    assert env.plugin.track["mobsleft"] == []
    assert env.fake.group_on("gqcheck")


def test_other_commands_do_not_trigger_the_watch(env: Env) -> None:
    """A command that is not a check leaves the group off."""
    env.fake.type_watch("gq info")
    env.fake.type_watch("gq join")
    assert env.fake.toggles == []


def test_not_started_and_not_in_a_gquest_turn_groups_off(env: Env) -> None:
    """The not-started and not-in lines end the check with the groups off."""
    for line in (NOTSTARTED, NONE):
        env.fake.feed(DECLARED, JOINED, STARTED)
        env.fake.finished.clear()
        env.fake.feed(line)
        assert env.fake.finished == [CMDTYPE]
        assert not env.fake.group_on("gqcheck")
        assert not env.fake.group_on("gqin")


def test_not_in_a_gquest_while_joined_resets_quietly(env: Env) -> None:
    """The gquest ended unseen: joined goes back to -1 and nothing is raised."""
    env.join(RAT)
    env.fake.raised.clear()
    env.plugin.gqinfo["qpmobs"] = 6
    env.fake.type_watch("gq check")
    env.fake.feed(NONE)
    assert env.fake.settings["joined"] == -1
    assert env.fake.raised == []
    assert env.plugin.gqinfo["qpmobs"] == 0


def test_mob_dead_then_kill(env: Env) -> None:
    """The dead line adds 3 qpmobs; the kill counts down the first mob and raises once."""
    env.join(RAT, BAT)
    env.fake.raised.clear()
    env.fake.feed(DEAD)
    assert env.plugin.gqinfo["qpmobs"] == 3
    env.kill("A rat")
    assert [(m["name"], m["num"]) for m in env.plugin.track["mobsleft"]] == [
        ("A rat", 1),
        ("A bat", 1),
    ]
    env.fake.feed(DEAD)
    env.kill("A rat")
    assert [m["name"] for m in env.plugin.track["mobsleft"]] == ["A bat"]
    assert len(env.fake.events(EVENT_MOBSLEFT)) == 2
    env.fake.feed(DEAD)
    env.kill("A bat")
    assert env.plugin.track["mobsleft"] == []


def test_kill_is_handled_once(env: Env) -> None:
    """A second kill without a dead line changes nothing."""
    env.join(RAT)
    env.fake.feed(DEAD)
    env.kill("A rat")
    before = len(env.fake.events(EVENT_MOBSLEFT))
    env.kill("A rat")
    assert len(env.fake.events(EVENT_MOBSLEFT)) == before
    assert env.plugin.track["mobsleft"][0]["num"] == 1


def test_maxkills_stops_the_qp(env: Env) -> None:
    """With the maxkills line seen, a dead mob adds no qpmobs."""
    env.join(RAT)
    env.fake.feed(MAXKILLS)
    assert env.fake.settings["maxkills"] is True
    env.fake.feed(DEAD)
    assert env.plugin.gqinfo["qpmobs"] == 0


def test_kill_of_an_unknown_mob_queues_a_check(env: Env, caplog: pytest.LogCaptureFixture) -> None:
    """A kill that matches no target queues a check."""
    env.join(RAT)
    env.fake.queued.clear()
    env.fake.feed(DEAD)
    with caplog.at_level(logging.DEBUG):
        env.kill("A dragon")
    assert env.fake.queued == [CMDTYPE]


def test_no_kill_event_leaves_the_mobs_left(env: Env) -> None:
    """Without mobk no kill event arrives, and the mobs wait for the next check."""
    env.join(RAT)
    env.fake.feed(DEAD)
    assert [m["num"] for m in env.plugin.track["mobsleft"]] == [2]


def test_extended_time_only_for_the_joined_gquest(env: Env) -> None:
    """The extended line sets extended for the joined gquest only."""
    env.join(RAT)
    env.fake.feed(EXTENDED.replace("# 12", "# 13"))
    assert env.plugin.gqinfo["extended"] == 0
    env.fake.feed(EXTENDED)
    assert env.plugin.gqinfo["extended"] == 1


def test_win(env: Env) -> None:
    """A win raises won with the rewards, then leaves the gquest."""
    env.join(RAT)
    env.fake.feed(DEAD)
    env.fake.raised.clear()
    env.win()
    (payload,) = env.fake.events(EVENT_WON)
    assert payload["won"] == 1
    assert payload["finishtime"] == NOW
    assert (payload["qp"], payload["gold"], payload["tp"]) == (120, 300, 4)
    assert (payload["trains"], payload["pracs"], payload["qpmobs"]) == (5, 6, 3)
    assert env.fake.settings["joined"] == -1
    assert isinstance(env.fake.settings["joined"], int)
    assert not any(env.fake.group_on(group) for group in GROUPS)
    assert env.plugin.gqinfo["won"] == 0


def test_announce_of_another_winner_does_nothing(env: Env) -> None:
    """Someone else winning leaves the state alone."""
    env.join(RAT)
    env.fake.raised.clear()
    env.fake.feed(ANNOUNCE.replace("Bast", "Other"))
    assert env.fake.raised == []
    assert env.fake.settings["joined"] == 12


def test_announce_of_another_gquest_does_nothing(env: Env) -> None:
    """A win announced for a gquest other than the one joined leaves the state alone."""
    env.join(RAT)
    env.fake.raised.clear()
    env.fake.feed(ANNOUNCE.replace("#12", "#13"))
    assert env.fake.raised == []
    assert env.fake.settings["joined"] == 12


def test_quoted_announce_does_not_match(env: Env) -> None:
    """An announce quoted inside another line, such as a channel, raises nothing."""
    env.join(RAT)
    env.fake.raised.clear()
    env.fake.feed(f"(Gossip) Other: {ANNOUNCE}")
    assert env.fake.raised == []
    assert env.fake.settings["joined"] == 12


def test_unknown_reward_type_is_ignored(env: Env) -> None:
    """A reward of an unknown type changes nothing."""
    env.join(RAT)
    env.fake.feed(WON, "  Reward of 5 widgets and more added.")
    assert env.plugin.gqinfo["qp"] == 0


def test_finished_in_extended_time(env: Env) -> None:
    """Finishing in extended time with kills raises completed and leaves."""
    env.join(RAT)
    env.fake.feed(DEAD, EXTENDED, EXTFIN)
    (payload,) = env.fake.events(EVENT_COMPLETED)
    assert payload["completed"] == 1
    assert payload["extended"] == 1
    assert env.fake.settings["joined"] == -1


def test_finished_in_extended_time_without_kills(env: Env) -> None:
    """Without kills nothing is raised and the gquest goes on."""
    env.join(RAT)
    env.fake.raised.clear()
    env.fake.feed(EXTFIN)
    assert env.fake.raised == []
    assert env.fake.settings["joined"] == 12


def test_quit_with_kills_raises_done(env: Env) -> None:
    """Quitting after kills raises done and resets."""
    env.join(RAT)
    env.fake.feed(DEAD, QUIT)
    (payload,) = env.fake.events(EVENT_DONE)
    assert payload["qpmobs"] == 3
    assert env.fake.settings["joined"] == -1
    assert env.fake.events(EVENT_NOTAVAILABLE) != []


def test_quit_without_kills_only_resets(env: Env) -> None:
    """Quitting with no kills raises no done."""
    env.join(RAT)
    env.fake.feed(QUIT)
    assert env.fake.events(EVENT_DONE) == []
    assert env.fake.settings["joined"] == -1


def test_cancel_of_the_joined_gquest(env: Env) -> None:
    """Cancelling the joined gquest raises cancelled, done after kills, then resets."""
    env.join(RAT)
    env.fake.feed(DEAD)
    env.fake.raised.clear()
    env.fake.feed(CANCELLED)
    assert env.fake.events(EVENT_CANCELLED) == [{"gqnum": 12}]
    assert len(env.fake.events(EVENT_DONE)) == 1
    assert env.fake.names()[:2] == ["cancelled", "done"]
    assert env.fake.settings["joined"] == -1


def test_cancel_of_another_gquest(env: Env) -> None:
    """Cancelling a gquest that is not joined removes it and raises notavailable."""
    env.fake.feed(DECLARED, STARTED)
    env.fake.raised.clear()
    env.fake.feed(CANCELLED)
    assert env.fake.names() == ["cancelled", "notavailable"]
    assert env.plugin._declared == set()
    assert env.plugin._started == set()
    assert env.fake.events(EVENT_AVAILABLE) == []


def test_note_of_the_joined_gquest(env: Env) -> None:
    """The note of the joined gquest raises done after kills and clears the lists."""
    env.join(RAT)
    env.fake.feed(DEAD, NOTE)
    assert len(env.fake.events(EVENT_DONE)) == 1
    assert env.fake.settings["joined"] == -1
    assert env.plugin._declared == set()


def test_note_of_another_gquest_clears_the_lists(env: Env) -> None:
    """The note clears the declared and started lists, joined or not."""
    env.fake.feed(DECLARED, STARTED, NOTE)
    assert env.plugin._declared == set()
    assert env.plugin._started == set()
    assert env.fake.events(EVENT_DONE) == []
    assert env.fake.events(EVENT_NOTAVAILABLE) != []


def test_payloads_are_plain_copies(env: Env) -> None:
    """A payload is a plain dict, and changing it does not change the state."""
    env.join(RAT)
    payload = env.fake.events(EVENT_MOBSLEFT)[0]
    assert type(payload) is dict
    payload["mobsleft"][0]["name"] = "changed"
    assert env.plugin.track["mobsleft"][0]["name"] == "A rat"
    env.fake.feed(DEAD, QUIT)
    done = env.fake.events(EVENT_DONE)[0]
    assert type(done) is dict
    assert type(done["mobs"]) is list
    done["mobs"].clear()
    assert env.plugin.gqinfo["mobs"] == []
    assert set(done) == {
        "mobs",
        "trains",
        "pracs",
        "gold",
        "tp",
        "qp",
        "qpmobs",
        "level",
        "starttime",
        "finishtime",
        "length",
        "won",
        "completed",
        "extended",
    }


def test_state_is_persisted_and_survives_a_reload(env: Env) -> None:
    """The state and the mobs left are on disk and a rebuilt plugin sees them."""
    from bastproxy.libs.persistentdict import PersistentDict

    env.join(RAT, BAT)
    env.fake.feed(MAXKILLS)
    saved = PersistentDict(PLUGIN_ID, env.home / "gq.txt", "c")
    assert len(saved["mobs"]) == 2
    left = PersistentDict(PLUGIN_ID, env.home / "gqmobsleft.txt", "c")
    assert len(left["mobsleft"]) == 2
    again_fake = FakeApi(env.fake.settings)
    again = build(env.home, again_fake)
    assert again_fake.settings["joined"] == 12
    assert again_fake.settings["maxkills"] is True
    assert len(again.gqinfo["mobs"]) == 2
    assert [m["name"] for m in again.track["mobsleft"]] == ["A rat", "A bat"]


def test_reload_with_an_active_character_checks_and_follows(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A reload while joined queues a check; the wins line turns gqin on."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    fake = FakeApi({"joined": 12, "maxkills": False})
    fake.active = True
    build(tmp_path, fake)
    assert fake.queued == [CMDTYPE]
    assert not fake.group_on("gqin")
    fake.feed(RAT, WINS)
    assert fake.group_on("gqin")


def test_reload_not_joined_or_inactive_queues_no_check(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Nothing is queued without a joined gquest or an active character."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    fake = FakeApi()
    fake.active = True
    build(tmp_path, fake)
    assert fake.queued == []
    other = FakeApi({"joined": 12, "maxkills": False})
    build(tmp_path, other)
    assert other.queued == []


def test_character_active_queues_a_check_only_when_joined(env: Env) -> None:
    """The active event checks the gquest when one is joined."""
    env.fake.record = {"is_character_active": True}
    env.plugin._eventcb_character_active()
    assert env.fake.queued == []
    env.fake.feed(DECLARED, JOINED)
    env.fake.record = {"is_character_active": False}
    env.plugin._eventcb_character_active()
    assert env.fake.queued == []
    env.fake.record = {"is_character_active": True}
    env.plugin._eventcb_character_active()
    assert env.fake.queued == [CMDTYPE]


def test_disconnect_turns_groups_off_and_clears_the_kill_flag(env: Env) -> None:
    """A disconnect turns every group off and forgets that a mob died."""
    env.join(RAT)
    env.fake.feed(DEAD)
    env.plugin._eventcb_disconnect()
    assert not any(env.fake.group_on(group) for group in GROUPS)
    env.kill("A rat")
    assert env.plugin.track["mobsleft"][0]["num"] == 2


def test_save_hook_syncs(env: Env) -> None:
    """The save hook writes both files."""
    from bastproxy.libs.persistentdict import PersistentDict

    env.plugin.gqinfo["extra"] = 1
    env.plugin.track["extra"] = 2
    env.plugin._phook_save()
    assert PersistentDict(PLUGIN_ID, env.home / "gq.txt", "c")["extra"] == 1
    assert PersistentDict(PLUGIN_ID, env.home / "gqmobsleft.txt", "c")["extra"] == 2


def test_failed_trigger_add_is_logged_and_group_not_toggled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A trigger that could not be added is logged and its group is never toggled."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    fake = FakeApi()
    fake.add_ok = False
    with caplog.at_level(logging.ERROR):
        plugin = build(tmp_path, fake)
    plugin._toggle_all_groups(True)
    assert fake.toggles == []
    assert plugin._groups_ready == set()


def test_won_payload_is_saved_by_statdb(env: Env, tmp_path: Path) -> None:
    """The gq_won payload feeds statdb's save_gq."""
    from aardwolf.statdb.libs import StatStore

    env.join(RAT, BAT)
    env.fake.feed(DEAD)
    env.win()
    payload = env.fake.events(EVENT_WON)[0]
    database = make_db(tmp_path / "db")
    try:
        store = StatStore(database)
        store.save_whois(WHOIS)
        store.save_gq(payload)
        row = database.select("SELECT * FROM gquests")[0]
        assert row["qp"] == 120
        assert row["qpmobs"] == 3
        assert row["level"] == LEVEL
        assert row["won"] == 1
        assert len(database.select("SELECT * FROM gqmobs")) == 2
        stat = database.select("SELECT gquestswon FROM stats WHERE milestone = 'current'")
        assert stat[0]["gquestswon"] == 1
    finally:
        database.close()


def test_done_payload_does_not_count_a_win(env: Env, tmp_path: Path) -> None:
    """The gq_done payload feeds save_gq without a win."""
    from aardwolf.statdb.libs import StatStore

    env.join(RAT)
    env.fake.feed(DEAD, QUIT)
    payload = env.fake.events(EVENT_DONE)[0]
    database = make_db(tmp_path / "db")
    try:
        store = StatStore(database)
        store.save_whois(WHOIS)
        store.save_gq(payload)
        stat = database.select("SELECT gquestswon FROM stats WHERE milestone = 'current'")
        assert stat[0]["gquestswon"] == 0
    finally:
        database.close()


def test_raised_keys_are_all_described(env: Env) -> None:
    """A global quest raises only keys its events describe in arg_descriptions (#43)."""
    env.join(RAT)
    env.fake.feed(DEAD)
    env.win()
    assert env.fake.events(EVENT_WON)
    assert_raised_described(env.fake.raised, EVENTS)
