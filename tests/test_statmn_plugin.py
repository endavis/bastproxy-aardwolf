"""Tests for the Aardwolf statmn plugin, with a stubbed API over a real synthetic database."""

import ast
import sqlite3
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from statdb_support import make_db

import aardwolf
from aardwolf.statmn.libs import EMPTYLINE_ID, NO_DB, SELECT_API

if TYPE_CHECKING:
    from bastproxy.plugins.core.sqldb.libs._sqlite import Sqldb

    from aardwolf.statmn.plugin import _statmn

PLUGIN_ID = "plugins.aardwolf.statmn"
TIMER = f"{PLUGIN_ID}_report"


def _verify(value: str, vtype: str) -> int:
    """A stand-in for value.verify with the timelength type: ``<n>m`` or ``<n>s``."""
    assert vtype == "timelength"
    if value[:-1].isdigit() and value[-1] in "ms":
        return int(value[:-1]) * (60 if value[-1] == "m" else 1)
    raise ValueError(f"{value} is not a time length")


class FakeApi:
    """A stand-in for the bastproxy API."""

    def __init__(self, db: "Sqldb") -> None:
        self.db = db
        self.settings: dict[str, Any] = {}
        self.setting_defs: dict[str, tuple[Any, ...]] = {}
        self.triggers: dict[str, list[Callable[[], None]]] = {}
        self.register_calls = 0
        self.timers: dict[str, tuple[Callable[[], None], float]] = {}
        self.removed: list[str] = []
        self.record: dict[str, Any] = {}
        self.args: dict[str, Any] = {}
        self.connected = True
        self.perlevel: object = 2000
        self.select_exists = True
        self.select_error: Exception | None = None
        self.selects: list[tuple[str, tuple[Any, ...]]] = []

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.settings:setting.add": self._setting_add,
            "plugins.core.settings:setting.get": lambda pid, key: self.settings[key],
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.triggers:trigger.register": self._trigger_register,
            "plugins.core.triggers:trigger.unregister": self._trigger_unregister,
            "plugins.core.timers:timer.exists": lambda n: n in self.timers,
            "plugins.core.timers:timer.add": self._timer_add,
            "plugins.core.timers:timer.remove": self._timer_remove,
            "plugins.core.commands:command.current.args.get": lambda: self.args,
            "plugins.core.proxy:mud.is.connected": lambda: self.connected,
            "plugins.core.utils:timelength.format": self._format_time,
            "plugins.core.utils:string.center.colored": self._center,
            "plugins.core.utils:value.verify": _verify,
            "libs.net.protocols:gmcp.value.get": lambda key: self.perlevel,
            "libs.api:api.exists": lambda api: api == SELECT_API and self.select_exists,
            SELECT_API: self._select,
        }
        return table[name]

    def _setting_add(
        self, pid: str, name: str, default: object, stype: object, *rest: object
    ) -> None:
        self.setting_defs[name] = (default, stype)
        self.settings[name] = (
            _verify(str(default), "timelength") if stype == "timelength" else default
        )

    def _trigger_register(self, trigger_id: str, func: Callable[[], None]) -> bool:
        self.register_calls += 1
        self.triggers.setdefault(trigger_id, []).append(func)
        return True

    def _trigger_unregister(self, trigger_id: str, func: Callable[[], None]) -> bool:
        self.triggers[trigger_id].remove(func)
        return True

    def _timer_add(self, name: str, func: Callable[[], None], seconds: float) -> None:
        assert name not in self.timers
        self.timers[name] = (func, seconds)

    def _timer_remove(self, name: str) -> None:
        assert name in self.timers
        self.removed.append(name)
        del self.timers[name]

    @staticmethod
    def _format_time(seconds: float, nosec: bool = False) -> str:
        whole = int(seconds)
        return f"{whole // 60:02d}m" if nosec else f"{whole // 60:02d}m:{whole % 60:02d}s"

    @staticmethod
    def _center(text: str, filler: str, length: int, filler_color: str) -> str:
        return f"{filler_color}-- {text} --"

    def _select(self, sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
        self.selects.append((sql, params))
        if self.select_error is not None:
            raise self.select_error
        return self.db.select(sql, params)


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: "_statmn.StatmnPlugin", fake: FakeApi) -> None:
        self.plugin = plugin
        self.fake = fake
        self.sent: list[list[str]] = []

    @property
    def waiting(self) -> list[Callable[[], None]]:
        """The callbacks on the empty line trigger."""
        return self.fake.triggers.get(EMPTYLINE_ID, [])

    def event(self, callback: Callable[[], None], record: dict[str, Any]) -> None:
        """Raise an event: set its data and run a callback."""
        self.fake.record = record
        callback()

    def empty_line(self) -> None:
        """An empty line arrives: run the callbacks on the trigger."""
        for func in list(self.waiting):
            func()

    def shown(self) -> list[str]:
        """Every line sent to the clients, in order."""
        return [line for batch in self.sent for line in batch]


