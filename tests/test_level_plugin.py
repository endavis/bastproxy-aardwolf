"""Tests for the Aardwolf level plugin, with a stubbed API that drives its triggers."""

import logging
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from event_keys import assert_raised_described
from statdb_support import make_db

import aardwolf
from aardwolf.level.libs import EVENTS
from aardwolf.libs.aardu import actual_level

if TYPE_CHECKING:
    from aardwolf.level.plugin._level import LevelPlugin

PLUGIN_ID = "plugins.aardwolf.level"
EMPTYLINE = "t_plugins.core.triggers_emptyline"
GAINS = "You gain 30 hit points, 25 mana, 20 moves, 5 practices and 6 trains."
GMCP: dict[str, Any] = {
    "char.status.level": 50,
    "char.status.state": 3,
    "char.base.remorts": 1,
    "char.base.tier": 0,
    "char.base.redos": 0,
}
WHOIS = {"name": "Bast", "level": 50, "totallevels": 50, "remorts": 1, "classes": []}
EVENT_PREFIX = "ev_plugins.aardwolf.level_"
GMCP_STATUS = "ev_libs.net.mud_gmcp_char.status"
GMCP_BASE = "ev_libs.net.mud_gmcp_char.base"
FAILURES = [
    "*" * 71,
    "Use either: 'superhero loud'   - 30 mins of double xp, 1000qp and 500,000 gold",
    "You must be carrying at least 500,000 gold coins.",
    "You must have at least 1000 quest points.",
    "You cannot superhero loud until double exp is over.",
    "You have to be level 200 to superhero.",
]


