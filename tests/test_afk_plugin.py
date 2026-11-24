"""Tests for the Aardwolf afk plugin, with a stubbed API that drives its triggers."""

import ast
import re
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from mudcmds_support import CoreHide

import aardwolf
from aardwolf.afk.libs import TIMEOUT_EVENT, TITLE_SET_REGEX, TYPE_TITLE, WATCH_NAME

if TYPE_CHECKING:
    from aardwolf.afk.plugin import _afk

PLUGIN_ID = "plugins.aardwolf.afk"
GROUP = f"{PLUGIN_ID}.reply"
PROMPT = "<100/100hp 50/50mn 90/90mv> "
REPLY = "Title now set to: is AFK."


class FakeApi:
    """A stand-in for the bastproxy API that records the calls and drives the triggers."""

    def __init__(self) -> None:
        self.settings: dict[str, Any] = {}
        self.setting_defs: dict[str, tuple[Any, ...]] = {}
        self.sets: list[tuple[str, Any]] = []
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
        # uuid to (logged in, view only)
        self.clients: dict[str, tuple[bool, bool]] = {}
        self.connected = True
        self.watches: dict[str, str] = {}
        self.modules: list[list[str]] = []

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.settings:setting.add": self._setting_add,
            "plugins.core.settings:setting.get": lambda pid, key: self.settings[key],
            "plugins.core.settings:setting.set": self._setting_set,
            "plugins.core.events:event.register": self.registered.__setitem__,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.mudcmds:type.add": self._type_add,
            "plugins.core.mudcmds:command.queue": lambda t, a="": self.queued.append((t, a)),
            "plugins.core.mudcmds:command.start": self.started.append,
            "plugins.core.mudcmds:command.finish": self._command_finish,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
            "plugins.core.triggers:group.toggle.enable": self._group_toggle,
            "plugins.core.watch:watch.add": self.watches.__setitem__,
            "plugins.core.clients:client.list": lambda uuid_only=False: list(self.clients),
            "plugins.core.clients:client.is.logged.in": lambda u: self.clients[u][0],
            "plugins.core.clients:client.is.view.client": lambda u: self.clients[u][1],
            "plugins.core.proxy:mud.is.connected": lambda: self.connected,
            "libs.net.protocols:gmcp.modules.add": self.modules.append,
        }
        return table[name]

    def _setting_add(
        self, pid: str, name: str, default: object, stype: object, *rest: object, **kw: object
    ) -> None:
        self.setting_defs[name] = (default, stype, kw)
        self.settings[name] = default

    def _setting_set(self, pid: str, name: str, value: object) -> bool:
        self.sets.append((name, value))
        self.settings[name] = value
        return True

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

    def __init__(self, plugin: "_afk.AfkPlugin", fake: FakeApi, home: Path) -> None:
        self.plugin = plugin
        self.fake = fake
        self.home = home
        self.notices: list[list[str]] = []

    def add_client(self, uuid: str, logged_in: bool = True, view_only: bool = False) -> None:
        """Add a connected client."""
        self.fake.clients[uuid] = (logged_in, view_only)

    def leave(self, uuid: str) -> None:
        """A client disconnects."""
        del self.fake.clients[uuid]
        self.plugin._eventcb_client_disconnected()

    def login(self, uuid: str, view_only: bool = False) -> None:
        """A client logs in; a view client raises no logged in event."""
        self.fake.clients[uuid] = (True, view_only)
        if not view_only:
            self.plugin._eventcb_client_logged_in()

    def tell(self, data: object) -> None:
        """A GMCP comm.channel message arrives."""
        self.fake.record = {"data": data}
        self.plugin._eventcb_comm()

    def queued_title(self, title: str) -> None:
        """mudcmds sends a queued title: run its beforef, then arm its hide window."""
        spec = self.fake.types[TYPE_TITLE]
        spec["beforef"]()
        self.fake.core.sent(TYPE_TITLE, f"title {title}")

    def typed(self, title: str) -> None:
        """A client types a title."""
        self.fake.record = {"matched": {"title": title}, "data": f"title {title}"}
        self.fake.registered[f"watch_{WATCH_NAME}"]()

    def stored(self) -> list[Any]:
        """The kept tells."""
        return self.plugin._entries()


