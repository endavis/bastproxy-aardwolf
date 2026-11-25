"""Tests for the Aardwolf iceage plugin, with a stubbed API that drives its triggers."""

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
from aardwolf.iceage.libs import EVENTS as SUFFIX_EVENTS
from aardwolf.iceage.libs import TRIGGERS

if TYPE_CHECKING:
    from aardwolf.iceage.plugin._iceage import IceAgePlugin

PLUGIN_ID = "plugins.aardwolf.iceage"
EVENT_ICEAGE = f"ev_{PLUGIN_ID}_iceage"
EVENT_REBOOT = f"ev_{PLUGIN_ID}_reboot"
EVENTS = {f"ev_{PLUGIN_ID}_{suffix}": info for suffix, info in SUFFIX_EVENTS.items()}
ICEAGE = "INFO: An Ice Age Approaches - 5 minutes - See 'help iceage'."
REBOOT = "INFO: Aardwolf will Reboot in 3 minutes."
REBOOT_REASON = "INFO: Aardwolf will reboot for a code update in 10 minutes."


class FakeApi:
    """A stand-in for the bastproxy API that records the calls and drives the triggers."""

    def __init__(self) -> None:
        self.events_added: dict[str, dict[str, Any]] = {}
        self.raised: list[tuple[str, dict[str, Any] | None]] = []
        self.triggers: dict[str, str] = {}
        self.kwargs: dict[str, dict[str, Any]] = {}
        self.trigger_cbs: dict[str, list[Callable[..., Any]]] = {}
        self.add_ok = True
        self.record: dict[str, Any] = {}
        self.table: dict[str, Callable[..., Any]] = {
            "plugins.core.events:event.add": self._event_add,
            "plugins.core.events:event.raise": self._event_raise,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
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
        self.kwargs[name] = dict(kwargs)
        self.trigger_cbs.setdefault(name, [])
        return SimpleNamespace(success=self.add_ok, trigger=SimpleNamespace(trigger_id=name))

    def _trigger_register(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        self.trigger_cbs[trigger_id].append(func)
        return True

    def feed(self, *lines: str) -> None:
        """Run each line through the triggers the way the core matcher does."""
        for line in lines:
            for name, regex in list(self.triggers.items()):
                match = re.match(regex, line)
                if not match:
                    continue
                groups = match.groupdict()
                for arg, argtype in (self.kwargs[name].get("argtypes") or {}).items():
                    groups[arg] = argtype(groups[arg])
                self.record = {"matches": groups}
                for func in list(self.trigger_cbs[name]):
                    func()


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: "IceAgePlugin", fake: FakeApi) -> None:
        self.plugin = plugin
        self.fake = fake


def build(fake: FakeApi) -> "IceAgePlugin":
    """Build and load a plugin."""
    from aardwolf.iceage.plugin import _iceage

    plugin = _iceage.IceAgePlugin.__new__(_iceage.IceAgePlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_initialize()
    return plugin


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build an IceAgePlugin with a fake API and load it."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    fake = FakeApi()
    yield Env(build(fake), fake)
    assert_raised_described(fake.raised, EVENTS)


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.iceage" in {p["plugin_id"] for p in result.plugins}


def test_plugin_imports_no_other_plugin() -> None:
    """A plugin reaches another through its API: only aardwolf._libs and its own package."""
    root = Path(aardwolf.__file__).resolve().parent / "iceage"
    own = ("aardwolf._libs", "aardwolf.iceage")
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
    """The plugin is optional and needs the events and triggers core plugins only."""
    from aardwolf import iceage

    assert iceage.PLUGIN_REQUIRED is False
    assert set(iceage.PLUGIN_DEPENDENCIES) == {"plugins.core.events", "plugins.core.triggers"}


def test_after_load_adds_events_and_triggers(env: Env) -> None:
    """Both events and triggers are added, with argtypes and a callback each."""
    fake = env.fake
    assert set(fake.events_added) == set(EVENTS)
    assert all(kw["description"] for kw in fake.events_added.values())
    assert set(fake.triggers) == {spec.name for spec in TRIGGERS}
    assert all(kw["argtypes"] == {"minutes": int} for kw in fake.kwargs.values())
    assert all(len(cbs) == 1 for cbs in fake.trigger_cbs.values())


def test_trigger_add_failure_logs_and_registers_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A trigger that cannot be added is logged and skipped."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    fake = FakeApi()
    fake.add_ok = False
    with caplog.at_level(logging.ERROR):
        build(fake)
    assert all(not cbs for cbs in fake.trigger_cbs.values())
    assert "could not add the iceage trigger" in caplog.text
    assert "could not add the reboot trigger" in caplog.text


def test_iceage_line_raises_one_event(env: Env) -> None:
    """The Ice Age line raises its event once with the minutes."""
    env.fake.feed(ICEAGE)
    assert env.fake.raised == [(EVENT_ICEAGE, {"minutes": 5})]


def test_reboot_lines_raise_events(env: Env) -> None:
    """Each reboot line raises the reboot event with its own minutes."""
    env.fake.feed(REBOOT, REBOOT_REASON)
    assert env.fake.raised == [
        (EVENT_REBOOT, {"minutes": 3}),
        (EVENT_REBOOT, {"minutes": 10}),
    ]


def test_unrelated_line_raises_nothing(env: Env) -> None:
    """A line that is not a countdown raises nothing."""
    env.fake.feed("You kill a rat.", "Aardwolf will reboot soon.")
    assert env.fake.raised == []


@pytest.mark.parametrize("record", [{}, {"matches": {}}, {"matches": {"minutes": "5"}}])
def test_bad_record_raises_nothing(env: Env, record: dict[str, Any]) -> None:
    """A missing or non-int minutes raises nothing."""
    env.fake.record = record
    env.plugin._trigger_iceage()
    env.plugin._trigger_reboot()
    assert env.fake.raised == []


def test_debug_lines_carry_the_minutes(env: Env, monkeypatch: pytest.MonkeyPatch) -> None:
    """The old send.msg echoes are debug log lines with the minutes."""
    from aardwolf.iceage.plugin import _iceage

    logged: list[tuple[int, str]] = []
    monkeypatch.setattr(
        _iceage, "log_to", lambda _target, level, msg, *args: logged.append((level, msg % args))
    )
    env.fake.feed(ICEAGE, REBOOT)
    assert logged == [
        (logging.DEBUG, "Ice Age imminent: 5 minutes"),
        (logging.DEBUG, "Reboot imminent: 3 minutes"),
    ]
