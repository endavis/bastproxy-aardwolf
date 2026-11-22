"""Tests for the Aardwolf mobk plugin, with a stubbed API that drives its triggers."""

import logging
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock

import pytest
from statdb_support import make_db

import aardwolf
from aardwolf.libs.aardu import actual_level
from aardwolf.mobk.libs import EQ_WORN_API, EVENT_KILL, EVENTS, TRIGGERS

if TYPE_CHECKING:
    from aardwolf.mobk.plugin._mobk import MobkPlugin

PLUGIN_ID = "plugins.aardwolf.mobk"
GMCP: dict[str, Any] = {
    "char.status.level": 50,
    "char.base.remorts": 1,
    "char.base.tier": 0,
    "char.base.redos": 0,
    "room.info.num": 4321,
}
XP = "You receive 100 experience points."
SAC = "Mocktar gives you 5 gold coins for the corpse of A rat."
GOLD = "You get 1,234 gold coins from the corpse of A rat."
HIT = "[2] Your slash hits A rat! [30]"


class FakeApi:
    """A stand-in for the bastproxy API that records the calls and drives the triggers."""

    def __init__(self) -> None:
        self.gmcp: dict[str, Any] = dict(GMCP)
        self.events_added: dict[str, dict[str, Any]] = {}
        self.raised: list[tuple[str, dict[str, Any]]] = []
        self.triggers: dict[str, str] = {}
        self.argtypes: dict[str, dict[str, Callable[[str], Any]]] = {}
        self.trigger_cbs: dict[str, list[Callable[..., Any]]] = {}
        self.add_ok = True
        self.record: dict[str, Any] = {}
        self.eq_items: dict[int, Any] | None = None
        self.eq_calls: list[int] = []
        self.table: dict[str, Callable[..., Any]] = {
            "plugins.core.events:event.add": self._event_add,
            "plugins.core.events:event.raise": self._event_raise,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
            "plugins.core.colors:colorcode.strip": lambda text: re.sub(r"@[a-zA-Z]", "", text),
            "libs.net.protocols:gmcp.value.get": self.gmcp.get,
            "libs.api:api.exists": lambda name: name == EQ_WORN_API and self.eq_items is not None,
            EQ_WORN_API: self._eq_worn,
        }

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name; an unknown name is a KeyError."""
        return self.table[name]

    def _eq_worn(self, slot: int) -> object:
        self.eq_calls.append(slot)
        assert self.eq_items is not None
        return self.eq_items.get(slot)

    def _event_add(self, name: str, created_by: str, **kwargs: object) -> None:
        self.events_added[name] = kwargs

    def _event_raise(self, name: str, event_args: dict[str, Any] | None = None) -> None:
        self.raised.append((name, event_args or {}))

    def _trigger_add(self, name: str, regex: str, **kwargs: object) -> SimpleNamespace:
        self.triggers[name] = regex
        self.argtypes[name] = cast("dict[str, Callable[[str], Any]]", kwargs.get("argtypes") or {})
        self.trigger_cbs.setdefault(name, [])
        return SimpleNamespace(success=self.add_ok, trigger=SimpleNamespace(trigger_id=name))

    def _trigger_register(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        assert trigger_id in self.trigger_cbs, f"unknown trigger {trigger_id}"
        self.trigger_cbs[trigger_id].append(func)
        return True

    def feed(self, *lines: str) -> None:
        """Run each line through the triggers, as the triggers plugin does."""
        for line in lines:
            for name, regex in list(self.triggers.items()):
                match = re.match(regex, line)
                if not match:
                    continue
                groups = match.groupdict()
                for arg, argtype in self.argtypes[name].items():
                    groups[arg] = argtype(groups[arg])
                self.record = {"matches": groups, "line": SimpleNamespace(noansi=line)}
                for func in list(self.trigger_cbs[name]):
                    func()

    def kills(self) -> list[dict[str, Any]]:
        """The payloads of the raised kills."""
        assert all(name == EVENT_KILL for name, _ in self.raised)
        return [payload for _, payload in self.raised]


class Env:
    """The plugin under test with its fake API and clock."""

    def __init__(self, plugin: "MobkPlugin", fake: FakeApi) -> None:
        self.plugin = plugin
        self.fake = fake
        self.clock = {"now": 1000.0}

    def gmcp_enemy(self, enemy: str) -> None:
        """A GMCP char.status message with an enemy."""
        self.fake.gmcp["char.status.enemy"] = enemy
        self.plugin._eventcb_char_status()

    def kill(self) -> None:
        """An ordinary kill: damage, xp, gold and the sacrifice."""
        self.fake.feed(HIT, XP, GOLD, SAC)


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build a MobkPlugin with a fake API and load it."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from aardwolf.mobk.plugin import _mobk

    clock = {"now": 1000.0}
    monkeypatch.setattr(_mobk.MobkPlugin, "_now", staticmethod(lambda: clock["now"]))
    fake = FakeApi()
    plugin = _mobk.MobkPlugin.__new__(_mobk.MobkPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    plugin._phook_initialize()
    result = Env(plugin, fake)
    result.clock = clock
    yield result


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin, with its dependencies, without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.mobk" in {p["plugin_id"] for p in result.plugins}
    from aardwolf import mobk

    for dependency in (
        "plugins.aardwolf.connect",
        "plugins.core.triggers",
        "plugins.core.events",
        "plugins.core.colors",
    ):
        assert dependency in mobk.PLUGIN_DEPENDENCIES


def test_after_load(env: Env) -> None:
    """after_load adds the event with every key described, and every trigger with a callback."""
    fake = env.fake
    assert list(fake.events_added) == [EVENT_KILL]
    assert set(fake.events_added[EVENT_KILL]["arg_descriptions"]) == set(
        EVENTS[EVENT_KILL]["arg_descriptions"]
    )
    assert set(fake.triggers) == {spec.name for spec in TRIGGERS}
    assert all(fake.trigger_cbs[name] for name in fake.triggers)
    assert len(fake.trigger_cbs["mobk_slit"]) == 1


def test_failed_trigger_add_registers_nothing(env: Env, caplog: pytest.LogCaptureFixture) -> None:
    """A failed trigger.add logs an error and registers no callback."""
    fake = env.fake
    fake.add_ok = False
    fake.trigger_cbs.clear()
    fake.triggers.clear()
    with caplog.at_level(logging.ERROR):
        env.plugin._phook_initialize()
    assert all(not cbs for cbs in fake.trigger_cbs.values())
    assert "could not add the mobk_xp trigger" in caplog.text


def test_ordinary_kill(env: Env) -> None:
    """A kill raises once, with the xp, gold, name, room, level and times."""
    fake = env.fake
    env.gmcp_enemy("@RA rat@w")
    fake.feed(HIT, "[1] Your slash misses A rat. [0]", HIT)
    env.clock["now"] = 1010.0
    fake.feed(XP, GOLD, SAC)
    assert len(fake.kills()) == 1
    kill = fake.kills()[0]
    assert kill["name"] == "A rat"
    assert (kill["xp"], kill["gold"], kill["totalxp"]) == (100, 1234, 100)
    assert kill["room_id"] == 4321
    assert kill["level"] == actual_level(50, 1, 0, 0)
    assert kill["starttime"] == 1000.0
    assert kill["finishtime"] == 1010.0
    assert kill["time"] == 1010.0
    assert kill["damage"]["slash"] == {"hits": 4, "misses": 1, "damage": 60}


def test_summed_experience(env: Env) -> None:
    """123+45 is 168, not the last term and not dropped (old bug)."""
    env.fake.feed(
        "You receive 123+45 experience points.",
        GOLD,
        SAC,
    )
    assert env.fake.kills()[0]["xp"] == 168


def test_bonus_experience(env: Env) -> None:
    """Rare, bonus and blessing experience go to their own keys and add up."""
    fake = env.fake
    fake.feed(
        XP,
        "You receive 50 'rare kill' experience bonus.",
        "You receive 20 bonus experience points from your daily blessing.",
        "You receive 30 bonus experience points from the double event.",
        GOLD,
        SAC,
    )
    kill = fake.kills()[0]
    assert (kill["rarexp"], kill["blessingxp"], kill["bonusxp"]) == (50, 20, 30)
    assert kill["totalxp"] == 200


def test_blessing_line_is_not_a_bonus(env: Env) -> None:
    """The blessing line sets blessingxp only."""
    env.fake.feed(XP, "You receive 20 bonus experience points from your daily blessing.", GOLD, SAC)
    kill = env.fake.kills()[0]
    assert kill["blessingxp"] == 20
    assert kill["bonusxp"] == 0


def test_no_experience(env: Env) -> None:
    """A don't receive line sets noexp, and a pointless kill has xp 0 and still raises."""
    env.fake.feed("You don't receive 100 experience points.", GOLD, SAC)
    assert env.fake.kills()[0]["noexp"] == 1
    env.fake.feed("That was a pointless no experience kill!", GOLD, SAC)
    kill = env.fake.kills()[1]
    assert kill["xp"] == 0
    assert kill["noexp"] == 0