def make_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> "Iterator[Env]":
    """Build the plugin with a fake API over a new statdb database, and load it."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("BASTPROXY_HOME", str(home))
    # importing bastproxy needs BASTPROXY_HOME, so the plugin module is imported here
    from aardwolf.statmn.plugin import _statmn

    db = make_db(tmp_path / "db")
    fake = FakeApi(db)
    plugin = _statmn.StatmnPlugin.__new__(_statmn.StatmnPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    plugin._phook_initialize()
    env = Env(plugin, fake)
    plugin._client = env.sent.append  # type: ignore[method-assign,assignment]
    yield env
    db.close()


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """The plugin loaded over an empty database."""
    yield from make_env(monkeypatch, tmp_path)


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.statmn" in {p["plugin_id"] for p in result.plugins}


def test_plugin_imports_no_other_plugin() -> None:
    """A plugin reaches another through its API: only aardwolf.libs and its own package."""
    root = Path(aardwolf.__file__).resolve().parent / "statmn"
    own = ("aardwolf.libs", "aardwolf.statmn")
    for path in root.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                if node.module.startswith("aardwolf."):
                    assert node.module.startswith(own), path
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("aardwolf.") or alias.name.startswith(own), (
                        path
                    )


def test_after_load_adds_the_settings_and_starts_the_timer(env: Env) -> None:
    fake = env.fake
    assert fake.setting_defs["statcolor"] == ("@W", "color")
    assert fake.setting_defs["infocolor"] == ("@x33", "color")
    assert fake.setting_defs["show"] == ("5m", "timelength")
    assert fake.setting_defs["reportminutes"] == ("60m", "timelength")
    assert fake.setting_defs["exppermin"] == (20, int)
    assert fake.timers[TIMER][1] == 300


def test_changing_show_replaces_the_timer(env: Env) -> None:
    env.fake.settings["show"] = 600
    env.plugin._eventcb_show_modified()
    assert env.fake.timers[TIMER][1] == 600
    assert env.fake.removed == [TIMER]
    assert env.sent == []


def test_show_of_zero_turns_the_report_off(env: Env) -> None:
    env.fake.settings["show"] = 0
    env.plugin._eventcb_show_modified()
    assert TIMER not in env.fake.timers
    assert env.sent == [["Turning off the statmon report"]]


def test_the_timer_sends_the_report_while_connected(env: Env) -> None:
    now = int(time.time())
    env.fake.db.modify(
        "INSERT INTO quests(finishtime, totqp, gold, tp) VALUES (?, 12, 2899, 0)", (now - 60,)
    )
    env.fake.timers[TIMER][0]()
    text = "\n".join(env.shown())
    assert "Stats for @x33@W60@x33m" in text
    assert "2899" in text
    assert len(env.sent) == 1


def test_the_timer_does_nothing_while_disconnected(env: Env) -> None:
    env.fake.connected = False
    env.fake.timers[TIMER][0]()
    assert env.sent == []
    assert env.fake.selects == []


def test_the_timer_does_nothing_without_the_database(env: Env) -> None:
    env.fake.select_exists = False
    env.fake.timers[TIMER][0]()
    assert env.sent == []


def test_rep_uses_the_reportminutes_setting(env: Env) -> None:
    before = time.time()
    result = env.plugin._command_rep()
    assert result.success
    assert any("Stats for" in line for line in result.message)
    start = env.fake.selects[0][1][0]
    assert before - 3600 - 5 < start < time.time() - 3600 + 5


def test_rep_with_a_length(env: Env) -> None:
    env.fake.args = {"minutes": "30m"}
    before = time.time()
    result = env.plugin._command_rep()
    assert result.success
    start = env.fake.selects[0][1][0]
    assert before - 1800 - 5 < start < time.time() - 1800 + 5


def test_rep_with_a_bad_length(env: Env) -> None:
    env.fake.args = {"minutes": "soon"}
    result = env.plugin._command_rep()
    assert not result.success
    assert "soon" in result.message[0]
    assert env.fake.selects == []


def test_rep_with_a_zero_length(env: Env) -> None:
    env.fake.args = {"minutes": "0m"}
    assert not env.plugin._command_rep().success


def test_rep_without_the_api(env: Env) -> None:
    env.fake.select_exists = False
    result = env.plugin._command_rep()
    assert result.success
    assert result.message == [NO_DB]


def test_a_failed_select_is_logged_and_rep_says_no_database(
    env: Env, caplog: pytest.LogCaptureFixture
) -> None:
    env.fake.select_error = sqlite3.OperationalError("boom")
    with caplog.at_level("ERROR"):
        result = env.plugin._command_rep()
    assert result.message == [NO_DB]
    assert any("could not read the stats" in r.getMessage() for r in caplog.records)


def test_a_failed_select_leaves_a_quest_message_without_the_average(env: Env) -> None:
    env.fake.select_error = sqlite3.OperationalError("boom")
    env.event(env.plugin._eventcb_quest_comp, QUEST)
    env.empty_line()
    assert "Avg" not in env.shown()[0]
    assert "Quest finished" in env.shown()[0]


QUEST = {"qp": 10, "totqp": 10, "starttime": 100, "finishtime": 280}


def test_a_quest_message_waits_for_the_empty_line(env: Env) -> None:
    env.event(env.plugin._eventcb_quest_comp, QUEST)
    assert env.sent == []
    assert len(env.waiting) == 1
    env.empty_line()
    assert len(env.sent) == 1
    assert "Quest finished for" in env.shown()[0]
    assert env.waiting == []


def test_the_quest_average_counts_the_quest_that_statdb_saved_and_not_failed(env: Env) -> None:
    quest = "INSERT INTO quests(totqp, failed) VALUES (?, ?)"
    for qp, failed in ((10, 0), (20, 0), (90, 1)):
        env.fake.db.modify(quest, (qp, failed))
    env.event(env.plugin._eventcb_quest_comp, QUEST)
    env.empty_line()
    assert "Avg: @W15.00" in env.shown()[0]
    assert "over @W2@x33 quests" in env.shown()[0]


def test_two_messages_share_one_registration_and_one_flush(env: Env) -> None:
    env.event(
        env.plugin._eventcb_cp_comp, {"qp": 20, "bonusqp": 5, "starttime": 0, "finishtime": 60}
    )
    env.event(env.plugin._eventcb_gq, {"qp": 5, "qpmobs": 2, "starttime": 0, "finishtime": 60})
    assert env.fake.register_calls == 1
    env.empty_line()
    assert len(env.sent) == 1
    first, second = env.shown()
    assert "CP finished" in first
    assert "GQ finished" in second
    env.event(env.plugin._eventcb_quest_comp, QUEST)
    assert env.fake.register_calls == 2


def test_a_level_message_uses_the_window_from_the_previous_level(env: Env) -> None:
    db = env.fake.db
    for start in (100, 400, 1000):
        db.modify("INSERT INTO levels(starttime) VALUES (?)", (start,))
    mob = "INSERT INTO mobkills(time, xp, totalxp) VALUES (?, ?, ?)"
    db.modify(mob, (450, 10, 10))
    db.modify(mob, (500, 20, 30))
    db.modify(mob, (1100, 10, 10))
    record = {"type": "level", "starttime": 1000, "finishtime": 1002, "hp": 1, "trains": 3}
    env.event(env.plugin._eventcb_level_gain, record)
    env.empty_line()
    msg = env.shown()[0]
    assert "Gained a level" in msg
    assert "@W2 @x33mobs killed" in msg
    assert "@W20.00@x33xp/mob" in msg
    # 2000 xp per level over a window of 600 seconds
    assert "@W200@x33xp/min" in msg


def test_a_level_message_without_perlevel_has_no_xp_per_min(env: Env) -> None:
    db = env.fake.db
    for start in (400, 1000):
        db.modify("INSERT INTO levels(starttime) VALUES (?)", (start,))
    db.modify("INSERT INTO mobkills(time, xp, totalxp) VALUES (500, 20, 30)")
    env.fake.perlevel = None
    env.event(env.plugin._eventcb_level_gain, {"type": "pup", "starttime": 1000})
    env.empty_line()
    msg = env.shown()[0]
    assert "mobs killed" in msg
    assert "xp/min" not in msg


def test_a_level_message_for_the_first_level_has_no_mob_part(env: Env) -> None:
    env.fake.db.modify("INSERT INTO mobkills(time, xp, totalxp) VALUES (500, 20, 30)")
    env.event(env.plugin._eventcb_level_gain, {"type": "level", "starttime": 1000})
    env.empty_line()
    assert "mobs killed" not in env.shown()[0]


def test_a_level_message_without_a_start_time(env: Env) -> None:
    env.event(env.plugin._eventcb_level_gain, {"type": "level"})
    env.empty_line()
    assert "Gained a level" in env.shown()[0]


def test_a_disconnect_flushes_the_held_messages(env: Env) -> None:
    env.event(env.plugin._eventcb_quest_comp, QUEST)
    env.plugin._eventcb_disconnect()
    assert len(env.sent) == 1
    assert env.waiting == []


def test_a_disconnect_with_nothing_held_sends_nothing(env: Env) -> None:
    env.plugin._eventcb_disconnect()
    assert env.sent == []


def test_uninitialize_stops_waiting(env: Env) -> None:
    env.event(env.plugin._eventcb_quest_comp, QUEST)
    env.plugin._phook_uninitialize()
    assert env.waiting == []


def test_the_event_callbacks_are_registered_at_priority_60() -> None:
    from aardwolf.statmn.plugin import _statmn

    plugin = _statmn.StatmnPlugin
    for name in ("_eventcb_quest_comp", "_eventcb_cp_comp", "_eventcb_gq", "_eventcb_level_gain"):
        registrations = getattr(plugin, name).event_registration
        assert registrations
        assert all(r["priority"] == 60 for r in registrations)
    names = {r["event_name"] for r in plugin._eventcb_gq.event_registration}
    assert names == {
        "ev_plugins.aardwolf.gq_won",
        "ev_plugins.aardwolf.gq_completed",
        "ev_plugins.aardwolf.gq_done",
    }
