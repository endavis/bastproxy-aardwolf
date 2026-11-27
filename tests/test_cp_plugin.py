"""Tests for the Aardwolf cp plugin, with a stubbed API that drives its triggers."""

import logging
import re
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from event_keys import assert_raised_described
from mudcmds_support import CoreHide
from statdb_support import make_db

import aardwolf
from aardwolf._libs.aardu import actual_level
from aardwolf.cp.libs import (
    ALL_LINES_ID,
    CHECK_HIDE_START,
    CMDTYPE,
    CMDTYPE_INFO,
    CP_DURATION,
    EVENT_QUESTMASTERS_CHANGED,
    HIDE_MAX_LINES,
    INFO_HIDE_START,
    MOBS_LEFT_COLUMNS,
    TRIGGERS,
)
from aardwolf.cp.libs import EVENTS as SUFFIX_EVENTS

if TYPE_CHECKING:
    from aardwolf.cp.plugin._cp import CpPlugin

PLUGIN_ID = "plugins.aardwolf.cp"
EVENT_COMP = f"ev_{PLUGIN_ID}_comp"
EVENT_FAILED = f"ev_{PLUGIN_ID}_failed"
EVENT_MOBSLEFT = f"ev_{PLUGIN_ID}_mobsleft"
EVENT_MOBSORIG = f"ev_{PLUGIN_ID}_mobsorig"
EVENTS = {f"ev_{PLUGIN_ID}_{suffix}": info for suffix, info in SUFFIX_EVENTS.items()}
NOW = 1000.0
GMCP: dict[str, Any] = {
    "char.status.level": 50,
    "char.base.remorts": 2,
    "char.base.tier": 1,
    "char.base.redos": 0,
}
WHOIS = {"name": "Bast", "level": 50, "totallevels": 50, "remorts": 1, "classes": []}
LEVEL = actual_level(50, 2, 1, 0)
NEW = "Commander Barcett tells you 'Type 'campaign info' to see what you must kill.'"
QUESTOR_NEW = "A QuestoR tells you 'Type 'campaign info' to see what you must kill.'"
NONE = "You are not currently on a campaign."
TIME = "You have 30 minutes to finish this campaign."
RAT = "You still have to kill * A rat (Sewers)"
BAT = "You still have to kill * A bat (Cave - Dead)"
DEAD = "Congratulations, that was one of your CAMPAIGN mobs!"
COMPLETE = "CONGRATULATIONS! You have completed your campaign."
DASHES = "-" * 62
BONUS = "You receive 15 quest points bonus for your first campaign completed today."
COUNT = "You have completed 2 campaigns today."
REWARDS = (
    "  Reward of 120 quest points added.",
    "  Reward of 300 gold pieces added.",
    "  Reward of 4 trivia points added.",
    "  Reward of 5 training sessions added.",
    "  Reward of 6 practice sessions added.",
)
GROUPS = ("cpcheck", "cpin", "cprew", "cpdone", "cpinfo")
INFO_COMPLETEBY = "Complete By........: [ 12:34PM on 30 Nov 2026 ]"
INFO_TIMELEFT_TEXT = "6 days, 23 hours and 56 minutes"
INFO_SECONDS_LEFT = 6 * 86400 + 23 * 3600 + 56 * 60
INFO_END = "Use 'cp check' to see only targets that you still need to kill."
INFO_CANTAKE = "You may take a campaign at this level."
INFO_NEEDTOLEVEL = "You will have to level before you can go on another campaign."


def info_lines(
    *targets: str,
    completeby: str = INFO_COMPLETEBY,
    level: int = 2,
) -> list[str]:
    """Return the lines of ``campaign info`` on a campaign, in the captured format.

    Each target is the text after ``Find and kill ``, such as ``1 * A rat (Sewers)``.
    """
    return [
        "-" * 26 + "[ YOUR CURRENT CAMPAIGN ]" + "-" * 22,
        completeby,
        f"Time Left  ........: [ {INFO_TIMELEFT_TEXT} ]",
        f"Level Taken........: [ {level:>5} ]",
        "Quest Points.......: [    27 ]",
        "Gold Coins.........: [  6613 ]",
        "-" * 28 + "[ Campaign Victims ]" + "-" * 26,
        "The targets for this campaign are:",
        *(f"Find and kill {target}" for target in targets),
        "-" * 74,
        INFO_END,
    ]


def info_for(*check_lines: str, level: int = 50) -> list[str]:
    """Return the info lines of the campaign whose ``campaign check`` lines are given."""
    targets = []
    for line in check_lines:
        found = re.match(r"You still have to kill \* (.*) \((.*?)(?: - Dead|)\)$", line)
        assert found is not None
        targets.append(f"1 * {found.group(1)} ({found.group(2)})")
    return info_lines(*targets, level=level)


