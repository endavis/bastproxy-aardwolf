"""Tests for the a102 plugin, with a stubbed API."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from aardwolf.a102.plugin._a102 import A102Plugin

PLUGIN_ID = "plugins.aardwolf.a102"


class FakeApi:
    """Records the API calls the plugin makes."""

    def __init__(self) -> None:
        self.sent: list[tuple[int, bytes]] = []
        self.send_result = True
        self.registered: list[int] = []
        self.added: list[str] = []
        self.raised: list[tuple[str, dict[str, Any]]] = []
        self.record: dict[str, Any] = {}
        self.mud_enabled = False

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the stub for an API name."""
        stubs: dict[str, Callable[..., Any]] = {
            "libs.net.protocols:telopt.register": self._register,
            "libs.net.protocols:telopt.send": self._send,
            "libs.net.protocols:telopt.get": self._get,
            "plugins.core.events:event.add": self._add,
            "plugins.core.events:event.raise": self._raise,
            "plugins.core.events:event.current.record.get": lambda: self.record,
        }
        return stubs[name]

    def _register(self, option: int) -> bool:
        self.registered.append(option)
        return True

    def _send(self, option: int, payload: bytes) -> bool:
        self.sent.append((option, payload))
        return self.send_result

    def _get(self, option: int) -> dict[str, Any]:
        return {"mud_enabled": self.mud_enabled}

    def _add(self, name: str, created_by: str, **kwargs: object) -> None:
        self.added.append(name)

    def _raise(self, name: str, args: dict[str, Any]) -> None:
        self.raised.append((name, args))


@pytest.fixture
def api() -> FakeApi:
    """A fresh fake API."""
    return FakeApi()


@pytest.fixture
def make_plugin(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, api: FakeApi
) -> Callable[[], A102Plugin]:
    """Build a plugin without the BasePlugin constructor."""
    # Importing bastproxy raises unless BASTPROXY_HOME is an existing directory.
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))

    def build() -> A102Plugin:
        from aardwolf.a102.plugin import Plugin

        plugin = Plugin.__new__(Plugin)
        plugin.plugin_id = PLUGIN_ID
        plugin.api = api  # type: ignore[assignment]
        plugin._phook_init_plugin()
        return plugin

    return build


@pytest.fixture
def plugin(make_plugin: Callable[[], A102Plugin]) -> A102Plugin:
    """A plugin that has not seen option 102 enabled."""
    return make_plugin()


@pytest.fixture
def enabled(plugin: A102Plugin, api: FakeApi) -> A102Plugin:
    """A plugin whose option 102 is enabled on the MUD link."""
    plugin._eventcb_mud_enabled()
    api.sent.clear()
    return plugin


def test_after_load_owns_the_option(plugin: A102Plugin, api: FakeApi) -> None:
    """after_load registers option 102 and adds the data event."""
    plugin._phook_initialize()
    assert api.registered == [102]
    assert api.added == [f"ev_{PLUGIN_ID}_mud_data"]
    assert api.sent == []


def test_after_load_when_link_already_up(plugin: A102Plugin, api: FakeApi) -> None:
    """After a reload with the link up, the cached state is sent without an enabled event."""
    plugin.option_counts = {7: 1}
    api.mud_enabled = True
    plugin._phook_initialize()
    assert api.sent == [(102, bytes([7, 1]))]


def test_reload_caches_option_counts(plugin: A102Plugin) -> None:
    """The counts survive a reload."""
    assert plugin.attributes_to_save_on_reload == ["option_counts"]


def test_registrations() -> None:
    """Callbacks use the core telopt event names and the APIs are named by the grammar."""
    from aardwolf.a102.plugin import Plugin

    events = {
        reg["event_name"]
        for attr in vars(Plugin).values()
        for reg in getattr(attr, "event_registration", [])
    }
    assert events == {
        "ev_libs.net.mud_telopt_102_enabled",
        "ev_libs.net.mud_telopt_102_disabled",
        "ev_libs.net.client_telopt_102",
        "ev_libs.net.mud_telopt_102",
    }
    apis = {attr.api["name"] for attr in vars(Plugin).values() if hasattr(attr, "api")}
    assert {"option.toggle", "payload.send"} <= apis


