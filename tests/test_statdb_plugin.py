"""Tests for the statdb plugin, with a stubbed API and a real database."""

import copy
import inspect
import sqlite3
from collections.abc import Awaitable, Callable, Iterable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock

import pytest
from statdb_old_db import build_old_database
from statdb_support import make_db

import aardwolf

if TYPE_CHECKING:
    from bastproxy.libs.records import NetworkData
    from bastproxy.plugins.core.web.libs._http import Response

    from aardwolf.statdb.libs import StatStore, TablePage, TableParams, TableResult
    from aardwolf.statdb.plugin._statdb import StatdbPlugin

PLUGIN_ID = "plugins.aardwolf.statdb"
PREFIX = "ev_plugins.aardwolf."


class FakeApi:
    """A stand-in for the bastproxy API that records what the plugin calls."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.db_error: Exception | None = None
        self.database_add_kwargs: dict[str, object] = {}
        self.settings_added: list[tuple[str, str, object, object]] = []
        self.setting_values: dict[str, object] = {"backupstart": "0300", "backupinterval": 14400}
        self.validators: dict[str, Callable[..., Any]] = {}
        self.trigger_adds: list[tuple[str, str]] = []
        self.trigger_regs: list[tuple[str, Callable[..., Any]]] = []
        self.trigger_ok = True
        self.timers: list[tuple[str, Callable[..., Any], float, dict[str, object]]] = []
        self.timers_removed: list[str] = []
        self.record: dict[str, Any] = {}
        self.gmcp: dict[str, Any] = {}
        self.args: dict[str, Any] = {}
        self.routes: list[
            tuple[str, str, Callable[..., Any], str, list[dict[str, str]] | None]
        ] = []
        self.route_paths: bool = True
        self.unlisted: set[str] = set()
        self.mapper_rooms: dict[str, dict[str, Any]] | None = None
        self.mapper_areas: dict[str, dict[str, Any]] = {}
        # every table.format call: (title, the rows, the columns)
        self.tables: list[tuple[str, list[dict[str, str]], list[dict[str, str]]]] = []

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
            "plugins.core.utils:table.format": self._table_format,
            "plugins.core.web:web.route.add": self._route_add,
            "libs.api:api.exists": self._api_exists,
            "plugins.client.mapper:room.get": lambda uid: (self.mapper_rooms or {}).get(uid),
            "plugins.client.mapper:area.get": lambda uid: self.mapper_areas.get(uid),
        }
        return table[name]

    def _table_format(
        self, title: str, data: Iterable[dict[str, str]], columns: list[dict[str, str]]
    ) -> list[str]:
        """Record a table.format call and return the title as its only line."""
        self.tables.append((title, list(data), columns))
        return [title]

    def _route_add(
        self,
        owner: str,
        subpath: str,
        handler: Callable[..., Any],
        title: str,
        columns: list[dict[str, str]] | None = None,
        *,
        listed: bool = True,
    ) -> str | None:
        self.routes.append((owner, subpath, handler, title, columns))
        if not listed:
            self.unlisted.add(subpath)
        if not self.route_paths:
            return None
        return f"/aardwolf/statdb/{subpath}".rstrip("/")

    def _api_exists(self, name: str) -> bool:
        return self.mapper_rooms is not None or not name.startswith("plugins.client.mapper:")

    def _setting_add(
        self,
        plugin_id: str,
        name: str,
        default: object,
        stype: object,
        help: str,
        **kwargs: object,
    ) -> None:
        self.settings_added.append((plugin_id, name, default, stype))
        self.setting_values.setdefault(name, default)
        if "validator" in kwargs:
            self.validators[name] = cast("Callable[..., Any]", kwargs["validator"])

    def _database_add(self, owner_id: str, name: str, tables: object, **kwargs: object) -> object:
        if self.db_error is not None:
            raise self.db_error
        self.database_add_kwargs = kwargs
        journal_mode = kwargs.get("journal_mode")
        assert journal_mode is None or isinstance(journal_mode, str)
        return make_db(self.directory, journal_mode=journal_mode)

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
        (PLUGIN_ID, "mobkillcount", 10, int),
        (PLUGIN_ID, "chartdays", 30, int),
        (PLUGIN_ID, "chartlevels", 50, int),
        (PLUGIN_ID, "chartareas", 20, int),
        (PLUGIN_ID, "timeformat", "%a, %d %b %Y %H:%M:%S", str),
    ]
    assert env.fake.trigger_adds == [("dead", r"^You die\.$")]
    assert env.fake.trigger_regs == [("tid", env.plugin._trigger_dead)]
    assert env.fake.timers_removed == []
    name, func, seconds, kwargs = env.fake.timers[0]
    assert (name, seconds) == (f"{PLUGIN_ID}_backup_start", 86400)
    assert kwargs == {"time": "0300", "onetime": True}
    assert func == env.plugin._timer_backup_start
    assert len(_statdb.EVENTS) == 14
    assert env.fake.database_add_kwargs["journal_mode"] == "wal"
    journal = env.plugin.statdb.db.select("PRAGMA journal_mode")
    assert next(iter(journal[0].values())) == "wal"


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
        "mobkills",
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


@pytest.fixture
def sent(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Collect the messages the plugin sends directly to the client."""
    from aardwolf.statdb.plugin import _statdb

    lines: list[str] = []

    class FakeSend:
        def __init__(self, data: "NetworkData") -> None:
            lines.extend(str(line.original_line) for line in data)

        def __call__(self) -> None:
            return None

    monkeypatch.setattr(_statdb, "SendDataDirectlyToClient", FakeSend)
    return lines


