"""Tests for the Aardwolf aarch plugin, with a stubbed API serving a real eq cache."""

import ast
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

import aardwolf
from aardwolf.aarch.libs import API_EQ_FIND_BY_NAME, count_items
from aardwolf.eq.libs import INVENTORY, VAULT, EqState, parse_item_line

if TYPE_CHECKING:
    from aardwolf.aarch.plugin import _aarch

PLUGIN_ID = "plugins.aardwolf.aarch"


def strip(text: str) -> str:
    """A stand-in for the colour code stripper."""
    return text


def line(serial: int, name: str) -> str:
    """An invdata item line."""
    return f"{serial},,{name},1,0,0,-1,-1"


def parsed(serial: int, name: str) -> dict[str, Any]:
    """An item line parsed as eq does."""
    item = parse_item_line(line(serial, name), None, strip)
    assert item is not None
    return item


class FakeApi:
    """A stand-in for the bastproxy API serving eq's find by name from a real EqState."""

    def __init__(self) -> None:
        self.state = EqState()
        self.eq_loaded = True
        self.args: dict[str, Any] = {}
        self.override: list[Any] | None = None

    def find(self, name: str) -> list[Any]:
        """The fake item.find.by.name."""
        if self.override is not None:
            return self.override
        return self.state.find_by_name(name)

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "libs.api:api.exists": lambda api_name: (
                self.eq_loaded and api_name == API_EQ_FIND_BY_NAME
            ),
            API_EQ_FIND_BY_NAME: self.find,
            "plugins.core.commands:command.current.args.get": lambda: self.args,
        }
        return table[name]


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: "_aarch.AarchPlugin", fake: FakeApi) -> None:
        self.plugin = plugin
        self.fake = fake

    def need(self, *words: str) -> list[str]:
        """Run the need command with the words as its filter."""
        self.fake.args = {"filter": list(words)}
        result = self.plugin._command_need()
        assert result.success
        return list(result.message)


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build an AarchPlugin with a fake API."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    # importing bastproxy needs BASTPROXY_HOME, so the plugin module is imported here
    from aardwolf.aarch.plugin import _aarch

    fake = FakeApi()
    plugin = _aarch.AarchPlugin.__new__(_aarch.AarchPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    yield Env(plugin, fake)


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.aarch" in {p["plugin_id"] for p in result.plugins}


def test_plugin_imports_no_other_plugin() -> None:
    """A plugin reaches another through its API: only aardwolf._libs and its own package."""
    root = Path(aardwolf.__file__).resolve().parent / "aarch"
    own = ("aardwolf._libs", "aardwolf.aarch")
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


def test_empty_cache_lists_all_fifty(env: Env) -> None:
    lines = env.need()
    assert lines[0] == "You have 0 Aarchaeology items (0 different) and 0 Pamphlets"
    assert lines[1] == "You need 50 pieces:"
    assert len(lines) == 52


def test_eq_cache_end_to_end(env: Env) -> None:
    state = env.fake.state
    state.commit(
        INVENTORY,
        [
            parsed(1, "(Aarchaeology) An Ancient Skull"),
            parsed(2, "(Aarchaeology) An Ancient Skull"),
            parsed(3, "(Aarchaeology) Collectable Pamphlet #12"),
            parsed(4, "a plain sword"),
            parsed(5, "(Aarchaeology) A Mystery"),
        ],
    )
    state.commit(VAULT, [parsed(6, "(Aarchaeology) Fox Tooth")])
    lines = env.need()
    assert lines[0] == "You have 3 Aarchaeology items (2 different) and 1 Pamphlets"
    assert lines[1] == "You need 47 pieces:"
    assert "2  - An Ancient Skull" not in lines
    assert "12 - A Golden Cross" not in lines
    assert "47 - Fox Tooth" not in lines
    assert lines[-1] == "Not a known piece: A Mystery"


def test_filter_in_any_case(env: Env) -> None:
    env.fake.state.commit(INVENTORY, [parsed(1, "(Aarchaeology) Fox Tooth")])
    assert env.need("TOOTH")[1:] == [
        "You need 49 pieces, 2 match 'TOOTH':",
        "10 - An Old Coyote's Tooth",
        "19 - A Dragon's Tooth",
    ]


def test_multi_word_filter(env: Env) -> None:
    assert env.need("ancient", "skull")[1:] == [
        "You need 50 pieces, 1 match 'ancient skull':",
        "2  - An Ancient Skull",
    ]


def test_no_match(env: Env) -> None:
    assert env.need("zzz")[1] == "You need 50 pieces, none match 'zzz'"


def test_no_filter_key(env: Env) -> None:
    env.fake.args = {}
    assert env.plugin._command_need().message[1] == "You need 50 pieces:"


def test_eq_not_loaded(env: Env) -> None:
    env.fake.eq_loaded = False
    assert env.need() == ["The eq plugin is not loaded, so no items are known"]


def test_non_dict_entry_is_skipped(env: Env) -> None:
    env.fake.override = ["junk", None, {"name": "(Aarchaeology) Fox Tooth"}, {"no": "name"}]
    lines = env.need()
    assert lines[0] == "You have 1 Aarchaeology items (1 different) and 0 Pamphlets"
    assert count_items([None]).items == 0