class FakeApi:
    """A stand-in for the bastproxy API that records the calls and drives the triggers."""

    def __init__(self) -> None:
        self.gmcp: dict[str, Any] = dict(GMCP)
        self.events_added: dict[str, dict[str, Any]] = {}
        self.raised: list[tuple[str, dict[str, Any]]] = []
        self.triggers: dict[str, str] = {}
        self.kwargs: dict[str, dict[str, Any]] = {}
        self.trigger_cbs: dict[str, list[Callable[..., Any]]] = {}
        self.enabled: dict[str, bool] = {}
        self.toggles: list[tuple[str, bool]] = []
        self.add_ok = True
        self.questmasters = ["Commander Barcett", "A QuestoR"]
        self.record: dict[str, Any] = {}
        self.active = False
        self.omitted: list[str] = []
        self.shown: list[str] = []
        self.hidden: list[str] = []
        self.types: dict[str, dict[str, Any]] = {}
        self.cmds: dict[str, str] = {}
        # the real core hide window; the queue below is the fake's own
        self.core = CoreHide(lambda: self.record)
        self.queued: list[str] = []
        self.pending: list[str] = []
        self.started: list[str] = []
        self.finished: list[str] = []
        self.current: str | None = None
        self.tables: list[tuple[str, list[dict[str, str]], list[dict[str, str]]]] = []
        self.table: dict[str, Callable[..., Any]] = {
            "plugins.core.events:event.add": self._event_add,
            "plugins.core.events:event.raise": self._event_raise,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.aardwolf.config:questmasters.get": lambda: list(self.questmasters),
            "plugins.core.triggers:trigger.update": self._trigger_update,
            "plugins.core.triggers:trigger.register": self._trigger_register,
            "plugins.core.triggers:trigger.unregister": self._trigger_unregister,
            "plugins.core.triggers:group.toggle.enable": self._group_toggle,
            "plugins.core.mudcmds:type.add": self._type_add,
            "plugins.core.mudcmds:command.queue": self._command_queue,
            "plugins.core.mudcmds:command.start": self.started.append,
            "plugins.core.mudcmds:command.finish": self._command_finish,
            "plugins.core.utils:table.format": self._table_format,
            "libs.net.protocols:gmcp.value.get": self.gmcp.get,
            "libs.api:character.is.active": lambda: self.active,
        }

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name; an unknown name is a KeyError."""
        return self.table[name]

    def _event_add(self, name: str, created_by: str, **kwargs: object) -> None:
        self.events_added[name] = kwargs

    def _event_raise(self, name: str, event_args: dict[str, Any] | None = None) -> None:
        self.raised.append((name, event_args or {}))

    def _trigger_add(self, name: str, regex: str, **kwargs: object) -> SimpleNamespace:
        self.triggers[name] = regex
        self.kwargs[name] = dict(kwargs)
        self.enabled[name] = bool(kwargs.get("enabled", True))
        self.trigger_cbs.setdefault(name, [])
        return SimpleNamespace(success=self.add_ok, trigger=SimpleNamespace(trigger_id=name))

    def _trigger_update(self, name: str, data: dict[str, Any]) -> bool:
        self.triggers[name] = data["regex"]
        return True

    def _trigger_register(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        assert trigger_id == ALL_LINES_ID or trigger_id in self.trigger_cbs
        self.trigger_cbs.setdefault(trigger_id, []).append(func)
        return True

    def _trigger_unregister(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        self.trigger_cbs[trigger_id].remove(func)
        return True

    def _group_toggle(self, group: str, flag: bool) -> None:
        self.toggles.append((group, flag))
        for name, kwargs in self.kwargs.items():
            if kwargs.get("group") == group:
                self.enabled[name] = flag

    def _table_format(
        self, title: str, data: Iterable[dict[str, str]], columns: list[dict[str, str]]
    ) -> list[str]:
        """Record a table.format call and return its title as the lines."""
        self.tables.append((title, list(data), columns))
        return [title]

    def _type_add(self, cmdtype: str, cmd: str, regex: str, **kwargs: object) -> None:
        self.types[cmdtype] = dict(kwargs)
        self.cmds[cmdtype] = cmd
        self.core.add_type(cmdtype, cmd, regex, **kwargs)

    def _command_queue(self, cmdtype: str, arguments: str = "") -> None:
        """Queue a command like mudcmds: one already pending or running is not queued twice."""
        if cmdtype in self.pending or cmdtype == self.current:
            return
        self.queued.append(cmdtype)
        if self.current is None:
            self.current = cmdtype
            self.types[cmdtype]["beforef"]()
            self.core.sent(cmdtype, self.cmds[cmdtype])
        else:
            self.pending.append(cmdtype)

    def _command_finish(self, cmdtype: str) -> None:
        """Finish the command, run its after function and send the next one."""
        self.finished.append(cmdtype)
        if self.current == cmdtype:
            self.current = None
            self.types[cmdtype]["afterf"]()
            self.core.finished(cmdtype)
            if self.pending and self.current is None:
                self.current = self.pending.pop(0)
                self.types[self.current]["beforef"]()
                self.core.sent(self.current, self.cmds[self.current])

    def disconnect(self) -> None:
        """The MUD link closed: the core drops its hide windows."""
        self.core.disconnect()

    def group_on(self, suffix: str) -> bool:
        """Return True when every trigger of the group is on."""
        group = f"{PLUGIN_ID}.{suffix}"
        names = [n for n, k in self.kwargs.items() if k.get("group") == group]
        assert names
        return all(self.enabled[n] for n in names)

    def feed(self, *lines: str, prompt: bool = False) -> None:
        """Run each line through the enabled triggers and then the every-line callbacks."""
        for line in lines:
            line_obj = SimpleNamespace(noansi=line, is_prompt=prompt, send=True, internal=False)
            self.record = {"matches": {}, "line": line_obj}
            self.core.line()
            for name, regex in list(self.triggers.items()):
                match = re.match(regex, line)
                if not match or not self.enabled[name]:
                    continue
                groups = match.groupdict()
                for arg, argtype in (self.kwargs[name].get("argtypes") or {}).items():
                    groups[arg] = argtype(groups[arg])
                if self.kwargs[name].get("omit"):
                    self.omitted.append(line)
                    line_obj.send = False
                self.record = {"matches": groups, "line": line_obj}
                for func in list(self.trigger_cbs[name]):
                    func()
            self.record = {"matches": {}, "line": line_obj}
            for func in list(self.trigger_cbs.get(ALL_LINES_ID, [])):
                func()
            (self.shown if line_obj.send else self.hidden).append(line)

    def events(self, name: str) -> list[dict[str, Any]]:
        """The payloads raised for an event."""
        return [payload for event, payload in self.raised if event == name]


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: "CpPlugin", fake: FakeApi, home: Path) -> None:
        self.plugin = plugin
        self.fake = fake
        self.home = home

    def disconnect(self) -> None:
        """The MUD link closes: the plugin and the core hide window see it."""
        self.plugin._eventcb_disconnect()
        self.fake.disconnect()

    def kill(self, name: str) -> None:
        """The mobk plugin raises a kill."""
        self.fake.record = {"name": name}
        self.plugin._eventcb_mobk_kill()

    def take_cp(self, *mobs: str) -> None:
        """Take a campaign: the tell, its info output, then its check output."""
        self.fake.feed(NEW, *info_for(*mobs), *mobs, TIME)

    def complete(self) -> None:
        """Complete the campaign and read the rewards, up to the line after them."""
        self.fake.feed(COMPLETE, *REWARDS, DASHES)


def build(home: Path, fake: FakeApi) -> "CpPlugin":
    """Build and load a plugin on a data directory."""
    from aardwolf.cp.plugin import _cp

    plugin = _cp.CpPlugin.__new__(_cp.CpPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.plugin_info = SimpleNamespace(data_directory=home)  # type: ignore[assignment]
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    plugin._phook_initialize()
    return plugin


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build a CpPlugin with a fake API and load it."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from aardwolf.cp.plugin import _cp

    monkeypatch.setattr(_cp.CpPlugin, "_now", staticmethod(lambda: NOW))
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
    assert "aardwolf.cp" in {p["plugin_id"] for p in result.plugins}


def test_dependencies() -> None:
    """The plugin needs mudcmds and connect, and not mobk."""
    from aardwolf import cp

    assert "plugins.core.mudcmds" in cp.PLUGIN_DEPENDENCIES
    assert "plugins.core.utils" in cp.PLUGIN_DEPENDENCIES
    assert "plugins.aardwolf.connect" in cp.PLUGIN_DEPENDENCIES
    assert "plugins.aardwolf.config" in cp.PLUGIN_DEPENDENCIES
    assert "plugins.aardwolf.mobk" not in cp.PLUGIN_DEPENDENCIES


def test_after_load_adds_events_type_and_triggers(env: Env) -> None:
    """The four events, the check and info types and the 26 triggers are added."""
    assert set(env.fake.events_added) == set(EVENTS)
    assert set(env.fake.types) == {CMDTYPE, CMDTYPE_INFO}
    assert set(env.fake.triggers) == {spec.name for spec in TRIGGERS}
    assert len(env.fake.triggers) == 26
    omitted = {n for n, k in env.fake.kwargs.items() if k.get("omit")}
    assert omitted == {s.name for s in TRIGGERS if s.omit}
    assert {"cp_none", "cp_time", "cp_mob", "cp_scramble", "cp_info_mob", "cp_info_end"} <= omitted
    assert "cp_info_cantake" not in omitted
    assert env.fake.kwargs["cp_info_mob"]["group"] == f"{PLUGIN_ID}.cpinfo"
    assert env.fake.kwargs["cp_info_mob"]["argtypes"] == {"count": int}
    assert env.fake.kwargs["cp_reward"]["argtypes"] == {"amount": int}
    assert env.fake.kwargs["cp_mob"]["group"] == f"{PLUGIN_ID}.cpcheck"


def test_inactive_character_queues_no_check(env: Env) -> None:
    """Nothing is queued while the character is not active."""
    assert env.fake.queued == []


def test_active_character_queues_a_check_on_load(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A reload with an active character reads the campaign info, then checks it."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    fake = FakeApi()
    fake.active = True
    build(tmp_path, fake)
    assert fake.queued == [CMDTYPE_INFO, CMDTYPE]


def test_character_active_event_queues_a_check(env: Env) -> None:
    """The first active event reads the info and checks the campaign; an inactive one does not."""
    env.fake.record = {"is_character_active": False}
    env.plugin._eventcb_character_active()
    assert env.fake.queued == []
    env.fake.record = {"is_character_active": True}
    env.plugin._eventcb_character_active()
    assert env.fake.queued == [CMDTYPE_INFO, CMDTYPE]


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


def test_new_campaign_tell_only_queues_info(env: Env) -> None:
    """The Barcett line queues campaign info and changes no state."""
    env.plugin.cp["qp"] = 99
    env.fake.feed(NEW)
    assert env.fake.queued == [CMDTYPE_INFO]
    assert env.fake.started == [CMDTYPE_INFO]
    assert env.fake.group_on("cpinfo")
    assert env.plugin.cp["qp"] == 99
    assert "oncp" not in env.plugin.cp
    assert env.fake.events(EVENT_MOBSORIG) == []


def test_new_campaign_from_another_questmaster(env: Env) -> None:
    """A QuestoR queues campaign info like Commander Barcett."""
    env.fake.feed(QUESTOR_NEW)
    assert env.fake.queued == [CMDTYPE_INFO]
    assert env.fake.group_on("cpinfo")


def test_player_tell_does_not_reset_the_campaign(env: Env) -> None:
    """A player's tell or an emote of the line queues nothing and leaves the campaign alone."""
    env.take_cp(RAT)
    env.fake.queued.clear()
    env.fake.feed("Some Player tells you 'Type 'campaign info' to see what you must kill.'")
    env.fake.feed("Bob " + NEW)
    assert env.fake.queued == []
    assert env.plugin.cp["mobsleft"]


