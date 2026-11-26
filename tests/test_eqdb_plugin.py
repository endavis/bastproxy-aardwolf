"""Tests for the eqdb plugin, with a stubbed API and a real database."""

import inspect
import sqlite3
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from eqdb_support import make_db, sample_item

import aardwolf

if TYPE_CHECKING:
    from aardwolf.eqdb.plugin._eqdb import EqdbPlugin

PLUGIN_ID = "plugins.aardwolf.eqdb"


class FakeApi:
    """A stand-in for the bastproxy API that records what the plugin calls."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.db_error: Exception | None = None
        self.database_add_kwargs: dict[str, object] = {}
        self.settings_added: list[tuple[str, str, object, str]] = []
        self.setting_values: dict[str, object] = {"backupstart": "0300", "backupinterval": 14400}
        self.timers: list[tuple[str, Callable[..., Any], float, dict[str, object]]] = []
        self.timers_removed: list[str] = []
        self.args: dict[str, Any] = {}

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.settings:setting.add": self._setting_add,
            "plugins.core.settings:setting.get": lambda _plugin, key: self.setting_values[key],
            "plugins.core.sqldb:database.add": self._database_add,
            "plugins.core.timers:timer.add": self._timer_add,
            "plugins.core.timers:timer.remove": self._timer_remove,
            "plugins.core.timers:timer.exists": self._timer_exists,
            "plugins.core.commands:command.current.args.get": lambda: self.args,
        }
        return table[name]

    def _setting_add(
        self, plugin_id: str, name: str, default: object, stype: str, help: str
    ) -> None:
        self.settings_added.append((plugin_id, name, default, stype))

    def _database_add(self, owner_id: str, name: str, tables: object, **kwargs: object) -> object:
        if self.db_error is not None:
            raise self.db_error
        self.database_add_kwargs = kwargs
        journal_mode = kwargs.get("journal_mode")
        assert journal_mode is None or isinstance(journal_mode, str)
        return make_db(self.directory, journal_mode=journal_mode)

    def _timer_exists(self, name: str) -> bool:
        return any(timer[0] == name for timer in self.timers)

    def _timer_remove(self, name: str) -> None:
        if not self._timer_exists(name):
            raise AssertionError(f"removed a timer that does not exist: {name}")
        self.timers_removed.append(name)
        self.timers = [timer for timer in self.timers if timer[0] != name]

    def _timer_add(
        self, name: str, func: Callable[..., Any], seconds: float, **kwargs: object
    ) -> None:
        self.timers.append((name, func, seconds, kwargs))


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: "EqdbPlugin", fake: FakeApi) -> None:
        self.plugin = plugin
        self.fake = fake


def _build(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, db_error: Exception | None) -> Env:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("BASTPROXY_HOME", str(home))
    from aardwolf.eqdb.plugin import _eqdb

    fake = FakeApi(tmp_path / "db")
    fake.db_error = db_error
    plugin = _eqdb.EqdbPlugin.__new__(_eqdb.EqdbPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    plugin._phook_initialize()
    return Env(plugin, fake)


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build an EqdbPlugin with a fake API and load it."""
    built = _build(monkeypatch, tmp_path, None)
    yield built
    if built.plugin.store is not None:
        built.plugin.store.db.close()  # type: ignore[attr-defined]


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    found = {p["plugin_id"]: p for p in result.plugins}
    assert "aardwolf.eqdb" in found
    assert not [d for d in found["aardwolf.eqdb"].get("dependencies", []) if "aardwolf" in d]


def test_after_load(env: Env) -> None:
    """Loading adds the settings, opens the database and adds the start timer."""
    assert env.plugin.store is not None
    assert env.fake.settings_added == [
        (PLUGIN_ID, "backupstart", "0000", "miltime"),
        (PLUGIN_ID, "backupinterval", "4h", "timelength"),
    ]
    assert env.fake.timers_removed == []
    name, func, seconds, kwargs = env.fake.timers[0]
    assert (name, seconds) == (f"{PLUGIN_ID}_backup_start", 86400)
    assert kwargs == {"time": "0300", "onetime": True}
    assert func == env.plugin._timer_backup_start
    assert env.plugin.store.db.checktableexists("items")  # type: ignore[attr-defined]
    assert env.fake.database_add_kwargs["journal_mode"] == "wal"
    journal = env.plugin.store.db.select("PRAGMA journal_mode")
    assert next(iter(journal[0].values())) == "wal"


def test_registered_events(env: Env) -> None:
    """The plugin listens to its own two backup settings only."""
    names: set[str] = set()
    for _, method in inspect.getmembers(env.plugin, inspect.ismethod):
        for item in getattr(method, "event_registration", []):
            names.add(item["event_name"].format(**env.plugin.__dict__))
    assert names == {
        f"ev_{PLUGIN_ID}_var_backupstart_modified",
        f"ev_{PLUGIN_ID}_var_backupinterval_modified",
    }


def test_item_save_and_get_round_trip(env: Env) -> None:
    """item.save then item.get through the plugin."""
    item = sample_item()
    assert env.plugin._api_item_save(item) is True
    assert env.plugin._api_item_get(1001) == item
    assert env.plugin._api_item_get("1001", details=False) is not None
    assert env.plugin._api_item_get(555) is None


def test_item_save_without_serial_is_false(env: Env) -> None:
    """A mapping with no serial is not saved."""
    assert env.plugin._api_item_save({"name": "x"}) is False


