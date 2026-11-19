"""Tests for the aardu helper library."""

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from aardwolf.libs.aardu import (
    CLASSABB,
    CLASSABBREV,
    DAMAGES,
    REWARDTABLE,
    actual_level,
    convert_level,
    parse_damage_line,
)

TIER = 1407
MAX_TOTAL = TIER * 60


def test_class_tables_are_inverses() -> None:
    """CLASSABBREV inverts CLASSABB."""
    assert len(CLASSABB) == 7
    assert {v: k for k, v in CLASSABB.items()} == CLASSABBREV


def test_reward_table() -> None:
    """The reward table maps names to abbreviations."""
    assert REWARDTABLE["quest"] == "qp"
    assert len(REWARDTABLE) == 5


def test_damages_table() -> None:
    """The damage table keeps its size and order."""
    assert len(DAMAGES) == 57
    assert DAMAGES[0] == "misses"
    assert DAMAGES[-1] == "pimpslaps"


def test_actual_level_without_redos() -> None:
    """Total level for a plain tier."""
    assert actual_level(1, 1, 0, 0) == 1
    assert actual_level(201, 7, 0, 0) == TIER
    assert actual_level(5, 2, 1, 0) == TIER + 201 + 5


def test_actual_level_with_redos() -> None:
    """Redos count as extra tiers."""
    assert actual_level(1, 1, 9, 2) == 11 * TIER + 1


@pytest.mark.parametrize(
    ("total", "expected"),
    [
        (1, (0, 0, 1, 1)),
        (201, (0, 0, 1, 201)),
        (202, (0, 0, 2, 1)),
        (402, (0, 0, 2, 201)),
        (403, (0, 0, 3, 1)),
        (TIER, (0, 0, 7, 201)),
        (TIER + 1, (1, 0, 1, 1)),
        (10 * TIER, (9, 0, 7, 201)),
        (10 * TIER + 1, (9, 1, 1, 1)),
        (11 * TIER + 5, (9, 2, 1, 5)),
    ],
)
def test_convert_level_examples(total: int, expected: tuple[int, int, int, int]) -> None:
    """Boundaries, level 201, the old divisor bug and the tier cap."""
    tier, redos, remort, level = expected
    assert convert_level(total) == {
        "tier": tier,
        "redos": redos,
        "remort": remort,
        "level": level,
    }


def test_convert_level_regressions() -> None:
    """The old divisor of 202 got these wrong."""
    assert convert_level(403)["remort"] == 3
    assert convert_level(1207)["remort"] == 7


@pytest.mark.parametrize("total", [0, -1, -500])
def test_convert_level_below_one(total: int) -> None:
    """Totals below 1 give -1 everywhere."""
    assert convert_level(total) == {"tier": -1, "redos": -1, "remort": -1, "level": -1}


def test_parse_damage_line_decorated_with_counts() -> None:
    """Hits, damage, a decorated verb and the enemy."""
    assert parse_damage_line("[3] Your fire <-*-> RAVAGES <-*-> a goblin! [123]") == {
        "damage": 123,
        "hits": 3,
        "damtype": "fire",
        "damverb": "<-*-> RAVAGES <-*->",
        "enemy": "a goblin",
    }


def test_parse_damage_line_plain() -> None:
    """A plain line without counts."""
    assert parse_damage_line("Your slash hits a goblin.") == {
        "damage": 0,
        "hits": 1,
        "damtype": "slash",
        "damverb": "hits",
        "enemy": "a goblin",
    }


def test_parse_damage_line_with_counts() -> None:
    """Hits prefix and damage suffix."""
    assert parse_damage_line("[2] Your slash hits a goblin! [45]") == {
        "damage": 45,
        "hits": 2,
        "damtype": "slash",
        "damverb": "hits",
        "enemy": "a goblin",
    }


def test_parse_damage_line_phrase_verb() -> None:
    """A multi-word verb."""
    result = parse_damage_line("Your blast does UNSPEAKABLE things to a rat!")
    assert result["damverb"] == "does UNSPEAKABLE things to"
    assert result["damtype"] == "blast"
    assert result["enemy"] == "a rat"


def test_parse_damage_line_decorated_verb() -> None:
    """A decorated verb."""
    result = parse_damage_line("Your fire -= DEMOLISHES =- a rat!")
    assert result["damverb"] == "-= DEMOLISHES =-"
    assert result["enemy"] == "a rat"


def test_parse_damage_line_mob_attack() -> None:
    """A mob attack has no leading Your."""
    result = parse_damage_line("A goblin's bite scratches you.")
    assert result["damverb"] == "scratches"
    assert result["damtype"] == "A goblin's bite"
    assert result["enemy"] == "you"


@pytest.mark.parametrize("line", ["", "[]", "[3]", "You die.", "hello world"])
def test_parse_damage_line_degenerate(line: str) -> None:
    """Non-damage and degenerate lines never raise and return every key."""
    result = parse_damage_line(line)
    assert set(result) == {"damage", "hits", "damtype", "damverb", "enemy"}
    assert result["damverb"] == ""
    assert result["damtype"] == ""
    assert result["enemy"] == ""


@given(st.integers(min_value=1, max_value=MAX_TOTAL))
@example(403)
@example(1207)
@example(TIER)
@example(10 * TIER)
def test_total_round_trip(total: int) -> None:
    """Total to parts to total gives the total back."""
    parts = convert_level(total)
    assert 1 <= parts["level"] <= 201
    assert 1 <= parts["remort"] <= 7
    assert 0 <= parts["tier"] <= 9
    assert actual_level(parts["level"], parts["remort"], parts["tier"], parts["redos"]) == total


@given(
    tier=st.integers(min_value=0, max_value=9),
    remort=st.integers(min_value=1, max_value=7),
    level=st.integers(min_value=1, max_value=201),
    redos=st.integers(min_value=0, max_value=50),
)
def test_parts_round_trip(tier: int, remort: int, level: int, redos: int) -> None:
    """Canonical parts to total to parts give the parts back."""
    if tier != 9:
        redos = 0
    total = actual_level(level, remort, tier, redos)
    assert convert_level(total) == {
        "tier": tier,
        "redos": redos,
        "remort": remort,
        "level": level,
    }


@given(st.integers(max_value=0))
def test_below_one_is_all_minus_one(total: int) -> None:
    """Any total below 1 gives -1s."""
    assert set(convert_level(total).values()) == {-1}
