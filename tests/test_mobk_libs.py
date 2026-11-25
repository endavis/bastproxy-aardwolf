"""Tests for the pure helpers of the mobk plugin."""

import re

import pytest

from aardwolf.mobk.libs import (
    EVENTS,
    SUFFIX_KILL,
    TRIGGERS,
    add_to_damage,
    damage_default,
    new_kill,
    parse_gold,
    sum_xp,
    to_int,
    total_xp,
)

SPECS = {spec.name: spec for spec in TRIGGERS}

SAMPLES: dict[str, str] = {
    "mobk_xp": "You receive 123+45 experience points.",
    "mobk_rarexp": "You receive 50 'rare kill' experience bonus.",
    "mobk_blessxp": "You receive 20 bonus experience points from your daily blessing.",
    "mobk_bonusxp": "You receive 30 bonus experience points from the double event.",
    "mobk_xpptless": "That was a pointless no experience kill!",
    "mobk_switch": "You switch targets and direct your attacks at a rat!.",
    "mobk_flee": "You flee from combat!",
    "mobk_retreat": "You retreat from the combat!",
    "mobk_gold": "You get 1,234 gold coins from the corpse of a rat.",
    "mobk_splitgold": "Bob splits 100 gold coins. Your share is 50 gold.",
    "mobk_corpseget": "You get a sword from the corpse of a rat.",
    "mobk_sac": "Mocktar gives you 5 gold coins for the corpse of a rat.",
    "mobk_consume": "You bury your fangs deep into the corpse of a rat, drinking thirstily.",
    "mobk_trivia": "You killed a Triv bonus mob!! Triv point added.",
    "mobk_trivia2": "You killed a Trivia Point bonus mob!! Trivia point added.",
    "mobk_vorpal": "Deep magic stirs within your weapon. It seems to have a life of its own.",
    "mobk_assassin": "You assassinate a rat with cold efficiency.",
    "mobk_deathblow": "Your death blow CLEAVES a rat in two!",
    "mobk_slit": "You sneak behind a rat and slit its throat.",
    "mobk_disintegrate": "You have disintegrated a rat!",
    "mobk_banish": "You look at a rat very strangely.",
    "mobk_damage": "[3] Your slash hits a rat! [45]",
    "mobk_damage2": "Your slash hits a rat! [45]",
    "mobk_bsincombat": (
        "You spin around a rat, catching it off guard, and execute a vicious double backstab."
    ),
}


def test_every_trigger_has_a_sample() -> None:
    """The samples and the specs name the same triggers."""
    assert set(SAMPLES) == set(SPECS)


@pytest.mark.parametrize("name", sorted(SAMPLES))
def test_trigger_matches_its_sample(name: str) -> None:
    """Each regex matches its sample line."""
    assert re.match(SPECS[name].regex, SAMPLES[name])


def test_trigger_names_are_unique_and_prefixed() -> None:
    """Trigger names are global, so each carries the mobk_ prefix."""
    names = [spec.name for spec in TRIGGERS]
    assert len(names) == len(set(names))
    assert all(name.startswith("mobk_") for name in names)


def test_bonusxp_skips_the_blessing_line() -> None:
    """The lookahead keeps the blessing line out of the bonus trigger."""
    assert not re.match(SPECS["mobk_bonusxp"].regex, SAMPLES["mobk_blessxp"])
    assert not re.match(SPECS["mobk_blessxp"].regex, SAMPLES["mobk_bonusxp"])


def test_xp_groups() -> None:
    """The xp trigger gives the sum text and the don't group."""
    match = re.match(SPECS["mobk_xp"].regex, "You don't receive 12 experience points.")
    assert match
    assert match.group("xp") == "12"
    assert match.group("dont")
    match = re.match(SPECS["mobk_xp"].regex, "You receive 1 experience point.")
    assert match
    assert match.group("dont") is None


def test_event_describes_every_key() -> None:
    """The event describes each key of a new kill, and its text has no raw braces."""
    assert SUFFIX_KILL == "kill"
    info = EVENTS[SUFFIX_KILL]
    assert set(info["arg_descriptions"]) == set(new_kill())
    text = " ".join(info["description"]) + " ".join(info["arg_descriptions"].values())
    assert "{" not in text
    assert "}" not in text


def test_damage_default() -> None:
    """A default entry is all zero, and a new one each call."""
    assert damage_default() == {"hits": 0, "misses": 0, "damage": 0}
    assert damage_default() is not damage_default()


def test_add_to_damage_hit_and_accumulate() -> None:
    """A hit adds hits and damage, and the next hit of the type adds to them."""
    table: dict[str, dict[str, int]] = {}
    tdam = {"damtype": "slash", "damverb": "hits", "hits": 2, "damage": 30}
    assert add_to_damage(tdam, table) is table
    add_to_damage(tdam, table)
    assert table == {"slash": {"hits": 4, "misses": 0, "damage": 60}}


def test_add_to_damage_miss() -> None:
    """A miss adds its hits to the misses and no damage."""
    table: dict[str, dict[str, int]] = {}
    add_to_damage({"damtype": "slash", "damverb": "misses", "hits": 3, "damage": 0}, table)
    assert table == {"slash": {"hits": 0, "misses": 3, "damage": 0}}


def test_add_to_damage_unknown_type() -> None:
    """An empty damage type is Unknown."""
    table: dict[str, dict[str, int]] = {}
    add_to_damage({"damtype": "", "damverb": "hits", "hits": 1, "damage": 5}, table)
    assert list(table) == ["Unknown"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [("123", 123), ("123+45", 168), ("1+2+3", 6), ("abc", 0), ("1+x", 0), ("", 0)],
)
def test_sum_xp(text: str, expected: int) -> None:
    """The experience is the sum of its parts, 0 for bad input."""
    assert sum_xp(text) == expected


@pytest.mark.parametrize(("text", "expected"), [("1,234", 1234), ("5", 5), ("abc", None)])
def test_parse_gold(text: str, expected: int | None) -> None:
    """Commas are stripped, a non-number is None."""
    assert parse_gold(text) == expected


def test_to_int() -> None:
    """Numbers and numeric text convert, the rest is 0."""
    assert to_int("12") == 12
    assert to_int(None) == 0
    assert to_int("x") == 0
    assert to_int([1]) == 0


def test_new_kill() -> None:
    """A new kill has every key at its default, and no shared dicts."""
    kill = new_kill()
    assert kill["name"] == ""
    assert kill["room_id"] == -1
    assert kill["level"] == -1
    assert kill["damage"] == {}
    assert kill["immunities"] == {}
    for key in ("time", "starttime", "finishtime"):
        assert kill[key] is None
    assert "raised" not in kill
    assert new_kill()["damage"] is not kill["damage"]


def test_total_xp() -> None:
    """The total is the sum of the four experience keys."""
    kill = new_kill()
    kill.update({"xp": 100, "rarexp": 10, "bonusxp": 5, "blessingxp": 1})
    assert total_xp(kill) == 116
