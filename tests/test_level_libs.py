"""Tests for the pure helpers of the level plugin."""

import re
from typing import Any

import pytest

from aardwolf.level.libs import (
    EVENTS,
    PREFIX,
    STATS,
    TRIGGERS,
    WATCHES,
    bonus_stat_key,
    new_record,
    next_starttime,
    should_finish,
    to_int,
)

SPECS = {spec.name: spec for spec in TRIGGERS}

SAMPLES: dict[str, tuple[str, dict[str, str]]] = {
    "lvlpup": ("Congratulations, hero. You have increased your powers!", {}),
    "lvlpupbless": ("You gain a powerup.", {}),
    "lvllevel": ("You raise a level! You are now level 51.", {"level": "51"}),
    "lvlshloud": (
        "Congratulations! You are now a superhero! You receive 10 trains for superhero loud.",
        {"trains": "10"},
    ),
    "lvlsh": ("Congratulations! You are now a superhero!", {}),
    "lvlbless": ("You gain a level - you are now level 52.", {"level": "52"}),
    "lvlgains": (
        "You gain 30 hit points, 25 mana, 20 moves, 5 practices and 6 trains.",
        {"hp": "30", "mp": "25", "mv": "20", "pr": "5", "tr": "6"},
    ),
    "lvlblesstrain": ("You gain 1 extra train daily blessing bonus.", {"tr": "1"}),
    "lvlpupgains": ("You gain 10 trains.", {"tr": "10"}),
    "lvlbattlelearntrains": (
        "You gain 2 additional training sessions from your enhanced battle learning.",
        {"tr": "2"},
    ),
    "lvlbonustrains": ("Lucky! You gain an extra 2 training sessions!", {"tr": "2"}),
    "lvlbonusstat": ("You gain a bonus Strength point!", {"stat": "Strength"}),
    "lvlshbadstar": ("*" * 71, {}),
    "lvlshbad": (
        "Use either: 'superhero loud'   - 30 mins of double xp, 1000qp and 500,000 gold",
        {"mins": "30", "qp": "1000", "gold": "500,000"},
    ),
    "lvlshnogold": ("You must be carrying at least 500,000 gold coins.", {}),
    "lvlshnoqp": ("You must have at least 1000 quest points.", {}),
    "lvlshnodbl": ("You cannot superhero loud until double exp is over.", {}),
    "lvlshnot200": ("You have to be level 200 to superhero.", {}),
    "lvlpreremort": ("You are now flagged as remorting.", {}),
    "lvlremortcomp": ("* Remort transformation complete!", {}),
    "lvltier": ("## You have already remorted the max number of times.", {}),
}


def test_every_trigger_has_a_sample() -> None:
    """The samples cover every trigger."""
    assert set(SAMPLES) == set(SPECS)


@pytest.mark.parametrize("name", sorted(SAMPLES))
def test_regex_matches_its_sample(name: str) -> None:
    """Each regex matches its sample line and captures the expected groups."""
    line, groups = SAMPLES[name]
    match = re.match(SPECS[name].regex, line)
    assert match is not None
    assert match.groupdict() == groups


def test_superhero_loud_captures_the_trains() -> None:
    """Fix 1: the trains group takes a number, and an empty one does not match."""
    regex = SPECS["lvlshloud"].regex
    match = re.match(regex, SAMPLES["lvlshloud"][0])
    assert match is not None
    assert match.group("trains") == "10"
    assert re.match(regex, "Congratulations! You are now a superhero! You receive  trains.") is None


def test_star_line_is_exactly_71_stars() -> None:
    """The superhero failure star line is 71 stars."""
    regex = SPECS["lvlshbadstar"].regex
    assert re.match(regex, "*" * 71)
    assert not re.match(regex, "*" * 70)
    assert not re.match(regex, "*" * 72)


def test_argtypes_name_the_regex_groups() -> None:
    """Fix 2: every argtype key is a group of its regex, so lvlgains converts mana."""
    for spec in TRIGGERS:
        groups = set(re.compile(spec.regex).groupindex)
        assert set(spec.argtypes or {}) <= groups, spec.name
    assert set(SPECS["lvlgains"].argtypes or {}) == {"hp", "mp", "mv", "pr", "tr"}


