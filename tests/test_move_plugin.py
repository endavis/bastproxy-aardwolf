"""Tests for the Aardwolf move plugin, with a stubbed API."""

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from event_keys import assert_raised_described

import aardwolf
from aardwolf.move.libs import EVENT_MOVE_ROOM, EVENTS

if TYPE_CHECKING:
    from aardwolf.move.plugin._move import MovePlugin

PLUGIN_ID = "plugins.aardwolf.move"
A: dict[str, Any] = {"num": 1, "exits": {"n": 2}}
B: dict[str, Any] = {"num": 2, "exits": {"s": 1}}
C: dict[str, Any] = {"num": 3, "exits": {}}


class FakeApi:
    """A stand-in for the bastproxy API."""

    def __init__(self) -> None:
        self.gmcp: dict[str, Any] = {}
        self.events_added: list[tuple[str, str]] = []
        self.raised: list[tuple[str, dict[str, Any]]] = []
        self.record: dict[str, Any] = {}

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.events:event.add": self._event_add,
            "plugins.core.events:event.raise": self._event_raise,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "libs.net.protocols:gmcp.value.get": self.gmcp.get,
        }
        return table[name]

    def _event_add(self, name: str, created_by: str, **kwargs: object) -> None:
        self.events_added.append((name, created_by))

    def _event_raise(self, name: str, event_args: dict[str, Any] | None = None) -> None:
        self.raised.append((name, {} if event_args is None else event_args))


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: "MovePlugin", fake: FakeApi) -> None:
        self.plugin = plugin
        self.fake = fake

    def send(self, data: object) -> None:
        """The MUD sends a Room.Info message."""
        self.fake.record = {"package": "Room.Info", "data": data}
        self.plugin._eventcb_room_info()


def build(fake: FakeApi) -> "MovePlugin":
    """Build and load a plugin."""
    from aardwolf.move.plugin import _move

    plugin = _move.MovePlugin.__new__(_move.MovePlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    plugin._phook_initialize()
    return plugin


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build a MovePlugin with a fake API and load it."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    fake = FakeApi()
    yield Env(build(fake), fake)


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.move" in {p["plugin_id"] for p in result.plugins}


def test_dependencies() -> None:
    """The plugin depends on events and connect."""
    from aardwolf import move

    assert "plugins.aardwolf.connect" in move.PLUGIN_DEPENDENCIES
    assert "plugins.core.events" in move.PLUGIN_DEPENDENCIES


def test_after_load_adds_event(env: Env) -> None:
    """One event is added by the plugin."""
    assert env.fake.events_added == [(EVENT_MOVE_ROOM, PLUGIN_ID)]


def test_first_and_same_room_raise_nothing(env: Env) -> None:
    """The first room and the same room again raise nothing."""
    env.send(A)
    env.send(dict(A))
    assert env.fake.raised == []


def test_move_raises(env: Env) -> None:
    """A move raises with from, to and direction."""
    env.send(A)
    env.send(B)
    assert env.fake.raised == [(EVENT_MOVE_ROOM, {"from": A, "to": B, "direction": "n"})]


def test_unknown_direction(env: Env) -> None:
    """A move through no listed exit has direction unknown."""
    env.send(B)
    env.send(C)
    assert env.fake.raised[0][1]["direction"] == "unknown"


def test_chain(env: Env) -> None:
    """The second move comes from the middle room."""
    env.send(A)
    env.send(B)
    env.send(C)
    assert len(env.fake.raised) == 2
    assert env.fake.raised[1][1]["from"] == B
    assert env.fake.raised[1][1]["to"] == C


@pytest.mark.parametrize("bad", [{"name": "x"}, "text", None, [1]])
def test_bad_message_ignored(env: Env, bad: object) -> None:
    """A message with no num is ignored and keeps the last room."""
    env.send(A)
    env.send(bad)
    assert env.fake.raised == []
    env.send(B)
    assert env.fake.raised[0][1]["from"] == A


def test_missing_record_data(env: Env) -> None:
    """An empty record raises nothing."""
    env.fake.record = {}
    env.plugin._eventcb_room_info()
    assert env.fake.raised == []


def test_disconnect_clears_last_room(env: Env) -> None:
    """After a disconnect the next room raises nothing."""
    env.send(A)
    env.plugin._eventcb_disconnect()
    env.send(B)
    assert env.fake.raised == []


def test_seed_from_gmcp_cache() -> None:
    """A room in the GMCP cache at load is the last room."""
    fake = FakeApi()
    fake.gmcp["room.info"] = A
    plugin = build(fake)
    Env(plugin, fake).send(B)
    assert fake.raised[0][1]["from"] == A


def test_no_seed_with_empty_cache(env: Env) -> None:
    """With an empty cache the first room raises nothing."""
    env.send(B)
    assert env.fake.raised == []


def test_payload_mutation_does_not_leak(env: Env) -> None:
    """Changing a raised payload does not change the next event's from."""
    env.send(A)
    env.send(B)
    env.fake.raised[0][1]["to"]["num"] = 99
    env.send(C)
    assert env.fake.raised[1][1]["from"] == B


def test_raised_payloads_are_described(env: Env) -> None:
    """Every raised key is described by the event."""
    env.send(A)
    env.send(B)
    assert_raised_described(env.fake.raised, EVENTS)
