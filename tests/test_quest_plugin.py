"""Tests for the Aardwolf quest plugin, with a stubbed API."""

from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from event_keys import assert_raised_described
from statdb_support import make_db

import aardwolf
from aardwolf.quest.libs import EVENTS as SUFFIX_EVENTS

if TYPE_CHECKING:
    from aardwolf.quest.plugin._quest import QuestPlugin

PLUGIN_ID = "plugins.aardwolf.quest"
EVENTS = {f"ev_{PLUGIN_ID}_{suffix}": info for suffix, info in SUFFIX_EVENTS.items()}
NOW = 1000.0
START = {"action": "start", "targ": "a rat", "area": "Sewers", "room": "Dark Hall", "timer": 30}
WHOIS = {"name": "Bast", "level": 50, "totallevels": 50, "remorts": 1, "classes": []}
COMP = {"action": "comp", "qp": 20, "totqp": 25, "tp": 5, "gold": 300}
GMCP: dict[str, Any] = {
    "char.status.level": 50,
    "char.base.remorts": 2,
    "char.base.tier": 1,
    "char.base.redos": 0,
}


class FakeApi:
    """A stand-in for the bastproxy API."""

    def __init__(self) -> None:
        self.gmcp: dict[str, Any] = dict(GMCP)
        self.events_added: list[tuple[str, str]] = []
        self.raised: list[tuple[str, dict[str, Any]]] = []
        self.record: dict[str, Any] = {}
        self.provider_ok = True
        self.providers: dict[
            str, tuple[Callable[[], Any], list[dict[str, str]] | None, str, Any]
        ] = {}
        self.provider_changes: list[tuple[str, str]] = []

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.events:event.add": self._event_add,
            "plugins.core.events:event.raise": self._event_raise,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "libs.net.protocols:gmcp.value.get": self.gmcp.get,
            "plugins.core.web:web.provider.add": self._provider_add,
            "plugins.core.web:web.provider.changed.raise": self._provider_changed,
        }
        return table[name]

    def _provider_add(
        self,
        owner: str,
        name: str,
        snapshot: Callable[[], Any],
        columns: list[dict[str, str]] | None = None,
        kind: str = "json",
        event: str | None = None,
    ) -> str | None:
        """Record a web.provider.add call; return the topic, or None when refused."""
        if not self.provider_ok:
            return None
        self.providers[name] = (snapshot, columns, kind, event)
        return f"{owner}.{name}"

    def _provider_changed(self, owner: str, name: str) -> bool:
        """Record a web.provider.changed.raise call."""
        self.provider_changes.append((owner, name))
        return True

    def _event_add(self, name: str, created_by: str, **kwargs: object) -> None:
        self.events_added.append((name, created_by))

    def _event_raise(self, name: str, event_args: dict[str, Any] | None = None) -> None:
        self.raised.append((name, {} if event_args is None else event_args))


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: "QuestPlugin", fake: FakeApi, home: Path) -> None:
        self.plugin = plugin
        self.fake = fake
        self.home = home

    def send(self, data: object) -> None:
        """The MUD sends a Comm.Quest message."""
        self.fake.record = {"package": "Comm.Quest", "data": data}
        self.plugin._eventcb_quest()