@pytest.mark.parametrize(
    ("line", "key"),
    [
        ("Deep magic stirs within your weapon. It seems to have a life of its own.", "vorpal"),
        ("You assassinate A rat with cold efficiency.", "assassinate"),
        ("Your death blow CLEAVES A rat in two!", "deathblow"),
    ],
)
def test_special_kill_flags(env: Env, line: str, key: str) -> None:
    """A vorpal, assassination or death blow sets its flag, and the sacrifice raises it."""
    env.fake.feed(line, XP, GOLD, SAC)
    kill = env.fake.kills()[0]
    assert kill[key] == 1
    assert kill["name"] == "A rat"


@pytest.mark.parametrize(
    ("line", "key"),
    [
        ("You sneak behind A rat and slit its throat.", "slit"),
        ("You have disintegrated A rat!", "disintegrate"),
        ("You look at A rat very strangely.", "banishment"),
    ],
)
def test_finishers_raise_at_once(env: Env, line: str, key: str) -> None:
    """A slit, disintegration or banishment raises at once, with its flag and name."""
    env.fake.feed(XP, line)
    assert len(env.fake.kills()) == 1
    assert env.fake.kills()[0][key] == 1
    assert env.fake.kills()[0]["name"] == "A rat"
    env.fake.feed(SAC)
    assert len(env.fake.kills()) == 1