def test_questmasters_changed_updates_the_trigger(env: Env) -> None:
    """A questmaster added through the config plugin starts campaigns."""
    line = "Sergeant Pike tells you 'Type 'campaign info' to see what you must kill.'"
    env.fake.feed(line)
    assert env.fake.queued == []
    env.fake.record = {"questmasters": ["Commander Barcett", "Sergeant Pike"]}
    env.plugin._eventcb_questmasters_changed()
    env.fake.feed(line)
    assert env.fake.queued == [CMDTYPE_INFO]
    env.fake.queued.clear()
    env.fake.feed(QUESTOR_NEW)
    assert env.fake.queued == []


def test_no_questmasters_matches_nothing(env: Env) -> None:
    """An empty list after a change, or at load, leaves no campaign recognisable."""
    env.fake.record = {"questmasters": []}
    env.plugin._eventcb_questmasters_changed()
    env.fake.feed(NEW, QUESTOR_NEW)
    assert env.fake.queued == []

    fake = FakeApi()
    fake.questmasters = []
    (env.home / "empty").mkdir()
    build(env.home / "empty", fake)
    fake.feed(NEW)
    assert fake.queued == []


def test_changed_event_is_registered_by_name() -> None:
    """The plugin listens to the config plugin's changed event."""
    from aardwolf.cp.plugin import _cp

    assert EVENT_QUESTMASTERS_CHANGED == "ev_plugins.aardwolf.config_questmasters_changed"
    assert hasattr(_cp.CpPlugin, "_eventcb_questmasters_changed")


def test_check_output_raises_the_mobs(env: Env) -> None:
    """The mob lines and the time line raise mobsorig and mobsleft and finish the check."""
    env.take_cp(RAT, BAT)
    expected = [
        {"name": "A rat", "nocolorname": "A rat", "location": "Sewers", "mobdead": False},
        {"name": "A bat", "nocolorname": "A bat", "location": "Cave", "mobdead": True},
    ]
    # the original targets come from campaign info, which does not know which are dead
    original = [dict(mob, mobdead=False) for mob in expected]
    assert env.fake.events(EVENT_MOBSORIG) == [{"mobsleft": original}]
    assert env.fake.events(EVENT_MOBSLEFT) == [{"mobsleft": expected}]
    assert env.fake.finished == [CMDTYPE_INFO, CMDTYPE]
    assert env.fake.group_on("cpin")
    assert not env.fake.group_on("cpcheck")
    assert env.fake.omitted[-3:] == [RAT, BAT, TIME]