def test_counted_toggles(enabled: A102Plugin, api: FakeApi) -> None:
    """Only the first on and the last off reach the MUD."""
    flags = (True, True, False, False)
    results = [enabled._api_option_toggle("SPELLUPTAGS", flag) for flag in flags]
    assert results == [True] * 4
    assert api.sent == [(102, bytes([7, 1])), (102, bytes([7, 2]))]


def test_lone_off_sends_nothing(enabled: A102Plugin, api: FakeApi) -> None:
    """An off at 0 sends nothing and keeps the count at 0."""
    assert enabled._api_option_toggle("prompt", False) is True
    assert api.sent == []
    assert enabled.option_counts == {}


def test_unknown_name_returns_false_and_warns(
    enabled: A102Plugin, api: FakeApi, caplog: pytest.LogCaptureFixture
) -> None:
    """An unknown or non-str name is rejected with a warning."""
    with caplog.at_level(logging.WARNING):
        assert enabled._api_option_toggle("NOPE", True) is False
        assert enabled._api_option_toggle(7, True) is False
    assert api.sent == []
    assert enabled.option_counts == {}
    assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_toggle_before_enable_applies_on_enabled(plugin: A102Plugin, api: FakeApi) -> None:
    """A toggle while disabled only counts; enabling sends the state."""
    plugin._api_option_toggle("SPELLUPTAGS", True)
    plugin._api_option_toggle("PROMPT", True)
    plugin._api_option_toggle("PROMPT", False)
    assert api.sent == []
    plugin._eventcb_mud_enabled()
    assert api.sent == [(102, bytes([7, 1])), (102, bytes([52, 2]))]


def test_reconnect_resends_state(enabled: A102Plugin, api: FakeApi) -> None:
    """After a disconnect and a new enable the counted state is sent again."""
    enabled._api_option_toggle("SPELLUPTAGS", True)
    api.sent.clear()
    enabled._eventcb_mud_disabled()
    enabled._api_option_toggle("PROMPT", True)
    assert api.sent == []
    enabled._eventcb_mud_enabled()
    assert api.sent == [(102, bytes([7, 1])), (102, bytes([52, 1]))]


def test_client_toggles_share_counts(enabled: A102Plugin, api: FakeApi) -> None:
    """A client's toggle goes through the same counts as a plugin's."""
    api.record = {"data": bytes([7, 1]), "client_id": "c1", "view_only": False}
    enabled._eventcb_client_data()
    enabled._api_option_toggle("SPELLUPTAGS", True)
    assert api.sent == [(102, bytes([7, 1]))]
    enabled._api_option_toggle("SPELLUPTAGS", False)
    assert len(api.sent) == 1
    api.record = {"data": bytes([7, 2]), "client_id": "c1", "view_only": False}
    enabled._eventcb_client_data()
    assert api.sent[-1] == (102, bytes([7, 2]))
    assert enabled.option_counts == {7: 0}


@pytest.mark.parametrize(
    "data", [b"", b"\x07", bytes([7, 1, 1]), bytes([7, 3]), bytes([99, 1]), bytes([100, 1])]
)
def test_malformed_client_payload_ignored(enabled: A102Plugin, api: FakeApi, data: bytes) -> None:
    """Anything but a known option and a flag of 1 or 2 is ignored."""
    api.record = {"data": data, "client_id": "c1", "view_only": False}
    enabled._eventcb_client_data()
    assert api.sent == []
    assert enabled.option_counts == {}


def test_view_only_client_ignored(enabled: A102Plugin, api: FakeApi) -> None:
    """A view only client cannot change the counts."""
    api.record = {"data": bytes([7, 1]), "client_id": "c1", "view_only": True}
    enabled._eventcb_client_data()
    assert api.sent == []
    assert enabled.option_counts == {}


def test_mud_data_raises_both_events(plugin: A102Plugin, api: FakeApi) -> None:
    """A two-byte message raises the per-message and the per-option event."""
    api.record = {"data": bytes([100, 3])}
    plugin._eventcb_mud_data()
    args = {"option": 100, "flag": 3}
    assert api.raised == [
        (f"ev_{PLUGIN_ID}_mud_data", args),
        (f"ev_{PLUGIN_ID}_mud_option_100", args),
    ]