def test_raised_once_per_kill(env: Env) -> None:
    """A second sacrifice, and a sacrifice with no xp line, raise nothing."""
    env.kill()
    env.fake.feed(SAC)
    assert len(env.fake.kills()) == 1
    env.fake.feed(HIT, SAC)
    assert len(env.fake.kills()) == 1


def test_consume(env: Env) -> None:
    """Consuming the corpse raises like a sacrifice."""
    env.fake.feed(HIT, XP, "You bury your fangs deep into the corpse of A rat, drinking thirstily.")
    assert len(env.fake.kills()) == 1


def test_flee_and_retreat(env: Env) -> None:
    """Fleeing or retreating clears the name and damage, so a later sacrifice raises nothing."""
    for line in ("You flee from combat!", "You retreat from the combat!"):
        env.fake.feed(HIT, line, SAC)
        assert env.plugin.kill["name"] == ""
        assert env.plugin.kill["damage"] == {}
    assert env.fake.kills() == []


def test_switch_targets(env: Env) -> None:
    """Switching sets the new name and resets the damage."""
    env.fake.feed(HIT, "You switch targets and direct your attacks at A bat!.")
    assert env.plugin.kill["name"] == "A bat"
    assert env.plugin.kill["damage"] == {}
    assert env.plugin.kill["starttime"] is None


def test_damage_cache(env: Env) -> None:
    """Damage to another enemy is cached, and becomes the damage after a switch."""
    plugin = env.plugin
    env.fake.feed("You switch targets and direct your attacks at A rat!.", HIT)
    env.fake.feed("[1] Your slash hits A bat! [10]")
    assert plugin.mobdamcache == {"A bat": {"slash": {"hits": 1, "misses": 0, "damage": 10}}}
    assert plugin.kill["damage"]["slash"]["damage"] == 30
    env.fake.feed("You switch targets and direct your attacks at A bat!.")
    env.fake.feed("[1] Your slash hits A bat! [5]")
    assert plugin.mobdamcache == {}
    assert plugin.kill["damage"]["slash"] == {"hits": 2, "misses": 0, "damage": 15}


def test_damage_sets_the_name(env: Env) -> None:
    """A damage line with no name set takes the enemy from the line."""
    env.fake.feed("Your slash misses A rat. [0]")
    assert env.plugin.kill["name"] == "A rat"
    assert env.plugin.kill["damage"]["slash"]["misses"] == 1


def test_backstab(env: Env) -> None:
    """An in-combat backstab marks the damage."""
    env.fake.feed(
        "You spin around A rat, catching it off guard, and execute a vicious double backstab."
    )
    assert env.plugin.kill["damage"]["backstab"]["incombat"] is True
    env.fake.feed(
        "You spin around A rat, catching it off guard, and execute a vicious double backstab."
    )
    assert env.plugin.kill["damage"]["backstab"]["hits"] == 0