def test_second_check_raises_only_mobsleft(env: Env) -> None:
    """Only the first check raises mobsorig."""
    env.take_cp(RAT)
    env.fake.queued.clear()
    env.plugin._queue_check()
    env.fake.feed(RAT, BAT, TIME)
    assert len(env.fake.events(EVENT_MOBSORIG)) == 1
    assert len(env.fake.events(EVENT_MOBSLEFT)) == 2
    assert [m["name"] for m in env.fake.events(EVENT_MOBSLEFT)[1]["mobsleft"]] == [
        "A rat",
        "A bat",
    ]
    assert [m["name"] for m in env.plugin.cp["mobs"]] == ["A rat"]


def test_mob_line_with_no_name_is_logged_not_added(
    env: Env, caplog: pytest.LogCaptureFixture
) -> None:
    """A mob line without a name or a location adds nothing."""
    env.fake.record = {"matches": {"mob": "", "location": "x", "dead": ""}}
    env.plugin._trigger_mob()
    assert env.plugin.cp.get("mobsleft", []) == []


def test_target_kill_removes_the_first_mob(env: Env) -> None:
    """A kill after the mob-dead line removes the first mob of the list."""
    env.take_cp(RAT, BAT)
    env.fake.feed(DEAD)
    env.kill("A rat")
    last = env.fake.events(EVENT_MOBSLEFT)[-1]
    assert [m["name"] for m in last["mobsleft"]] == ["A bat"]
    assert [m["name"] for m in env.plugin.cp["mobsleft"]] == ["A bat"]


def test_kill_without_mob_dead_line_changes_nothing(env: Env) -> None:
    """A kill that is not a campaign mob is ignored."""
    env.take_cp(RAT)
    before = len(env.fake.raised)
    env.kill("A rat")
    assert len(env.fake.raised) == before
    assert len(env.plugin.cp["mobsleft"]) == 1


def test_kill_is_used_once(env: Env) -> None:
    """The flag clears after a kill, so the next kill is ignored."""
    env.take_cp(RAT, BAT)
    env.fake.feed(DEAD)
    env.kill("A rat")
    env.kill("A bat")
    assert [m["name"] for m in env.plugin.cp["mobsleft"]] == ["A bat"]


def test_kill_of_unknown_mob_queues_a_check(env: Env) -> None:
    """A campaign kill with an unknown name asks for a new check."""
    env.take_cp(RAT)
    env.fake.queued.clear()
    before = len(env.fake.events(EVENT_MOBSLEFT))
    env.fake.feed(DEAD)
    env.kill("Nobody")
    assert len(env.fake.events(EVENT_MOBSLEFT)) == before
    assert env.fake.queued == [CMDTYPE]


RAT_KITCHEN = "You still have to kill * A rat (Kitchen)"


def test_kill_of_a_name_at_several_locations_queues_a_check(env: Env) -> None:
    """The first match goes, and a check replaces the guess with the server's list."""
    env.take_cp(RAT, BAT, RAT_KITCHEN)
    env.fake.queued.clear()
    env.fake.feed(DEAD)
    env.kill("A rat")
    last = env.fake.events(EVENT_MOBSLEFT)[-1]
    assert [(m["name"], m["location"]) for m in last["mobsleft"]] == [
        ("A bat", "Cave"),
        ("A rat", "Kitchen"),
    ]
    assert env.fake.queued == [CMDTYPE]
    env.fake.feed(RAT, BAT, TIME)
    last = env.fake.events(EVENT_MOBSLEFT)[-1]
    assert [(m["name"], m["location"]) for m in last["mobsleft"]] == [
        ("A rat", "Sewers"),
        ("A bat", "Cave"),
    ]


def test_kill_of_a_name_at_one_location_queues_no_check(env: Env) -> None:
    """Two mobs with the name at the same location are unambiguous."""
    env.fake.feed(NEW, *info_lines("2 * A rat (Sewers)"), RAT, RAT, TIME)
    assert len(env.plugin.cp["mobsleft"]) == 2
    env.fake.queued.clear()
    env.fake.feed(DEAD)
    env.kill("A rat")
    assert len(env.plugin.cp["mobsleft"]) == 1
    assert env.fake.queued == []


def test_completion_with_bonus_line(env: Env) -> None:
    """The bonus line sets bonusqp and raises the campaign once."""
    env.take_cp(RAT)
    env.complete()
    assert env.fake.events(EVENT_COMP) == []
    assert len(env.fake.trigger_cbs[ALL_LINES_ID]) == 1
    env.fake.feed(BONUS)
    (payload,) = env.fake.events(EVENT_COMP)
    assert payload["bonusqp"] == 15
    assert payload["qp"] == 120
    assert payload["gold"] == 300
    assert payload["tp"] == 4
    assert payload["trains"] == 5
    assert payload["pracs"] == 6
    assert payload["oncp"] is False
    assert payload["finishtime"] == NOW
    assert env.fake.trigger_cbs[ALL_LINES_ID] == []
    assert not env.fake.group_on("cprew")
    assert not env.fake.group_on("cpdone")
    env.fake.feed(COUNT, BONUS)
    assert len(env.fake.events(EVENT_COMP)) == 1


def test_completion_with_count_line(env: Env) -> None:
    """The count line without a bonus raises the campaign with bonusqp 0."""
    env.take_cp(RAT)
    env.complete()
    env.fake.feed(COUNT)
    (payload,) = env.fake.events(EVENT_COMP)
    assert payload["bonusqp"] == 0


def test_completion_falls_back_to_the_prompt(env: Env) -> None:
    """With neither line, the campaign is raised at the prompt and not before."""
    env.take_cp(RAT)
    env.complete()
    env.fake.feed("Some other line.", "Another line.")
    assert env.fake.events(EVENT_COMP) == []
    env.fake.feed("<100hp>", prompt=True)
    (payload,) = env.fake.events(EVENT_COMP)
    assert payload["bonusqp"] == 0
    assert env.fake.trigger_cbs[ALL_LINES_ID] == []


def test_unknown_reward_type_is_ignored(env: Env) -> None:
    """A reward of an unknown type is logged and changes nothing."""
    env.take_cp(RAT)
    env.fake.feed(COMPLETE, "  Reward of 5 bogus things added.")
    assert not env.fake.group_on("cpdone")


def test_disconnect_while_waiting_raises_the_campaign(env: Env) -> None:
    """A disconnect before the last line still raises the campaign and turns the groups off."""
    env.take_cp(RAT)
    env.complete()
    env.plugin._eventcb_disconnect()
    assert len(env.fake.events(EVENT_COMP)) == 1
    assert env.fake.trigger_cbs[ALL_LINES_ID] == []
    assert not any(env.fake.group_on(group) for group in GROUPS)


