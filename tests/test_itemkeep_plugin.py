"""Tests for the Aardwolf itemkeep plugin, with a stubbed API that drives its triggers."""

import ast
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from mudcmds_support import CoreHide

import aardwolf
from aardwolf.itemkeep.libs import (
    EVENT_EQ_INVENTORY_ADDED,
    EVENT_EQ_REMOVED,
    EVENT_EQ_TAKEN,
    SETTINGS,
    TYPE_KEEP,
)
from aardwolf.itemkeep.plugin import _itemkeep

PLUGIN_ID = "plugins.aardwolf.itemkeep"
GROUP = f"{PLUGIN_ID}.reply"
PROMPT = "<100/100hp 50/50mn 90/90mv> "
REPLY = "Keep status added to a test blade."
# what follows a kept reply on Aardwolf, before the prompt
REPLY_TAIL = [
    "**NOTE: This is NOT the same as a 'keepflag' which is a trivia point",
    "        option that makes an item not count towards your item limit.",
    "{invitem}1234,K,a test blade,1,5,0,-1,-1",
]


def item(serial: int = 1234, itype: int = 5, flags: str = "") -> dict[str, Any]:
    """An item as eq raises it."""
    return {"serial": serial, "itype": itype, "shortflags": flags}


class FakeApi:
    """A stand-in for the bastproxy API that records the calls and drives the triggers."""

    def __init__(self) -> None:
        self.settings_added: list[tuple[Any, ...]] = []
        self.values: dict[str, bool] = {}
        self.registered: dict[str, Callable[..., Any]] = {}
        self.types: dict[str, dict[str, Any]] = {}
        self.started: list[str] = []
        self.finished: list[str] = []
        self.queued: list[tuple[str, str]] = []
        self.triggers: dict[str, dict[str, Any]] = {}
        self.callbacks: dict[str, Callable[..., Any]] = {}
        self.group_toggles: list[tuple[str, bool]] = []
        self.record: dict[str, Any] = {}
        self.core = CoreHide(lambda: self.record)
        self.shown: list[str] = []
        self.hidden: list[str] = []

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.settings:setting.add": lambda *a: self.settings_added.append(a),
            "plugins.core.settings:setting.get": lambda pid, key: self.values.get(key, False),
            "plugins.core.events:event.register": self.registered.__setitem__,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.mudcmds:type.add": self._type_add,
            "plugins.core.mudcmds:command.queue": lambda t, a="": self.queued.append((t, a)),
            "plugins.core.mudcmds:command.start": self.started.append,
            "plugins.core.mudcmds:command.finish": self._command_finish,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
            "plugins.core.triggers:group.toggle.enable": self._group_toggle,
        }
        return table[name]

    def _type_add(self, cmdtype: str, cmd: str, regex: str, **kwargs: object) -> None:
        self.types[cmdtype] = {"cmd": cmd, "regex": regex, **kwargs}
        self.core.add_type(cmdtype, cmd, regex, **kwargs)

    def _command_finish(self, cmdtype: str) -> None:
        self.finished.append(cmdtype)
        self.core.finished(cmdtype)

    def _trigger_add(self, name: str, regex: str, **kwargs: object) -> SimpleNamespace:
        self.triggers[name] = {
            "regex": regex,
            "enabled": kwargs.get("enabled", True),
            "group": kwargs.get("group"),
        }
        return SimpleNamespace(success=True, trigger=SimpleNamespace(trigger_id=name))

    def _trigger_register(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        self.callbacks[trigger_id] = func
        return True

    def _group_toggle(self, group: str, flag: bool) -> bool:
        assert any(t["group"] == group for t in self.triggers.values()), f"unknown group {group}"
        self.group_toggles.append((group, flag))
        for trigger in self.triggers.values():
            if trigger["group"] == group:
                trigger["enabled"] = flag
        return True

    def feed(self, lines: list[str], prompt: bool = False) -> None:
        """Run each line through the hide window and the enabled triggers."""
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
            for name, trigger in list(self.triggers.items()):
                if not trigger["enabled"]:
                    continue
                match = re.match(trigger["regex"], text)
                if match and name in self.callbacks:
                    self.record = {"matches": match.groupdict(), "line": line}
                    self.callbacks[name]()
            (self.shown if line.send else self.hidden).append(text)

    def enabled(self) -> set[str]:
        """The names of the enabled triggers."""
        return {name for name, trigger in self.triggers.items() if trigger["enabled"]}


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: _itemkeep.ItemKeepPlugin, fake: FakeApi) -> None:
        self.plugin = plugin
        self.fake = fake

    def deliver(self, event: str, payload: dict[str, Any]) -> None:
        """Deliver an eq event to its callback."""
        callbacks = {
            EVENT_EQ_INVENTORY_ADDED: self.plugin._eventcb_inventory_added,
            EVENT_EQ_TAKEN: self.plugin._eventcb_taken,
            EVENT_EQ_REMOVED: self.plugin._eventcb_removed,
        }
        self.fake.record = payload
        callbacks[event]()

    def queued_keep(self, serial: int) -> None:
        """mudcmds sends a queued keep: run its beforef, then arm its hide window."""
        spec = self.fake.types[TYPE_KEEP]
        spec["beforef"]()
        self.fake.core.sent(TYPE_KEEP, f"{spec['cmd']} {serial}")


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build an ItemKeepPlugin with a fake API and load it."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    fake = FakeApi()
    plugin = _itemkeep.ItemKeepPlugin.__new__(_itemkeep.ItemKeepPlugin)
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
    assert "aardwolf.itemkeep" in {p["plugin_id"] for p in result.plugins}


