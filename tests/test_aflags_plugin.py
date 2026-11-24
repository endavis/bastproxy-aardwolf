"""Tests for the Aardwolf aflags plugin, with a stubbed API that drives its all-lines callback."""

import ast
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from mudcmds_support import CoreHide

import aardwolf
from aardwolf.aflags.libs import (
    ALL_LINES_ID,
    EVENT_AFFECTED_UPDATE,
    EVENT_AFFOFF,
    EVENT_AFFON,
    EVENT_DIFF,
    EVENT_UPTODATE,
    HEADER_REGEX,
    HIDE_MAX_LINES,
    TYPE_AFLAGS,
)

if TYPE_CHECKING:
    from aardwolf.aflags.plugin import _aflags

PLUGIN_ID = "plugins.aardwolf.aflags"
PROMPT = "<100/100hp 50/50mn 90/90mv> "
HEADER = "Affect Flags: Sanctuary, Haste"
MORE = "              Fly"


class FakeApi:
    """A stand-in for the bastproxy API that records the calls and drives the callback."""

    def __init__(self) -> None:
        self.registered: dict[str, Callable[..., Any]] = {}
        self.types: dict[str, dict[str, Any]] = {}
        self.events_added: list[str] = []
        self.started: list[str] = []
        self.finished: list[str] = []
        self.queued: list[tuple[str, str]] = []
        self.raised: list[tuple[str, dict[str, Any]]] = []
        self.all_lines: list[Callable[..., Any]] = []
        self.unregistered = 0
        self.args: dict[str, Any] = {}
        self.record: dict[str, Any] = {}
        self.core = CoreHide(lambda: self.record)
        self.shown: list[str] = []
        self.hidden: list[str] = []

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.events:event.add": lambda event, *a, **k: self.events_added.append(event),
            "plugins.core.events:event.register": self.registered.__setitem__,
            "plugins.core.events:event.raise": lambda n, event_args=None: self.raised.append(
                (n, event_args or {})
            ),
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.mudcmds:type.add": self._type_add,
            "plugins.core.mudcmds:command.queue": lambda t, a="": self.queued.append((t, a)),
            "plugins.core.mudcmds:command.start": self.started.append,
            "plugins.core.mudcmds:command.finish": self._command_finish,
            "plugins.core.triggers:trigger.register": self._register,
            "plugins.core.triggers:trigger.unregister": self._unregister,
            "plugins.core.commands:command.current.args.get": lambda: self.args,
        }
        return table[name]

    def _type_add(self, cmdtype: str, cmd: str, regex: str, **kwargs: object) -> None:
        self.types[cmdtype] = {"cmd": cmd, "regex": regex, **kwargs}
        self.core.add_type(cmdtype, cmd, regex, **kwargs)

    def _command_finish(self, cmdtype: str) -> None:
        self.finished.append(cmdtype)
        self.core.finished(cmdtype)

    def _register(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        assert trigger_id == ALL_LINES_ID
        self.all_lines.append(func)
        return True

    def _unregister(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        assert trigger_id == ALL_LINES_ID
        self.all_lines.remove(func)
        self.unregistered += 1
        return True

    def feed(self, lines: list[str], prompt: bool = False) -> None:
        """Run each line through the hide window and the all-lines callbacks."""
        for index, text in enumerate(lines):
            line = SimpleNamespace(
                noansi=text,
                colorcoded=text,
                is_prompt=prompt and index == len(lines) - 1,
                send=True,
                internal=False,
            )
            self.record = {"matches": {}, "line": line}
            self.core.line()
            for func in list(self.all_lines):
                func()
            (self.shown if line.send else self.hidden).append(text)


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: "_aflags.AflagsPlugin", fake: FakeApi) -> None:
        self.plugin = plugin
        self.fake = fake

    def sent(self) -> None:
        """mudcmds sends a queued aflags: run its beforef, then arm its hide window."""
        spec = self.fake.types[TYPE_AFLAGS]
        spec["beforef"]()
        self.fake.core.sent(TYPE_AFLAGS, spec["cmd"])

    def read(self, flags: str, tail: list[str] | None = None) -> None:
        """Send aflags and feed an answer ending at a blank line, then the prompt."""
        self.sent()
        self.fake.feed([f"Affect Flags: {flags}", *(tail or []), ""])
        self.fake.feed([PROMPT], prompt=True)

    def deliver(self, callback: Callable[[], None], payload: dict[str, Any]) -> None:
        """Deliver an event to its callback."""
        self.fake.record = payload
        callback()


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build an AflagsPlugin with a fake API and load it."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    # importing bastproxy needs BASTPROXY_HOME, so the plugin module is imported here
    from aardwolf.aflags.plugin import _aflags

    fake = FakeApi()
    plugin = _aflags.AflagsPlugin.__new__(_aflags.AflagsPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    plugin._phook_initialize()
    yield Env(plugin, fake)


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.aflags" in {p["plugin_id"] for p in result.plugins}


def test_plugin_imports_no_other_plugin() -> None:
    """A plugin reaches another through its API: only aardwolf._libs and its own package."""
    root = Path(aardwolf.__file__).resolve().parent / "aflags"
    own = ("aardwolf._libs", "aardwolf.aflags")
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


def test_after_load(env: Env) -> None:
    fake = env.fake
    assert fake.events_added == [EVENT_DIFF]
    spec = fake.types[TYPE_AFLAGS]
    assert (spec["cmd"], spec["regex"]) == ("aflags", "^aflags$")
    assert spec["hide_output"] is True
    assert spec["hide_start"] == HEADER_REGEX
    assert spec["hide_max"] == HIDE_MAX_LINES + 2
    assert "hide_end" not in spec
    assert f"cmd_{TYPE_AFLAGS}_timeout" in fake.registered
    assert fake.all_lines == []


def test_character_active_queues_a_read(env: Env) -> None:
    env.plugin._phook_character_active()
    assert env.fake.queued == [(TYPE_AFLAGS, "")]


@pytest.mark.parametrize("name", ["_eventcb_affected_update", "_eventcb_uptodate"])
def test_update_events_queue_a_read(env: Env, name: str) -> None:
    env.deliver(getattr(env.plugin, name), {})
    assert env.fake.queued == [(TYPE_AFLAGS, "")]


@pytest.mark.parametrize("name", ["_eventcb_affon", "_eventcb_affoff"])
def test_affect_events_queue_a_read(env: Env, name: str) -> None:
    env.deliver(getattr(env.plugin, name), {"sn": 12})
    assert env.fake.queued == [(TYPE_AFLAGS, "")]


def test_recovery_events_are_not_listened_to() -> None:
    root = Path(aardwolf.__file__).resolve().parent / "aflags"
    text = "".join(p.read_text(encoding="utf-8") for p in root.rglob("*.py"))
    assert "recon" not in text
    assert "recoff" not in text
    assert {EVENT_AFFON, EVENT_AFFOFF, EVENT_AFFECTED_UPDATE, EVENT_UPTODATE}


def test_a_read_sets_the_flags_and_stops_listening(env: Env) -> None:
    env.read("Sanctuary, Haste", [MORE])
    assert env.plugin._api_flag_check("fly")
    assert env.plugin._flags == {"sanctuary", "haste", "fly"}
    assert env.fake.started == [TYPE_AFLAGS]
    assert env.fake.finished == [TYPE_AFLAGS]
    assert env.fake.all_lines == []


def test_the_header_to_the_prompt_is_hidden(env: Env) -> None:
    env.fake.feed([PROMPT], prompt=True)
    env.fake.shown.clear()
    env.sent()
    env.fake.feed([HEADER, MORE, ""])
    env.fake.feed([PROMPT], prompt=True)
    assert env.fake.hidden == [HEADER, MORE, "", PROMPT]
    assert env.fake.shown == []


def test_a_prompt_before_the_header_is_ignored(env: Env) -> None:
    env.sent()
    env.fake.feed([PROMPT], prompt=True)
    assert env.fake.finished == []
    env.fake.feed([HEADER, ""])
    assert env.fake.finished == [TYPE_AFLAGS]


def test_a_typed_aflags_is_shown_and_ignored(env: Env) -> None:
    env.fake.feed([HEADER, MORE, ""])
    env.fake.feed([PROMPT], prompt=True)
    assert env.fake.shown == [HEADER, MORE, "", PROMPT]
    assert env.fake.hidden == []
    assert env.plugin._flags == set()
    assert env.fake.finished == []


def test_a_removed_flag_disappears_and_the_event_carries_it(env: Env) -> None:
    env.read("Sanctuary, Haste")
    env.fake.raised.clear()
    env.read("Haste")
    assert env.plugin._flags == {"haste"}
    assert not env.plugin._api_flag_check("sanctuary")
    assert env.fake.raised == [(EVENT_DIFF, {"added": [], "removed": ["sanctuary"], "sn": None})]


def test_the_event_carries_the_sn_of_one_change(env: Env) -> None:
    env.read("Haste")
    env.fake.raised.clear()
    env.deliver(env.plugin._eventcb_affon, {"sn": 12})
    env.read("Haste, Sanctuary")
    assert env.fake.raised == [(EVENT_DIFF, {"added": ["sanctuary"], "removed": [], "sn": 12})]
    assert env.plugin._learner.table == {12: ["sanctuary"]}


def test_no_event_when_nothing_changed(env: Env) -> None:
    env.read("Haste")
    env.fake.raised.clear()
    env.read("Haste")
    assert env.fake.raised == []


def test_an_affect_during_a_read_queues_a_second_read(env: Env) -> None:
    env.sent()
    env.fake.feed([HEADER])
    env.deliver(env.plugin._eventcb_affoff, {"sn": 3})
    assert env.fake.queued == []
    env.fake.feed([""])
    assert env.fake.queued == [(TYPE_AFLAGS, "")]


def test_the_timeout_keeps_the_flags(env: Env) -> None:
    env.read("Haste")
    env.sent()
    env.fake.feed([HEADER.replace("Sanctuary, Haste", "Fly")])
    env.fake.registered[f"cmd_{TYPE_AFLAGS}_timeout"]()
    assert env.plugin._flags == {"haste"}
    assert env.fake.all_lines == []
    env.deliver(env.plugin._eventcb_affon, {"sn": 1})
    assert env.fake.queued == [(TYPE_AFLAGS, "")]


def test_disconnect_clears_the_flags_and_drops_a_read(env: Env) -> None:
    env.read("Haste")
    env.sent()
    env.fake.feed([HEADER])
    env.plugin._eventcb_disconnect()
    assert env.plugin._flags == set()
    assert env.fake.all_lines == []
    env.fake.feed([""])
    assert env.fake.finished == [TYPE_AFLAGS]
    assert env.plugin._flags == set()


def test_flag_check_ignores_case(env: Env) -> None:
    env.read("Detect Magic")
    assert env.plugin._api_flag_check("DETECT magic")
    assert not env.plugin._api_flag_check("")
    assert not env.plugin._api_flag_check("fly")


def test_commands(env: Env) -> None:
    assert env.plugin._command_list().message == ["There are no affects active"]
    env.read("Sanctuary, Haste")
    result = env.plugin._command_list()
    assert result.message == ["The following 2 affects are active", "  haste", "  sanctuary"]
    env.fake.args = {"flag": "Haste"}
    assert env.plugin._command_check().message == ["Affect Haste is active"]
    env.fake.args = {"flag": "fly"}
    assert env.plugin._command_check().message == ["Affect fly is inactive"]
    env.fake.args = {"flag": ""}
    assert env.plugin._command_check().message == ["Please specify a flag"]
    assert env.plugin._command_refresh().message == ["Refreshing Affect Flags"]
    assert env.fake.queued[-1] == (TYPE_AFLAGS, "")