def test_disconnect_clears_the_kill_flag(env: Env) -> None:
    """A disconnect forgets that a campaign mob died."""
    env.take_cp(RAT)
    env.fake.feed(DEAD)
    env.plugin._eventcb_disconnect()
    env.kill("A rat")
    assert len(env.plugin.cp["mobsleft"]) == 1


def test_cleared_campaign(env: Env) -> None:
    """A cleared campaign raises failed, then is off the campaign with every group off."""
    env.take_cp(RAT)
    env.fake.feed("Campaign cleared.")
    (payload,) = env.fake.events(EVENT_FAILED)
    assert payload["failed"] == 1
    assert env.plugin.cp["oncp"] is False
    assert not any(env.fake.group_on(group) for group in GROUPS)


def test_not_on_a_campaign(env: Env) -> None:
    """The not-on-a-campaign line sets oncp False, finishes the check and turns groups off."""
    env.plugin._queue_check()
    env.fake.feed(NONE)
    assert env.plugin.cp["oncp"] is False
    assert env.fake.finished == [CMDTYPE]
    assert not any(env.fake.group_on(group) for group in GROUPS)


def test_cantake_needtolevel_and_shnext(env: Env) -> None:
    """The lines of the campaign limits set the state."""
    env.take_cp(RAT)
    env.fake.feed("You may take a campaign at this level.")
    assert env.plugin.cp["cantake"] is True
    env.fake.feed("You will have to level before you can go on another campaign.")
    assert env.plugin.cp.get("cantake") is False
    env.fake.feed("You cannot take another campaign for 3m 4s.")
    assert env.plugin.cp["shtime"] == "3m 4s"


def test_payloads_are_plain_copies(env: Env) -> None:
    """A payload is a plain dict, and changing it does not change the state."""
    env.take_cp(RAT)
    payload = env.fake.events(EVENT_MOBSLEFT)[0]
    assert type(payload) is dict
    payload["mobsleft"][0]["name"] = "changed"
    assert env.plugin.cp["mobsleft"][0]["name"] == "A rat"
    env.complete()
    env.fake.feed(BONUS)
    comp = env.fake.events(EVENT_COMP)[0]
    assert type(comp) is dict
    assert type(comp["mobsleft"]) is list
    comp["mobsleft"].clear()
    assert len(env.plugin.cp["mobsleft"]) == 1


def test_apis(env: Env) -> None:
    """oncp is a bool and mobs.left.get is a copy."""
    assert env.plugin._api_oncp() is False
    env.take_cp(RAT)
    assert env.plugin._api_oncp() is True
    mobs = env.plugin._api_mobs_left_get()
    assert [m["name"] for m in mobs] == ["A rat"]
    mobs.clear()
    assert len(env.plugin.cp["mobsleft"]) == 1


def test_show_command(env: Env) -> None:
    """show lists the mobs left, or says there is no campaign."""
    assert env.plugin._command_show().message == ["You are not on a cp"]
    env.take_cp(RAT, BAT)
    result = env.plugin._command_show()
    assert result.success is True
    assert result.message == ["Mobs left"]
    assert env.fake.tables == [
        (
            "Mobs left",
            [
                {"name": "@wA rat", "location": "@wSewers"},
                {"name": "@RA bat", "location": "@RCave"},
            ],
            MOBS_LEFT_COLUMNS,
        )
    ]


def test_show_command_with_no_mobs_left(env: Env) -> None:
    """show prints the table once with no rows when no mob is left."""
    env.take_cp(RAT)
    env.plugin.cp["mobsleft"] = []
    result = env.plugin._command_show()
    assert result.success is True
    assert env.fake.tables == [("Mobs left", [], MOBS_LEFT_COLUMNS)]


def test_refresh_command(env: Env) -> None:
    """refresh queues a check only on a campaign."""
    result = env.plugin._command_refresh()
    assert result.message == ["You are not on a cp"]
    assert env.fake.queued == []
    env.take_cp(RAT)
    env.fake.queued.clear()
    result = env.plugin._command_refresh()
    assert result.message == ["Refreshing cp mobs"]
    assert env.fake.queued == [CMDTYPE]


def test_state_is_persisted_and_survives_a_reload(env: Env) -> None:
    """The mobs and the mobs left are on disk and a rebuilt plugin sees them."""
    from bastproxy.libs.persistentdict import PersistentDict

    env.take_cp(RAT, BAT)
    saved = PersistentDict(PLUGIN_ID, env.home / "cp.txt", "c")
    assert len(saved["mobs"]) == 2
    assert len(saved["mobsleft"]) == 2
    again = build(env.home, FakeApi())
    assert again.cp["oncp"] is True
    assert [m["name"] for m in again.cp["mobsleft"]] == ["A rat", "A bat"]


def test_save_hook_syncs(env: Env) -> None:
    """The save hook writes the state."""
    from bastproxy.libs.persistentdict import PersistentDict

    env.plugin.cp["extra"] = 1
    env.plugin._phook_save()
    assert PersistentDict(PLUGIN_ID, env.home / "cp.txt", "c")["extra"] == 1


def test_comp_payload_is_saved_by_statdb(env: Env, tmp_path: Path) -> None:
    """The cp_comp payload feeds statdb's save_cp."""
    from aardwolf.statdb.libs import StatStore

    env.take_cp(RAT, BAT)
    env.complete()
    env.fake.feed(BONUS)
    payload = env.fake.events(EVENT_COMP)[0]
    database = make_db(tmp_path / "db")
    try:
        store = StatStore(database)
        store.save_whois(WHOIS)
        store.save_cp(payload)
        row = database.select("SELECT * FROM campaigns")[0]
        assert row["qp"] == 120
        assert row["bonusqp"] == 15
        assert row["level"] == LEVEL
        assert row["failed"] == 0
        assert len(database.select("SELECT * FROM cpmobs")) == 2
        stat = database.select("SELECT campaignsdone FROM stats WHERE milestone = 'current'")
        assert stat[0]["campaignsdone"] == 1
    finally:
        database.close()


def test_failed_payload_is_saved_by_statdb(env: Env, tmp_path: Path) -> None:
    """The cp_failed payload feeds statdb's save_cp."""
    from aardwolf.statdb.libs import StatStore

    env.take_cp(RAT)
    env.fake.feed("Campaign cleared.")
    payload = env.fake.events(EVENT_FAILED)[0]
    database = make_db(tmp_path / "db")
    try:
        store = StatStore(database)
        store.save_whois(WHOIS)
        store.save_cp(payload)
        row = database.select("SELECT * FROM campaigns")[0]
        assert row["failed"] == 1
        stat = database.select("SELECT campaignsfld FROM stats WHERE milestone = 'current'")
        assert stat[0]["campaignsfld"] == 1
    finally:
        database.close()