def make_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, clients: int) -> Env:
    """Build an AfkPlugin with a fake API, with a number of active clients, and load it."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    # importing bastproxy needs BASTPROXY_HOME, so the plugin module is imported here
    from aardwolf.afk.plugin import _afk

    fake = FakeApi()
    for index in range(clients):
        fake.clients[f"c{index}"] = (True, False)
    plugin = _afk.AfkPlugin.__new__(_afk.AfkPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.plugin_info = SimpleNamespace(data_directory=tmp_path)  # type: ignore[assignment]
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    plugin._phook_initialize()
    env = Env(plugin, fake, tmp_path)
    plugin._client = env.notices.append  # type: ignore[method-assign,assignment]
    return env


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """The plugin loaded with one active client."""
    yield make_env(monkeypatch, tmp_path, 1)


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.afk" in {p["plugin_id"] for p in result.plugins}


def test_plugin_imports_no_other_plugin() -> None:
    """A plugin reaches another through its API: only aardwolf.libs and its own package."""
    root = Path(aardwolf.__file__).resolve().parent / "afk"
    own = ("aardwolf.libs", "aardwolf.afk")
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
    assert fake.setting_defs["afktitle"][0] == "is AFK."
    assert fake.setting_defs["lasttitle"][0] == ""
    assert fake.setting_defs["isafk"][2] == {"readonly": True}
    assert "queue" not in fake.setting_defs
    title = fake.types[TYPE_TITLE]
    assert (title["cmd"], title["hide_output"]) == ("title", True)
    assert re.match(title["hide_start"], REPLY)
    assert "hide_end" not in title
    assert fake.triggers["afk_title_set"]["group"] == GROUP
    assert fake.triggers["afk_title_set"]["regex"] == TITLE_SET_REGEX
    assert fake.enabled() == set()
    assert WATCH_NAME in fake.watches
    assert TIMEOUT_EVENT.format(TYPE_TITLE) in fake.registered
    assert fake.modules == [["Comm 1"]]


def test_initial_isafk_follows_the_active_clients_without_sending(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    first = tmp_path / "a"
    first.mkdir()
    empty = make_env(monkeypatch, first, 0)
    assert empty.fake.settings["isafk"] is True
    assert empty.fake.queued == []
    other = tmp_path / "b"
    other.mkdir()
    active = make_env(monkeypatch, other, 1)
    assert active.fake.settings["isafk"] is False
    assert active.fake.sets == []


def test_initial_isafk_ignores_view_and_unlogged_clients(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env = make_env(monkeypatch, tmp_path, 0)
    env.fake.settings["isafk"] = False
    env.add_client("v", view_only=True)
    env.add_client("u", logged_in=False)
    assert env.plugin._active_count() == 0


def test_last_active_client_leaving_turns_afk_on(env: Env) -> None:
    env.fake.settings["lasttitle"] = "mine"
    env.leave("c0")
    assert env.fake.settings["isafk"] is True
    assert env.fake.queued == [(TYPE_TITLE, "is AFK.")]


def test_view_and_unlogged_leftovers_still_count_as_away(env: Env) -> None:
    env.add_client("v", view_only=True)
    env.add_client("u", logged_in=False)
    env.leave("c0")
    assert env.fake.settings["isafk"] is True
    assert env.fake.queued == [(TYPE_TITLE, "is AFK.")]


def test_another_active_client_keeps_afk_off(env: Env) -> None:
    env.add_client("c1")
    env.leave("c0")
    assert env.fake.settings["isafk"] is False
    assert env.fake.queued == []


def test_a_second_disconnect_sends_nothing(env: Env) -> None:
    env.add_client("v", view_only=True)
    env.leave("c0")
    env.leave("v")
    assert env.fake.queued == [(TYPE_TITLE, "is AFK.")]
    assert [s for s in env.fake.sets if s[0] == "isafk"] == [("isafk", True)]


def test_an_active_login_turns_afk_off_and_restores_the_title(env: Env) -> None:
    env.fake.settings["lasttitle"] = "mine"
    env.leave("c0")
    env.fake.queued.clear()
    env.login("c1")
    assert env.fake.settings["isafk"] is False
    assert env.fake.queued == [(TYPE_TITLE, "mine")]


def test_login_tells_how_many_tells_wait(env: Env) -> None:
    env.leave("c0")
    env.tell({"chan": "tell", "msg": "one", "player": "Zed"})
    env.tell({"chan": "tell", "msg": "two", "player": "Zed"})
    env.login("c1")
    assert env.notices == [["@BAFK Queue", "@BYou have 2 tells in the queue"]]


def test_login_with_an_empty_queue_and_title_sends_nothing(env: Env) -> None:
    env.leave("c0")
    env.fake.queued.clear()
    env.login("c1")
    assert env.fake.queued == []
    assert env.notices == []


def test_a_view_login_keeps_afk(env: Env) -> None:
    env.leave("c0")
    env.fake.queued.clear()
    env.login("v", view_only=True)
    assert env.fake.settings["isafk"] is True
    assert env.fake.queued == []


def test_an_unconnected_mud_queues_no_title(env: Env) -> None:
    env.fake.connected = False
    env.leave("c0")
    assert env.fake.settings["isafk"] is True
    assert env.fake.queued == []


def test_character_active_sends_the_afk_title_while_afk(env: Env) -> None:
    env.fake.connected = False
    env.leave("c0")
    env.fake.connected = True
    env.plugin._phook_character_active()
    assert env.fake.queued == [(TYPE_TITLE, "is AFK.")]


def test_character_active_sends_the_last_title_otherwise(env: Env) -> None:
    env.fake.settings["lasttitle"] = "mine"
    env.plugin._phook_character_active()
    assert env.fake.queued == [(TYPE_TITLE, "mine")]


def test_character_active_with_no_title_sends_nothing(env: Env) -> None:
    env.plugin._phook_character_active()
    assert env.fake.queued == []


def test_a_tell_is_kept_and_saved_while_afk(env: Env) -> None:
    env.leave("c0")
    before = time.time()
    env.tell({"chan": "tell", "msg": "hello there", "player": "Zed"})
    [entry] = env.stored()
    assert (entry["player"], entry["msg"]) == ("Zed", "hello there")
    assert entry["timestamp"] >= before
    from bastproxy.libs.persistentdict import PersistentDict

    saved = PersistentDict(PLUGIN_ID, env.home / "tells.txt", "c")
    assert saved["queue"] == [entry]


def test_tells_survive_a_reload(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    first = make_env(monkeypatch, tmp_path, 0)
    first.tell({"chan": "tell", "msg": "kept", "player": "Zed"})
    second = make_env(monkeypatch, tmp_path, 0)
    assert [e["msg"] for e in second.stored()] == ["kept"]


@pytest.mark.parametrize(
    "data",
    [{"chan": "gossip", "msg": "x", "player": "Zed"}, None, "tell", {}, ["tell"]],
)
def test_other_channels_and_bad_data_are_ignored(env: Env, data: object) -> None:
    env.leave("c0")
    env.tell(data)
    assert env.stored() == []


def test_a_tell_is_ignored_when_not_afk(env: Env) -> None:
    env.tell({"chan": "tell", "msg": "x", "player": "Zed"})
    assert env.stored() == []


def test_a_tell_with_no_data_key_is_ignored(env: Env) -> None:
    env.leave("c0")
    env.fake.record = {}
    env.plugin._eventcb_comm()
    assert env.stored() == []


def test_a_queued_title_is_hidden_with_its_prompt(env: Env) -> None:
    env.queued_title("is AFK.")
    env.fake.feed([REPLY])
    env.fake.feed([PROMPT], prompt=True)
    assert env.fake.hidden == [REPLY, PROMPT]
    assert env.fake.shown == []
    assert env.fake.finished == [TYPE_TITLE]
    assert env.fake.enabled() == set()


def test_a_typed_title_is_shown_and_remembered(env: Env) -> None:
    env.typed("a fine title")
    assert env.fake.enabled() == {"afk_title_set"}
    env.fake.feed(["Title now set to: a fine title"])
    env.fake.feed([PROMPT], prompt=True)
    assert env.fake.shown == ["Title now set to: a fine title", PROMPT]
    assert env.fake.finished == []
    assert env.fake.settings["lasttitle"] == "a fine title"
    assert env.fake.enabled() == set()


def test_a_typed_title_equal_to_the_afk_title_is_not_remembered(env: Env) -> None:
    env.fake.settings["lasttitle"] = "mine"
    env.typed("is AFK.")
    env.fake.feed([REPLY])
    assert env.fake.settings["lasttitle"] == "mine"


def test_an_unanswered_typed_title_is_not_taken_for_a_later_one(env: Env) -> None:
    env.typed("rejected title")
    env.queued_title("is AFK.")
    env.fake.feed([REPLY])
    assert env.fake.finished == [TYPE_TITLE]
    assert env.fake.settings["lasttitle"] == ""
    env.fake.feed([REPLY])
    assert env.fake.settings["lasttitle"] == ""


def test_the_timeout_turns_the_group_off(env: Env) -> None:
    env.queued_title("is AFK.")
    env.fake.registered[TIMEOUT_EVENT.format(TYPE_TITLE)]()
    assert env.fake.enabled() == set()
    assert env.fake.finished == []
    env.fake.feed([REPLY])
    assert env.fake.finished == []


def test_mud_disconnect_clears_the_state(env: Env) -> None:
    env.typed("a fine title")
    env.queued_title("is AFK.")
    env.plugin._eventcb_disconnect()
    assert env.fake.enabled() == set()
    assert env.plugin._pending_title is None
    assert env.plugin._queued_title is False


def test_show_lists_the_tells(env: Env) -> None:
    env.leave("c0")
    env.tell({"chan": "tell", "msg": "hello there", "player": "Zed"})
    result = env.plugin._command_show()
    assert result.success
    assert result.message[0] == "Tells received while afk"
    assert result.message[1].endswith("Zed: hello there")


def test_show_of_nothing(env: Env) -> None:
    assert env.plugin._command_show().message == ["The queue is empty"]


def test_clear_forgets_the_tells(env: Env) -> None:
    env.leave("c0")
    env.tell({"chan": "tell", "msg": "x", "player": "Zed"})
    result = env.plugin._command_clear()
    assert result.message == ["AFK tell queue cleared"]
    assert env.stored() == []
    assert env.plugin._command_show().message == ["The queue is empty"]


def test_toggle_flips_afk_and_says_so(env: Env) -> None:
    on = env.plugin._command_toggle()
    assert on.message == ["AFK is now on"]
    assert env.fake.settings["isafk"] is True
    assert env.fake.queued == [(TYPE_TITLE, "is AFK.")]
    off = env.plugin._command_toggle()
    assert off.message == ["AFK is now off"]
    assert env.fake.settings["isafk"] is False