def test_whois_for_another_character_warns_and_saves(
    env: Env, sent: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    """A whois for a different character warns in the log and the client, and still saves."""
    _send(env, "_eventcb_whois", dict(WHOIS))
    with caplog.at_level("WARNING"):
        _send(env, "_eventcb_whois", {**WHOIS, "name": "Other", "totallevels": 12})
    assert len(sent) == 1
    assert "holds Tester" in sent[0]
    assert "Other" in sent[0]
    assert any("holds Tester" in r.getMessage() for r in caplog.records)
    assert env.store.stored_name() == "Other"


@pytest.mark.parametrize("name", ["Tester", "tester", " TESTER "])
def test_whois_for_the_same_character_does_not_warn(
    env: Env, sent: list[str], caplog: pytest.LogCaptureFixture, name: str
) -> None:
    """The first whois and a whois for the same name, in any case, do not warn."""
    with caplog.at_level("WARNING"):
        _send(env, "_eventcb_whois", dict(WHOIS))
        _send(env, "_eventcb_whois", {**WHOIS, "name": name})
    assert sent == []
    assert not caplog.records


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
    _run(env, "comp", milestone1="3")
    assert [c["name"] for c in env.fake.tables[-1][2][:3]] == ["Milestone", "3", "current"]
    _run(env, "quests", count=2)
    assert env.fake.tables[-1][1][-1]["id"] == "1"
    _run(env, "quests", number=1)
    assert env.fake.tables[-2][1][0]["id"] == "1"
    _run(env, "levels", count=1)
    assert env.fake.tables[-1][1][-1]["id"] == "3"
    env.fake.gmcp = {"char.base.perlevel": 600}
    assert _run(env, "levels", number=3)[1].split() == ["3", "lev", "5", "re0t0r1l5"]
    assert _run(env, "cps", count=1)[-1].split()[-1] == "Failed"
    assert _run(env, "cps", number=1)[-2].startswith("@Gan orc")
    assert _run(env, "gqs", count=1)[-1].split()[0] == "2"
    assert _run(env, "gqs", number=1)[-2].startswith("@G3")
    assert _run(env, "mobs", count=1)[-1].split()[2] == "bat"
    _run(env, "mobkills", count=10)
    assert len(env.fake.tables[-1][1]) == 3
    _run(env, "mobkills", count=1)
    assert len(env.fake.tables[-1][1]) == 1
    assert "a bat" in env.fake.tables[-1][1][-1]["name"]


def test_mobkills_on_an_empty_database(env: Env) -> None:
    """With no kills the command says so."""
    assert _run(env, "mobkills", count=10) == ["No kills recorded"]


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


def test_mobkills_argument_is_declared(env: Env) -> None:
    """The count is an optional whole number; with none the mobkillcount setting applies."""
    data = env.plugin._command_mobkills.command_data
    assert [item["args"] for item in data.arguments] == [("-c", "--count")]
    assert data.arguments[0]["kwargs"]["type"] is int
    assert data.arguments[0]["kwargs"]["default"] is None
    assert data.command["kwargs"]["group"] == "Stats"


def test_mobkills_count_defaults_to_the_setting(env: Env) -> None:
    """With no -c the mobkillcount setting says how many kills are listed; -c wins."""
    for number in range(1, 6):
        env.store.save_mobkill({"name": f"mob {number}", "totalxp": 1, "time": number * 100})
    assert env.fake.setting_values["mobkillcount"] == 10
    env.fake.setting_values["mobkillcount"] = 2
    _run(env, "mobkills", count=None)
    assert len(env.fake.tables[-1][1]) == 2
    _run(env, "mobkills", count=3)
    assert len(env.fake.tables[-1][1]) == 3


def test_new_settings_refuse_bad_values(env: Env) -> None:
    """Counts must be whole numbers in range and the time format a usable pattern."""
    for name in ("mobkillcount", "chartdays", "chartlevels", "chartareas"):
        assert env.fake.validators[name](0) is not None
        assert env.fake.validators[name](5) is None
        assert env.fake.validators[name]("5") is not None
    assert env.fake.validators["timeformat"]("%H:%M") is None
    assert env.fake.validators["timeformat"]("no directive") is not None


def test_formatters_table_goes_through_the_core_table_format(env: Env) -> None:
    """The table helper of the formatters calls plugins.core.utils:table.format."""
    cols = [{"name": "A", "key": "a"}]
    assert env.plugin._formatters().table("T", [{"a": "1"}], cols) == ["T"]
    assert env.fake.tables[-1] == ("T", [{"a": "1"}], cols)


def test_timeformat_setting_reaches_the_report_formatters(env: Env) -> None:
    """The formatters carry the timeformat setting, read each time."""
    assert env.plugin._formatters().time_format == "%a, %d %b %Y %H:%M:%S"
    env.fake.setting_values["timeformat"] = "%Y"
    assert env.plugin._formatters().time_format == "%Y"


# web pages

TABLE_ROUTES = {
    "milestones",
    "quests",
    "levels",
    "cps",
    "cpmobs",
    "gqs",
    "gqmobs",
    "mobs",
    "mobkills",
}
CHART_ROUTES = {"chart/qp-per-day", "chart/gold-per-day", "chart/level-time", "chart/area-kills"}


def _web_routes(env: Env) -> dict[str, tuple[Callable[..., Any], str, list[dict[str, str]] | None]]:
    """Return the routes the plugin registered, by subpath."""
    return {
        subpath: (handler, title, columns)
        for _owner, subpath, handler, title, columns in env.fake.routes
    }


async def _wait(value: Awaitable[object]) -> object:
    """Await a handler's result."""
    return await value


def _call(env: Env, subpath: str, query: dict[str, str] | None = None) -> dict[str, Any]:
    """Run a route handler the way the web plugin does, with a validated table query."""
    import asyncio

    from bastproxy.plugins.core.web.libs._table import make_columns, parse_table_query

    handler, _title, columns = _web_routes(env)[subpath]
    params = query or {}
    table = parse_table_query(params, make_columns(columns)) if columns is not None else None
    result = handler(SimpleNamespace(query=params, table=table))
    if inspect.isawaitable(result):
        result = asyncio.run(_wait(result))
    assert isinstance(result, dict)
    return result


def _fill_web_data(env: Env) -> None:
    """Give the plugin's database a few made-up rows."""
    _start(env)
    env.store.save_quest(
        {"starttime": 100, "finishtime": 160, "mobname": "a rat", "qp": 20, "totqp": 25,
         "gold": 300, "level": 5}
    )  # fmt: skip
    env.store.save_cp(
        {"starttime": 10, "finishtime": 70, "qp": 30, "level": 4, "mobs": [{"name": "an orc"}]}
    )
    env.store.save_gq({"starttime": 5, "finishtime": 65, "qp": 40, "level": 5, "won": 1})
    env.store.save_level({"type": "level", "level": 5, "totallevels": 5, "starttime": 1000})
    env.store.save_level({"type": "level", "level": 6, "totallevels": 6, "starttime": 1600})
    env.store.save_mobkill({"name": "a bat", "totalxp": 4, "time": 2600, "level": 5, "room_id": 7})
    env.store.save_mobkill({"name": "a cat", "totalxp": 5, "time": 2700, "level": 5, "room_id": 8})


def test_web_routes_are_registered_under_the_plugin(env: Env) -> None:
    """Fifteen routes are added by the plugin itself; tables declare their columns."""
    routes = _web_routes(env)
    assert len(env.fake.routes) == 15
    assert {owner for owner, *_rest in env.fake.routes} == {PLUGIN_ID}
    assert set(routes) == {"", "comp", *TABLE_ROUTES, *CHART_ROUTES}
    for subpath, (_handler, _title, columns) in routes.items():
        assert (columns is not None) == (subpath in TABLE_ROUTES)
    assert [column["name"] for column in routes["mobs"][2] or []][:3] == ["lvl", "mob", "txp"]
    assert env.fake.unlisted == {"comp"}


def test_web_routes_follow_the_unload_contract(env: Env) -> None:
    """The real route table accepts every route under /aardwolf/statdb and removes them."""
    from bastproxy.plugins.core.web.libs._store import RouteTable

    table = RouteTable()
    for owner, subpath, handler, title, columns in env.fake.routes:
        path = table.add(
            owner, subpath, handler, title, columns, listed=subpath not in env.fake.unlisted
        )
        assert path == f"/aardwolf/statdb/{subpath}".rstrip("/")
        assert table.match(path) is not None
    assert table.count() == 15
    assert table.remove(PLUGIN_ID) == 15
    assert table.count() == 0


def test_web_index_lists_the_pages_as_text(env: Env) -> None:
    """The index page holds one text line per page the web plugin accepted."""
    result = _call(env, "")
    assert result["kind"] == "html"
    assert len(result["lines"]) == 14
    assert "Quests: /aardwolf/statdb/quests" in result["lines"]
    env.fake.routes.clear()
    env.fake.route_paths = False
    env.plugin._add_web_routes()
    assert _call(env, "")["lines"] == []


def test_table_handler_returns_a_page_with_the_summary(env: Env) -> None:
    """A table route returns its rows, the total and the text report's summary."""
    _fill_web_data(env)
    result = _call(env, "quests")
    assert result["kind"] == "table"
    assert result["total"] == 1
    assert result["rows"][0][1] == 20
    assert result["rows"][0][0] == {"text": "1", "href": "/aardwolf/statdb/quests?f_id=1"}
    assert any(line.startswith("@GDB Stats") for line in result["lines"])
    paged = _call(env, "mobkills", {"count": "1", "page": "2"})
    assert paged["total"] == 2
    assert [row[1] for row in paged["rows"]] == ["a bat"]
    filtered = _call(env, "mobs", {"f_mob": "cat"})
    assert filtered["total"] == 1
    assert _call(env, "cpmobs", {"f_cp_id": "1"})["rows"] == [[1, "an orc", "Unknown"]]
    assert _call(env, "milestones")["lines"]


def test_table_handler_says_when_there_is_nothing_to_show(env: Env) -> None:
    """A report without data returns the text command's message as a page."""
    assert _call(env, "quests") == {
        "kind": "html",
        "title": "Quests",
        "lines": ["No stats available"],
    }
    _start(env)
    assert _call(env, "cps")["lines"] == ["No campaign stats available"]


def test_comp_handler_statuses(env: Env) -> None:
    """The comp page is 400 without both names, 404 for an unknown one, else the comparison."""
    _fill_web_data(env)
    for query in ({}, {"first": "start"}, {"first": "", "second": "current"}):
        result = _call(env, "comp", query)
        assert result == {
            "kind": "error",
            "status": 400,
            "message": "first and second milestone names are required",
        }
    missing = _call(env, "comp", {"first": "nope' OR 1=1 --", "second": "current"})
    assert missing == {
        "kind": "error",
        "status": 404,
        "message": "milestone nope' OR 1=1 -- does not exist",
    }
    both = _call(env, "comp", {"first": "nope", "second": "nada"})
    assert both["status"] == 404
    assert both["message"] == "milestone nope does not exist; milestone nada does not exist"
    result = _call(env, "comp", {"first": "start", "second": "current"})
    assert result["kind"] == "html"
    assert [c["name"] for c in env.fake.tables[-1][2][:3]] == ["Milestone", "start", "current"]


def test_table_handler_links_cells(env: Env) -> None:
    """The listed cells are link cells; a mob kill's room links to the core mapper."""
    _fill_web_data(env)

    def link(path: str, key: str, value: int) -> dict[str, str]:
        return {"text": str(value), "href": f"{path}?{key}={value}"}

    base = "/aardwolf/statdb"
    assert _call(env, "quests")["rows"][0][0] == link(f"{base}/quests", "f_id", 1)
    assert _call(env, "levels")["rows"][0][0] == link(f"{base}/levels", "f_id", 2)
    assert _call(env, "cps")["rows"][0][0] == link(f"{base}/cpmobs", "f_cp_id", 1)
    assert _call(env, "gqs")["rows"][0][0] == link(f"{base}/gqmobs", "f_gq_id", 1)
    cells = [
        cell for row in _call(env, "mobkills")["rows"] for cell in row if isinstance(cell, dict)
    ]
    assert cells == [
        link("/client/mapper/room", "uid", 8),
        link("/client/mapper/room", "uid", 7),
    ]


def test_linked_columns_still_sort_filter_and_page(env: Env) -> None:
    """Sorting, filtering and paging work on the linked columns."""
    _fill_web_data(env)
    link = {"text": "8", "href": "/client/mapper/room?uid=8"}
    desc = _call(env, "mobkills", {"sort": "room", "dir": "desc"})
    assert desc["total"] == 2
    assert link in desc["rows"][0]
    filtered = _call(env, "mobkills", {"f_room": "7"})
    assert filtered["total"] == 1
    assert {"text": "7", "href": "/client/mapper/room?uid=7"} in filtered["rows"][0]
    paged = _call(env, "cps", {"f_id": "1", "count": "1"})
    assert paged["total"] == 1
    assert paged["rows"][0][0] == {"text": "1", "href": "/aardwolf/statdb/cpmobs?f_cp_id=1"}


def test_links_fall_back_to_plain_values_when_a_route_is_refused(env: Env) -> None:
    """A refused route gives plain cells; the mapper room path is a constant."""
    _fill_web_data(env)
    env.fake.routes.clear()
    env.fake.route_paths = False
    env.plugin._add_web_routes()
    assert _call(env, "quests")["rows"][0][0] == 1
    assert _call(env, "cps")["rows"][0][0] == 1
    cells = [cell for row in _call(env, "mobkills")["rows"] for cell in row]
    assert {"text": "7", "href": "/client/mapper/room?uid=7"} in cells


def test_core_index_omits_comp(env: Env) -> None:
    """The route table lists the tables and leaves the comp page out of the core index."""
    from bastproxy.plugins.core.web.libs._store import RouteTable

    table = RouteTable()
    for owner, subpath, handler, title, columns in env.fake.routes:
        table.add(owner, subpath, handler, title, columns, listed=subpath not in env.fake.unlisted)
    comp = table.match("/aardwolf/statdb/comp")
    quests = table.match("/aardwolf/statdb/quests")
    assert comp is not None
    assert quests is not None
    assert comp.listed is False
    assert quests.listed is True


def test_chart_handlers_return_svg(env: Env) -> None:
    """Each day and level chart returns an SVG document with its title."""
    _fill_web_data(env)
    for subpath in ("chart/qp-per-day", "chart/gold-per-day", "chart/level-time"):
        result = _call(env, subpath)
        assert result["kind"] == "svg"
        assert result["svg"].startswith("<svg")
        assert "No data" not in result["svg"]
    assert "Quest points per day" in _call(env, "chart/qp-per-day")["svg"]


def test_chart_settings_set_the_bars_and_the_titles(env: Env) -> None:
    """The chart settings are read for each request: bars and the SVG title follow them."""
    _fill_web_data(env)
    env.fake.setting_values["chartdays"] = 7
    env.fake.setting_values["chartlevels"] = 9
    env.fake.setting_values["chartareas"] = 3
    assert "newest 7 days" in _call(env, "chart/qp-per-day")["svg"]
    assert "newest 7 days" in _call(env, "chart/gold-per-day")["svg"]
    assert "last 9 levels" in _call(env, "chart/level-time")["svg"]
    assert "top 3" in _call(env, "chart/area-kills")["svg"]
    titles = {subpath: title for _, subpath, _, title, _ in env.fake.routes}
    assert titles["chart/qp-per-day"] == "Quest points per day"
    assert titles["chart/area-kills"] == "Kills per area"


def test_area_chart_without_the_mapper_counts_unknown(env: Env) -> None:
    """With no mapper every kill is in the Unknown area."""
    _fill_web_data(env)
    assert env.fake.mapper_rooms is None
    svg = _call(env, "chart/area-kills")["svg"]
    assert "Unknown: 2 kills" in svg


def test_area_chart_maps_rooms_to_areas(env: Env) -> None:
    """With the mapper, kills are added per area name; a missing area uses its uid."""
    _fill_web_data(env)
    env.fake.mapper_rooms = {"7": {"area": "cave"}, "8": {"area": "pit"}}
    env.fake.mapper_areas = {"cave": {"name": "The Cave"}}
    svg = _call(env, "chart/area-kills")["svg"]
    assert "The Cave: 1 kills" in svg
    assert "pit: 1 kills" in svg
    assert "Unknown" not in svg


def test_area_chart_yields_between_lookups(env: Env) -> None:
    """Looking up many rooms still maps every room."""
    _start(env)
    for room in range(1, 121):
        env.store.save_mobkill({"name": "x", "room_id": room, "time": 1})
    env.fake.mapper_rooms = {str(room): {"area": "all"} for room in range(1, 121)}
    env.fake.mapper_areas = {"all": {"name": "Everywhere"}}
    assert "Everywhere: 120 kills" in _call(env, "chart/area-kills")["svg"]


def test_pages_say_so_when_there_is_no_database(env: Env) -> None:
    """Without a database every page says it is not available."""
    env.plugin.statdb = None
    for subpath in TABLE_ROUTES:
        assert _call(env, subpath)["lines"] == ["The stats database is not available"]
    both = {"first": "start", "second": "current"}
    assert _call(env, "comp", both)["lines"] == ["The stats database is not available"]
    for subpath in CHART_ROUTES:
        result = _call(env, subpath)
        assert "The stats database is not available" in result["svg"]
        assert "No data" in result["svg"]


def test_pages_say_so_when_the_database_cannot_be_read(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A sqlite error is logged and the page says the database could not be read."""
    from aardwolf.statdb.plugin import _statdb

    def fail(*_args: object) -> object:
        raise sqlite3.OperationalError("disk I/O error")

    for name in ("read_table", "read_milestone_rows", "read_chart", "read_room_kills"):
        monkeypatch.setattr(_statdb, name, fail)
    assert _call(env, "quests")["lines"] == ["The stats database could not be read"]
    both = {"first": "start", "second": "current"}
    assert _call(env, "comp", both)["lines"] == ["The stats database could not be read"]
    assert "The stats database could not be read" in _call(env, "chart/qp-per-day")["svg"]
    assert "The stats database could not be read" in _call(env, "chart/area-kills")["svg"]


def test_database_path_comes_from_the_open_database(env: Env, tmp_path: Path) -> None:
    """The path is the database file, and None when the database is not open."""
    assert env.plugin._db_path() == tmp_path / "db" / "stats.sqlite"
    env.plugin.statdb = None
    assert env.plugin._db_path() is None


def test_real_web_app_gates_and_serves_the_routes(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Through the real web app: POST is 405, no session 401, bad parameters 400, GET 200."""
    import asyncio

    from bastproxy.plugins.core.web.libs._http import Request
    from bastproxy.plugins.core.web.libs._server import SESSION_COOKIE, WebApp
    from bastproxy.plugins.core.web.libs._store import PageStore, RouteTable, SessionStore

    from aardwolf.statdb.plugin import _statdb

    _fill_web_data(env)
    routes = RouteTable()
    for owner, subpath, handler, title, columns in env.fake.routes:
        routes.add(owner, subpath, handler, title, columns, listed=subpath not in env.fake.unlisted)
    sessions = SessionStore()
    app = WebApp(PageStore(), routes=routes, sessions=sessions)
    cookies = {SESSION_COOKIE: sessions.create(60)}
    path = "/aardwolf/statdb/quests"

    def get(request: Request) -> "Response":
        return asyncio.run(app.dispatch(request))

    assert get(Request("POST", path, {}, cookies)).status == 405
    assert get(Request("GET", path, {}, {})).status == 401

    opened: list[object] = []
    real = _statdb.read_table

    def spy(path: Path, page: "TablePage", table: "TableParams") -> "TableResult":
        opened.append(path)
        return real(path, page, table)

    monkeypatch.setattr(_statdb, "read_table", spy)
    for query in (
        {"sort": "nope"},
        {"dir": "sideways"},
        {"page": "0"},
        {"count": "501"},
        {"f_nope": "x"},
        {"f_qp": "abc"},
        {"f_mob": "x" * 201},
    ):
        assert get(Request("GET", path, query, cookies)).status == 400
    assert opened == []

    response = get(Request("GET", path, {"sort": "qp", "dir": "desc"}, cookies))
    assert response.status == 200
    assert b"a rat" in response.body
    assert len(opened) == 1
    assert b"<a href='/aardwolf/statdb/quests?f_id=1'>1</a>" in response.body
    comp = "/aardwolf/statdb/comp"
    assert get(Request("GET", comp, {}, cookies)).status == 400
    assert get(Request("GET", comp, {"first": "nope", "second": "current"}, cookies)).status == 404
    assert get(Request("GET", comp, {"first": "start", "second": "current"}, cookies)).status == 200
    kills = get(Request("GET", "/aardwolf/statdb/mobkills", {}, cookies))
    assert kills.status == 200
    assert b"<a href='/client/mapper/room?uid=7'>7</a>" in kills.body
    assert get(Request("GET", "/aardwolf/statdb/chart/qp-per-day", {}, cookies)).status == 200


def test_mud_text_in_link_text_stays_escaped(env: Env) -> None:
    """Through the web app, MUD text and the text of a link cell are both HTML-escaped."""
    import asyncio

    from bastproxy.plugins.core.web.libs._http import Request
    from bastproxy.plugins.core.web.libs._server import SESSION_COOKIE, WebApp
    from bastproxy.plugins.core.web.libs._store import PageStore, RouteTable, SessionStore

    from aardwolf.statdb.libs import link_cell

    _start(env)
    env.store.save_mobkill(
        {"name": "<b>x&</b>", "totalxp": 4, "time": 2600, "level": 5, "room_id": 7}
    )
    routes = RouteTable()
    for owner, subpath, handler, title, columns in env.fake.routes:
        routes.add(owner, subpath, handler, title, columns, listed=subpath not in env.fake.unlisted)
    routes.add("test", "evil", lambda _request: {
        "kind": "table",
        "title": "Evil",
        "rows": [[link_cell("<i>", "/aardwolf/statdb/quests", "f_id", 1)]],
        "total": 1,
        "lines": [],
    }, "Evil", [{"name": "id", "label": "ID", "type": "text"}])  # fmt: skip
    sessions = SessionStore()
    app = WebApp(PageStore(), routes=routes, sessions=sessions)
    cookies = {SESSION_COOKIE: sessions.create(60)}
    body = asyncio.run(app.dispatch(Request("GET", "/aardwolf/statdb/mobkills", {}, cookies))).body
    assert b"&lt;b&gt;x&amp;&lt;/b&gt;" in body
    assert b"<b>" not in body
    evil = asyncio.run(app.dispatch(Request("GET", "/test/evil", {}, cookies))).body
    assert b"<a href='/aardwolf/statdb/quests?f_id=1'>&lt;i&gt;</a>" in evil