def test_option_event_added_once(plugin: A102Plugin, api: FakeApi) -> None:
    """The per-option event is added on first use only."""
    api.record = {"data": bytes([100, 3])}
    plugin._eventcb_mud_data()
    plugin._eventcb_mud_data()
    api.record = {"data": bytes([100, 1])}
    plugin._eventcb_mud_data()
    api.record = {"data": bytes([5, 1])}
    plugin._eventcb_mud_data()
    assert api.added == [f"ev_{PLUGIN_ID}_mud_option_100", f"ev_{PLUGIN_ID}_mud_option_5"]
    assert len(api.raised) == 8


@pytest.mark.parametrize("data", [b"", b"\x64", bytes([100, 3, 1])])
def test_wrong_length_mud_data_raises_nothing(
    plugin: A102Plugin, api: FakeApi, data: bytes
) -> None:
    """Only two-byte messages raise events."""
    api.record = {"data": data}
    plugin._eventcb_mud_data()
    assert api.raised == []
    assert api.added == []


@pytest.mark.parametrize("result", [True, False])
def test_payload_send_wraps_telopt_send(plugin: A102Plugin, api: FakeApi, result: bool) -> None:
    """payload.send passes the bytes to telopt.send and returns its result."""
    api.send_result = result
    assert plugin._api_payload_send(b"\x07\x01") is result
    assert api.sent == [(102, b"\x07\x01")]


def test_discovery_finds_the_plugin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The bastproxy loader finds a102 under the package's search path."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    import aardwolf

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert "aardwolf.a102" in {plugin["plugin_id"] for plugin in result.plugins}
    assert "aardwolf.a102" not in {p["package_id"] for p in result.packages}


def test_unload_turns_counted_options_off(enabled: A102Plugin, api: FakeApi) -> None:
    """A real unload sends off for options with a count above 0 and nothing for 0."""
    enabled.option_counts = {52: 2, 7: 1, 5: 0}
    enabled.is_reloading_f = False
    enabled._phook_turn_options_off()
    assert api.sent == [(102, bytes([7, 2])), (102, bytes([52, 2]))]


def test_reload_sends_nothing_on_unload(enabled: A102Plugin, api: FakeApi) -> None:
    """A reload leaves the toggles on."""
    enabled.option_counts = {7: 1}
    enabled.is_reloading_f = True
    enabled._phook_turn_options_off()
    assert api.sent == []


def test_unload_not_enabled_sends_nothing(plugin: A102Plugin, api: FakeApi) -> None:
    """Without option 102 enabled on the MUD link, nothing is sent."""
    plugin.option_counts = {7: 1}
    plugin.is_reloading_f = False
    plugin._phook_turn_options_off()
    assert api.sent == []


def test_unload_sends_before_the_option_is_unregistered(enabled: A102Plugin, api: FakeApi) -> None:
    """The full uninitialize run sends the offs before telopt.unregister.for.owner."""
    events: list[str] = []
    stubs: dict[str, Callable[..., Any]] = {}

    def record(name: str) -> Callable[..., Any]:
        def stub(*args: object, **kwargs: object) -> None:
            events.append(name)

        return stub

    for name in (
        f"{PLUGIN_ID}:plugin.state.save",
        "plugins.core.events:event.raise",
        "libs.api:api.toplevel.remove",
        "libs.net.protocols:gmcp.modules.remove.for.owner",
        "libs.net.protocols:telopt.unregister.for.owner",
    ):
        stubs[name] = record(name)

    def send(option: int, payload: bytes) -> bool:
        events.append("send")
        return True

    stubs["libs.net.protocols:telopt.send"] = send
    enabled.api = lambda name: stubs[name]  # type: ignore[assignment]
    enabled.option_counts = {7: 1, 52: 1}
    enabled.is_reloading_f = False
    enabled.uninitialize()
    unregister = events.index("libs.net.protocols:telopt.unregister.for.owner")
    assert events[:2] == ["send", "send"]
    assert events.count("send") == 2
    assert events.index("send") < unregister
    assert max(i for i, e in enumerate(events) if e == "send") < unregister