def test_trigger_states_and_groups() -> None:
    """Gain triggers start disabled in linfo, failure ones in superhero, remort ones enabled."""
    for name in ("lvlgains", "lvlblesstrain", "lvlpupgains", "lvlbonusstat"):
        assert SPECS[name].group == "linfo"
        assert not SPECS[name].enabled
    for name in ("lvlshbadstar", "lvlshbad", "lvlshnot200"):
        assert SPECS[name].group == "superhero"
        assert not SPECS[name].enabled
    for name in ("lvlpreremort", "lvlremortcomp", "lvltier"):
        assert SPECS[name].group == "remort"
        assert SPECS[name].enabled
    for name in ("lvlsh", "lvlshloud", "lvlpup", "lvllevel"):
        assert SPECS[name].group is None
        assert SPECS[name].enabled


def test_watches() -> None:
    """The five superhero commands are watched under prefixed names."""
    assert set(WATCHES) == {
        "level_sh",
        "level_shsilent",
        "level_shloud",
        "level_shconfirm",
        "level_shloudconfirm",
    }
    assert re.match(WATCHES["level_shloudconfirm"], "superhero loud confirm")
    assert not re.match(WATCHES["level_shloud"], "superhero loud confirm")


def test_events_have_no_raw_braces() -> None:
    """Descriptions go through str.format, so they hold no braces."""
    assert all(name.startswith(PREFIX) for name in EVENTS)
    for info in EVENTS.values():
        text = " ".join(info["description"]) + " ".join(info["arg_descriptions"].values())
        assert "{" not in text
        assert "}" not in text


@pytest.mark.parametrize(
    ("trains", "remortcomp", "tiering", "expected"),
    [
        (0, False, False, False),
        (1, False, False, True),
        (0, True, False, True),
        (0, False, True, True),
        (5, True, True, True),
    ],
)
def test_should_finish(trains: int, remortcomp: bool, tiering: bool, expected: bool) -> None:
    """Fix 3: finish when trains were gained, or when a remort or a tier is completing."""
    assert should_finish(trains, remortcomp, tiering) is expected


@pytest.mark.parametrize(
    ("old", "expected"),
    [
        ({"finishtime": 500.0, "starttime": 100.0}, 500.0),
        ({"finishtime": -1, "starttime": 100.0}, 100.0),
        ({"starttime": 100.0}, 100.0),
        ({"finishtime": 0, "starttime": 0}, 999.0),
        ({}, 999.0),
        ({"finishtime": "x", "starttime": None}, 999.0),
    ],
)
def test_next_starttime(old: dict[str, Any], expected: float) -> None:
    """The start is the last finish, else the last start, else now."""
    assert next_starttime(old, 999.0) == expected


@pytest.mark.parametrize(
    ("stat", "key"),
    [
        ("Strength", "str"),
        ("Intelligence", "int"),
        ("Wisdom", "wis"),
        ("Dexterity", "dex"),
        ("Constitution", "con"),
        ("Luck", "luc"),
        ("Charisma", None),
        ("", None),
    ],
)
def test_bonus_stat_key(stat: str, key: str | None) -> None:
    """A bonus stat maps to its record key, and anything else to None."""
    assert bonus_stat_key(stat) == key


@pytest.mark.parametrize(
    ("value", "expected"),
    [("5", 5), (7, 7), ("201", 201), (None, 0), ("", 0), ("x", 0), ([], 0), (float("inf"), 0)],
)
def test_to_int(value: object, expected: int) -> None:
    """A number or numeric string converts and anything else is 0."""
    assert to_int(value) == expected


def test_new_record_keys() -> None:
    """A new record has every gain key at 0 and no finish time."""
    record = new_record("level", 51, 300, 12.5)
    assert set(record) == {
        "type",
        "level",
        "totallevels",
        "starttime",
        "finishtime",
        "hp",
        "mp",
        "mv",
        "pracs",
        "trains",
        "bonustrains",
        "blessingtrains",
        "battlelearntrains",
        *STATS,
    }
    assert record["type"] == "level"
    assert record["level"] == 51
    assert record["totallevels"] == 300
    assert record["starttime"] == 12.5
    assert record["finishtime"] == -1
    assert all(record[key] == 0 for key in ("hp", "trains", *STATS))