class FakeApi:
    """A stand-in for the bastproxy API that records the calls and drives the triggers.

    An unregister of something that is not registered fails, as the core APIs log an error.
    """

    def __init__(self) -> None:
        self.gmcp: dict[str, Any] = dict(GMCP)
        self.events_added: list[str] = []
        self.event_cbs: dict[str, list[Callable[..., Any]]] = {}
        self.watches: dict[str, str] = {}
        self.raised: list[tuple[str, dict[str, Any]]] = []
        self.triggers: dict[str, dict[str, Any]] = {}
        self.trigger_cbs: dict[str, list[Callable[..., Any]]] = {EMPTYLINE: []}
        self.group_toggles: list[tuple[str, bool]] = []
        self.trigger_unregisters: list[str] = []
        self.settings: dict[str, bool] = {}
        self.setting_defaults: dict[str, bool] = {}
        self.add_ok = True
        self.record: dict[str, Any] = {}
        self.table: dict[str, Callable[..., Any]] = {
            "plugins.core.events:event.add": self._event_add,
            "plugins.core.events:event.register": self._event_register,
            "plugins.core.events:event.unregister": self._event_unregister,
            "plugins.core.events:event.raise": self._event_raise,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.watch:watch.add": self._watch_add,
            "plugins.core.settings:setting.add": self._setting_add,
            "plugins.core.settings:setting.get": lambda pid, name: self.settings[name],
            "plugins.core.settings:setting.set": self._setting_set,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
            "plugins.core.triggers:trigger.unregister": self._trigger_unregister,
            "plugins.core.triggers:group.toggle.enable": self._group_toggle,
            "libs.net.protocols:gmcp.value.get": self.gmcp.get,
        }

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name; an unknown name is a KeyError."""
        return self.table[name]

    def _event_add(self, name: str, created_by: str, **kwargs: object) -> None:
        self.events_added.append(name)

    def _event_register(self, name: str, func: Callable[..., Any]) -> None:
        self.event_cbs.setdefault(name, []).append(func)

    def _event_unregister(self, name: str, func: Callable[..., Any]) -> None:
        assert func in self.event_cbs.get(name, []), f"{func} is not registered on {name}"
        self.event_cbs[name].remove(func)

    def _event_raise(self, name: str, event_args: dict[str, Any] | None = None) -> None:
        self.raised.append((name, event_args or {}))

    def _watch_add(self, name: str, regex: str) -> bool:
        self.watches[name] = regex
        return True

    def _setting_add(
        self, pid: str, name: str, default: bool, stype: object, help_text: str
    ) -> None:
        assert stype is bool
        self.setting_defaults[name] = default
        self.settings.setdefault(name, default)

    def _setting_set(self, pid: str, name: str, value: bool) -> bool:
        assert name in self.settings, f"unknown setting {name}"
        self.settings[name] = value
        return True

    def _trigger_add(self, name: str, regex: str, **kwargs: object) -> SimpleNamespace:
        self.triggers[name] = {
            "regex": regex,
            "enabled": kwargs.get("enabled", True),
            "group": kwargs.get("group"),
            "argtypes": kwargs.get("argtypes") or {},
        }
        self.trigger_cbs.setdefault(name, [])
        return SimpleNamespace(success=self.add_ok, trigger=SimpleNamespace(trigger_id=name))

    def _trigger_register(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        assert trigger_id in self.trigger_cbs, f"unknown trigger {trigger_id}"
        self.trigger_cbs[trigger_id].append(func)
        return True

    def _trigger_unregister(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        assert func in self.trigger_cbs.get(trigger_id, []), f"{func} not on {trigger_id}"
        self.trigger_unregisters.append(trigger_id)
        self.trigger_cbs[trigger_id].remove(func)
        return True

    def _group_toggle(self, group: str, flag: bool) -> bool:
        assert any(t["group"] == group for t in self.triggers.values()), f"unknown group {group}"
        self.group_toggles.append((group, flag))
        for trigger in self.triggers.values():
            if trigger["group"] == group:
                trigger["enabled"] = flag
        return True

    def feed(self, *lines: str) -> None:
        """Run each line through the enabled triggers, as the triggers plugin does."""
        for line in lines:
            if line == "":
                for func in list(self.trigger_cbs[EMPTYLINE]):
                    func()
                continue
            for name, trigger in list(self.triggers.items()):
                if not trigger["enabled"]:
                    continue
                match = re.match(trigger["regex"], line)
                if not match:
                    continue
                groups = match.groupdict()
                for arg, argtype in trigger["argtypes"].items():
                    groups[arg] = argtype(groups[arg])
                self.record = {"matches": groups}
                for func in list(self.trigger_cbs[name]):
                    func()

    def gmcp_message(self, package: str, data: dict[str, Any]) -> None:
        """Set the cached GMCP values, then call what is registered on the GMCP event."""
        for key, value in data.items():
            self.gmcp[f"char.{package}.{key}"] = value
        for func in list(self.event_cbs.get(f"ev_libs.net.mud_gmcp_char.{package}", [])):
            func()

    def setting(self, name: str) -> bool:
        """The current value of a setting."""
        return self.settings[name]

    def enabled(self) -> set[str]:
        """The names of the enabled triggers."""
        return {name for name, trigger in self.triggers.items() if trigger["enabled"]}

    def raised_names(self) -> list[str]:
        """The names of the raised events, without the prefix."""
        return [name.removeprefix(EVENT_PREFIX) for name, _ in self.raised]

    def type_watch(self, command: str) -> None:
        """A client types a command: call what is registered on the watch it matches."""
        for name, regex in self.watches.items():
            if re.match(regex, command):
                for func in list(self.event_cbs.get(f"watch_{name}", [])):
                    func()


class Env:
    """The plugin under test with its fake API and clock."""

    def __init__(self, plugin: "LevelPlugin", fake: FakeApi, home: Path) -> None:
        self.plugin = plugin
        self.fake = fake
        self.home = home
        self.clock = {"now": 1000.0}

    def level(self, line: str = "You raise a level! You are now level 51.") -> None:
        """Feed a level line, the gains line and the empty line."""
        self.fake.feed(line, GAINS, "")


def make_plugin(
    fake: FakeApi, home: Path, monkeypatch: pytest.MonkeyPatch, clock: dict[str, float]
) -> "LevelPlugin":
    """Build a LevelPlugin on the fake API and run its init hook."""
    from aardwolf.level.plugin import _level

    monkeypatch.setattr(_level.LevelPlugin, "_now", staticmethod(lambda: clock["now"]))
    plugin = _level.LevelPlugin.__new__(_level.LevelPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.plugin_info = SimpleNamespace(data_directory=home)  # type: ignore[assignment]
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    return plugin


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build a LevelPlugin with a fake API and load it."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    fake = FakeApi()
    clock = {"now": 1000.0}
    plugin = make_plugin(fake, tmp_path, monkeypatch, clock)
    plugin._phook_initialize()
    result = Env(plugin, fake, tmp_path)
    result.clock = clock
    yield result
    assert_raised_described(fake.raised, EVENTS)


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin, with its dependencies, without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.level" in {p["plugin_id"] for p in result.plugins}
    from aardwolf import level

    for dependency in (
        "plugins.aardwolf.connect",
        "plugins.core.triggers",
        "plugins.core.watch",
        "plugins.core.settings",
        "plugins.core.events",
    ):
        assert dependency in level.PLUGIN_DEPENDENCIES


def test_after_load(env: Env) -> None:
    """after_load adds the events, settings, watches and triggers in their states."""
    fake = env.fake
    assert sorted(fake.events_added) == sorted(
        f"{EVENT_PREFIX}{n}" for n in ("gain", "hero", "superhero", "remort", "tier", "preremort")
    )
    assert fake.setting_defaults == {
        "preremort": False,
        "remortcomp": False,
        "tiering": False,
        "seen2": False,
    }
    assert set(fake.watches) == {
        "level_sh",
        "level_shsilent",
        "level_shloud",
        "level_shconfirm",
        "level_shloudconfirm",
    }
    assert all(f"watch_{name}" in fake.event_cbs for name in fake.watches)
    assert len(fake.triggers) == 21
    assert fake.enabled() == {
        "lvlpup",
        "lvlpupbless",
        "lvllevel",
        "lvlshloud",
        "lvlsh",
        "lvlbless",
        "lvlpreremort",
        "lvlremortcomp",
        "lvltier",
    }
    groups = {t["group"] for t in fake.triggers.values()} - {None}
    assert groups == {f"{PLUGIN_ID}.linfo", f"{PLUGIN_ID}.superhero", f"{PLUGIN_ID}.remort"}
    assert fake.trigger_cbs["lvlsh"] == []
    assert fake.trigger_cbs[EMPTYLINE] == []
    assert env.plugin._collecting is False


def test_failed_trigger_add_is_not_toggled(env: Env) -> None:
    """When no trigger could be added, no toggle is attempted for the unknown groups."""
    fake = env.fake
    fake.add_ok = False
    fake.triggers.clear()
    env.plugin._groups_ready.clear()
    env.plugin._phook_initialize()
    env.plugin._watch_superhero()
    env.plugin._eventcb_disconnect()
    assert fake.group_toggles == []


def test_level(env: Env) -> None:
    """A level raises level_gain once, with the gains, and turns the collecting off."""
    fake = env.fake
    fake.feed("You raise a level! You are now level 51.")
    assert f"{PLUGIN_ID}.linfo" in {t["group"] for t in fake.triggers.values() if t["enabled"]}
    assert fake.trigger_cbs[EMPTYLINE] == [env.plugin._finish]
    env.clock["now"] = 1100.0
    fake.feed(
        GAINS,
        "Lucky! You gain an extra 2 training sessions!",
        "You gain a bonus Strength point!",
        "",
    )
    assert fake.raised_names() == ["gain"]
    payload = fake.raised[0][1]
    assert payload["type"] == "level"
    assert payload["level"] == 51
    assert payload["totallevels"] == 51
    assert (payload["hp"], payload["mp"], payload["mv"]) == (30, 25, 20)
    assert (payload["pracs"], payload["trains"], payload["bonustrains"]) == (5, 6, 2)
    assert payload["str"] == 1
    assert payload["int"] == 0
    assert payload["finishtime"] == 1100.0
    assert payload["starttime"] == 1000.0
    assert not fake.enabled() & {"lvlgains", "lvlbonustrains", "lvlbonusstat"}
    assert fake.trigger_cbs[EMPTYLINE] == []
    assert type(payload) is dict
    payload["hp"] = -1
    assert env.plugin.levelinfo["hp"] == 30


def test_empty_line_before_the_gains_does_not_finish(env: Env) -> None:
    """With no trains yet, an empty line leaves the level collecting until the gains arrive."""
    env.fake.feed("You raise a level! You are now level 51.", "")
    assert env.fake.raised == []
    assert env.fake.trigger_cbs[EMPTYLINE] == [env.plugin._finish]
    env.fake.feed(GAINS, "")
    assert env.fake.raised_names() == ["gain"]


def test_second_level_does_not_register_the_finish_twice(env: Env) -> None:
    """A second level line while collecting restarts the record and registers _finish once."""
    env.fake.feed("You raise a level! You are now level 51.")
    env.fake.feed("You raise a level! You are now level 52.", GAINS, "")
    assert env.fake.raised_names() == ["gain"]
    assert env.fake.raised[0][1]["level"] == 52


def test_blessing_level(env: Env) -> None:
    """A blessing level records the blessing trains."""
    env.fake.feed(
        "You gain a level - you are now level 52.",
        GAINS,
        "You gain 1 extra train daily blessing bonus.",
        "You gain 2 additional training sessions from your enhanced battle learning.",
        "",
    )
    payload = env.fake.raised[0][1]
    assert payload["level"] == 52
    assert payload["blessingtrains"] == 1
    assert payload["battlelearntrains"] == 2


def test_powerup(env: Env) -> None:
    """A powerup is a pup: its level is the GMCP one, converted from a string."""
    env.fake.gmcp["char.status.level"] = "201"
    env.fake.gmcp["char.base.remorts"] = 7
    env.fake.gmcp["char.base.tier"] = 1
    env.fake.feed(
        "Congratulations, hero. You have increased your powers!", "You gain 10 trains.", ""
    )
    assert env.fake.raised_names() == ["gain"]
    payload = env.fake.raised[0][1]
    assert payload["type"] == "pup"
    assert payload["level"] == 201
    assert payload["trains"] == 10
    assert payload["totallevels"] == actual_level(201, 7, 1, 0)


def test_powerup_bless_line(env: Env) -> None:
    """The powerup blessing line starts a pup record too."""
    env.fake.feed("You gain a powerup.", "You gain 3 trains.", "")
    assert env.fake.raised[0][1]["type"] == "pup"
    assert env.fake.raised[0][1]["trains"] == 3


def test_hero(env: Env) -> None:
    """Level 200 raises level_gain and then level_hero; a powerup at 200 raises no hero."""
    env.level("You raise a level! You are now level 200.")
    assert env.fake.raised_names() == ["gain", "hero"]
    env.fake.raised.clear()
    env.fake.gmcp["char.status.level"] = 200
    env.fake.feed("You gain a powerup.", "You gain 3 trains.", "")
    assert env.fake.raised_names() == ["gain"]


def test_superhero_loud(env: Env) -> None:
    """The watch, the loud line and an empty line raise level_gain and level_superhero."""
    fake = env.fake
    fake.type_watch("superhero loud")
    assert {f"{PLUGIN_ID}.superhero"} <= {
        t["group"] for t in fake.triggers.values() if t["enabled"]
    }
    fake.feed(
        "Congratulations! You are now a superhero! You receive 10 trains for superhero loud.",
        "",
    )
    assert fake.raised_names() == ["gain", "superhero"]
    payload = fake.raised[0][1]
    assert payload["level"] == 201
    assert payload["trains"] == 10
    assert payload["type"] == "level"
    assert not any(
        t["enabled"] for t in fake.triggers.values() if t["group"] == f"{PLUGIN_ID}.superhero"
    )
    assert fake.trigger_cbs[EMPTYLINE] == []


@pytest.mark.parametrize(
    "command",
    [
        "superhero",
        "superhero silent",
        "superhero loud",
        "superhero confirm",
        "superhero loud confirm",
    ],
)
def test_every_superhero_command_starts_a_record(env: Env, command: str) -> None:
    """Each of the five watched commands starts a level 201 record."""
    env.fake.type_watch(command)
    assert env.plugin.levelinfo["level"] == 201
    assert env.fake.trigger_cbs[EMPTYLINE] == [env.plugin._finish]


def test_superhero_loud_line_outside_a_record_changes_nothing(env: Env) -> None:
    """The loud line with no level 201 record being collected does not touch the record."""
    env.level()
    env.fake.raised.clear()
    env.fake.feed(
        "Congratulations! You are now a superhero! You receive 10 trains for superhero loud."
    )
    assert env.plugin.levelinfo["trains"] == 6
    assert env.fake.raised == []


@pytest.mark.parametrize("failure", FAILURES)
def test_failed_superhero(env: Env, failure: str) -> None:
    """A failed superhero turns the groups off, raises nothing and a later empty line neither."""
    fake = env.fake
    fake.type_watch("superhero")
    fake.feed(failure)
    assert fake.raised == []
    assert not any(
        t["enabled"] for t in fake.triggers.values() if t["group"] and "remort" not in t["group"]
    )
    assert fake.trigger_cbs[EMPTYLINE] == []
    fake.feed("")
    assert fake.raised == []


def test_failure_line_without_a_watch_is_ignored(env: Env) -> None:
    """With the superhero group off, the failure lines do nothing."""
    env.fake.feed(*FAILURES)
    assert env.fake.group_toggles == []
    assert env.fake.trigger_unregisters == []


def test_preremort(env: Env) -> None:
    """The remort flag line raises level_preremort and sets the setting."""
    env.fake.feed("You are now flagged as remorting.")
    assert env.fake.raised_names() == ["preremort"]
    assert env.fake.setting("preremort")


def test_remort(env: Env) -> None:
    """A remort raises level_gain at level 1 with no trains, then level_remort."""
    env.fake.gmcp["char.status.level"] = 1
    env.fake.feed("You are now flagged as remorting.")
    env.fake.raised.clear()
    env.fake.feed("* Remort transformation complete!", "")
    assert env.fake.raised_names() == ["gain", "remort"]
    payload = env.fake.raised[0][1]
    assert payload["level"] == 1
    assert payload["trains"] == 0
    assert not env.fake.setting("remortcomp")
    assert not env.fake.setting("preremort")


def test_tier(env: Env) -> None:
    """A tier waits for status state 2, then 3, then a new base, and raises level_tier."""
    fake = env.fake
    fake.feed("## You have already remorted the max number of times.")
    assert fake.setting("tiering")
    assert fake.event_cbs[GMCP_STATUS] == [env.plugin._gmcp_status]
    fake.gmcp_message("status", {"state": "2"})
    assert fake.setting("seen2")
    assert fake.event_cbs[GMCP_STATUS] == []
    assert fake.event_cbs[GMCP_BASE] == [env.plugin._gmcp_base]
    fake.gmcp_message("status", {"state": "3", "level": "1"})
    assert fake.raised == []
    fake.gmcp_message("base", {"remorts": 1, "tier": 2, "redos": 0})
    assert fake.event_cbs[GMCP_BASE] == []
    assert fake.trigger_cbs[EMPTYLINE] == [env.plugin._finish]
    fake.gmcp_message("base", {"remorts": 1, "tier": 2, "redos": 0})
    fake.feed("")
    assert fake.raised_names() == ["gain", "tier"]
    assert fake.raised[0][1]["level"] == 1
    assert not fake.setting("tiering")
    assert not fake.setting("seen2")
    assert fake.event_cbs[GMCP_STATUS] == []


def test_base_frame_without_seen2_starts_nothing(env: Env) -> None:
    """A base frame with state 3 but no state 2 seen starts no record."""
    env.fake.feed("## You have already remorted the max number of times.")
    env.plugin._gmcp_base()
    assert env.fake.trigger_cbs[EMPTYLINE] == []
    env.fake.gmcp_message("status", {"state": "2"})
    env.fake.gmcp_message("base", {"remorts": 1})
    assert env.fake.trigger_cbs[EMPTYLINE] == []
    assert env.fake.event_cbs[GMCP_BASE] == [env.plugin._gmcp_base]


def test_a_second_tier_line_moves_the_callback_back_to_status(env: Env) -> None:
    """A tier line while waiting on the base unregisters the base callback first."""
    fake = env.fake
    fake.feed("## You have already remorted the max number of times.")
    fake.gmcp_message("status", {"state": 2})
    fake.feed("## You have already remorted the max number of times.")
    assert fake.event_cbs[GMCP_BASE] == []
    assert fake.event_cbs[GMCP_STATUS] == [env.plugin._gmcp_status]


def test_tier_path_calls_no_client_output(env: Env, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fix 5: the status path calls only known APIs (the fake raises KeyError otherwise)."""
    from aardwolf.level.plugin import _level

    logged: list[tuple[int, str]] = []
    monkeypatch.setattr(
        _level, "log_to", lambda _target, level, msg, *args: logged.append((level, msg % args))
    )
    env.fake.feed("## You have already remorted the max number of times.")
    env.fake.gmcp_message("status", {"state": 2})
    assert (logging.DEBUG, "seen state 2 while tiering") in logged


