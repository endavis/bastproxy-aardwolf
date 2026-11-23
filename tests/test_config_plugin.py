"""Tests for the config plugin, with a stubbed API."""

import argparse
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from event_keys import assert_raised_described

from aardwolf.config.libs import (
    DEFAULT_QUESTMASTERS,
    EVENT_QUESTMASTERS_CHANGED,
    EVENTS,
)

if TYPE_CHECKING:
    from bastproxy.plugins.core.commands import CommandResult

    from aardwolf.config.plugin._config import ConfigPlugin

PLUGIN_ID = "plugins.aardwolf.config"


class FakeApi:
    """A stand-in for the bastproxy API that records what the plugin calls."""

    def __init__(self) -> None:
        self.plugin: ConfigPlugin | None = None
        self.settings_added: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        self.values: dict[str, Any] = {}
        self.events_added: dict[str, dict[str, Any]] = {}
        self.raised: list[tuple[str, dict[str, Any]]] = []
        self.record: dict[str, Any] = {}
        self.args: dict[str, Any] = {}

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name; an unknown name is a KeyError."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.settings:setting.add": self._setting_add,
            "plugins.core.settings:setting.get": lambda _plugin, key: self.values[key],
            "plugins.core.settings:setting.set": self._setting_set,
            "plugins.core.events:event.add": self._event_add,
            "plugins.core.events:event.raise": self._event_raise,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.commands:command.current.args.get": lambda: self.args,
        }
        return table[name]

    def _setting_add(self, *args: Any, **kwargs: object) -> None:  # noqa: ANN401  # mirrors setting.add, which takes Any
        self.settings_added.append((args, kwargs))
        self.values[args[1]] = list(args[2])

    def _setting_set(self, _plugin: str, key: str, value: list[str]) -> None:
        """Store the value, then notify like the core settings plugin does."""
        assert self.plugin is not None
        old = self.values[key]
        self.values[key] = value
        self.record = {"var": key, "newvalue": value, "oldvalue": old}
        self.plugin._eventcb_questmasters_modified()

    def _event_add(self, name: str, created_by: str, **kwargs: object) -> None:
        self.events_added[name] = dict(kwargs)

    def _event_raise(self, name: str, event_args: dict[str, Any] | None = None) -> None:
        self.raised.append((name, event_args or {}))


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: "ConfigPlugin", fake: FakeApi) -> None:
        self.plugin = plugin
        self.fake = fake

    def run(self, action: str = "", *words: str) -> "CommandResult":
        """Run the questmaster command with the given arguments."""
        self.fake.args = {"action": action, "name": list(words)}
        result: CommandResult = self.plugin._command_questmaster()
        return result


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build a ConfigPlugin with a fake API and load it."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from aardwolf.config.plugin import _config

    fake = FakeApi()
    plugin = _config.ConfigPlugin.__new__(_config.ConfigPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    fake.plugin = plugin
    plugin._phook_initialize()
    yield Env(plugin, fake)
    assert_raised_described(fake.raised, EVENTS)


def test_load_adds_setting_and_events(env: Env) -> None:
    """The setting is a read-only list with the defaults, and every event is added."""
    assert len(env.fake.settings_added) == 1
    args, kwargs = env.fake.settings_added[0]
    assert args[:4] == (PLUGIN_ID, "questmasters", list(DEFAULT_QUESTMASTERS), list)
    assert kwargs == {"readonly": True}
    assert list(env.fake.events_added) == list(EVENTS)
    for name, info in EVENTS.items():
        assert env.fake.events_added[name]["arg_descriptions"] == info["arg_descriptions"]


def test_api_returns_defaults_as_a_copy(env: Env) -> None:
    """The API gives the defaults, and changing the result changes nothing."""
    result = env.plugin._api_questmasters_get()
    assert result == ["Commander Barcett", "A QuestoR"]
    result.append("X")
    assert env.fake.values["questmasters"] == ["Commander Barcett", "A QuestoR"]


def test_no_action_lists_names(env: Env) -> None:
    """With no action the command lists the names."""
    result = env.run()
    assert result.success
    assert "Commander Barcett" in result.message
    assert "A QuestoR" in result.message


def test_no_action_with_empty_list(env: Env) -> None:
    """An empty list gives the no questmasters message."""
    env.fake.values["questmasters"] = []
    assert env.run().message == ["There are no questmasters"]


def test_add_multiword_name(env: Env) -> None:
    """A multi-word name is added and the change event is raised."""
    result = env.run("add", "Some", "Name")
    assert result.success
    expected = ["Commander Barcett", "A QuestoR", "Some Name"]
    assert env.fake.values["questmasters"] == expected
    assert env.fake.raised == [(EVENT_QUESTMASTERS_CHANGED, {"questmasters": expected})]


def test_add_duplicate_changes_nothing(env: Env) -> None:
    """A duplicate is reported and raises no event."""
    result = env.run("add", "Commander", "Barcett")
    assert "already" in result.message[0]
    assert env.fake.values["questmasters"] == ["Commander Barcett", "A QuestoR"]
    assert env.fake.raised == []


def test_remove_name(env: Env) -> None:
    """A removed name goes and the event carries the new list."""
    result = env.run("remove", "A", "QuestoR")
    assert result.success
    assert env.fake.values["questmasters"] == ["Commander Barcett"]
    expected = {"questmasters": ["Commander Barcett"]}
    assert env.fake.raised == [(EVENT_QUESTMASTERS_CHANGED, expected)]


@pytest.mark.parametrize("words", [("Nobody",), ("a", "questor")])
def test_remove_missing_changes_nothing(env: Env, words: tuple[str, ...]) -> None:
    """A missing name or a case miss is reported and raises no event."""
    result = env.run("remove", *words)
    assert "not a questmaster" in result.message[0]
    assert env.fake.values["questmasters"] == ["Commander Barcett", "A QuestoR"]
    assert env.fake.raised == []


@pytest.mark.parametrize("action", ["add", "remove"])
def test_action_without_name_fails(env: Env, action: str) -> None:
    """An action with no name fails and changes nothing."""
    result = env.run(action)
    assert not result.success
    assert env.fake.values["questmasters"] == ["Commander Barcett", "A QuestoR"]
    assert env.fake.raised == []


def test_init_record_raises_nothing(env: Env) -> None:
    """The load-time settings event is not passed on."""
    env.fake.record = {"var": "questmasters", "newvalue": ["A"], "oldvalue": "__init__"}
    env.plugin._eventcb_questmasters_modified()
    assert env.fake.raised == []


def test_unknown_action_fails(env: Env) -> None:
    """An action other than add or remove fails and changes nothing."""
    result = env.run("rename", "A", "QuestoR")
    assert not result.success
    assert env.fake.values["questmasters"] == ["Commander Barcett", "A QuestoR"]
    assert env.fake.raised == []


def test_command_arguments_are_declared(env: Env) -> None:
    """The action is optional, and the name takes any number of words."""
    arguments = env.plugin._command_questmaster.command_data.arguments
    assert [item["args"] for item in arguments] == [("action",), ("name",)]
    assert arguments[0]["kwargs"]["nargs"] == "?"
    assert arguments[1]["kwargs"]["nargs"] == "*"


@pytest.mark.parametrize(
    ("words", "action", "name"),
    [
        ([], "", []),
        (["add", "A", "QuestoR"], "add", ["A", "QuestoR"]),
        (["remove", "Commander", "Barcett"], "remove", ["Commander", "Barcett"]),
    ],
)
def test_declared_arguments_parse(env: Env, words: list[str], action: str, name: list[str]) -> None:
    """The declared arguments parse with argparse, including no arguments at all."""
    parser = argparse.ArgumentParser(exit_on_error=False)
    for item in env.plugin._command_questmaster.command_data.arguments:
        parser.add_argument(*item["args"], **item["kwargs"])
    parsed = parser.parse_args(words)
    assert parsed.action == action
    assert parsed.name == name
