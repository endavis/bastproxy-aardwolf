"""Tests for the Aardwolf su plugin, with a stubbed API."""

import ast
import json
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

import aardwolf
from aardwolf.su.libs import (
    API_SKILL_CAN_USE,
    API_SKILL_GET,
    API_SKILL_IS_AFFECTED,
    API_SKILL_IS_BLOCKED,
    API_SKILL_IS_PRACTICED,
    API_SKILL_IS_SPELLUP,
    API_SKILL_SEND,
    API_SPELLUPS_GET,
    API_UP_TO_DATE,
    SPELLUP_FILE,
    TIMER_NAME,
    WAIT_TIMEOUT,
)

if TYPE_CHECKING:
    from bastproxy.plugins.core.commands import CommandResult

    from aardwolf.su.plugin import _su

PLUGIN_ID = "plugins.aardwolf.su"
BLESS = 10
SANC = 20
HASTE = 30


def skill(sn: int, name: str, percent: int = 80, spellup: bool = True) -> dict[str, Any]:
    """A skill as the skills plugin returns it."""
    return {"sn": sn, "name": name, "percent": percent, "spellup": spellup}


class FakeApi:
    """A stand-in for the bastproxy API."""

    def __init__(self) -> None:
        self.settings: dict[str, Any] = {}
        self.settings_added: list[tuple[Any, ...]] = []
        self.gmcp: dict[str, Any] = {
            "char.status.state": 3,
            "char.vitals.mana": 100,
            "char.vitals.moves": 100,
            "room.info.num": 1000,
        }
        self.timers: dict[str, tuple[Callable[[], None], float, bool]] = {}
        self.skills: dict[int, dict[str, Any]] = {
            BLESS: skill(BLESS, "bless"),
            SANC: skill(SANC, "sanctuary"),
            HASTE: skill(HASTE, "haste"),
            40: skill(40, "fireball", spellup=False),
            50: skill(50, "cure light", percent=5),
        }
        self.cannot_use: set[int] = set()
        self.affected: set[int] = set()
        self.recblocked: set[int] = set()
        self.sent: list[int] = []
        self.send_ok = True
        self.up_to_date = True
        self.connected = True
        self.active = True
        self.record: dict[str, Any] = {}
        self.args: dict[str, Any] = {}

    def _find(self, key: int | str) -> dict[str, Any] | None:
        for entry in self.skills.values():
            if key in (entry["sn"], entry["name"]):
                return dict(entry)
        return None

    def _send(self, sn: int) -> bool:
        self.sent.append(sn)
        return self.send_ok

    def _setting_set(self, pid: str, name: str, value: object) -> None:
        self.settings[name] = value

    def _timer_add(self, name: str, func: Callable[[], None], seconds: float, **kw: object) -> None:
        assert name not in self.timers
        self.timers[name] = (func, seconds, bool(kw.get("onetime")))

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.settings:setting.add": lambda *a, **k: self.settings_added.append(a),
            "plugins.core.settings:setting.get": lambda pid, key: self.settings[key],
            "plugins.core.settings:setting.set": self._setting_set,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.commands:command.current.args.get": lambda: self.args,
            "plugins.core.timers:timer.add": self._timer_add,
            "plugins.core.timers:timer.exists": lambda n: n in self.timers,
            "plugins.core.timers:timer.remove": self.timers.pop,
            "plugins.core.proxy:mud.is.connected": lambda: self.connected,
            "libs.api:character.is.active": lambda: self.active,
            "libs.net.protocols:gmcp.value.get": lambda path: self.gmcp.get(path),
            API_SKILL_GET: self._find,
            API_SKILL_SEND: self._send,
            API_SKILL_CAN_USE: lambda sn: sn not in self.cannot_use,
            API_SKILL_IS_AFFECTED: lambda sn: sn in self.affected,
            API_SKILL_IS_BLOCKED: lambda sn: sn in self.recblocked,
            API_SKILL_IS_PRACTICED: lambda sn: self.skills[sn]["percent"] > 10,
            API_SKILL_IS_SPELLUP: lambda sn: self.skills[sn]["spellup"],
            API_SPELLUPS_GET: lambda: [dict(s) for s in self.skills.values() if s["spellup"]],
            API_UP_TO_DATE: lambda: self.up_to_date,
        }
        return table[name]


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: "_su.SuPlugin", fake: FakeApi, home: Path) -> None:
        self.plugin = plugin
        self.fake = fake
        self.home = home
        self.notices: list[list[str]] = []

    def event(self, handler: Callable[[], None], **record: object) -> None:
        """Deliver an event record to a handler."""
        self.fake.record = record
        handler()

    def fail(self, sn: int, reason: str) -> None:
        """Deliver a skills_fail event."""
        self.event(self.plugin._eventcb_fail, sn=sn, reason=reason, target="self", recovery=-1)

    def command(self, handler: Callable[[], "CommandResult"], **args: object) -> "CommandResult":
        """Run a command with arguments."""
        self.fake.args = args
        return handler()

    def add(self, *sns: int) -> None:
        """Put spells in the list."""
        for sn in sns:
            self.plugin.ups.add(sn)

    def state(self, name: str) -> object:
        """Read an attribute of the plugin (mypy narrows one that a test assigned)."""
        return getattr(self.plugin, name)


