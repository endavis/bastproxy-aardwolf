"""Tests for the Aardwolf ct plugin, with a stubbed API."""

import ast
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

import aardwolf
from aardwolf.ct.libs import EMPTYLINE_ID, EVENT_MOBK_KILL, SETTINGS

if TYPE_CHECKING:
    from aardwolf.ct.plugin._ct import CtPlugin

PLUGIN_ID = "plugins.aardwolf.ct"


class FakeApi:
    """A stand-in for the bastproxy API that records the calls."""

    def __init__(self) -> None:
        self.settings: dict[str, Any] = {}
        self.setting_defs: dict[str, tuple[Any, ...]] = {}
        self.callbacks: dict[str, list[Callable[[], None]]] = {}
        self.register_calls = 0
        self.unregister_calls = 0
        self.record: dict[str, Any] = {}

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.settings:setting.add": self._setting_add,
            "plugins.core.settings:setting.get": lambda pid, key: self.settings[key],
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.triggers:trigger.register": self._register,
            "plugins.core.triggers:trigger.unregister": self._unregister,
            "plugins.core.utils:string.center.colored": self._center,
            "plugins.core.utils:timedelta.to.string": self._duration,
            "plugins.core.colors:colorcode.escape": lambda text: text.replace("@", "@@"),
        }
        return table[name]

    def _setting_add(
        self, pid: str, name: str, default: object, stype: object, help_text: str
    ) -> None:
        self.setting_defs[name] = (default, stype, help_text)
        self.settings[name] = default

    def _register(self, trigger_id: str, func: Callable[[], None]) -> bool:
        self.register_calls += 1
        self.callbacks.setdefault(trigger_id, []).append(func)
        return True

    def _unregister(self, trigger_id: str, func: Callable[[], None]) -> bool:
        self.unregister_calls += 1
        self.callbacks[trigger_id].remove(func)
        return True

    @staticmethod
    def _center(text: str, filler: str, length: int) -> str:
        return f"CENTER[{filler}{length}]{text}"

    @staticmethod
    def _duration(start: float, end: float, colorn: str = "", colors: str = "") -> str:
        return f"{colorn}{int(end - start):02d}{colors}s"


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: "CtPlugin", fake: FakeApi) -> None:
        self.plugin = plugin
        self.fake = fake
        self.sent: list[str] = []

    def kill(self, name: str = "a rat", damage: int = 10) -> None:
        """A mobk kill event arrives."""
        self.fake.record = {
            "name": name,
            "totalxp": 5,
            "starttime": 1.0,
            "finishtime": 4.0,
            "damage": {"slash": {"hits": 1, "misses": 0, "damage": damage}},
        }
        self.plugin._eventcb_kill()

    def empty_line(self) -> None:
        """An empty line arrives: every callback on the trigger runs."""
        for func in list(self.fake.callbacks.get(EMPTYLINE_ID, [])):
            func()

    def waiting(self) -> int:
        """The number of callbacks registered on the empty line trigger."""
        return len(self.fake.callbacks.get(EMPTYLINE_ID, []))


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """The plugin loaded, with its sends recorded."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    # importing bastproxy needs BASTPROXY_HOME, so the plugin module is imported here
    from aardwolf.ct.plugin import _ct

    fake = FakeApi()
    plugin = _ct.CtPlugin.__new__(_ct.CtPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    plugin._phook_initialize()
    result = Env(plugin, fake)
    plugin._client = result.sent.append  # type: ignore[method-assign,assignment]
    yield result


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.ct" in {p["plugin_id"] for p in result.plugins}


def test_plugin_imports_no_other_plugin() -> None:
    """A plugin reaches another through its API: only aardwolf._libs and its own package."""
    root = Path(aardwolf.__file__).resolve().parent / "ct"
    own = ("aardwolf._libs", "aardwolf.ct")
    for path in root.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.level == 0
                and node.module.startswith("aardwolf.")
            ):
                assert node.module.startswith(own), path


def test_plugin_depends_on_mobk() -> None:
    """The plugin asks for the plugins it uses, mobk among them."""
    import aardwolf.ct as package

    assert "plugins.aardwolf.mobk" in package.PLUGIN_DEPENDENCIES
    assert "plugins.core.utils" in package.PLUGIN_DEPENDENCIES


def test_settings_added(env: Env) -> None:
    """The two color settings are added with the color type."""
    assert set(env.fake.setting_defs) == set(SETTINGS)
    assert env.fake.setting_defs["statcolor"][:2] == ("@W", "color")
    assert env.fake.setting_defs["infocolor"][:2] == ("@x033", "color")


def test_event_is_registered() -> None:
    """The kill handler is declared for the mobk kill event."""
    path = Path(aardwolf.__file__).resolve().parent / "ct" / "plugin" / "_ct.py"
    assert "RegisterToEvent(event_name=EVENT_MOBK_KILL)" in path.read_text(encoding="utf-8")
    assert EVENT_MOBK_KILL == "ev_plugins.aardwolf.mobk_kill"


def test_kill_queues_and_registers_once(env: Env) -> None:
    """A kill sends nothing yet and registers on the empty line once, however many kills."""
    env.kill()
    env.kill("a bat")
    assert env.sent == []
    assert env.waiting() == 1
    assert env.fake.register_calls == 1


def test_empty_line_sends_and_unregisters(env: Env) -> None:
    """The next empty line sends the table and stops listening."""
    env.kill()
    env.empty_line()
    assert len(env.sent) == 1
    assert "a rat" in env.sent[0]
    assert env.waiting() == 0
    env.empty_line()
    assert len(env.sent) == 1


def test_two_kills_sent_in_order(env: Env) -> None:
    """Every queued table is sent, in the order of the kills."""
    env.kill("first")
    env.kill("second")
    env.empty_line()
    assert len(env.sent) == 2
    assert "first" in env.sent[0]
    assert "second" in env.sent[1]


def test_a_kill_after_the_show_registers_again(env: Env) -> None:
    """After the tables were shown, the next kill waits for its own empty line."""
    env.kill()
    env.empty_line()
    env.kill("again")
    assert env.waiting() == 1
    env.empty_line()
    assert len(env.sent) == 2


def test_no_kill_sends_nothing(env: Env) -> None:
    """An empty line without a kill sends nothing."""
    env.empty_line()
    assert env.sent == []


def test_settings_colors_are_used(env: Env) -> None:
    """The colors of the settings are in the table."""
    env.fake.settings["statcolor"] = "@R"
    env.fake.settings["infocolor"] = "@G"
    env.kill()
    env.empty_line()
    assert env.sent[0].startswith("@G" + "-" * 72)
    assert "@Rslash" in env.sent[0]


def test_helpers_are_used(env: Env) -> None:
    """The title goes through the center helper and the time through the duration helper."""
    env.kill()
    env.empty_line()
    assert "CENTER[-72]" in env.sent[0]
    assert "@W03@x033s" in env.sent[0]


def test_event_without_damage_is_ignored(env: Env) -> None:
    """A payload without a damage table queues nothing."""
    env.fake.record = {}
    env.plugin._eventcb_kill()
    assert env.waiting() == 0
