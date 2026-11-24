"""Tests for the Aardwolf idle plugin, with a stubbed API that drives its trigger."""

import ast
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

import aardwolf
from aardwolf.idle.libs import GLAZE_REGEX

if TYPE_CHECKING:
    from bastproxy.libs.records import NetworkData

    from aardwolf.idle.plugin._idle import IdlePlugin

PLUGIN_ID = "plugins.aardwolf.idle"
GLAZE_LINE = "Your eyes glaze over."


class FakeApi:
    """A stand-in for the bastproxy API that records the trigger and drives it."""

    def __init__(self, add_ok: bool = True) -> None:
        self.add_ok = add_ok
        self.triggers: dict[str, dict[str, Any]] = {}
        self.callbacks: dict[str, Callable[..., Any]] = {}

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
        }
        return table[name]

    def _trigger_add(self, name: str, regex: str, **kwargs: object) -> SimpleNamespace:
        if not self.add_ok:
            return SimpleNamespace(success=False)
        self.triggers[name] = {
            "regex": regex,
            "enabled": kwargs.get("enabled", True),
            "group": kwargs.get("group"),
        }
        return SimpleNamespace(success=True, trigger=SimpleNamespace(trigger_id=name))

    def _trigger_register(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        self.callbacks[trigger_id] = func
        return True

    def feed(self, text: str) -> None:
        """Run a line through the enabled triggers."""
        for name, trigger in self.triggers.items():
            if trigger["enabled"] and re.match(trigger["regex"], text) and name in self.callbacks:
                self.callbacks[name]()


class Env:
    """The plugin under test with its fake API and what it sent."""

    def __init__(
        self, plugin: "IdlePlugin", fake: FakeApi, mud: list[str], owners: list[str]
    ) -> None:
        self.plugin = plugin
        self.fake = fake
        self.mud = mud
        self.owners = owners


def build(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, add_ok: bool = True) -> Env:
    """Build an IdlePlugin with a fake API and a fake send."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from aardwolf.idle.plugin import _idle

    mud: list[str] = []
    owners: list[str] = []

    class FakeSend:
        def __init__(self, message: "NetworkData") -> None:
            self.message = message

        def __call__(self) -> None:
            mud.extend(str(item.line) for item in self.message)
            owners.append(str(self.message.owner_id))

    monkeypatch.setattr(_idle, "SendDataDirectlyToMud", FakeSend)
    fake = FakeApi(add_ok)
    plugin = _idle.IdlePlugin.__new__(_idle.IdlePlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    return Env(plugin, fake, mud, owners)


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """A loaded plugin."""
    built = build(monkeypatch, tmp_path)
    built.plugin._phook_initialize()
    yield built


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.idle" in {p["plugin_id"] for p in result.plugins}


def test_imports_no_other_plugin() -> None:
    """The plugin never imports another plugin."""
    root = Path(aardwolf.__file__).resolve().parent / "idle"
    for path in root.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names = [node.module]
            for name in names:
                assert not name.startswith("aardwolf.") or name.startswith("aardwolf.idle")
                assert not name.startswith("bastproxy.plugins.") or name in (
                    "bastproxy.plugins._baseplugin",
                )


def test_after_load(env: Env) -> None:
    """after_load adds one enabled ungrouped trigger and registers its callback."""
    assert env.fake.triggers == {"glaze": {"regex": GLAZE_REGEX, "enabled": True, "group": None}}
    assert set(env.fake.callbacks) == {"glaze"}


def test_glaze_sends_look(env: Env) -> None:
    """The glaze line sends exactly look, each time."""
    env.fake.feed(GLAZE_LINE)
    assert env.mud == ["look"]
    env.fake.feed(GLAZE_LINE)
    assert env.mud == ["look", "look"]


@pytest.mark.parametrize("line", ["Your eyes glaze overX", "You look around.", ""])
def test_other_lines_send_nothing(env: Env, line: str) -> None:
    """Non-matching lines send nothing."""
    env.fake.feed(line)
    assert env.mud == []


def test_owner_id(env: Env) -> None:
    """The sent data is owned by the plugin's send helper."""
    env.fake.feed(GLAZE_LINE)
    assert env.owners == ["plugins.aardwolf.idle:_send_to_mud"]


def test_add_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A failed trigger.add registers nothing, logs an error and sends nothing."""
    built = build(monkeypatch, tmp_path, add_ok=False)
    with caplog.at_level("ERROR"):
        built.plugin._phook_initialize()
    built.fake.feed(GLAZE_LINE)
    assert built.fake.callbacks == {}
    assert built.mud == []
    assert any("could not add" in r.getMessage() for r in caplog.records)