@pytest.mark.parametrize(("seen2", "event"), [(False, GMCP_STATUS), (True, GMCP_BASE)])
def test_rearm_on_load(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, seen2: bool, event: str
) -> None:
    """A tier in progress at load registers the matching GMCP callback again."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    fake = FakeApi()
    fake.settings.update({"tiering": True, "seen2": seen2})
    plugin = make_plugin(fake, tmp_path, monkeypatch, {"now": 1.0})
    plugin._phook_initialize()
    assert [name for name, funcs in fake.event_cbs.items() if funcs and "gmcp" in name] == [event]


def test_no_rearm_when_not_tiering(env: Env) -> None:
    """With no tier in progress no GMCP callback is registered."""
    assert GMCP_STATUS not in env.fake.event_cbs
    assert GMCP_BASE not in env.fake.event_cbs


def test_disconnect_mid_level(env: Env) -> None:
    """A disconnect in the middle of a level turns the groups off and drops the finish."""
    fake = env.fake
    fake.feed("You raise a level! You are now level 51.")
    env.plugin._eventcb_disconnect()
    assert fake.trigger_cbs[EMPTYLINE] == []
    assert not fake.enabled() & {"lvlgains", "lvlshbad"}
    fake.feed("")
    assert fake.raised == []


def test_disconnect_while_idle(env: Env) -> None:
    """A disconnect with nothing collecting does not unregister anything."""
    env.plugin._eventcb_disconnect()
    assert env.fake.trigger_unregisters == []


def test_persistence_and_starttime(env: Env, monkeypatch: pytest.MonkeyPatch) -> None:
    """The record survives a rebuilt plugin, and the next starttime is the new now."""
    from bastproxy.libs.persistentdict import PersistentDict

    env.clock["now"] = 1500.0
    env.level()
    env.plugin._phook_save()
    saved = PersistentDict(PLUGIN_ID, env.home / "level.txt", "c")
    assert saved["finishtime"] == 1500.0
    assert saved["level"] == 51
    rebuilt = make_plugin(env.fake, env.home, monkeypatch, env.clock)
    assert rebuilt.levelinfo["finishtime"] == 1500.0
    env.clock["now"] = 2000.0
    env.fake.raised.clear()
    env.level("You raise a level! You are now level 52.")
    assert env.fake.raised[0][1]["starttime"] == 2000.0
    assert env.fake.raised[0][1]["finishtime"] == 2000.0


def test_starttime_after_a_failed_superhero_is_its_own_now(env: Env) -> None:
    """After a failed superhero, the next level starts when it is reached, not at an old time."""
    env.clock["now"] = 1500.0
    env.level()
    env.clock["now"] = 1600.0
    env.fake.type_watch("superhero")
    env.fake.feed("You have to be level 200 to superhero.")
    env.clock["now"] = 1700.0
    env.fake.raised.clear()
    env.level("You raise a level! You are now level 52.")
    assert env.fake.raised[0][1]["starttime"] == 1700.0
    assert all(payload["starttime"] != 1600.0 for _, payload in env.fake.raised)


def test_two_level_ups_start_when_each_was_reached(env: Env) -> None:
    """Each level's starttime is its own level-up time, not the previous record's finish."""
    env.clock["now"] = 1000.0
    env.fake.feed("You raise a level! You are now level 51.", GAINS)
    env.clock["now"] = 1100.0
    env.fake.feed("")
    env.clock["now"] = 5000.0
    env.fake.raised.clear()
    env.fake.feed("You raise a level! You are now level 52.", GAINS)
    env.clock["now"] = 5050.0
    env.fake.feed("")
    payload = env.fake.raised[0][1]
    assert payload["starttime"] == 5000.0
    assert payload["finishtime"] == 5050.0


def test_pup_between_levels_starts_at_its_own_line(env: Env) -> None:
    """A level, a powerup and a level each start at the clock of their own start line."""
    env.fake.gmcp["char.status.level"] = 51
    starts: list[tuple[str, float]] = []
    for clock, lines in (
        (1000.0, ("You raise a level! You are now level 51.", GAINS)),
        (2000.0, ("Congratulations, hero. You have increased your powers!", "You gain 10 trains.")),
        (3000.0, ("You raise a level! You are now level 52.", GAINS)),
    ):
        env.fake.raised.clear()
        env.clock["now"] = clock
        env.fake.feed(*lines)
        env.clock["now"] = clock + 50
        env.fake.feed("")
        payload = env.fake.raised[0][1]
        starts.append((payload["type"], payload["starttime"]))
    assert starts == [("level", 1000.0), ("pup", 2000.0), ("level", 3000.0)]


def test_remort_starts_at_the_complete_line(env: Env) -> None:
    """A remort record starts when the transformation completes, not at an earlier time."""
    env.clock["now"] = 1000.0
    env.level()
    env.fake.gmcp["char.status.level"] = 1
    env.clock["now"] = 1500.0
    env.fake.feed("You are now flagged as remorting.")
    env.clock["now"] = 2500.0
    env.fake.raised.clear()
    env.fake.feed("* Remort transformation complete!", "")
    assert env.fake.raised[0][1]["starttime"] == 2500.0


def test_tier_starts_at_the_base_frame(env: Env) -> None:
    """A tier record starts when the base frame arrives, not at the tier line or state 2."""
    fake = env.fake
    env.clock["now"] = 1000.0
    fake.feed("## You have already remorted the max number of times.")
    env.clock["now"] = 1100.0
    fake.gmcp_message("status", {"state": "2"})
    env.clock["now"] = 1200.0
    fake.gmcp_message("status", {"state": "3", "level": "1"})
    env.clock["now"] = 1300.0
    fake.gmcp_message("base", {"remorts": 1, "tier": 2, "redos": 0})
    env.clock["now"] = 1400.0
    fake.feed("")
    assert fake.raised[0][1]["starttime"] == 1300.0


def test_first_level_starts_now(env: Env) -> None:
    """With no earlier record, the start time is now."""
    env.clock["now"] = 777.0
    env.level()
    assert env.fake.raised[0][1]["starttime"] == 777.0


def test_unknown_bonus_stat_is_ignored(env: Env) -> None:
    """A bonus stat that is not one of the six adds no key to the record."""
    env.fake.feed(
        "You raise a level! You are now level 51.", "You gain a bonus Charisma point!", GAINS, ""
    )
    assert "cha" not in env.fake.raised[0][1]


def test_payload_is_saved_by_statdb(env: Env, tmp_path: Path) -> None:
    """The level_gain payload feeds statdb's save_level."""
    from aardwolf.statdb.libs import StatStore

    env.fake.feed(
        "You raise a level! You are now level 51.",
        GAINS,
        "Lucky! You gain an extra 2 training sessions!",
        "",
    )
    database = make_db(tmp_path / "db")
    try:
        store = StatStore(database)
        store.save_whois(WHOIS)
        store.save_level(env.fake.raised[0][1])
        row = database.select("SELECT * FROM levels")[0]
        assert row["hp"] == 30
        assert row["mp"] == 25
        assert row["trains"] == 6
        assert row["bonustrains"] == 2
        assert row["type"] == "level"
        stat = database.select("SELECT totallevels FROM stats WHERE milestone = 'current'")
        assert stat[0]["totallevels"] == 51
    finally:
        database.close()


def test_raised_keys_are_all_described(env: Env) -> None:
    """A level raises only keys its events describe in arg_descriptions (#43)."""
    env.fake.feed("You raise a level! You are now level 51.", GAINS, "")
    assert env.fake.raised_names() == ["gain"]
    assert_raised_described(env.fake.raised, EVENTS)