def make_env(monkeypatch: pytest.MonkeyPatch, home: Path) -> Env:
    """Build a SuPlugin with a fake API and load it."""
    monkeypatch.setenv("BASTPROXY_HOME", str(home))
    # importing bastproxy needs BASTPROXY_HOME, so the plugin module is imported here
    from aardwolf.su.plugin import _su

    fake = FakeApi()
    plugin = _su.SuPlugin.__new__(_su.SuPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.plugin_info = SimpleNamespace(data_directory=home)  # type: ignore[assignment]
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    fake.settings["enabled"] = True
    fake.settings["nocastrooms"] = {}
    plugin._phook_initialize()
    env = Env(plugin, fake, home)
    plugin._client = env.notices.append  # type: ignore[method-assign,assignment]
    return env


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Env:
    """The plugin loaded with an empty list."""
    return make_env(monkeypatch, tmp_path)


@pytest.fixture
def ready(env: Env) -> Env:
    """The plugin with bless, sanctuary and haste in the list, nothing cast yet."""
    env.add(BLESS, SANC, HASTE)
    return env


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.su" in {p["plugin_id"] for p in result.plugins}


def test_plugin_imports_no_other_plugin() -> None:
    """A plugin reaches another through its API: only aardwolf.libs and its own package."""
    root = Path(aardwolf.__file__).resolve().parent / "su"
    own = ("aardwolf.libs", "aardwolf.su")
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
    added = {a[1]: a for a in env.fake.settings_added}
    assert set(added) == {"enabled", "nocastrooms"}
    assert added["enabled"][2] is True
    assert added["nocastrooms"][3] is dict


def test_after_load_seeds_nocast_from_the_room(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env = make_env(monkeypatch, tmp_path)
    env.fake.settings["nocastrooms"] = {"1000": True}
    env.plugin._phook_initialize()
    assert env.plugin._nocast is True


def test_casts_when_the_character_is_active(ready: Env) -> None:
    ready.plugin._phook_character_active()
    assert ready.fake.sent == [BLESS]
    assert ready.plugin._waiting == BLESS
    func, seconds, onetime = ready.fake.timers[TIMER_NAME]
    assert (seconds, onetime) == (WAIT_TIMEOUT, True)
    assert func == ready.plugin._timer_waiting


@pytest.mark.parametrize(
    "change",
    [
        lambda f: f.settings.__setitem__("enabled", False),
        lambda f: setattr(f, "connected", False),
        lambda f: setattr(f, "active", False),
        lambda f: setattr(f, "up_to_date", False),
        lambda f: f.gmcp.__setitem__("char.status.state", 8),
        lambda f: f.gmcp.__setitem__("char.status.state", True),
    ],
)
def test_no_cast_when_the_gate_is_closed(ready: Env, change: Callable[[FakeApi], None]) -> None:
    change(ready.fake)
    ready.plugin._phook_character_active()
    assert ready.fake.sent == []


@pytest.mark.parametrize("flag", ["_nocast", "_nomana", "_nomoves"])
def test_no_cast_when_a_state_flag_is_set(ready: Env, flag: str) -> None:
    setattr(ready.plugin, flag, True)
    ready.plugin._phook_character_active()
    assert ready.fake.sent == []


def test_no_cast_while_waiting(ready: Env) -> None:
    ready.plugin._phook_character_active()
    ready.event(ready.plugin._eventcb_affoff, sn=SANC)
    assert ready.fake.sent == [BLESS]


def test_state_given_as_text_is_active(ready: Env) -> None:
    ready.fake.gmcp["char.status.state"] = "3"
    ready.plugin._phook_character_active()
    assert ready.fake.sent == [BLESS]


def test_skips_disabled_unusable_and_blocked(ready: Env) -> None:
    ready.plugin.ups.set_enabled(BLESS, False)
    ready.fake.cannot_use.add(SANC)
    ready.plugin._phook_character_active()
    assert ready.fake.sent == [HASTE]
    ready.plugin._clear_waiting()
    ready.plugin._blocked.add(HASTE)
    ready.fake.sent.clear()
    ready.plugin._phook_character_active()
    assert ready.fake.sent == []


def test_a_send_that_fails_tries_the_next(ready: Env) -> None:
    results = iter([False, True])
    ready.fake.send_ok = False
    original = ready.fake._send

    def send(sn: int) -> bool:
        original(sn)
        return next(results)

    ready.plugin.api = MagicMock(
        side_effect=lambda name: send if name == API_SKILL_SEND else ready.fake(name)
    )
    ready.plugin._phook_character_active()
    assert ready.fake.sent == [BLESS, SANC]
    assert ready.plugin._waiting == SANC


def test_affon_for_the_waiting_spell_casts_the_next(ready: Env) -> None:
    ready.plugin._phook_character_active()
    ready.fake.affected.add(BLESS)
    ready.fake.cannot_use.add(BLESS)
    ready.event(ready.plugin._eventcb_affon, sn=BLESS, duration=100)
    assert ready.fake.sent == [BLESS, SANC]
    assert ready.plugin._waiting == SANC


def test_affon_for_another_spell_keeps_waiting(ready: Env) -> None:
    ready.plugin._phook_character_active()
    ready.event(ready.plugin._eventcb_affon, sn=HASTE, duration=100)
    assert ready.plugin._waiting == BLESS
    assert ready.fake.sent == [BLESS]


def test_nomana_stops_and_vitals_resume(ready: Env) -> None:
    ready.fake.gmcp["char.vitals.mana"] = 5
    ready.plugin._phook_character_active()
    ready.fail(BLESS, "nomana")
    assert ready.plugin._nomana is True
    assert ready.plugin._waiting is None
    assert TIMER_NAME not in ready.fake.timers
    assert ready.plugin._lastmana == 5
    ready.event(ready.plugin._eventcb_affoff, sn=SANC)
    assert ready.fake.sent == [BLESS]
    ready.event(ready.plugin._eventcb_vitals)
    assert ready.fake.sent == [BLESS]
    ready.fake.gmcp["char.vitals.mana"] = 6
    ready.event(ready.plugin._eventcb_vitals)
    assert ready.state("_nomana") is False
    assert ready.fake.sent == [BLESS, BLESS]


def test_nomoves_records_the_moves_not_the_mana(ready: Env) -> None:
    """Regression: the old plugin stored the moves in lastmana."""
    ready.fake.gmcp["char.vitals.mana"] = 90
    ready.fake.gmcp["char.vitals.moves"] = 7
    ready.plugin._phook_character_active()
    ready.fail(BLESS, "nomoves")
    assert ready.plugin._nomoves is True
    assert ready.plugin._lastmoves == 7
    assert ready.plugin._lastmana == -1
    ready.fake.gmcp["char.vitals.moves"] = 8
    ready.event(ready.plugin._eventcb_vitals)
    assert ready.state("_nomoves") is False
    assert ready.fake.sent == [BLESS, BLESS]


def test_nomana_for_a_cast_not_waited_on_still_applies(ready: Env) -> None:
    ready.fail(HASTE, "nomana")
    assert ready.plugin._nomana is True


def test_nocastroom_saves_the_room_and_a_move_clears_it(ready: Env) -> None:
    ready.plugin._phook_character_active()
    ready.fail(BLESS, "nocastroom")
    assert ready.plugin._nocast is True
    assert ready.plugin._waiting is None
    assert ready.fake.settings["nocastrooms"] == {"1000": True}
    ready.event(ready.plugin._eventcb_move_room, to={"num": 2000})
    assert ready.state("_nocast") is False
    assert ready.fake.sent == [BLESS, BLESS]
    ready.plugin._clear_waiting()
    ready.event(ready.plugin._eventcb_move_room, to={"num": 1000})
    assert ready.plugin._nocast is True
    assert ready.fake.sent == [BLESS, BLESS]


def test_a_move_between_castable_rooms_does_not_cast(ready: Env) -> None:
    ready.event(ready.plugin._eventcb_move_room, to={"num": 2000})
    assert ready.fake.sent == []


def test_a_nocast_fail_in_an_unknown_room_saves_nothing(ready: Env) -> None:
    ready.fake.gmcp["room.info.num"] = None
    ready.fail(BLESS, "nocastroom")
    assert ready.plugin._nocast is True
    assert ready.fake.settings["nocastrooms"] == {}


@pytest.mark.parametrize("reason", ["fighting", "notactive"])
def test_fighting_and_notactive_stop_waiting_until_the_state_is_active(
    ready: Env, reason: str
) -> None:
    ready.plugin._phook_character_active()
    ready.fail(BLESS, reason)
    assert ready.plugin._waiting is None
    assert ready.fake.sent == [BLESS]
    ready.fake.gmcp["char.status.state"] = 8
    ready.event(ready.plugin._eventcb_status)
    assert ready.fake.sent == [BLESS]
    ready.fake.gmcp["char.status.state"] = 3
    ready.event(ready.plugin._eventcb_status)
    assert ready.fake.sent == [BLESS, BLESS]


def test_lostconc_resends_and_restarts_the_timer(ready: Env) -> None:
    ready.plugin._phook_character_active()
    ready.fail(BLESS, "lostconc")
    assert ready.fake.sent == [BLESS, BLESS]
    assert ready.plugin._waiting == BLESS
    assert TIMER_NAME in ready.fake.timers


def test_lostconc_for_another_spell_is_ignored(ready: Env) -> None:
    ready.plugin._phook_character_active()
    ready.fail(HASTE, "lostconc")
    assert ready.fake.sent == [BLESS]
    assert ready.plugin._waiting == BLESS


@pytest.mark.parametrize(
    ("reason", "why"),
    [
        ("alreadyaff", "you are already affected"),
        ("disabled", "it is disabled mudside"),
        ("wrongtarget", "it can not be cast on yourself"),
    ],
)
def test_disabling_failures(ready: Env, reason: str, why: str) -> None:
    ready.plugin._phook_character_active()
    ready.fail(BLESS, reason)
    assert not ready.plugin.ups.is_enabled(BLESS)
    assert ready.notices == [[f"@BSpellup - disabled bless because {why}"]]
    assert ready.fake.sent == [BLESS, SANC]
    saved = json.loads((ready.home / SPELLUP_FILE).read_text(encoding="utf-8"))
    assert saved["self"]["10"] == {"enabled": False}


def test_a_disabling_failure_for_another_spell_is_ignored(ready: Env) -> None:
    ready.plugin._phook_character_active()
    ready.fail(HASTE, "alreadyaff")
    assert ready.plugin.ups.is_enabled(HASTE)
    assert ready.notices == []


def test_recblock_skips_the_spell_until_a_recovery_ends(ready: Env) -> None:
    ready.plugin._phook_character_active()
    ready.fail(BLESS, "recblock")
    assert ready.plugin._blocked == {BLESS}
    assert ready.fake.sent == [BLESS, SANC]
    ready.plugin._clear_waiting()
    ready.event(ready.plugin._eventcb_affoff, sn=SANC)
    assert ready.fake.sent == [BLESS, SANC, SANC]
    ready.fake.cannot_use.add(SANC)
    ready.plugin._clear_waiting()
    ready.event(ready.plugin._eventcb_recoff, sn=1)
    assert ready.plugin._blocked == set()
    assert ready.fake.sent[-1] == BLESS


@pytest.mark.parametrize("reason", ["dontknow", "17"])
def test_dontknow_and_unknown_reasons_stop_waiting_without_casting(ready: Env, reason: str) -> None:
    ready.plugin._phook_character_active()
    ready.fail(BLESS, reason)
    assert ready.plugin._waiting is None
    assert ready.fake.sent == [BLESS]
    assert TIMER_NAME not in ready.fake.timers
    ready.event(ready.plugin._eventcb_uptodate)
    assert ready.fake.sent == [BLESS, BLESS]


def test_an_unrelated_fail_is_ignored(ready: Env) -> None:
    ready.fail(HASTE, "recblock")
    ready.fail(HASTE, "dontknow")
    assert ready.plugin._blocked == set()
    assert ready.fake.sent == []


def test_the_timer_clears_waiting_without_casting(ready: Env) -> None:
    ready.plugin._phook_character_active()
    func, _, _ = ready.fake.timers.pop(TIMER_NAME)
    func()
    assert ready.plugin._waiting is None
    assert ready.fake.sent == [BLESS]


def test_disconnect_forgets_the_state(ready: Env) -> None:
    ready.plugin._phook_character_active()
    ready.plugin._nocast = ready.plugin._nomana = ready.plugin._nomoves = True
    ready.plugin._lastmana = ready.plugin._lastmoves = 4
    ready.plugin._blocked.add(SANC)
    ready.plugin._eventcb_disconnect()
    plugin = ready.plugin
    assert plugin._waiting is None
    assert TIMER_NAME not in ready.fake.timers
    assert not (plugin._nocast or plugin._nomana or plugin._nomoves)
    assert (plugin._lastmana, plugin._lastmoves) == (-1, -1)
    assert plugin._blocked == set()


def test_enabled_modified(ready: Env) -> None:
    ready.event(ready.plugin._eventcb_enabled_modified, newvalue=True, oldvalue="__init__")
    ready.event(ready.plugin._eventcb_enabled_modified, newvalue=False, oldvalue=True)
    assert ready.fake.sent == []
    ready.event(ready.plugin._eventcb_enabled_modified, newvalue=True, oldvalue=False)
    assert ready.fake.sent == [BLESS]


def test_gain_for_a_listed_spell_casts(ready: Env) -> None:
    ready.event(ready.plugin._eventcb_gain, sn=40, percent=60)
    assert ready.fake.sent == []
    ready.event(ready.plugin._eventcb_gain, sn=HASTE, percent=11)
    assert ready.fake.sent == [BLESS]


@pytest.mark.parametrize(
    "name", ["_eventcb_affoff", "_eventcb_affected_update", "_eventcb_uptodate"]
)
def test_refresh_events_cast(ready: Env, name: str) -> None:
    ready.event(getattr(ready.plugin, name), sn=BLESS)
    assert ready.fake.sent == [BLESS]


def test_a_missing_self_entry_does_not_raise(ready: Env) -> None:
    """Regression: the old plugin raised a KeyError for an sn with no self entry."""
    del ready.plugin.spellups["self"][BLESS]
    ready.plugin._phook_character_active()
    assert ready.fake.sent == [SANC]


def test_command_add(env: Env) -> None:
    result = env.command(env.plugin._command_add, spell=[])
    assert result.success is False
    result = env.command(env.plugin._command_add, spell=["bless", "fireball", "nothing"])
    assert result.success is True
    assert env.plugin.ups.order() == [BLESS]
    assert "not a spellup" in result.message[1]
    assert "does not exist" in result.message[2]
    result = env.command(env.plugin._command_add, spell=["bless"])
    assert "already activated" in result.message[0]
    result = env.command(env.plugin._command_add, spell=["fireball"], override=True)
    assert env.plugin.ups.order() == [BLESS, 40]
    result = env.command(env.plugin._command_add, spell=["20:0", "haste:x"])
    assert env.plugin.ups.order() == [SANC, BLESS, 40]
    assert "place" in result.message[1] or "number" in result.message[1]


def test_command_add_all_adds_practiced_spellups(env: Env) -> None:
    env.fake.skills[50]["spellup"] = True
    env.command(env.plugin._command_add, spell=["all"])
    assert env.plugin.ups.order() == [BLESS, SANC, HASTE]


def test_command_add_casts_and_saves(env: Env) -> None:
    env.command(env.plugin._command_add, spell=["bless", "haste"])
    assert env.fake.sent == [BLESS]
    saved = json.loads((env.home / SPELLUP_FILE).read_text(encoding="utf-8"))
    assert saved["sorder"] == [BLESS, HASTE]


def test_command_list(ready: Env) -> None:
    ready.fake.affected.add(BLESS)
    ready.fake.recblocked.add(SANC)
    ready.plugin.ups.set_enabled(HASTE, False)
    ready.plugin._waiting = BLESS
    result = ready.command(ready.plugin._command_list, match="")
    rows = result.message[2:]
    assert rows[0].split() == ["0", "-", "bless", ":", "A", "P"]
    assert rows[1].split() == ["1", "-", "sanctuary", ":", "B"]
    assert rows[2].split() == ["2", "-", "haste", ":", "D"]
    result = ready.command(ready.plugin._command_list, match="SANC")
    assert len(result.message) == 3


def test_command_list_empty_and_unknown_skill(env: Env) -> None:
    assert env.command(env.plugin._command_list, match="").message == ["There are no spellups"]
    env.plugin.ups.add(999)
    assert "please check the skills plugin" in env.command(env.plugin._command_list).message[2]


def test_command_rem(ready: Env) -> None:
    result = ready.command(ready.plugin._command_rem, spell=[])
    assert result.message == ["Please supply a spell/skill to remove"]
    ready.plugin._waiting = SANC
    result = ready.command(ready.plugin._command_rem, spell=["sanctuary", "haste", "nothing"])
    assert result.success is True
    assert ready.plugin.ups.order() == [BLESS]
    assert result.message[0] == "Removed sanctuary from spellups to self"
    assert result.message[1] == "Removed haste from spellups to self"
    assert "does not exist" in result.message[2]
    assert ready.state("_waiting") is None
    result = ready.command(ready.plugin._command_rem, spell=["haste"])
    assert "not in the spellups" in result.message[0]


def test_command_rem_all_returns_a_result_and_saves(ready: Env) -> None:
    """Regression: the old plugin returned None and never saved for ``rem all``."""
    ready.plugin._waiting = BLESS
    result = ready.command(ready.plugin._command_rem, spell=["all"])
    assert result is not None
    assert result.success is True
    assert result.message == ["All spellups to be cast on self cleared"]
    assert ready.plugin.ups.order() == []
    assert ready.state("_waiting") is None
    saved = json.loads((ready.home / SPELLUP_FILE).read_text(encoding="utf-8"))
    assert saved == {"sorder": [], "self": {}}


def test_command_en_and_dis(ready: Env) -> None:
    result = ready.command(ready.plugin._command_dis, spell=[])
    assert result.message == ["Please supply a spell/skill to disable"]
    result = ready.command(ready.plugin._command_en, spell=[])
    assert result.message == ["Please supply a spell/skill to enable"]
    result = ready.command(ready.plugin._command_dis, spell=["all"])
    assert result.message == ["All spellups disabled"]
    assert ready.fake.sent == []
    assert not any(ready.plugin.ups.is_enabled(sn) for sn in ready.plugin.ups.order())
    result = ready.command(ready.plugin._command_en, spell=["haste", "fireball", "nothing"])
    assert result.message == [
        "haste: enabled",
        "fireball: not in self spellup list",
        "nothing: could not find spell",
    ]
    assert ready.fake.sent == [HASTE]
    result = ready.command(ready.plugin._command_dis, spell=["haste"])
    assert result.message == ["haste: disabled"]
    result = ready.command(ready.plugin._command_en, spell=["all"])
    assert result.message == ["All spellups enabled"]
    saved = json.loads((ready.home / SPELLUP_FILE).read_text(encoding="utf-8"))
    assert all(entry["enabled"] for entry in saved["self"].values())


def test_command_check(ready: Env) -> None:
    lines = ready.command(ready.plugin._command_check).message
    assert len(lines) == 9
    ready.fake.up_to_date = False
    assert "False" in ready.command(ready.plugin._command_check).message[7]


def test_the_list_persists_across_instances(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    first = make_env(monkeypatch, tmp_path)
    first.add(BLESS, SANC)
    first.plugin.ups.set_enabled(SANC, False)
    first.plugin._phook_save()
    second = make_env(monkeypatch, tmp_path)
    assert second.plugin.ups.order() == [BLESS, SANC]
    assert second.plugin.ups.is_enabled(BLESS)
    assert not second.plugin.ups.is_enabled(SANC)


def test_an_old_file_is_normalized_and_saved(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    old = {
        "sorder": ["10", 20, 20],
        "self": {"10": {"enabled": False}, "99": {"enabled": True}},
        "oorder": [],
        "other": {},
    }
    (tmp_path / SPELLUP_FILE).write_text(json.dumps(old), encoding="utf-8")
    env = make_env(monkeypatch, tmp_path)
    assert env.plugin.ups.order() == [BLESS, SANC]
    assert not env.plugin.ups.is_enabled(BLESS)
    assert env.plugin.ups.is_enabled(SANC)
    saved = json.loads((tmp_path / SPELLUP_FILE).read_text(encoding="utf-8"))
    assert saved == {
        "sorder": [10, 20],
        "self": {"10": {"enabled": False}, "20": {"enabled": True}},
    }


def test_uninitialize_removes_the_timer(ready: Env) -> None:
    ready.plugin._phook_character_active()
    ready.plugin._phook_uninitialize()
    assert TIMER_NAME not in ready.fake.timers
    ready.plugin._phook_uninitialize()