def build(home: Path, fake: FakeApi) -> "QuestPlugin":
    """Build and load a plugin on a data directory."""
    from aardwolf.quest.plugin import _quest

    plugin = _quest.QuestPlugin.__new__(_quest.QuestPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.plugin_info = SimpleNamespace(data_directory=home)  # type: ignore[assignment]
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    plugin._phook_initialize()
    return plugin


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build a QuestPlugin with a fake API and load it."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    fake = FakeApi()
    plugin = build(tmp_path, fake)
    monkeypatch.setattr(type(plugin), "_now", staticmethod(lambda: NOW))
    yield Env(plugin, fake, tmp_path)


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.quest" in {p["plugin_id"] for p in result.plugins}


def test_dependencies() -> None:
    """The plugin depends on events and connect."""
    from aardwolf import quest

    assert "plugins.aardwolf.connect" in quest.PLUGIN_DEPENDENCIES
    assert "plugins.core.events" in quest.PLUGIN_DEPENDENCIES
    assert "plugins.core.web" in quest.PLUGIN_DEPENDENCIES


def test_after_load_adds_all_events(env: Env) -> None:
    """All seven events are added by the plugin."""
    assert len(env.fake.events_added) == 7
    assert {created for _, created in env.fake.events_added} == {PLUGIN_ID}
    assert all(n.startswith("ev_plugins.aardwolf.quest_") for n, _ in env.fake.events_added)


@pytest.mark.parametrize("action", ["ready", "reset"])
def test_ready_and_reset_raise_empty(env: Env, action: str) -> None:
    """Ready and reset raise their event with no data."""
    env.send({"action": action})
    assert env.fake.raised == [(f"ev_plugins.aardwolf.quest_{action}", {})]


def test_start_resets_state(env: Env) -> None:
    """Start clears the old state and raises the new one."""
    env.plugin.quest["qp"] = 99
    env.send(START)
    name, payload = env.fake.raised[0]
    assert name == "ev_plugins.aardwolf.quest_start"
    assert "qp" not in payload
    assert "qp" not in env.plugin.quest
    assert payload["mobname"] == "a rat"
    assert payload["mobarea"] == "Sewers"
    assert payload["mobroom"] == "Dark Hall"
    assert payload["stimer"] == 30
    assert payload["starttime"] == NOW
    assert payload["finishtime"] == payload["killedtime"] == -1
    assert payload["failed"] == 0
    assert payload["level"] == (1 + 0) * 1407 + (2 - 1) * 201 + 50


def test_start_with_missing_gmcp(env: Env) -> None:
    """Start still raises when the char data is missing."""
    env.fake.gmcp.clear()
    env.send(START)
    assert env.fake.raised[0][0] == "ev_plugins.aardwolf.quest_start"
    assert isinstance(env.fake.raised[0][1]["level"], int)


def test_killed(env: Env) -> None:
    """Killed sets killedtime and keeps the start fields."""
    env.send(START)
    env.send({"action": "killed"})
    name, payload = env.fake.raised[1]
    assert name == "ev_plugins.aardwolf.quest_killed"
    assert payload["killedtime"] == NOW
    assert payload["mobname"] == "a rat"


def test_comp(env: Env) -> None:
    """Comp sets finishtime and merges the message."""
    env.send(START)
    env.send(COMP)
    name, payload = env.fake.raised[1]
    assert name == "ev_plugins.aardwolf.quest_comp"
    assert payload["finishtime"] == NOW
    assert payload["qp"] == 20
    assert payload["totqp"] == 25
    assert payload["tp"] == 5
    assert payload["gold"] == 300
    assert payload["failed"] == 0


@pytest.mark.parametrize("action", ["fail", "timeout"])
def test_fail_and_timeout(env: Env, action: str) -> None:
    """Fail and timeout raise quest_failed."""
    env.send(START)
    env.send({"action": action})
    name, payload = env.fake.raised[1]
    assert name == "ev_plugins.aardwolf.quest_failed"
    assert payload["finishtime"] == NOW
    assert payload["failed"] == 1


def test_status_leaves_state(env: Env) -> None:
    """Status raises the message and does not change the state."""
    env.send(START)
    before = dict(env.plugin.quest)
    message = {"action": "status", "id": 3, "targ": "x"}
    env.send(message)
    assert env.fake.raised[1] == ("ev_plugins.aardwolf.quest_status", message)
    assert dict(env.plugin.quest) == before


@pytest.mark.parametrize(
    "data",
    [{"action": "bogus"}, {"targ": "x"}, None, "start", ["start"], {"action": ["start"]}],
)
def test_bad_input_raises_nothing(env: Env, data: object) -> None:
    """Unknown, missing and non-dict input raises nothing."""
    env.send(data)
    assert env.fake.raised == []


def test_payloads_are_plain_copies(env: Env) -> None:
    """Payloads are dicts and changing one leaves the state alone."""
    env.send(START)
    payload = env.fake.raised[0][1]
    assert type(payload) is dict
    payload["mobname"] = "changed"
    assert env.plugin.quest["mobname"] == "a rat"


def test_state_is_persisted(env: Env) -> None:
    """The state is on disk, survives a new plugin, and the save hook syncs."""
    from bastproxy.libs.persistentdict import PersistentDict

    env.send(START)
    assert PersistentDict(PLUGIN_ID, env.home / "quest.txt", "c")["mobname"] == "a rat"
    again = build(env.home, FakeApi())
    assert again.quest["mobname"] == "a rat"
    env.plugin.quest["extra"] = 1
    env.plugin._phook_save()
    assert PersistentDict(PLUGIN_ID, env.home / "quest.txt", "c")["extra"] == 1


def test_comp_payload_is_saved_by_statdb(env: Env, tmp_path: Path) -> None:
    """The quest_comp payload feeds statdb's save_quest."""
    from aardwolf.statdb.libs import StatStore

    env.send(START)
    env.send(COMP)
    database = make_db(tmp_path / "db")
    try:
        store = StatStore(database)
        store.save_whois(WHOIS)
        store.save_quest(env.fake.raised[1][1])
        row = database.select("SELECT * FROM quests")[0]
        assert row["mobname"] == "a rat"
        assert row["level"] == 1407 + 201 + 50
        assert row["starttime"] == NOW
        assert row["finishtime"] == NOW
        assert row["qp"] == 20
        assert row["totqp"] == 25
        assert row["tp"] == 5
        stat = database.select("SELECT questscomplete FROM stats WHERE milestone = 'current'")
        assert stat[0]["questscomplete"] == 1
    finally:
        database.close()


def test_failed_payload_is_saved_by_statdb(env: Env, tmp_path: Path) -> None:
    """The quest_failed payload feeds statdb's save_quest."""
    from aardwolf.statdb.libs import StatStore

    env.send(START)
    env.send({"action": "fail"})
    database = make_db(tmp_path / "db")
    try:
        store = StatStore(database)
        store.save_whois(WHOIS)
        store.save_quest(env.fake.raised[1][1])
        row = database.select("SELECT * FROM quests")[0]
        assert row["failed"] == 1
        stat = database.select("SELECT questsfailed FROM stats WHERE milestone = 'current'")
        assert stat[0]["questsfailed"] == 1
    finally:
        database.close()


def test_raised_keys_are_all_described(env: Env) -> None:
    """Every action raises only keys its event describes in arg_descriptions (#43)."""
    env.send({"action": "ready"})
    env.send(START)
    env.send({"action": "killed"})
    env.send(COMP)
    env.send(START)
    env.send({"action": "fail"})
    env.send({"action": "status", "status": "ready"})
    env.send({"action": "reset"})
    assert len(env.fake.raised) == 8
    assert_raised_described(env.fake.raised, EVENTS)


def test_live_comp_keys_are_described(env: Env) -> None:
    """The comp message from Aardwolf also carries completed and wait (#50)."""
    env.send(START)
    env.send({**COMP, "completed": 1, "wait": 30})
    name, payload = env.fake.raised[1]
    assert name == "ev_plugins.aardwolf.quest_comp"
    assert (payload["completed"], payload["wait"]) == (1, 30)
    assert_raised_described(env.fake.raised, EVENTS)


def test_live_status_keys_are_described(env: Env) -> None:
    """The status message from Aardwolf can carry wait (#164)."""
    env.send({"action": "status", "wait": 5})
    env.send({"action": "status", "status": "ready"})
    assert [name for name, _ in env.fake.raised] == ["ev_plugins.aardwolf.quest_status"] * 2
    assert env.fake.raised[0][1]["wait"] == 5
    assert_raised_described(env.fake.raised, EVENTS)


CHANGED = [(PLUGIN_ID, "current")]


def test_web_provider_is_registered(env: Env) -> None:
    """The current quest is a json provider with no event."""
    snapshot, columns, kind, event = env.fake.providers["current"]
    assert (columns, kind, event) == (None, "json", None)
    assert snapshot()["active"] is False


def test_web_snapshot_follows_the_quest(env: Env) -> None:
    """The snapshot has the target after the start, then the kill and the completion."""
    env.send(START)
    current = env.fake.providers["current"][0]()
    assert current["active"] is True
    assert (current["target"], current["area"], current["room"]) == ("a rat", "Sewers", "Dark Hall")
    assert current["timeleft"] == 30 * 60
    env.send({"action": "killed"})
    assert env.fake.providers["current"][0]()["killed"] is True
    env.send(COMP)
    current = env.fake.providers["current"][0]()
    assert (current["active"], current["complete"]) == (False, True)


@pytest.mark.parametrize(
    "data",
    [
        START,
        {"action": "killed"},
        COMP,
        {"action": "fail"},
        {"action": "timeout"},
        {"action": "status", "status": "ready"},
        {"action": "ready"},
        {"action": "reset"},
    ],
)
def test_each_handled_action_raises_a_change(env: Env, data: dict[str, Any]) -> None:
    """Every action the plugin handles tells the web plugin once."""
    env.send(data)
    assert env.fake.provider_changes == CHANGED


def test_a_failed_quest_is_reported(env: Env) -> None:
    """A fail makes the quest not active and failed."""
    env.send(START)
    env.send({"action": "fail"})
    current = env.fake.providers["current"][0]()
    assert (current["active"], current["failed"], current["complete"]) == (False, True, False)


@pytest.mark.parametrize("data", ["text", None, {"action": "bogus"}, {"action": 5}, {}])
def test_unhandled_messages_raise_nothing(env: Env, data: object) -> None:
    """A message that is not a known action changes nothing."""
    env.send(data)
    assert env.fake.provider_changes == []


def test_a_refused_provider_raises_nothing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """When the web plugin refuses the provider no change is raised."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    fake = FakeApi()
    fake.provider_ok = False
    plugin = build(tmp_path, fake)
    fake.record = {"package": "Comm.Quest", "data": START}
    plugin._eventcb_quest()
    assert fake.providers == {}
    assert fake.provider_changes == []