def test_gold(env: Env, monkeypatch: pytest.MonkeyPatch) -> None:
    """Split gold sets gold, bad gold keeps the old value, and corpse gold sets the name."""
    plugin = env.plugin
    env.fake.feed("Bob splits 100 gold coins. Your share is 50 gold.")
    assert plugin.kill["gold"] == 50
    assert plugin.kill["name"] == ""
    from aardwolf.mobk.plugin import _mobk

    log = MagicMock()
    monkeypatch.setattr(_mobk, "log_to", log)
    env.fake.feed("You get many gold coins from the corpse of A rat.")
    assert plugin.kill["gold"] == 50
    assert all(call.args[:2] == ([PLUGIN_ID], logging.DEBUG) for call in log.call_args_list)
    assert any("invalid gold" in call.args[2] for call in log.call_args_list)
    assert plugin.kill["name"] == "A rat"
    env.fake.feed("You get 7 gold coins from the corpse of A bat.")
    assert plugin.kill["gold"] == 7
    assert plugin.kill["name"] == "A rat"


def test_corpse_get_changes_nothing(env: Env) -> None:
    """Taking an item from a corpse is only logged."""
    env.fake.feed("You get a sword from the corpse of A rat.")
    assert env.plugin.kill["name"] == ""
    assert env.fake.kills() == []


@pytest.mark.parametrize(
    "line",
    [
        "You killed a Triv bonus mob!! Triv point added.",
        "You killed a Trivia Point bonus mob!! Trivia point added.",
    ],
)
def test_trivia(env: Env, line: str) -> None:
    """Either trivia line sets tp."""
    env.fake.feed(line, XP, GOLD, SAC)
    assert env.fake.kills()[0]["tp"] == 1


def test_gmcp_enemy(env: Env) -> None:
    """GMCP sets the name when none is set, ignores an empty enemy, never overrides."""
    env.gmcp_enemy("")
    assert env.plugin.kill["name"] == ""
    env.gmcp_enemy("@RA rat@w")
    assert env.plugin.kill["name"] == "A rat"
    env.gmcp_enemy("@RA bat@w")
    assert env.plugin.kill["name"] == "A rat"


def test_no_eq_plugin(env: Env) -> None:
    """With no eq API, the weapons are empty and the API is never called."""
    env.kill()
    kill = env.fake.kills()[0]
    assert (kill["wielded_weapon"], kill["second_weapon"]) == ("", "")
    assert env.fake.eq_calls == []


def test_eq_plugin(env: Env) -> None:
    """With an eq API, the serials of slots 24 and 25 are used, and a missing item is empty."""
    env.fake.eq_items = {24: SimpleNamespace(serial="111"), 25: {"serial": 222}}
    env.kill()
    env.fake.eq_items = {24: SimpleNamespace(serial="333")}
    env.kill()
    first, second = env.fake.kills()
    assert (first["wielded_weapon"], first["second_weapon"]) == ("111", "222")
    assert (second["wielded_weapon"], second["second_weapon"]) == ("333", "")
    assert env.fake.eq_calls == [24, 25, 24, 25]


def test_missing_room(env: Env) -> None:
    """With no GMCP room, the room is -1."""
    del env.fake.gmcp["room.info.num"]
    env.kill()
    assert env.fake.kills()[0]["room_id"] == -1


def test_room_zero(env: Env) -> None:
    """Room 0 is a room, not a missing one."""
    env.fake.gmcp["room.info.num"] = 0
    env.kill()
    assert env.fake.kills()[0]["room_id"] == 0


def test_payload_is_a_copy(env: Env) -> None:
    """Changing the payload leaves the next kill alone, and no old keys are in it."""
    env.kill()
    payload = env.fake.kills()[0]
    payload["damage"]["slash"]["hits"] = -1
    payload["xp"] = -1
    env.kill()
    assert env.fake.kills()[1]["xp"] == 100
    assert env.fake.kills()[1]["damage"]["slash"]["hits"] == 2
    assert not {"raised", "instatext", "instaback"} & set(payload)


def test_unknown_name(env: Env) -> None:
    """A kill with no name raised by a finisher says Unknown."""
    env.plugin._pending = True
    env.plugin._raise_kill()
    assert env.fake.kills()[0]["name"] == "Unknown"


def test_payload_is_saved_by_statdb(env: Env, tmp_path: Path) -> None:
    """The mobk_kill payload feeds statdb's save_mobkill."""
    from aardwolf.statdb.libs import StatStore

    env.kill()
    database = make_db(tmp_path / "db")
    try:
        store = StatStore(database)
        store.save_mobkill(env.fake.kills()[0])
        row = database.select("SELECT * FROM mobkills")[0]
        assert row["name"] == "A rat"
        assert row["xp"] == 100
        assert row["gold"] == 1234
        assert row["room_id"] == 4321
        assert row["totalxp"] == 100
    finally:
        database.close()
