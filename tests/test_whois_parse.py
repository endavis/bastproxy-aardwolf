"""Tests for the pure whois helpers."""

import re

import pytest

from aardwolf._libs.aardu import actual_level
from aardwolf.whois.libs import (
    CLASSES_REGEX,
    END_REGEX,
    HEADER_REGEX,
    POWERUP_REGEX,
    STAT1_REGEX,
    STAT2_REGEX,
    STAT3_REGEX,
    WHOIS_COMMAND_REGEX,
    header_values,
    multiclass_classes,
    single_class,
    stat_values,
    total_levels,
)

HEADER = "[ 201 Hero ]  Bast the Tester (Male Human)"
MULTI = "[Multiclass Player: Mage/Thief/Ranger ]"
STAT1 = "Quests Complete   : [ 12 ]"
STAT2 = "Campaigns Fld   : [ 3 ]   Monsters Killed   : [ 456 ]"
STAT3 = "Aaa   : [ 1 ]   Bbb   : [ 2 ]   Ccc   : [ 3 ]"
POWERUP = "Powerups Taken   : [ 5 ]   Powerups   : [ 3 ] [ 2 ]"


def groups(regex: str, line: str) -> dict[str, str | None]:
    """Return the groups of a full match."""
    match = re.match(regex, line)
    assert match
    return match.groupdict()


def test_command_regex() -> None:
    """The command regex matches whois and whoi only."""
    assert re.match(WHOIS_COMMAND_REGEX, "whois")
    assert re.match(WHOIS_COMMAND_REGEX, "whoi")
    assert not re.match(WHOIS_COMMAND_REGEX, "whois bob")


def test_header_regex_gives_sex() -> None:
    """The header gives the sex."""
    assert groups(HEADER_REGEX, HEADER)["sex"] == "Male"
    assert not re.match(HEADER_REGEX, STAT1)


def test_classes_regex() -> None:
    """The multiclass line gives the class text."""
    assert groups(CLASSES_REGEX, MULTI)["classes"] == "Mage/Thief/Ranger"
    assert not re.match(CLASSES_REGEX, HEADER)


def test_stat_regexes_match_only_their_line() -> None:
    """A line matches the regex for its number of pairs and no other."""
    assert re.match(STAT1_REGEX, STAT1)
    assert not re.match(STAT2_REGEX, STAT1)
    assert re.match(STAT2_REGEX, STAT2)
    assert not re.match(STAT1_REGEX, STAT2)
    assert re.match(STAT3_REGEX, STAT3)
    assert not re.match(STAT2_REGEX, STAT3)
    assert not re.match(STAT1_REGEX, STAT3)


def test_powerup_regex() -> None:
    """The power-up line matches its own regex and not the two-pair regex."""
    assert re.match(POWERUP_REGEX, POWERUP)
    assert not re.match(STAT2_REGEX, POWERUP)
    assert not re.match(STAT3_REGEX, POWERUP)
    assert not re.match(POWERUP_REGEX, STAT2)


@pytest.mark.parametrize(("count", "matches"), [(73, False), (74, True), (75, False)])
def test_end_regex_is_exactly_74_dashes(count: int, matches: bool) -> None:
    """The end line is 74 dashes."""
    assert bool(re.match(END_REGEX, "-" * count)) is matches


def test_stat_values_one_two_and_three_pairs() -> None:
    """Each pair becomes a lower-case key without spaces, with the value stripped."""
    assert stat_values(groups(STAT1_REGEX, STAT1)) == {"questscomplete": "12"}
    assert stat_values(groups(STAT2_REGEX, STAT2)) == {"campaignsfld": "3", "monsterskilled": "456"}
    assert stat_values(groups(STAT3_REGEX, STAT3)) == {"aaa": "1", "bbb": "2", "ccc": "3"}


def test_stat_values_skips_an_empty_name_and_none_groups() -> None:
    """An empty label and an unmatched group add nothing."""
    assert stat_values({"name1": "  ", "val1": "4", "name2": None, "val2": None}) == {}
    assert stat_values({}) == {}


def test_stat_values_powerups() -> None:
    """The power-up line gives the two counts and its own stat."""
    assert stat_values(groups(POWERUP_REGEX, POWERUP)) == {
        "powerupstaken": "5",
        "powerupsall": "3",
        "powerupsmort": "2",
    }


def test_multiclass_classes() -> None:
    """Each full name becomes an abbreviation at its remort; an unknown name passes through."""
    assert multiclass_classes("Mage/Thief/Ranger") == [
        {"remort": 1, "class": "mag"},
        {"remort": 2, "class": "thi"},
        {"remort": 3, "class": "ran"},
    ]
    assert multiclass_classes("Mage/Bard") == [
        {"remort": 1, "class": "mag"},
        {"remort": 2, "class": "bard"},
    ]


def test_single_class() -> None:
    """One class is remort 1; nothing gives an empty list."""
    assert single_class("Mage") == [{"remort": 1, "class": "mag"}]
    assert single_class(None) == []
    assert single_class("") == []


GMCP = {
    "char.base.name": "Bast",
    "char.status.level": 50,
    "char.base.tier": 2,
    "char.base.redos": "1",
    "char.base.race": "Human",
    "char.base.subclass": "Sorcerer",
    "char.base.remorts": 3,
}


def test_header_values() -> None:
    """The values come from GMCP, with lower-case race, subclass and sex and an int redos."""
    assert header_values(GMCP.get, "Male") == {
        "name": "Bast",
        "level": 50,
        "tiers": 2,
        "redos": 1,
        "race": "human",
        "sex": "male",
        "subclass": "sorcerer",
        "powerupsall": 0,
        "powerupsmort": 0,
        "remorts": 3,
    }


def test_header_values_with_missing_gmcp() -> None:
    """Missing GMCP values do not raise."""
    values = header_values(lambda path: None, "Female")
    assert values["name"] == ""
    assert values["race"] == ""
    assert values["redos"] == 0
    assert values["remorts"] == 1
    assert values["sex"] == "female"


def test_total_levels() -> None:
    """The total level is the actual level of the state."""
    state = {"level": 50, "remorts": 3, "tiers": 2, "redos": 1}
    assert total_levels(state) == actual_level(50, 3, 2, 1)
    assert (
        total_levels({"level": "50", "remorts": "3", "tiers": "2", "redos": "1"})
        == 3 * 1407 + 2 * 201 + 50
    )
    assert total_levels({}) == actual_level(0, 1, 0, 0)
