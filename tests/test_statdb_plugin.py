"""Tests for the statdb plugin, with a stubbed API and a real database."""

import copy
import inspect
import sqlite3
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from statdb_old_db import build_old_database
from statdb_support import make_db

import aardwolf

if TYPE_CHECKING:
    from aardwolf.statdb.libs import StatStore
    from aardwolf.statdb.plugin._statdb import StatdbPlugin

PLUGIN_ID = "plugins.aardwolf.statdb"
PREFIX = "ev_plugins.aardwolf."


class FakeApi:
    """A stand-in for the bastproxy API that records what the plugin calls."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.db_error: Exception | None = None
        self.settings_added: list[tuple[str, str, object, str]] = []
        self.setting_values: dict[str, object] = {"backupstart": "0300", "backupinterval": 14400}
        self.trigger_adds: list[tuple[str, str]] = []
        self.trigger_regs: list[tuple[str, Callable[..., Any]]] = []
        self.trigger_ok = True
        self.timers: list[tuple[str, Callable[..., Any], float, dict[str, object]]] = []
        self.timers_removed: list[str] = []
        self.record: dict[str, Any] = {}
        self.gmcp: dict[str, Any] = {}
        self.args: dict[str, Any] = {}

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.settings:setting.add": self._setting_add,
            "plugins.core.settings:setting.get": lambda _plugin, key: self.setting_values[key],
            "plugins.core.sqldb:database.add": self._database_add,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
            "plugins.core.timers:timer.add": self._timer_add,
            "plugins.core.timers:timer.remove": self._timer_remove,
            "plugins.core.timers:timer.exists": self._timer_exists,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "libs.net.protocols:gmcp.value.get": self.gmcp.get,
            "plugins.core.commands:command.current.args.get": lambda: self.args,
            "plugins.core.utils:timelength.format": lambda seconds: f"{int(seconds)}s",
            "plugins.core.utils:number.to.readable": lambda number: f"<{number}>",
            "plugins.core.proxy:line.length.get": lambda: 40,
        }
        return table[name]

    def _setting_add(
        self, plugin_id: str, name: str, default: object, stype: str, help: str
    ) -> None:
        self.settings_added.append((plugin_id, name, default, stype))

    def _database_add(self, owner_id: str, name: str, tables: object, **kwargs: object) -> object:
        if self.db_error is not None:
            raise self.db_error
        return make_db(self.directory)

    def _trigger_add(self, name: str, regex: str) -> SimpleNamespace:
        self.trigger_adds.append((name, regex))
        return SimpleNamespace(success=self.trigger_ok, trigger=SimpleNamespace(trigger_id="tid"))

    def _timer_exists(self, name: str) -> bool:
        return any(timer[0] == name for timer in self.timers)

    def _timer_remove(self, name: str) -> None:
        if not self._timer_exists(name):
            raise AssertionError(f"removed a timer that does not exist: {name}")
        self.timers_removed.append(name)
        self.timers = [timer for timer in self.timers if timer[0] != name]

    def _trigger_register(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        self.trigger_regs.append((trigger_id, func))
        return True

    def _timer_add(
        self, name: str, func: Callable[..., Any], seconds: float, **kwargs: object
    ) -> None:
        self.timers.append((name, func, seconds, kwargs))


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: "StatdbPlugin", fake: FakeApi) -> None:
        self.plugin = plugin
        self.fake = fake

    @property
    def store(self) -> "StatStore":
        """The plugin's store."""
        assert self.plugin.statdb is not None
        return self.plugin.statdb

    def select(self, sql: str) -> list[dict[str, Any]]:
        """Run a select against the plugin's database."""
        return list(self.store.db.select(sql))


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build a StatdbPlugin with a fake API and load it."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("BASTPROXY_HOME", str(home))
    from aardwolf.statdb.plugin import _statdb

    fake = FakeApi(tmp_path / "db")
    plugin = _statdb.StatdbPlugin.__new__(_statdb.StatdbPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    plugin._phook_initialize()
    yield Env(plugin, fake)
    if plugin.statdb is not None:
        plugin.statdb.db.close()  # type: ignore[attr-defined]


WHOIS: dict[str, Any] = {
    "name": "Tester",
    "level": 10,
    "totallevels": 10,
    "remorts": 1,
    "classes": [{"remort": 1, "class": "mag"}],
}


def _send(env: Env, method: str, record: dict[str, Any]) -> dict[str, Any]:
    """Call an event callback with a record and return a copy of it from before the call."""
    env.fake.record = record
    before = copy.deepcopy(record)
    getattr(env.plugin, method)()
    return before


def _start(env: Env) -> None:
    """Give the plugin a current stats row."""
    _send(env, "_eventcb_whois", dict(WHOIS))


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    found = {p["plugin_id"]: p for p in result.plugins}
    assert "aardwolf.statdb" in found
    assert not [d for d in found["aardwolf.statdb"].get("dependencies", []) if "aardwolf" in d]


def test_after_load(env: Env) -> None:
    """Loading adds the settings, opens the database, adds the trigger and the start timer."""
    from aardwolf.statdb.plugin import _statdb

    assert env.plugin.statdb is not None
    assert env.fake.settings_added == [
        (PLUGIN_ID, "backupstart", "0000", "miltime"),
        (PLUGIN_ID, "backupinterval", "4h", "timelength"),
    ]
    assert env.fake.trigger_adds == [("dead", r"^You die\.$")]
    assert env.fake.trigger_regs == [("tid", env.plugin._trigger_dead)]
    assert env.fake.timers_removed == []
    name, func, seconds, kwargs = env.fake.timers[0]
    assert (name, seconds) == (f"{PLUGIN_ID}_backup_start", 86400)
    assert kwargs == {"time": "0300", "onetime": True}
    assert func == env.plugin._timer_backup_start
    assert len(_statdb.EVENTS) == 14


def test_registered_events(env: Env) -> None:
    """The plugin listens to the 14 source events, GMCP status, disconnect and two settings."""
    from aardwolf.statdb.plugin import _statdb

    names: set[str] = set()
    for _, method in inspect.getmembers(env.plugin, inspect.ismethod):
        for item in getattr(method, "event_registration", []):
            names.add(item["event_name"].format(**env.plugin.__dict__))
    expected = {
        f"{PREFIX}{name}"
        for name in (
            "quest_comp",
            "quest_failed",
            "cp_comp",
            "cp_failed",
            "whois_received",
            "level_gain",
            "level_hero",
            "level_superhero",
            "level_remort",
            "level_tier",
            "mobk_kill",
            "gq_completed",
            "gq_done",
            "gq_won",
        )
    }
    assert set(_statdb.EVENTS) == expected
    assert names == expected | {
        f"ev_{PLUGIN_ID}_var_backupstart_modified",
        f"ev_{PLUGIN_ID}_var_backupinterval_modified",
    }


def test_loads_when_the_database_fails(env: Env, tmp_path: Path) -> None:
    """A database that cannot be opened is logged and the commands say it is not available."""
    from bastproxy.plugins.core.commands import CommandResult

    env.fake.db_error = ValueError("cannot upgrade")
    env.plugin._phook_initialize()
    assert env.plugin.statdb is None
    env.fake.db_error = sqlite3.OperationalError("disk")
    env.plugin._phook_initialize()
    assert env.plugin.statdb is None
    for command in (
        "list",
        "comp",
        "quests",
        "levels",
        "cps",
        "gqs",
        "mobs",
    ):
        env.fake.args = {"milestone1": "", "milestone2": "", "count": 0, "number": 0}
        result = getattr(env.plugin, f"_command_{command}")()
        assert result == CommandResult(True, ["The stats database is not available"])
    for method in ("_eventcb_quest", "_eventcb_hero", "_eventcb_remort"):
        env.fake.record = {"failed": 0}
        getattr(env.plugin, method)()
    env.plugin._trigger_dead()
    env.plugin._timer_backup_start()


def test_trigger_failure_is_logged(env: Env) -> None:
    """A trigger that cannot be added does not stop the plugin from loading."""
    env.fake.trigger_ok = False
    env.plugin._phook_initialize()
    assert env.plugin.statdb is not None


def test_whois_event(env: Env) -> None:
    """The first whois adds current and start; the next updates current."""
    before = _send(env, "_eventcb_whois", dict(WHOIS))
    assert env.fake.record == before
    assert [r["milestone"] for r in env.select("SELECT milestone FROM stats")] == [
        "current",
        "start",
    ]
    _send(env, "_eventcb_whois", {**WHOIS, "totallevels": 12})
    assert env.select("SELECT totallevels FROM stats WHERE milestone = 'current'") == [
        {"totallevels": 12}
    ]
    assert env.plugin.statdb is not None
    assert env.plugin.statdb.get_classes() == ["mage"]


def test_quest_event(env: Env) -> None:
    """A completed and a failed quest write their rows and counters."""
    _start(env)
    _send(env, "_eventcb_quest", {"totqp": 30, "tp": 1, "failed": 0, "mobname": "a rat"})
    before = _send(env, "_eventcb_quest", {"failed": 1})
    assert env.fake.record == before
    assert len(env.select("SELECT * FROM quests")) == 2
    row = env.select("SELECT * FROM stats WHERE milestone = 'current'")[0]
    assert (row["questscomplete"], row["questsfailed"], row["qpearned"]) == (1, 1, 30)
    assert row["totaltrivia"] == 1


def test_campaign_event(env: Env) -> None:
    """A campaign writes its row and its mobs, and leaves the event data as it was."""
    _start(env)
    mobs = [{"name": "a goblin", "location": "Forest"}]
    before = _send(env, "_eventcb_cp", {"qp": 10, "tp": 0, "failed": 0, "mobs": mobs})
    assert env.fake.record == before
    assert env.select("SELECT cp_id, name FROM cpmobs") == [{"cp_id": 1, "name": "a goblin"}]
    assert env.select("SELECT campaignsdone FROM stats WHERE milestone = 'current'") == [
        {"campaignsdone": 1}
    ]


def test_gquest_events(env: Env) -> None:
    """A global quest counts a win only when it was won."""
    _start(env)
    mobs = [{"num": 2, "name": "a troll", "location": "Cave"}]
    _send(env, "_eventcb_gq", {"qp": 5, "qpmobs": 5, "won": 1, "mobs": mobs})
    _send(env, "_eventcb_gq", {"qp": 0, "qpmobs": 1, "won": 0, "mobs": []})
    row = env.select("SELECT gquestswon, qpearned FROM stats WHERE milestone = 'current'")[0]
    assert (row["gquestswon"], row["qpearned"]) == (1, 11)
    assert env.select("SELECT gq_id FROM gqmobs") == [{"gq_id": 1}]


def test_level_and_mobkill_events(env: Env) -> None:
    """A level adds a milestone and a kill adds to the kill count."""
    _start(env)
    _send(env, "_eventcb_level_gain", {"type": "level", "totallevels": 11, "starttime": 5})
    _send(env, "_eventcb_mobkill", {"name": "a rat", "tp": 1})
    assert env.store.get_milestone("11") is not None
    assert env.store.get_stat("monsterskilled") == 1
    assert env.store.get_stat("totallevels") == 11


def test_hero_event(env: Env) -> None:
    """A hero, superhero or tier event adds a milestone named from the GMCP total level."""
    _start(env)
    env.fake.gmcp = {"char.status.level": 3, "char.base.remorts": 1, "char.base.tier": 1}
    _send(env, "_eventcb_hero", {})
    assert env.store.get_milestone("t1r1l3") is not None
    _send(env, "_eventcb_hero", {})
    assert len(env.select("SELECT * FROM stats WHERE milestone = 't1r1l3'")) == 1


def test_remort_event(env: Env) -> None:
    """A remort sets the stats from GMCP and adds a milestone."""
    _start(env)
    env.fake.gmcp = {"char.status.level": 1, "char.base.remorts": 2, "char.base.tier": 0}
    _send(env, "_eventcb_remort", {})
    row = env.select("SELECT * FROM stats WHERE milestone = 'current'")[0]
    assert (row["remorts"], row["tiers"], row["totallevels"], row["level"]) == (2, 0, 202, 1)
    assert env.store.get_milestone("t0r2l1") is not None


def test_dead_trigger(env: Env) -> None:
    """A death adds one to timeskilled."""
    _start(env)
    env.plugin._trigger_dead()
    env.plugin._trigger_dead()
    assert env.store.get_stat("timeskilled") == 2


def test_save_failure_is_logged(env: Env, monkeypatch: pytest.MonkeyPatch) -> None:
    """A database error while saving an event does not reach the event system."""
    _start(env)

    def broken(info: dict[str, Any]) -> int:
        raise sqlite3.OperationalError("locked")

    monkeypatch.setattr(env.store, "save_quest", broken)
    _send(env, "_eventcb_quest", {"failed": 0})


def test_backup_start_timer_backs_up_and_adds_the_interval(env: Env) -> None:
    """The start timer backs up, then adds the interval timer from the setting."""
    _start(env)
    env.plugin._timer_backup_start()
    archives = list((env.fake.directory / "archive").glob("stats_*.sqlite.zip"))
    assert len(archives) == 1
    name, func, seconds, kwargs = env.fake.timers[-1]
    assert (name, seconds, kwargs) == (f"{PLUGIN_ID}_backup", 14400, {})
    assert func == env.plugin._timer_backup
    for archive in archives:
        archive.unlink()
    env.plugin._timer_backup()
    assert len(list((env.fake.directory / "archive").glob("stats_*.sqlite.zip"))) == 1


def test_backup_interval_that_is_not_usable_adds_no_timer(env: Env) -> None:
    """An interval of zero backs up once and adds no repeating timer."""
    env.fake.setting_values["backupinterval"] = 0
    before = len(env.fake.timers)
    env.plugin._timer_backup_start()
    assert len(env.fake.timers) == before


def test_setting_change_reschedules(env: Env) -> None:
    """A backup setting change removes both timers and adds the start timer again."""
    env.plugin._timer_backup_start()
    env.fake.timers_removed.clear()
    env.fake.setting_values["backupstart"] = "1200"
    env.plugin._eventcb_backup_setting_modified()
    assert env.fake.timers_removed == [f"{PLUGIN_ID}_backup_start", f"{PLUGIN_ID}_backup"]
    assert env.fake.timers[-1][0] == f"{PLUGIN_ID}_backup_start"
    assert env.fake.timers[-1][3] == {"time": "1200", "onetime": True}
    for archive in (env.fake.directory / "archive").glob("stats_*.sqlite.zip"):
        archive.unlink()


def test_schedule_removes_no_timer_that_does_not_exist(env: Env) -> None:
    """Scheduling with no backup timers yet removes nothing; the core logs an error for that."""
    env.fake.timers.clear()
    env.fake.timers_removed.clear()
    env.plugin._eventcb_backup_setting_modified()
    assert env.fake.timers_removed == []
    assert [timer[0] for timer in env.fake.timers] == [f"{PLUGIN_ID}_backup_start"]


def _fill_from_old(env: Env, tmp_path: Path) -> None:
    """Replace the plugin's empty database with a copy of a made-up old one."""
    from statdb_support import make_db

    from aardwolf.statdb.libs import StatStore

    assert env.plugin.statdb is not None
    env.plugin.statdb.db.close()  # type: ignore[attr-defined]
    directory = tmp_path / "old"
    directory.mkdir()
    build_old_database(directory / "stats.sqlite")
    env.plugin.statdb = StatStore(make_db(directory))


def _run(env: Env, command: str, **args: object) -> list[str]:
    """Run a command and return its lines, checking it succeeded."""
    from bastproxy.plugins.core.commands import CommandResult

    env.fake.args = {"milestone1": "", "milestone2": "", "count": 0, "number": 0, **args}
    result = getattr(env.plugin, f"_command_{command}")()
    assert isinstance(result, CommandResult)
    assert result.success is True
    assert isinstance(result.message, list)
    return result.message


def test_commands_on_an_empty_database(env: Env) -> None:
    """With no stats the commands say so; list says there are no milestones."""
    assert _run(env, "list") == ["No milestones"]
    assert _run(env, "comp") == [
        "milestone start does not exist",
        "milestone current does not exist",
    ]
    for command in ("quests", "levels", "cps", "gqs", "mobs"):
        assert _run(env, command) == ["No stats available"]


def test_commands_with_an_old_database(env: Env, tmp_path: Path) -> None:
    """Each command shows rows from a database written by the old plugin."""
    _fill_from_old(env, tmp_path)
    assert _run(env, "list")[0] == "Levels between 3 and 5"
    assert _run(env, "comp", milestone1="3")[0].split()[:3] == ["Milestone", "3", "current"]
    assert _run(env, "quests", count=2)[-1].split()[0] == "1"
    assert _run(env, "quests", number=1)[2].split()[0] == "1"
    assert _run(env, "levels", count=1)[-1].split()[0] == "3"
    env.fake.gmcp = {"char.base.perlevel": 600}
    assert _run(env, "levels", number=3)[1].split() == ["3", "lev", "5", "re0t0r1l5"]
    assert _run(env, "cps", count=1)[-1].split()[-1] == "Failed"
    assert _run(env, "cps", number=1)[-2].startswith("@Gan orc")
    assert _run(env, "gqs", count=1)[-1].split()[0] == "2"
    assert _run(env, "gqs", number=1)[-2].startswith("@G3")
    assert _run(env, "mobs", count=1)[-1].split()[2] == "bat"


@pytest.mark.parametrize(
    ("command", "text"),
    [
        ("quests", "No such quest: 77"),
        ("levels", "No such level: 77"),
        ("cps", "No such campaign: 77"),
        ("gqs", "No such global quest: 77"),
    ],
)
def test_unknown_number_reports_instead_of_failing(
    env: Env, tmp_path: Path, command: str, text: str
) -> None:
    """A number that is not in the table reports that it is missing."""
    _fill_from_old(env, tmp_path)
    assert _run(env, command, number=77) == [text]


def test_command_arguments_are_declared(env: Env) -> None:
    """The count and number arguments are whole numbers, with count optional."""
    for command in ("quests", "levels", "cps", "gqs"):
        data = getattr(env.plugin, f"_command_{command}").command_data
        names = [item["args"] for item in data.arguments]
        assert names == [("count",), ("-n", "--number")]
        assert all(item["kwargs"]["type"] is int for item in data.arguments)
    assert env.plugin._command_mobs.command_data.arguments[0]["kwargs"]["nargs"] == "?"
    assert env.plugin._command_list.command_data.command["kwargs"]["group"] == "Milestones"
    assert env.plugin._command_quests.command_data.command["kwargs"]["group"] == "Stats"
