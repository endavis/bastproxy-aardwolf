"""Tests for the Aardwolf connect plugin."""

import re
from collections.abc import Callable, Iterator
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

import aardwolf

if TYPE_CHECKING:
    from bastproxy.libs.records import NetworkData

    from aardwolf.connect.plugin._connect import ConnectPlugin

CHAR_VALUES = {
    "char.base.redos": 1,
    "char.vitals.hp": 10,
    "char.stats.str": 5,
    "char.maxstats.maxhp": 10,
    "char.worth.gold": 3,
}
FULL_GMCP: dict[str, Any] = {
    **CHAR_VALUES,
    "room.info.num": 1,
    "comm.quest.action": "ready",
    "char.status.state": 3,
}


class FakeApi:
    """A stand-in for the bastproxy API that records what the plugin calls."""

    def __init__(self) -> None:
        self.gmcp: dict[str, Any] = {}
        self.mud_connected = True
        self.character_active = False
        self.gmcp_send_ok = True
        self.sent_gmcp: list[str] = []
        self.modules_added: list[list[str]] = []
        self.active_sets: list[bool] = []
        self.registered: dict[str, Callable[..., Any]] = {}
        self.trigger_adds: list[tuple[str, str]] = []
        self.trigger_regs: list[tuple[str, Callable[..., Any]]] = []
        self.provider_adds: list[tuple[str, str, Callable[..., Any]]] = []
        self.provider_ok = True
        self.provider_raises: list[tuple[str, str]] = []

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "libs.net.protocols:gmcp.modules.add": self.modules_added.append,
            "libs.net.protocols:gmcp.value.get": self._gmcp_get,
            "libs.net.protocols:gmcp.send": self._gmcp_send,
            "plugins.core.proxy:mud.is.connected": lambda: self.mud_connected,
            "libs.api:character.is.active": lambda: self.character_active,
            "libs.api:character.active.set": self._active_set,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
            "plugins.core.events:event.register": self._event_register,
            "plugins.core.web:web.provider.add": self._provider_add,
            "plugins.core.web:web.provider.changed.raise": self._provider_raise,
        }
        return table[name]

    def _gmcp_get(self, path: str) -> object:
        """Resolve a dotted path case-sensitively in a nested dict, like the real API."""
        nested: dict[str, Any] = {}
        for key, value in self.gmcp.items():
            *parents, leaf = key.split(".")
            node = nested
            for part in parents:
                node = node.setdefault(part, {})
            node[leaf] = value
        current: Any = nested
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current

    def _gmcp_send(self, package: str) -> bool:
        if self.gmcp_send_ok:
            self.sent_gmcp.append(package)
        return self.gmcp_send_ok

    def _active_set(self, flag: bool) -> None:
        self.active_sets.append(flag)
        self.character_active = flag

    def _trigger_add(self, name: str, regex: str) -> SimpleNamespace:
        self.trigger_adds.append((name, regex))
        return SimpleNamespace(success=True, trigger=SimpleNamespace(trigger_id="tid"))

    def _trigger_register(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        self.trigger_regs.append((trigger_id, func))
        return True

    def _provider_add(self, owner: str, name: str, snapshot: Callable[..., Any]) -> str | None:
        self.provider_adds.append((owner, name, snapshot))
        return f"{owner}.{name}" if self.provider_ok else None

    def _provider_raise(self, owner: str, name: str) -> bool:
        self.provider_raises.append((owner, name))
        return True

    def _event_register(self, name: str, func: Callable[..., Any]) -> None:
        self.registered[name] = func


class Env:
    """The plugin under test with its fake API and recorded mud lines."""

    def __init__(
        self, module: ModuleType, plugin: "ConnectPlugin", fake: FakeApi, lines: list[str]
    ) -> None:
        self.module = module
        self.plugin = plugin
        self.fake = fake
        self.lines = lines


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build a ConnectPlugin with a fake API."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from aardwolf.connect.plugin import _connect

    lines: list[str] = []

    class FakeSend:
        def __init__(self, message: "NetworkData") -> None:
            self.message = message

        def __call__(self) -> None:
            lines.extend(str(item.line) for item in self.message)

    monkeypatch.setattr(_connect, "SendDataDirectlyToMud", FakeSend)
    fake = FakeApi()
    plugin = _connect.ConnectPlugin.__new__(_connect.ConnectPlugin)
    plugin.plugin_id = "plugins.aardwolf.connect"
    plugin.api = MagicMock(side_effect=fake)
    plugin._vitals_offered = set()
    plugin._reset_state()
    yield Env(_connect, plugin, fake, lines)


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.connect" in {p["plugin_id"] for p in result.plugins}


def test_press_return_regex(env: Env) -> None:
    """The regex matches the pager prompt."""
    regex = env.module.PRESS_RETURN_REGEX
    assert re.match(regex, "[ Press Return to continue ]")
    assert re.match(regex, "  [ Press Return to continue ]")
    assert not re.match(regex, "nothing")


def test_after_load(env: Env) -> None:
    """after_load adds modules, the trigger and ten event callbacks."""
    env.fake.mud_connected = False
    env.plugin._phook_initialize()
    assert env.fake.modules_added == [env.module.GMCP_MODULES]
    assert env.fake.trigger_adds == [("press_return", env.module.PRESS_RETURN_REGEX)]
    assert env.fake.trigger_regs == [("tid", env.plugin._trigger_press_return)]
    assert len(env.fake.registered) == 10
    assert env.fake.sent_gmcp == []
    assert env.lines == []


def test_press_return_only_before_first_active(env: Env) -> None:
    """Press Return sends an empty line until first active."""
    env.plugin._trigger_press_return()
    assert env.lines == [""]
    env.plugin._first_active = True
    env.plugin._trigger_press_return()
    assert env.lines == [""]


def test_gmcp_setup_once_and_retry(env: Env) -> None:
    """GMCP setup sends once, and retries when the send failed."""
    env.fake.gmcp_send_ok = False
    env.plugin._eventcb_gmcp_setup()
    assert not env.plugin._gmcp_ready
    env.fake.gmcp_send_ok = True
    env.plugin._eventcb_gmcp_setup()
    env.plugin._eventcb_gmcp_setup()
    assert env.fake.sent_gmcp == ["rawcolor on", "group on"]


def test_client_login_requests(env: Env) -> None:
    """A client login requests data only when connected and ready."""
    env.plugin._eventcb_client_logged_in()
    assert env.fake.sent_gmcp == []
    env.plugin._gmcp_ready = True
    env.fake.mud_connected = False
    env.plugin._eventcb_client_logged_in()
    assert env.fake.sent_gmcp == []
    env.fake.mud_connected = True
    env.plugin._eventcb_client_logged_in()
    assert env.fake.sent_gmcp == ["request room", "request quest", "request char"]


@pytest.mark.parametrize(
    ("missing", "request_name"),
    [
        ("char.vitals.hp", "request char"),
        ("room.info.num", "request room"),
        ("comm.quest.action", "request quest"),
    ],
)
def test_missing_data_requested_once(env: Env, missing: str, request_name: str) -> None:
    """Missing data is requested once and blocks first active."""
    env.fake.gmcp = {k: v for k, v in FULL_GMCP.items() if k != missing}
    env.plugin._eventcb_check()
    env.plugin._eventcb_check()
    assert env.fake.sent_gmcp == [request_name]
    assert not env.plugin._first_active
    assert env.lines == []


def test_all_missing_requested_in_one_pass(env: Env) -> None:
    """Every check runs, so each request goes out once in one pass."""
    env.fake.gmcp = {"char.status.state": 3}
    env.plugin._eventcb_check()
    assert sorted(env.fake.sent_gmcp) == ["request char", "request quest", "request room"]


@pytest.mark.parametrize(("state", "fires"), [(2, False), (None, False), ("3", True), (3, True)])
def test_state_gates_first_active(env: Env, state: object, fires: bool) -> None:
    """Only state 3 (or "3") makes the character first active."""
    env.fake.gmcp = {**FULL_GMCP, "char.status.state": state}
    env.plugin._eventcb_check()
    assert env.plugin._first_active is fires


def test_first_active_fires_once(env: Env) -> None:
    """First active sends look and map and sets the character active once."""
    env.fake.gmcp = dict(FULL_GMCP)
    assert env.plugin._api_character_is_first_active() is False
    env.plugin._eventcb_check()
    env.plugin._eventcb_check()
    assert env.lines == ["look", "map"]
    assert env.fake.active_sets == [True]
    assert env.plugin._api_character_is_first_active() is True


def test_not_connected_does_not_fire(env: Env) -> None:
    """Nothing fires while the mud is not connected."""
    env.fake.gmcp = dict(FULL_GMCP)
    env.fake.mud_connected = False
    env.plugin._eventcb_check()
    assert not env.plugin._first_active
    assert env.fake.active_sets == []


def test_disconnect_resets_and_login_fires_again(env: Env) -> None:
    """A disconnect resets the state so the next login fires again."""
    env.fake.gmcp = dict(FULL_GMCP)
    env.plugin._eventcb_check()
    env.plugin._eventcb_mud_disconnected()
    assert not env.plugin._first_active
    assert not env.plugin._gmcp_ready
    env.fake.character_active = False
    env.plugin._eventcb_check()
    assert env.lines == ["look", "map", "look", "map"]
    assert env.fake.active_sets == [True, True]


def test_loaded_mid_session_fires(env: Env) -> None:
    """Loading mid-session fires without a reconnect."""
    env.fake.gmcp = dict(FULL_GMCP)
    env.plugin._phook_initialize()
    assert env.plugin._first_active
    assert env.lines == ["look", "map"]
    assert env.fake.sent_gmcp[:2] == ["rawcolor on", "group on"]


def test_reload_does_not_set_active_twice(env: Env) -> None:
    """With the character already active, the flag is not set again."""
    env.fake.gmcp = dict(FULL_GMCP)
    env.fake.character_active = True
    env.plugin._phook_initialize()
    assert env.plugin._first_active
    assert env.fake.active_sets == []


def test_mid_session_state_not_active_does_nothing(env: Env) -> None:
    """Mid-session with state 2 only registers; nothing is sent."""
    env.fake.gmcp = {**FULL_GMCP, "char.status.state": 2}
    env.plugin._phook_initialize()
    assert not env.plugin._first_active
    assert env.fake.sent_gmcp == []
    assert env.lines == []


def test_gmcp_stub_is_case_sensitive(env: Env) -> None:
    """A capitalised lookup misses, as in the real gmcp.value.get."""
    env.fake.gmcp = dict(FULL_GMCP)
    get = env.fake("libs.net.protocols:gmcp.value.get")
    assert get("char.status.state") == 3
    assert get("Char.Status.state") is None
    assert get("char.vitals.hp") == 10


VITALS_DATA: dict[str, Any] = {
    "char.vitals.hp": 90,
    "char.vitals.mana": 80,
    "char.vitals.moves": 70,
    "char.maxstats.maxhp": 100,
    "char.maxstats.maxmana": 110,
    "char.maxstats.maxmoves": 120,
    "char.status.level": 42,
    "char.status.tnl": 500,
    "char.status.align": -250,
    "char.status.state": 3,
    "char.status.pos": "Standing",
    "char.status.enemy": "a made-up foe",
    "char.status.enemypct": 60,
    "char.base.tier": 1,
    "char.base.remorts": 2,
}


def test_plugin_depends_on_web() -> None:
    """The plugin lists the web plugin as a dependency."""
    from aardwolf import connect

    assert "plugins.core.web" in connect.PLUGIN_DEPENDENCIES


def test_vitals_provider_added_once(env: Env) -> None:
    """The vitals provider is added once with the plugin id and the snapshot."""
    env.plugin._phook_add_web_providers()
    assert env.fake.provider_adds == [
        ("plugins.aardwolf.connect", "vitals", env.plugin._provider_vitals)
    ]


def test_vitals_full_data(env: Env) -> None:
    """The snapshot holds the 15 fields from the cached data."""
    env.fake.gmcp = dict(VITALS_DATA)
    data = env.plugin._provider_vitals()
    assert len(env.module.VITALS_FIELDS) == 15
    assert set(data) == set(env.module.VITALS_FIELDS)
    assert data["hp"] == 90
    assert data["maxmoves"] == 120
    assert data["tier"] == 1
    assert data["pos"] == "Standing"
    assert data["enemy"] == "a made-up foe"


def test_vitals_empty_cache(env: Env) -> None:
    """With no cached data every field is None."""
    data = env.plugin._provider_vitals()
    assert len(data) == 15
    assert all(value is None for value in data.values())


@pytest.mark.parametrize(
    ("package", "fields"),
    [
        ("vitals", {"hp", "mana", "moves"}),
        ("maxstats", {"maxhp", "maxmana", "maxmoves"}),
        ("status", {"level", "tnl", "align", "state", "pos", "enemy", "enemypct"}),
        ("base", {"tier", "remorts"}),
    ],
)
def test_vitals_missing_package(env: Env, package: str, fields: set[str]) -> None:
    """A missing package gives None for its fields only."""
    env.fake.gmcp = {k: v for k, v in VITALS_DATA.items() if k.split(".")[1] != package}
    data = env.plugin._provider_vitals()
    assert {name for name, value in data.items() if value is None} == fields


@pytest.mark.parametrize("package", ["vitals", "maxstats", "status", "base"])
def test_vitals_change_per_event(env: Env, package: str) -> None:
    """Each of the four package events raises exactly one change."""
    env.fake.mud_connected = False
    env.plugin._phook_initialize()
    env.plugin._phook_add_web_providers()
    callback = env.fake.registered[f"ev_libs.net.mud_gmcp_char.{package}"]
    callback()
    assert env.fake.provider_raises == [("plugins.aardwolf.connect", "vitals")]


def test_vitals_parent_event_not_used(env: Env) -> None:
    """The parent char event only runs the first-active check."""
    env.fake.mud_connected = False
    env.plugin._phook_initialize()
    env.plugin._phook_add_web_providers()
    env.fake.registered[env.module.EVENT_GMCP_CHAR]()
    assert env.fake.provider_raises == []


def test_vitals_refused_raises_nothing(env: Env) -> None:
    """A refused provider raises no change."""
    env.fake.provider_ok = False
    env.plugin._phook_add_web_providers()
    env.plugin._eventcb_vitals_changed()
    env.plugin._eventcb_mud_disconnected()
    assert env.fake.provider_raises == []


def test_vitals_disconnect_raises_change(env: Env) -> None:
    """A disconnect raises one change, as the GMCP cache clears."""
    env.plugin._phook_add_web_providers()
    env.plugin._eventcb_mud_disconnected()
    assert env.fake.provider_raises == [("plugins.aardwolf.connect", "vitals")]