def test_item_save_logs_a_database_error(
    env: Env, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A sqlite error is logged and the API returns False."""
    from aardwolf.eqdb.plugin import _eqdb

    assert env.plugin.store is not None

    def broken(item: object) -> bool:
        raise sqlite3.OperationalError("locked")

    logged: list[tuple[Any, ...]] = []
    monkeypatch.setattr(env.plugin.store, "save_item", broken)
    monkeypatch.setattr(_eqdb, "log_to", lambda *args, **kwargs: logged.append(args))
    assert env.plugin._api_item_save({"serial": 1}) is False
    assert len(logged) == 1


def test_item_save_logs_a_wrong_detail_shape(env: Env, monkeypatch: pytest.MonkeyPatch) -> None:
    """A wrong detail shape is logged, the API returns False and nothing is saved."""
    from aardwolf.eqdb.plugin import _eqdb

    logged: list[tuple[Any, ...]] = []
    monkeypatch.setattr(_eqdb, "log_to", lambda *args, **kwargs: logged.append(args))
    assert env.plugin._api_item_save({"serial": 7, "statmod": "bad"}) is False
    assert len(logged) == 1
    assert env.plugin._api_item_get(7) is None


@pytest.mark.parametrize("error", [ValueError("bad"), sqlite3.OperationalError("locked")])
def test_database_failure_loads_without_a_store(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, error: Exception
) -> None:
    """If the database cannot be opened the plugin loads and says so."""
    built = _build(monkeypatch, tmp_path, error)
    plugin = built.plugin
    assert plugin.store is None
    assert plugin._api_item_get(1) is None
    assert plugin._api_item_save({"serial": 1}) is False
    built.fake.args = {"id": "1"}
    result = plugin._command_getitem()
    assert result.message == ["The eq database is not available"]
    plugin._timer_backup_start()


def test_backup_start_timer_backs_up_and_adds_the_interval(env: Env) -> None:
    """The start timer backs up, then adds the interval timer from the setting."""
    env.plugin._timer_backup_start()
    archives = list((env.fake.directory / "archive").glob("eqdb_*.sqlite.zip"))
    assert len(archives) == 1
    name, func, seconds, kwargs = env.fake.timers[-1]
    assert (name, seconds, kwargs) == (f"{PLUGIN_ID}_backup", 14400, {})
    assert func == env.plugin._timer_backup
    for archive in archives:
        archive.unlink()
    env.plugin._timer_backup()
    assert len(list((env.fake.directory / "archive").glob("eqdb_*.sqlite.zip"))) == 1


def test_backup_interval_that_is_not_usable_adds_no_timer(env: Env) -> None:
    """An interval of zero backs up once and adds no repeating timer."""
    env.fake.setting_values["backupinterval"] = 0
    before = len(env.fake.timers)
    env.plugin._timer_backup_start()
    assert len(env.fake.timers) == before
    for archive in (env.fake.directory / "archive").glob("eqdb_*.sqlite.zip"):
        archive.unlink()


def test_setting_change_reschedules(env: Env) -> None:
    """A backup setting change removes both timers and adds the start timer again."""
    env.plugin._timer_backup_start()
    env.fake.timers_removed.clear()
    env.fake.setting_values["backupstart"] = "1200"
    env.plugin._eventcb_backup_setting_modified()
    assert env.fake.timers_removed == [f"{PLUGIN_ID}_backup_start", f"{PLUGIN_ID}_backup"]
    assert env.fake.timers[-1][0] == f"{PLUGIN_ID}_backup_start"
    assert env.fake.timers[-1][3] == {"time": "1200", "onetime": True}
    for archive in (env.fake.directory / "archive").glob("eqdb_*.sqlite.zip"):
        archive.unlink()


def test_schedule_removes_no_timer_that_does_not_exist(env: Env) -> None:
    """Scheduling with no backup timers yet removes nothing."""
    env.fake.timers.clear()
    env.fake.timers_removed.clear()
    env.plugin._eventcb_backup_setting_modified()
    assert env.fake.timers_removed == []
    assert [timer[0] for timer in env.fake.timers] == [f"{PLUGIN_ID}_backup_start"]


def _run(env: Env, **args: object) -> list[str]:
    """Run getitem and return its lines, checking it succeeded."""
    from bastproxy.plugins.core.commands import CommandResult

    env.fake.args = dict(args)
    result = env.plugin._command_getitem()
    assert isinstance(result, CommandResult)
    assert result.success is True
    assert isinstance(result.message, list)
    return result.message


def test_command_getitem(env: Env) -> None:
    """No id prompts, an unknown id says so, a saved item is shown."""
    assert _run(env, id="") == ["Give the serial or identifier of an item"]
    assert _run(env, id="1") == ["There is no item with that serial or identifier"]
    env.plugin._api_item_save(sample_item())
    lines = _run(env, id="1001")
    assert lines[0] == "Item 1001"
    assert "name: A Test Sword" in lines
    assert "flags: ['glow', 'hum']" in lines
    assert "statmod: {'Strength': 3}" in lines
    body = [line.split(":")[0] for line in lines[1:]]
    assert body == sorted(body)


def test_getitem_argument_is_declared(env: Env) -> None:
    """The id is an optional argument."""
    data = env.plugin._command_getitem.command_data
    assert [item["args"] for item in data.arguments] == [("id",)]
    assert data.arguments[0]["kwargs"]["nargs"] == "?"