def test_raised_keys_are_all_described(env: Env) -> None:
    """A campaign raises only keys its events describe in arg_descriptions (#43)."""
    env.take_cp(RAT)
    env.complete()
    env.fake.feed(BONUS)
    assert env.fake.events(EVENT_COMP)
    assert_raised_described(env.fake.raised, EVENTS)


CAT = "2 * a black cat (Gallows Hill)"
ALE = "1 * some wicked ale (Gallows Hill)"
CHECK_ALE = "You still have to kill * some wicked ale (Gallows Hill)"
CHECK_CAT = "You still have to kill * a black cat (Gallows Hill)"


def expected_start() -> float:
    """The start time of the captured info block: 7 days less its time left, before NOW."""
    return NOW - (CP_DURATION - INFO_SECONDS_LEFT)


def assert_captured_campaign(fake: FakeApi, plugin: "CpPlugin") -> None:
    """Check the state after the captured info block and its check output."""
    cp = plugin.cp
    assert cp["oncp"] is True
    assert cp["starttime"] == expected_start()
    assert cp["level"] == actual_level(2, 2, 1, 0)
    assert cp["completeby"] == "12:34PM on 30 Nov 2026"
    assert [m["name"] for m in cp["mobs"]] == ["some wicked ale", "a black cat", "a black cat"]
    assert all(not m["mobdead"] for m in cp["mobs"])
    (orig,) = fake.events(EVENT_MOBSORIG)
    assert [m["name"] for m in orig["mobsleft"]] == [m["name"] for m in cp["mobs"]]
    assert [m["name"] for m in fake.events(EVENT_MOBSLEFT)[-1]["mobsleft"]] == [
        "some wicked ale",
        "a black cat",
    ]
    assert fake.started.count(CMDTYPE) == 1
    assert fake.started.count(CMDTYPE_INFO) == 1
    assert fake.finished == [CMDTYPE_INFO, CMDTYPE]
    assert not any(fake.group_on(group) for group in ("cpinfo", "cpcheck"))
    assert set(info_lines(ALE, CAT)) <= set(fake.omitted)