def test_plugin_imports_no_other_plugin() -> None:
    """A plugin reaches another through its API: only aardwolf.libs and its own package."""
    root = Path(aardwolf.__file__).resolve().parent / "itemkeep"
    own = ("aardwolf.libs", "aardwolf.itemkeep")
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
    assert len(fake.settings_added) == 25
    assert {a[1] for a in fake.settings_added} == set(SETTINGS)
    assert all(a[0] == PLUGIN_ID and a[2] is False and a[3] is bool for a in fake.settings_added)
    keep = fake.types[TYPE_KEEP]
    assert (keep["cmd"], keep["regex"]) == ("keep", r"^keep \d+$")
    assert keep["hide_output"] is True
    assert re.match(keep["hide_start"], REPLY)
    assert "hide_end" not in keep
    assert fake.triggers["itemkeep_reply"]["group"] == GROUP
    assert fake.enabled() == set()
    assert f"cmd_{TYPE_KEEP}_timeout" in fake.registered


@pytest.mark.parametrize("event", [EVENT_EQ_INVENTORY_ADDED, EVENT_EQ_TAKEN, EVENT_EQ_REMOVED])
def test_each_event_queues_a_keep(env: Env, event: str) -> None:
    env.fake.values["weapon"] = True
    env.deliver(event, {"item": item(1234)})
    assert env.fake.queued == [(TYPE_KEEP, "1234")]


def test_raw_material_is_set_by_its_underscore_name(env: Env) -> None:
    env.fake.values["raw_material"] = True
    env.deliver(EVENT_EQ_INVENTORY_ADDED, {"item": item(7, itype=24)})
    assert env.fake.queued == [(TYPE_KEEP, "7")]


@pytest.mark.parametrize(
    "payload",
    [
        {"item": None},
        {},
        {"item": "not a dict"},
        {"item": item(itype=7)},
        {"item": item(flags="K")},
        {"item": item(itype=0)},
        {"item": item(itype=99)},
        {"item": item(serial=0)},
    ],
)
def test_nothing_is_queued(env: Env, payload: dict[str, Any]) -> None:
    env.fake.values["weapon"] = True
    env.deliver(EVENT_EQ_TAKEN, payload)
    assert env.fake.queued == []


def test_the_same_serial_queues_once_until_disconnect(env: Env) -> None:
    env.fake.values["weapon"] = True
    env.deliver(EVENT_EQ_INVENTORY_ADDED, {"item": item(1234)})
    env.deliver(EVENT_EQ_TAKEN, {"item": item(1234)})
    assert env.fake.queued == [(TYPE_KEEP, "1234")]
    env.plugin._eventcb_disconnect()
    env.deliver(EVENT_EQ_TAKEN, {"item": item(1234)})
    assert env.fake.queued == [(TYPE_KEEP, "1234")] * 2


def test_beforef_starts_the_command_and_turns_the_group_on(env: Env) -> None:
    env.fake.types[TYPE_KEEP]["beforef"]()
    assert env.fake.started == [TYPE_KEEP]
    assert env.fake.enabled() == {"itemkeep_reply"}


def test_the_reply_finishes_the_command_and_turns_the_group_off(env: Env) -> None:
    env.queued_keep(1234)
    env.fake.feed([REPLY])
    assert env.fake.finished == [TYPE_KEEP]
    assert env.fake.group_toggles == [(GROUP, True), (GROUP, False)]
    assert env.fake.enabled() == set()


def test_the_timeout_turns_the_group_off(env: Env) -> None:
    env.queued_keep(1234)
    env.fake.registered[f"cmd_{TYPE_KEEP}_timeout"]()
    assert env.fake.enabled() == set()
    assert env.fake.finished == []


def test_disconnect_turns_the_group_off(env: Env) -> None:
    env.queued_keep(1234)
    env.plugin._eventcb_disconnect()
    assert env.fake.enabled() == set()


def test_the_reply_and_the_prompt_are_hidden(env: Env) -> None:
    env.queued_keep(1234)
    env.fake.feed([REPLY])
    env.fake.feed([PROMPT], prompt=True)
    assert env.fake.hidden == [REPLY, PROMPT]
    assert env.fake.shown == []


def test_the_note_lines_after_the_reply_are_hidden(env: Env) -> None:
    env.queued_keep(1234)
    env.fake.feed([REPLY, *REPLY_TAIL])
    env.fake.feed([PROMPT], prompt=True)
    assert env.fake.hidden == [REPLY, *REPLY_TAIL, PROMPT]
    assert env.fake.shown == []


def test_a_typed_keep_is_shown(env: Env) -> None:
    env.fake.feed([REPLY])
    env.fake.feed([PROMPT], prompt=True)
    assert env.fake.shown == [REPLY, PROMPT]
    assert env.fake.hidden == []
    assert env.fake.finished == []
