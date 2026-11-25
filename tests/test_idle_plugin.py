"""Tests for the Aardwolf idle plugin, with a stubbed API that drives its trigger."""

import ast
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock

import pytest

import aardwolf
from aardwolf.idle.libs import GLAZE_REGEX, regex_error

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
        self.settings: dict[str, Any] = {}
        self.validators: dict[str, Callable[[Any], str | None]] = {}
        self.registered: dict[str, Callable[..., Any]] = {}

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
            "plugins.core.triggers:trigger.update": self._trigger_update,
            "plugins.core.settings:setting.add": self._setting_add,
            "plugins.core.settings:setting.get": self._setting_get,
            "plugins.core.events:event.register": self._event_register,
        }
        return table[name]

    def _setting_add(
        self,
        plugin_id: str,
        name: str,
        default: object,
        stype: type,
        help_text: str,
        **kwargs: object,
    ) -> None:
        self.settings.setdefault(name, default)
        if "validator" in kwargs:
            self.validators[name] = cast("Callable[[Any], str | None]", kwargs["validator"])

    def _setting_get(self, plugin_id: str, name: str) -> object:
        return self.settings[name]

    def set_setting(self, name: str, value: str) -> None:
        """Set a setting like core does: run the validator, raise ValueError on an error."""
        validator = self.validators.get(name)
        error = validator(value) if validator else None
        if error:
            raise ValueError(error)
        self.settings[name] = value

    def _event_register(self, event_name: str, func: Callable[..., Any]) -> bool:
        self.registered[event_name] = func
        return True

    def _trigger_update(self, name: str, changes: dict[str, Any]) -> bool:
        try:
            re.compile(changes["regex"])
        except re.error:
            return False
        self.triggers[name]["regex"] = changes["regex"]
        return True

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


def build(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    add_ok: bool = True,
    preset: dict[str, str] | None = None,
) -> Env:
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
    fake.settings.update(preset or {})
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


def test_settings_added(env: Env) -> None:
    """after_load adds both settings with their defaults and the regex validator."""
    assert env.fake.settings == {"command": "look", "regex": GLAZE_REGEX}
    assert env.fake.validators == {"regex": regex_error}


def test_regex_event_registered(env: Env) -> None:
    """after_load listens for the regex setting changing."""
    assert env.fake.registered == {
        "ev_plugins.aardwolf.idle_var_regex_modified": env.plugin._eventcb_regex_modified
    }


def test_preset_regex_used(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A persisted regex is the one the trigger is added with."""
    built = build(monkeypatch, tmp_path, preset={"regex": r"^You are idle\.$"})
    built.plugin._phook_initialize()
    assert built.fake.triggers["glaze"]["regex"] == r"^You are idle\.$"
    built.fake.feed(GLAZE_LINE)
    assert built.mud == []
    built.fake.feed("You are idle.")
    assert built.mud == ["look"]


def test_command_read_at_fire_time(env: Env) -> None:
    """Changing the command setting changes the next send, with no reload."""
    env.fake.set_setting("command", "score")
    env.fake.feed(GLAZE_LINE)
    assert env.mud == ["score"]


def test_regex_change_updates_trigger(env: Env) -> None:
    """A new regex setting retargets the trigger."""
    env.fake.set_setting("regex", r"^You feel sleepy\.$")
    env.plugin._eventcb_regex_modified()
    env.fake.feed("You feel sleepy.")
    assert env.mud == ["look"]
    env.fake.feed(GLAZE_LINE)
    assert env.mud == ["look"]


def test_invalid_regex_refused(env: Env) -> None:
    """The validator refuses a bad regex and nothing changes."""
    with pytest.raises(ValueError, match="invalid regex"):
        env.fake.set_setting("regex", "(")
    assert env.fake.settings["regex"] == GLAZE_REGEX
    assert env.fake.triggers["glaze"]["regex"] == GLAZE_REGEX
    env.fake.feed(GLAZE_LINE)
    assert env.mud == ["look"]


def test_invalid_regex_in_store_keeps_trigger(env: Env, caplog: pytest.LogCaptureFixture) -> None:
    """If a bad regex reaches the store anyway, the trigger keeps its working regex."""
    env.fake.settings["regex"] = "("
    with caplog.at_level("ERROR"):
        env.plugin._eventcb_regex_modified()
    assert env.fake.triggers["glaze"]["regex"] == GLAZE_REGEX
    assert any("could not update" in r.getMessage() for r in caplog.records)
    env.fake.feed(GLAZE_LINE)
    assert env.mud == ["look"]