def test_load_mid_campaign_tracks_it_from_info(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Loading with an active character reads info, then check, and starts the campaign."""
    from aardwolf.cp.plugin import _cp

    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    monkeypatch.setattr(_cp.CpPlugin, "_now", staticmethod(lambda: NOW))
    fake = FakeApi()
    fake.active = True
    plugin = build(tmp_path, fake)
    fake.feed(*info_lines(ALE, CAT), CHECK_ALE, CHECK_CAT, TIME)
    assert_captured_campaign(fake, plugin)
    assert_raised_described(fake.raised, EVENTS)


def test_character_active_event_tracks_it_from_info(env: Env) -> None:
    """The character-active event reads info and check the same way."""
    env.fake.record = {"is_character_active": True}
    env.plugin._eventcb_character_active()
    env.fake.feed(*info_lines(ALE, CAT), CHECK_ALE, CHECK_CAT, TIME)
    assert_captured_campaign(env.fake, env.plugin)


def test_campaign_from_an_unlisted_questmaster_starts_on_a_kill(env: Env) -> None:
    """The CAMPAIGN-mob line while off a campaign queues info, which then starts tracking."""
    env.fake.feed(DEAD)
    assert env.fake.queued == [CMDTYPE_INFO]
    assert env.plugin._await_kill is False
    env.fake.feed(*info_lines(ALE, CAT))
    assert env.plugin.cp["oncp"] is True
    assert env.fake.queued == [CMDTYPE_INFO, CMDTYPE]
    assert len(env.fake.events(EVENT_MOBSORIG)) == 1


def test_kill_line_on_a_campaign_does_not_queue_info(env: Env) -> None:
    """On a campaign the CAMPAIGN-mob line waits for the kill, as before."""
    env.take_cp(RAT)
    env.fake.queued.clear()
    env.fake.feed(DEAD)
    assert env.plugin._await_kill is True
    assert env.fake.queued == []


def test_tell_for_the_tracked_campaign_changes_nothing(env: Env) -> None:
    """The tell and the same info again leave the state alone and queue no check."""
    env.fake.feed(NEW, *info_lines(ALE, CAT), CHECK_ALE, CHECK_CAT, TIME)
    before = dict(env.plugin.cp)
    orig = len(env.fake.events(EVENT_MOBSORIG))
    env.fake.queued.clear()
    env.fake.feed(NEW)
    env.fake.feed(*info_lines(ALE, CAT))
    assert dict(env.plugin.cp) == before
    assert len(env.fake.events(EVENT_MOBSORIG)) == orig
    assert env.fake.queued == [CMDTYPE_INFO]
    assert env.fake.finished[-1] == CMDTYPE_INFO


def test_info_with_another_complete_by_replaces_the_campaign(env: Env) -> None:
    """A different Complete By is a new campaign: new mobs, a new mobsorig and a check."""
    env.fake.feed(NEW, *info_lines(ALE, CAT), CHECK_ALE, CHECK_CAT, TIME)
    env.fake.queued.clear()
    env.plugin.cp["qp"] = 99
    other = "Complete By........: [ 01:00AM on 7 Dec 2026 ]"
    env.fake.feed(NEW, *info_lines("1 * a rat (Sewers)", completeby=other))
    assert env.plugin.cp["completeby"] == "01:00AM on 7 Dec 2026"
    assert [m["name"] for m in env.plugin.cp["mobs"]] == ["a rat"]
    assert env.plugin.cp["qp"] == 0
    assert len(env.fake.events(EVENT_MOBSORIG)) == 2
    assert env.fake.queued == [CMDTYPE_INFO, CMDTYPE]


def test_new_info_after_completion_starts_a_campaign(env: Env) -> None:
    """When cp is off a campaign, the same Complete By still starts a new state."""
    env.fake.feed(NEW, *info_lines(ALE), CHECK_ALE, TIME)
    env.plugin.cp["oncp"] = False
    env.fake.feed(NEW, *info_lines(ALE))
    assert env.plugin.cp["oncp"] is True
    assert len(env.fake.events(EVENT_MOBSORIG)) == 2


def test_info_not_on_a_campaign_with_a_limit_line(env: Env) -> None:
    """The not-on-a-campaign reply and may-take line leave cp off and finish the command."""
    env.fake.feed(NEW, NONE, INFO_CANTAKE)
    assert env.plugin.cp["oncp"] is False
    assert env.plugin.cp["cantake"] is True
    assert env.fake.finished == [CMDTYPE_INFO]
    assert not env.fake.group_on("cpinfo")
    assert env.fake.trigger_cbs[ALL_LINES_ID] == []
    assert NONE in env.fake.omitted
    assert env.fake.events(EVENT_MOBSORIG) == []


def test_info_not_on_a_campaign_must_level(env: Env) -> None:
    """The must-level line sets cantake False and finishes the command."""
    env.plugin.cp["cantake"] = True
    env.fake.feed(NEW, NONE, INFO_NEEDTOLEVEL)
    assert env.plugin.cp["cantake"] is False
    assert env.fake.finished == [CMDTYPE_INFO]
    assert env.fake.trigger_cbs[ALL_LINES_ID] == []


def test_info_not_on_a_campaign_falls_back_to_the_prompt(env: Env) -> None:
    """With no limit line, the first prompt after the reply finishes the command."""
    env.fake.feed(NEW, NONE)
    assert env.fake.finished == []
    assert len(env.fake.trigger_cbs[ALL_LINES_ID]) == 1
    env.fake.feed("Some other line.")
    assert env.fake.finished == []
    env.fake.feed("<100hp>", prompt=True)
    assert env.fake.finished == [CMDTYPE_INFO]
    assert env.fake.trigger_cbs[ALL_LINES_ID] == []
    assert env.plugin._waiting_info is False
    assert not env.fake.group_on("cpinfo")


def test_prompt_before_the_none_line_does_not_finish_info(env: Env) -> None:
    """A prompt still in flight when info starts does not end the command."""
    env.fake.feed(NEW)
    env.fake.feed("<100hp>", prompt=True)
    assert env.fake.finished == []
    assert env.fake.trigger_cbs.get(ALL_LINES_ID, []) == []


def test_disconnect_while_waiting_for_the_info_prompt(env: Env) -> None:
    """A disconnect unregisters the prompt watcher and forgets the info values."""
    env.fake.feed(NEW, NONE)
    env.plugin._eventcb_disconnect()
    assert env.fake.trigger_cbs[ALL_LINES_ID] == []
    assert env.plugin._waiting_info is False
    assert env.plugin._info == {}
    assert not any(env.fake.group_on(group) for group in GROUPS)


@pytest.mark.parametrize(
    "lines",
    [
        [line for line in info_lines(ALE) if not line.startswith("Complete By")],
        info_lines(),
    ],
)
def test_incomplete_info_changes_nothing_and_finishes(env: Env, lines: list[str]) -> None:
    """Info with no Complete By line or no targets keeps the state and still finishes."""
    env.fake.feed(NEW, *lines)
    assert "oncp" not in env.plugin.cp
    assert env.fake.events(EVENT_MOBSORIG) == []
    assert env.fake.finished == [CMDTYPE_INFO]
    assert env.fake.queued == [CMDTYPE_INFO]


def test_info_with_an_unreadable_time_left_starts_now(env: Env) -> None:
    """When the time left has no number, the start time is now."""
    lines = [
        "Time Left  ........: [ soon ]" if line.startswith("Time Left") else line
        for line in info_lines(ALE)
    ]
    env.fake.feed(NEW, *lines)
    assert env.plugin.cp["starttime"] == NOW


def test_info_mob_line_with_no_name_is_logged_not_added(env: Env) -> None:
    """A target line without a name or a location adds nothing to the info."""
    env.fake.feed(NEW)
    env.fake.record = {"matches": {"mob": "", "location": "x", "count": 1}}
    env.plugin._trigger_info_mob()
    assert env.plugin._info["mobs"] == []


def test_info_state_is_saved_for_statdb(env: Env, tmp_path: Path) -> None:
    """The expanded targets and Complete By reach the cp_comp payload and statdb."""
    from aardwolf.statdb.libs import StatStore

    env.fake.feed(NEW, *info_lines(ALE, CAT), CHECK_ALE, CHECK_CAT, TIME)
    env.complete()
    env.fake.feed(BONUS)
    (payload,) = env.fake.events(EVENT_COMP)
    assert payload["completeby"] == "12:34PM on 30 Nov 2026"
    database = make_db(tmp_path / "db")
    try:
        store = StatStore(database)
        store.save_whois(WHOIS)
        store.save_cp(payload)
        assert len(database.select("SELECT * FROM cpmobs")) == 3
    finally:
        database.close()


PROMPT = "[198/201hp 168/176mn 630/630mv 10qt 773tnl] >"
STATE = "You cannot take another campaign for 3m 4s."


def is_hiding(env: Env) -> bool:
    """Whether the core hide window is open."""
    return env.fake.core.is_open()


def test_cp_req_shows_only_the_tell_and_one_prompt(env: Env) -> None:
    """The queued info and check are hidden, with their blank lines and prompts."""
    fake = env.fake
    fake.feed(NEW)
    fake.feed(PROMPT, prompt=True)
    fake.feed(*info_for(RAT), "")
    fake.feed(PROMPT, prompt=True)
    fake.feed(RAT, TIME, INFO_NEEDTOLEVEL, "")
    fake.feed(PROMPT, prompt=True)
    assert fake.shown == [NEW, PROMPT]
    assert env.plugin.cp["cantake"] is False
    assert not fake.core.is_open()


def test_hidden_state_line_still_updates_state(env: Env) -> None:
    """The cpin triggers fire on lines the hide window hides."""
    env.take_cp(RAT)
    env.fake.feed(STATE, INFO_CANTAKE)
    assert STATE in env.fake.hidden
    assert INFO_CANTAKE in env.fake.hidden
    assert env.plugin.cp["shtime"] == "3m 4s"
    assert env.plugin.cp["cantake"] is True


def test_first_active_not_on_a_campaign_hides_everything(env: Env) -> None:
    """The info and check queued on first active show nothing when not on a campaign."""
    fake = env.fake
    fake.record = {"is_character_active": True}
    env.plugin._eventcb_character_active()
    for _ in range(2):
        fake.feed(NONE, COUNT, INFO_NEEDTOLEVEL, "")
        fake.feed(PROMPT, prompt=True)
    assert fake.shown == []
    assert env.plugin.cp["oncp"] is False
    assert env.plugin.cp["cantake"] is False
    assert fake.finished == [CMDTYPE_INFO, CMDTYPE]


def test_mob_kill_with_an_unknown_name_hides_the_queued_check(env: Env) -> None:
    """The check queued by a kill of an unknown mob is hidden; the kill line is not."""
    env.take_cp(RAT)
    env.fake.feed(PROMPT, prompt=True)
    env.fake.feed(DEAD)
    env.kill("Nobody")
    assert env.fake.queued[-1] == CMDTYPE
    env.fake.feed(RAT, TIME, STATE, "")
    env.fake.feed(PROMPT, prompt=True)
    assert env.fake.shown[-1:] == [DEAD]
    assert env.fake.shown.count(DEAD) == 1


def test_typed_output_is_shown(env: Env) -> None:
    """A check or info the player types is shown in full."""
    env.take_cp(RAT)
    env.fake.feed("", PROMPT, prompt=False)
    env.fake.feed(PROMPT, prompt=True)
    env.fake.shown.clear()
    env.fake.feed(RAT, TIME, INFO_NEEDTOLEVEL, "")
    env.fake.feed(PROMPT, prompt=True)
    assert env.fake.shown == [RAT, TIME, INFO_NEEDTOLEVEL, "", PROMPT]
    assert env.plugin.cp["cantake"] is False
    typed_info = [*info_lines(RAT), ""]
    env.fake.shown.clear()
    env.fake.feed(*typed_info)
    assert env.fake.shown == typed_info


def test_window_ends_at_the_prompt(env: Env) -> None:
    """The line after the prompt of a queued check is shown."""
    env.take_cp(RAT)
    env.fake.feed(PROMPT, prompt=True)
    env.fake.feed("Some other line.")
    assert env.fake.shown[-1] == "Some other line."


def test_window_ends_at_the_line_cap(env: Env, caplog: pytest.LogCaptureFixture) -> None:
    """Without a prompt, HIDE_MAX_LINES lines after the opener are hidden and the next is shown.

    mudcmds counts the opener too, so the type gets HIDE_MAX_LINES + 1.
    """
    env.plugin._queue_check()
    env.fake.feed(RAT)
    assert is_hiding(env)
    others = [f"line {i}" for i in range(HIDE_MAX_LINES + 1)]
    with caplog.at_level(logging.WARNING):
        env.fake.feed(*others)
    assert env.fake.hidden[-HIDE_MAX_LINES:] == others[:HIDE_MAX_LINES]
    assert env.fake.shown == [others[-1]]
    assert not is_hiding(env)
    caps = [r for r in caplog.records if "reached its cap" in r.getMessage()]
    assert len(caps) == 1
    assert caps[0].levelno == logging.WARNING


def test_disconnect_ends_the_hide_window(env: Env) -> None:
    """A disconnect while hiding closes the window; the next line is shown."""
    env.plugin._queue_check()
    env.fake.feed(RAT)
    assert is_hiding(env)
    env.disconnect()
    assert not is_hiding(env)
    env.fake.feed("Hello")
    assert env.fake.shown == ["Hello"]


def test_one_hide_window_for_several_openers(env: Env) -> None:
    """Several opener lines in one queued check leave the same window open."""
    env.plugin._queue_check()
    env.fake.feed(RAT)
    window = env.fake.core.core._hide_open
    assert window is not None
    env.fake.feed(BAT)
    assert env.fake.core.core._hide_open is window


def test_issue_90_session_closes_every_window_at_the_marked_prompt(
    env: Env, caplog: pytest.LogCaptureFixture
) -> None:
    """Aardwolf sends no GA: prompts recognised from the template close the hide windows."""
    from aardwolf.promptfix.libs import build_prompt_pattern, is_prompt_text

    template = "@R[@W%h@R/@W%H@Rhp %m/%Mmn %v/%Vmv %qqt %Xtnl@R] >%c"
    regex = build_prompt_pattern(template).regex
    assert regex is not None
    prompt_line = "[201/201hp 176/176mn 630/630mv 0qt 773tnl] >*[NOEXP]*"

    def feed(*lines: str) -> None:
        for text in lines:
            env.fake.feed(text, prompt=is_prompt_text(text, [regex]))

    fake = env.fake
    fake.record = {"is_character_active": True}
    with caplog.at_level(logging.WARNING):
        env.plugin._eventcb_character_active()
        info = [*info_for(RAT), "", prompt_line]
        check = [RAT, TIME, INFO_NEEDTOLEVEL, "", prompt_line]
        whois = [
            "Name: Someone",
            "Class: Mage",
            "To see warfare stats, use 'warinfo <player>'",
            "",
            prompt_line,
        ]
        feed(*info)
        feed(*check)
        feed(*whois)
    assert all(text in fake.hidden for text in [*info, *check])
    assert fake.shown == whois
    assert not is_hiding(env)
    assert not [r for r in caplog.records if "reached its cap" in r.getMessage()]


def test_types_hide_their_output_through_mudcmds(env: Env) -> None:
    """Both types ask mudcmds to hide the output, opening on the group's omitted lines."""
    for cmdtype, start in ((CMDTYPE, CHECK_HIDE_START), (CMDTYPE_INFO, INFO_HIDE_START)):
        kwargs = env.fake.types[cmdtype]
        assert kwargs["hide_output"] is True
        assert kwargs["hide_start"] == start
        assert "hide_end" not in kwargs
        # mudcmds counts the opening line, so the type gets one more than the cap
        assert kwargs["hide_max"] == HIDE_MAX_LINES + 1
        assert env.fake.core.core.cmds[cmdtype].hide_output is True


def test_info_not_on_a_campaign_without_a_limit_line_closes_at_its_prompt(env: Env) -> None:
    """The reply, a state line and the prompt are hidden; the window is closed after it."""
    fake = env.fake
    env.plugin._queue_info()
    fake.feed(NONE, STATE)
    assert is_hiding(env)
    fake.feed(PROMPT, prompt=True)
    assert fake.finished == [CMDTYPE_INFO]
    assert not is_hiding(env)
    fake.feed("Some other line.")
    assert fake.hidden == [NONE, STATE, PROMPT]
    assert fake.shown == ["Some other line."]


def test_without_promptfix_a_queued_check_closes_at_cp_time(env: Env) -> None:
    """Before any prompt is seen, finishing closes the window at once and the prompt is shown."""
    fake = env.fake
    fake.core.prompts_seen = False
    env.plugin._queue_check()
    fake.feed(RAT, TIME)
    assert fake.finished == [CMDTYPE]
    assert not is_hiding(env)
    fake.feed(PROMPT, prompt=True)
    assert fake.shown == [PROMPT]
