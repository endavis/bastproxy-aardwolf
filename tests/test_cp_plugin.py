"""Tests for the Aardwolf cp plugin, with a stubbed API that drives its triggers."""

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
from aardwolf.cp.libs import (
    ALL_LINES_ID,
    CMDTYPE,
    EVENT_COMP,
    EVENT_FAILED,
    EVENT_MOBSLEFT,
    EVENT_MOBSORIG,
    EVENTS,
    TRIGGERS,
)
from aardwolf.libs.aardu import actual_level

if TYPE_CHECKING:
    from aardwolf.cp.plugin._cp import CpPlugin

PLUGIN_ID = "plugins.aardwolf.cp"
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
GROUPS = ("cpcheck", "cpin", "cprew", "cpdone")


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
        self.record: dict[str, Any] = {}
        self.active = False
        self.omitted: list[str] = []
        self.types: dict[str, dict[str, Any]] = {}
        self.queued: list[str] = []
        self.started: list[str] = []
        self.finished: list[str] = []
        self.current: str | None = None
        self.table: dict[str, Callable[..., Any]] = {
            "plugins.core.events:event.add": self._event_add,
            "plugins.core.events:event.raise": self._event_raise,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
            "plugins.core.triggers:trigger.unregister": self._trigger_unregister,
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

    def _event_raise(self, name: str, event_args: dict[str, Any] | None = None) -> None:
        self.raised.append((name, event_args or {}))

    def _trigger_add(self, name: str, regex: str, **kwargs: object) -> SimpleNamespace:
        self.triggers[name] = regex
        self.kwargs[name] = dict(kwargs)
        self.enabled[name] = bool(kwargs.get("enabled", True))
        self.trigger_cbs.setdefault(name, [])
        return SimpleNamespace(success=self.add_ok, trigger=SimpleNamespace(trigger_id=name))

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

    def feed(self, *lines: str, prompt: bool = False) -> None:
        """Run each line through the enabled triggers and then the every-line callbacks."""
        for line in lines:
            line_obj = SimpleNamespace(noansi=line, is_prompt=prompt)
            for name, regex in list(self.triggers.items()):
                match = re.match(regex, line)
                if not match or not self.enabled[name]:
                    continue
                groups = match.groupdict()
                for arg, argtype in (self.kwargs[name].get("argtypes") or {}).items():
                    groups[arg] = argtype(groups[arg])
                if self.kwargs[name].get("omit"):
                    self.omitted.append(line)
                self.record = {"matches": groups, "line": line_obj}
                for func in list(self.trigger_cbs[name]):
                    func()
            self.record = {"matches": {}, "line": line_obj}
            for func in list(self.trigger_cbs.get(ALL_LINES_ID, [])):
                func()

    def events(self, name: str) -> list[dict[str, Any]]:
        """The payloads raised for an event."""
        return [payload for event, payload in self.raised if event == name]


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: "CpPlugin", fake: FakeApi, home: Path) -> None:
        self.plugin = plugin
        self.fake = fake
        self.home = home

    def kill(self, name: str) -> None:
        """The mobk plugin raises a kill."""
        self.fake.record = {"name": name}
        self.plugin._eventcb_mobk_kill()

    def take_cp(self, *mobs: str) -> None:
        """Take a campaign and read its check output."""
        self.fake.feed(NEW, *mobs, TIME)

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
    assert "plugins.aardwolf.connect" in cp.PLUGIN_DEPENDENCIES
    assert "plugins.aardwolf.mobk" not in cp.PLUGIN_DEPENDENCIES


def test_after_load_adds_events_type_and_triggers(env: Env) -> None:
    """The four events, the check type and the 13 triggers are added."""
    assert set(env.fake.events_added) == set(EVENTS)
    assert set(env.fake.types) == {CMDTYPE}
    assert set(env.fake.triggers) == {spec.name for spec in TRIGGERS}
    assert len(env.fake.triggers) == 13
    omitted = {n for n, k in env.fake.kwargs.items() if k.get("omit")}
    assert omitted == {"cp_none", "cp_time", "cp_mob", "cp_scramble"}
    assert env.fake.kwargs["cp_reward"]["argtypes"] == {"amount": int}
    assert env.fake.kwargs["cp_mob"]["group"] == f"{PLUGIN_ID}.cpcheck"


def test_inactive_character_queues_no_check(env: Env) -> None:
    """Nothing is queued while the character is not active."""
    assert env.fake.queued == []


def test_active_character_queues_a_check_on_load(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A reload with an active character checks the campaign."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    fake = FakeApi()
    fake.active = True
    build(tmp_path, fake)
    assert fake.queued == [CMDTYPE]


def test_character_active_event_queues_a_check(env: Env) -> None:
    """The first active event checks the campaign; an inactive one does not."""
    env.fake.record = {"is_character_active": False}
    env.plugin._eventcb_character_active()
    assert env.fake.queued == []
    env.fake.record = {"is_character_active": True}
    env.plugin._eventcb_character_active()
    assert env.fake.queued == [CMDTYPE]


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


def test_new_campaign_resets_state_and_queues_a_check(env: Env) -> None:
    """The Barcett line starts the state with the total level and checks the mobs."""
    env.plugin.cp["qp"] = 99
    env.fake.feed(NEW)
    assert env.plugin.cp["level"] == LEVEL
    assert env.plugin.cp["starttime"] == NOW
    assert env.plugin.cp["qp"] == 0
    assert env.plugin.cp["oncp"] is True
    assert env.fake.queued == [CMDTYPE]
    assert env.fake.started == [CMDTYPE]
    assert env.fake.group_on("cpcheck")


def test_check_output_raises_the_mobs(env: Env) -> None:
    """The mob lines and the time line raise mobsorig and mobsleft and finish the check."""
    env.take_cp(RAT, BAT)
    expected = [
        {"name": "A rat", "nocolorname": "A rat", "location": "Sewers", "mobdead": False},
        {"name": "A bat", "nocolorname": "A bat", "location": "Cave", "mobdead": True},
    ]
    assert env.fake.events(EVENT_MOBSORIG) == [{"mobsleft": expected}]
    assert env.fake.events(EVENT_MOBSLEFT) == [{"mobsleft": expected}]
    assert env.fake.finished == [CMDTYPE]
    assert env.fake.group_on("cpin")
    assert not env.fake.group_on("cpcheck")
    assert env.fake.omitted == [RAT, BAT, TIME]


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
    env.fake.feed(NEW)
    env.fake.record = {"matches": {"mob": "", "location": "x", "dead": ""}}
    env.plugin._trigger_mob()
    assert env.plugin.cp["mobsleft"] == []


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
    env.fake.feed(NEW)
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
    assert result.message[0] == "Mobs left:"
    assert any(line.startswith("@wA rat") for line in result.message)
    assert any(line.startswith("@RA bat") for line in result.message)


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
