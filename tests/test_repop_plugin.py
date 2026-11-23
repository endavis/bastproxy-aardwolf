"""Tests for the Aardwolf repop plugin, with a stubbed API."""

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

import aardwolf
from aardwolf.repop.libs import DEFAULT_FORMAT

if TYPE_CHECKING:
    from bastproxy.libs.records import NetworkData

    from aardwolf.repop.plugin._repop import RepopPlugin

PLUGIN_ID = "plugins.aardwolf.repop"
EVENT = "ev_libs.net.mud_gmcp_comm.repop"


class FakeApi:
    """A stand-in for the bastproxy API."""

    def __init__(self) -> None:
        self.settings: dict[str, str] = {"channel": "gt", "format": DEFAULT_FORMAT}
        self.record: dict[str, Any] = {}
        self.added: list[tuple[object, ...]] = []
        self.added_kwargs: list[dict[str, object]] = []

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.settings:setting.add": self._add,
            "plugins.core.settings:setting.get": lambda pid, key: self.settings[key],
            "plugins.core.events:event.current.record.get": lambda: self.record,
        }
        return table[name]

    def _add(self, *args: object, **kwargs: object) -> None:
        self.added.append(args)
        self.added_kwargs.append(kwargs)


class Env:
    """The plugin under test with its fake API and what it sent."""

    def __init__(self, plugin: "RepopPlugin", fake: FakeApi, mud: list[str]) -> None:
        self.plugin = plugin
        self.fake = fake
        self.mud = mud

    def repop(self, data: object) -> None:
        """Deliver a comm.repop event with the given data."""
        self.fake.record = {"package": "comm.repop", "data": data}
        self.plugin._eventcb_repop()


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build a RepopPlugin with a fake API and a fixed time."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from aardwolf.repop.plugin import _repop

    mud: list[str] = []

    class FakeSend:
        def __init__(self, message: "NetworkData") -> None:
            self.message = message

        def __call__(self) -> None:
            mud.extend(str(item.line) for item in self.message)

    monkeypatch.setattr(_repop, "SendDataDirectlyToMud", FakeSend)
    monkeypatch.setattr(_repop.time, "strftime", lambda fmt, t=None: "12:34:56")
    fake = FakeApi()
    plugin = _repop.RepopPlugin.__new__(_repop.RepopPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    yield Env(plugin, fake, mud)


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.repop" in {p["plugin_id"] for p in result.plugins}


def test_after_load(env: Env) -> None:
    """after_load adds the two settings; format is shown raw."""
    env.plugin._phook_initialize()
    assert [a[:4] for a in env.fake.added] == [
        (PLUGIN_ID, "channel", "gt", str),
        (PLUGIN_ID, "format", DEFAULT_FORMAT, str),
    ]
    assert env.fake.added_kwargs == [{}, {"nocolor": True}]


def test_repop_sends_default(env: Env) -> None:
    """A repop sends the formatted line to the mud."""
    env.repop({"zone": "aylor"})
    assert env.mud == ["gt @r[@RRepop@r]@w aylor @R@@ @w12:34:56"]


def test_repop_custom_settings(env: Env) -> None:
    """The channel and format settings are used."""
    env.fake.settings = {"channel": "ft", "format": "${zone} repopped at ${time}"}
    env.repop({"zone": "aylor"})
    assert env.mud == ["ft aylor repopped at 12:34:56"]


@pytest.mark.parametrize("data", [{}, {"zone": ""}, None, "text"])
def test_repop_no_zone_sends_nothing(env: Env, data: object) -> None:
    """A message without a usable zone sends nothing."""
    env.repop(data)
    assert env.mud == []


def test_repop_blank_channel_sends_nothing(env: Env) -> None:
    """A blank channel sends nothing."""
    env.fake.settings["channel"] = "  "
    env.repop({"zone": "aylor"})
    assert env.mud == []


def test_event_name() -> None:
    """The callback is registered to the event the core raises."""
    from bastproxy.libs.net.protocols import gmcp_package_events

    from aardwolf.repop.plugin._repop import RepopPlugin

    registrations = RepopPlugin._eventcb_repop.event_registration
    assert [r["event_name"] for r in registrations] == [EVENT]
    assert gmcp_package_events("comm.repop")[0] == EVENT
