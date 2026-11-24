"""Tests for the Aardwolf daily plugin, with a stubbed API that drives its triggers."""

import ast
import logging
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from event_keys import assert_raised_described

import aardwolf
from aardwolf.daily.libs import (
    BLESSING_WAIT,
    EVENT_AVAILABLE,
    EVENTS,
    TIMER_NAME,
    TRIGGERS,
)

if TYPE_CHECKING:
    from bastproxy.libs.records import NetworkData

    from aardwolf.daily.plugin._daily import DailyPlugin

PLUGIN_ID = "plugins.aardwolf.daily"
WAIT = "You can receive a new daily blessing in 1 hour, 2 minutes and 3 seconds."
WAIT_SHORT = "You can receive a new daily blessing in 5 seconds."
WAIT_ZERO = "You can receive a new daily blessing in 0 seconds."
READY = "You are ready to receive a new daily blessing."
TOOK = "You bow your head to Ayla and receive your daily blessing."


class FakeApi:
    """A stand-in for the bastproxy API that records the calls and drives the triggers."""

    def __init__(self) -> None:
        self.events_added: dict[str, dict[str, Any]] = {}
        self.raised: list[tuple[str, dict[str, Any] | None]] = []
        self.triggers: dict[str, str] = {}
        self.trigger_cbs: dict[str, list[Callable[..., Any]]] = {}
        self.add_ok = True
        self.record: dict[str, Any] = {}
        self.active = False
        self.state: object = 3
        self.timers: dict[str, tuple[Callable[..., Any], float, dict[str, object]]] = {}
        self.removed: list[str] = []
        self.table: dict[str, Callable[..., Any]] = {
            "plugins.core.events:event.add": self._event_add,
            "plugins.core.events:event.raise": self._event_raise,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
            "plugins.core.timers:timer.add": self._timer_add,
            "plugins.core.timers:timer.exists": lambda name: name in self.timers,
            "plugins.core.timers:timer.remove": self._timer_remove,
            "libs.api:character.is.active": lambda: self.active,
            "libs.net.protocols:gmcp.value.get": lambda path: self.state,
        }

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name; an unknown name is a KeyError."""
        return self.table[name]

    def _event_add(self, name: str, created_by: str, **kwargs: object) -> None:
        self.events_added[name] = kwargs

    def _event_raise(self, name: str, event_args: dict[str, Any] | None = None) -> None:
        self.raised.append((name, event_args))

    def _trigger_add(self, name: str, regex: str, **kwargs: object) -> SimpleNamespace:
        self.triggers[name] = regex
        self.trigger_cbs.setdefault(name, [])
        return SimpleNamespace(success=self.add_ok, trigger=SimpleNamespace(trigger_id=name))

    def _trigger_register(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        self.trigger_cbs[trigger_id].append(func)
        return True

    def _timer_add(
        self, name: str, func: Callable[..., Any], seconds: float, **kwargs: object
    ) -> None:
        self.timers[name] = (func, seconds, kwargs)

    def _timer_remove(self, name: str) -> None:
        self.removed.append(name)
        del self.timers[name]

    def feed(self, *lines: str) -> None:
        """Run each line through the triggers the way the core matcher does."""
        for line in lines:
            for name, regex in list(self.triggers.items()):
                match = re.match(regex, line)
                if not match:
                    continue
                self.record = {"matches": match.groupdict()}
                for func in list(self.trigger_cbs[name]):
                    func()


class Env:
    """The plugin under test with its fake API and the lines sent to the mud."""

    def __init__(self, plugin: "DailyPlugin", fake: FakeApi, mud: list[str]) -> None:
        self.plugin = plugin
        self.fake = fake
        self.mud = mud

    def next_text(self) -> str:
        """Return the output of the next command."""
        result = self.plugin._command_next()
        assert result.success
        return str(result.message[0])


def build(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fake: FakeApi, load: bool = True) -> Env:
    """Build a plugin with a fake API and a fake send, and load it."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from aardwolf.daily.plugin import _daily

    mud: list[str] = []

    class FakeSend:
        def __init__(self, message: "NetworkData") -> None:
            self.message = message

        def __call__(self) -> None:
            mud.extend(str(item.line) for item in self.message)

    monkeypatch.setattr(_daily, "SendDataDirectlyToMud", FakeSend)
    plugin = _daily.DailyPlugin.__new__(_daily.DailyPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    if load:
        plugin._phook_initialize()
    return Env(plugin, fake, mud)


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """A loaded plugin with an inactive character."""
    fake = FakeApi()
    yield build(monkeypatch, tmp_path, fake)
    assert_raised_described(fake.raised, EVENTS)


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.daily" in {p["plugin_id"] for p in result.plugins}


def test_plugin_imports_no_other_plugin() -> None:
    """A plugin reaches another through its API: only aardwolf._libs and its own package."""
    root = Path(aardwolf.__file__).resolve().parent / "daily"
    own = ("aardwolf._libs", "aardwolf.daily")
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


def test_metadata() -> None:
    """The plugin is optional and depends on the core plugins it uses and connect."""
    from aardwolf import daily

    assert daily.PLUGIN_REQUIRED is False
    assert set(daily.PLUGIN_DEPENDENCIES) == {
        "plugins.core.events",
        "plugins.core.triggers",
        "plugins.core.timers",
        "plugins.core.commands",
        "plugins.aardwolf.connect",
    }


def test_after_load_adds_event_and_triggers(env: Env) -> None:
    """The event and the three triggers are added, with a callback each."""
    fake = env.fake
    assert set(fake.events_added) == set(EVENTS)
    assert all(kw["description"] for kw in fake.events_added.values())
    assert set(fake.triggers) == {spec.name for spec in TRIGGERS}
    assert all(len(cbs) == 1 for cbs in fake.trigger_cbs.values())
    assert env.mud == []


def test_trigger_add_failure_logs_and_continues(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A trigger that cannot be added is logged and skipped."""
    fake = FakeApi()
    fake.add_ok = False
    with caplog.at_level(logging.ERROR):
        build(monkeypatch, tmp_path, fake)
    assert all(not cbs for cbs in fake.trigger_cbs.values())
    for spec in TRIGGERS:
        assert f"could not add the {spec.name} trigger" in caplog.text


def test_wait_line_arms_a_one_time_timer(env: Env) -> None:
    """A wait line sets the next time and arms a one-time timer for the wait."""
    env.fake.feed(WAIT)
    func, seconds, kwargs = env.fake.timers[TIMER_NAME]
    assert seconds == 3723
    assert kwargs == {"onetime": True}
    assert func == env.plugin._timer_available
    assert env.next_text().startswith("Your next daily is at: ")
    assert env.fake.raised == []


def test_timer_fire_raises_once_and_clears(env: Env) -> None:
    """The timer raises the event, the next time is cleared and next says ready."""
    env.fake.feed(WAIT_SHORT)
    env.fake.timers[TIMER_NAME][0]()
    assert env.fake.raised == [(EVENT_AVAILABLE, None)]
    assert env.next_text() == "Your daily blessing is ready"
    assert TIMER_NAME not in env.fake.timers


def test_zero_second_wait_raises_without_a_timer(env: Env) -> None:
    """A wait the timer core would refuse raises the event at once."""
    env.fake.feed(WAIT_ZERO)
    assert env.fake.raised == [(EVENT_AVAILABLE, None)]
    assert env.fake.timers == {}


def test_bad_wait_does_nothing(env: Env) -> None:
    """A wait that cannot be read changes nothing."""
    env.fake.record = {"matches": {"wait": "soon"}}
    env.plugin._trigger_wait()
    env.fake.record = {}
    env.plugin._trigger_wait()
    assert env.fake.timers == {}
    assert env.fake.raised == []
    assert env.next_text() == "Please type daily to update plugin"


def test_ready_line_raises_and_removes_a_timer(env: Env) -> None:
    """The ready line raises the event and removes a timer that exists."""
    env.fake.feed(WAIT)
    env.fake.feed(READY)
    assert env.fake.raised == [(EVENT_AVAILABLE, None)]
    assert env.fake.removed == [TIMER_NAME]
    assert env.fake.timers == {}


def test_ready_line_without_a_timer_does_not_remove(env: Env) -> None:
    """With no timer there is no remove call, and the event is raised on every ready line."""
    env.fake.feed(READY, READY)
    assert env.fake.raised == [(EVENT_AVAILABLE, None)] * 2
    assert env.fake.removed == []


def test_took_line_arms_23_hours(env: Env) -> None:
    """The took line arms the blessing wait and replaces an earlier timer."""
    env.fake.feed(READY)
    env.fake.feed(TOOK)
    assert env.fake.timers[TIMER_NAME][1] == BLESSING_WAIT
    assert env.next_text().startswith("Your next daily is at: ")


def test_second_wait_replaces_the_timer(env: Env) -> None:
    """A new wait line removes the old timer and arms a new one."""
    env.fake.feed(WAIT, WAIT_SHORT)
    assert env.fake.removed == [TIMER_NAME]
    assert env.fake.timers[TIMER_NAME][1] == 5


def test_next_before_anything_is_known(env: Env) -> None:
    """Before any line the command asks for the daily."""
    assert env.next_text() == "Please type daily to update plugin"


@pytest.mark.parametrize(
    ("record", "state", "sent"),
    [
        ({"is_character_active": True}, 3, ["daily"]),
        ({"is_character_active": True}, 8, []),
        ({"is_character_active": True}, None, []),
        ({"is_character_active": False}, 3, []),
        ({}, 3, []),
    ],
)
def test_character_active_sends_daily(
    env: Env, record: dict[str, Any], state: object, sent: list[str]
) -> None:
    """daily is sent only for an active character in state 3."""
    env.fake.state = state
    env.fake.record = record
    env.plugin._eventcb_character_active()
    assert env.mud == sent


def test_character_active_sends_nothing_when_known(env: Env) -> None:
    """With a next time or an available daily nothing is sent."""
    env.fake.record = {"is_character_active": True}
    env.fake.feed(WAIT)
    env.fake.record = {"is_character_active": True}
    env.plugin._eventcb_character_active()
    env.fake.feed(READY)
    env.fake.record = {"is_character_active": True}
    env.plugin._eventcb_character_active()
    assert env.mud == []


def test_load_with_active_character_sends(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A plugin loaded while the character is active sends daily."""
    fake = FakeApi()
    fake.active = True
    assert build(monkeypatch, tmp_path, fake).mud == ["daily"]


def test_load_with_inactive_character_sends_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A plugin loaded before the character is active sends nothing."""
    fake = FakeApi()
    assert build(monkeypatch, tmp_path, fake).mud == []
