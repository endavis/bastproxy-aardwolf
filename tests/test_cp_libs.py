"""Tests for the pure helpers of the cp plugin."""

import re

import pytest

from aardwolf.cp.libs import (
    EVENTS,
    TRIGGERS,
    bonus_qp,
    is_count_line,
    new_mob,
    new_state,
    remove_mob,
    reward_key,
)

SPECS = {spec.name: spec for spec in TRIGGERS}


def groups(name: str, line: str) -> dict[str, str]:
    """Return the groups a trigger extracts from a line."""
    match = re.match(SPECS[name].regex, line)
    assert match is not None, f"{name} did not match {line!r}"
    return match.groupdict()


def test_there_are_thirteen_triggers_with_prefixed_names() -> None:
    """Every trigger name is unique and carries the cp_ prefix."""
    assert len(TRIGGERS) == 13
    assert len(SPECS) == 13
    assert all(name.startswith("cp_") for name in SPECS)


def test_only_cp_new_is_enabled_without_a_group() -> None:
    """Only the new campaign trigger is always on."""
    assert [s.name for s in TRIGGERS if s.enabled] == ["cp_new"]
    assert SPECS["cp_new"].group is None


def test_check_triggers_are_omitted() -> None:
    """The triggers of the check output hide it from the client."""
    omitted = {s.name for s in TRIGGERS if s.omit}
    assert omitted == {"cp_none", "cp_time", "cp_mob", "cp_scramble"}
    assert all(SPECS[name].group == "cpcheck" for name in omitted)


def test_mob_line_with_and_without_dead() -> None:
    """The mob line gives the name, the location and the dead marker."""
    alive = groups("cp_mob", "You still have to kill * A rat (Sewers)")
    assert alive == {"mob": "A rat", "location": "Sewers", "dead": ""}
    dead = groups("cp_mob", "You still have to kill * A rat (Sewers - Dead)")
    assert dead == {"mob": "A rat", "location": "Sewers", "dead": " - Dead"}


def test_time_and_shnext_lines() -> None:
    """The time lines give the time left."""
    assert groups("cp_time", "You have 1h 2m to finish this campaign.")["time"] == "1h 2m"
    line = "You cannot take another campaign for 3m 4s."
    assert groups("cp_shnext", line)["time"] == "3m 4s"


def test_reward_line_amount_is_int() -> None:
    """The reward line gives the amount and the type; the argtype makes it an int."""
    found = groups("cp_reward", "  Reward of 120 quest points added.")
    assert found == {"amount": "120", "type": "quest"}
    assert SPECS["cp_reward"].argtypes == {"amount": int}


def test_new_none_and_single_line_triggers() -> None:
    """The other triggers match their lines."""
    groups(
        "cp_new", "Commander Barcett tells you 'Type 'campaign info' to see what you must kill.'"
    )
    groups("cp_none", "You are not currently on a campaign.")
    groups("cp_needtolevel", "You will have to level before you can go on another campaign.")
    groups("cp_cantake", "You may take a campaign at this level.")
    groups("cp_mobdead", "Congratulations, that was one of your CAMPAIGN mobs!")
    groups("cp_complete", "CONGRATULATIONS! You have completed your campaign.")
    groups("cp_clear", "Campaign cleared.")
    groups(
        "cp_scramble",
        "Note: One or more target names in this campaign might be slightly scrambled.",
    )
    groups("cp_compdone", "-" * 62)


def test_new_state_has_every_key() -> None:
    """The state of a new campaign has all the documented keys."""
    state = new_state(5.0, 77)
    for info in EVENTS.values():
        if "oncp" in info["arg_descriptions"]:
            assert set(info["arg_descriptions"]) == set(state)
    assert state["oncp"] is True
    assert state["mobs"] == []
    assert state["mobsleft"] == []
    assert state["level"] == 77
    assert state["starttime"] == 5.0
    assert state["finishtime"] == 0


def test_new_mob() -> None:
    """A mob has its name, its plain name, its location and whether it is dead."""
    assert new_mob("A rat", "Sewers", " - Dead") == {
        "name": "A rat",
        "nocolorname": "A rat",
        "location": "Sewers",
        "mobdead": True,
    }
    assert new_mob("A rat", "Sewers", "")["mobdead"] is False


def mobs(*names: str) -> list[dict[str, object]]:
    """Return mobs with the names."""
    return [new_mob(name, "Sewers", "") for name in names]


def test_remove_mob_removes_the_first_entry() -> None:
    """The mob at index 0 is removed (the old plugin skipped it)."""
    left = mobs("a", "b", "c")
    assert remove_mob(left, "a") is True
    assert [m["name"] for m in left] == ["b", "c"]


def test_remove_mob_removes_a_middle_entry_once() -> None:
    """Only the first of two mobs with the same name goes."""
    left = mobs("a", "b", "b", "c")
    assert remove_mob(left, "b") is True
    assert [m["name"] for m in left] == ["a", "b", "c"]


def test_remove_mob_without_a_match() -> None:
    """An unknown name changes nothing and returns False."""
    left = mobs("a")
    assert remove_mob(left, "z") is False
    assert len(left) == 1
    assert remove_mob([], "z") is False


@pytest.mark.parametrize(
    ("rtype", "key"),
    [
        ("quest", "qp"),
        ("training", "trains"),
        ("gold", "gold"),
        ("trivia", "tp"),
        ("practice", "pracs"),
    ],
)
def test_reward_key(rtype: str, key: str) -> None:
    """The reward types map to the state keys."""
    assert reward_key(rtype) == key


def test_reward_key_unknown() -> None:
    """An unknown type has no key."""
    assert reward_key("bogus") is None


def test_bonus_qp() -> None:
    """The bonus line gives the quest points; other lines give None."""
    line = "You receive 15 quest points bonus for your first campaign completed today."
    assert bonus_qp(line) == 15
    assert bonus_qp("You have completed 2 campaigns today.") is None
    assert bonus_qp("You receive 15 quest points.") is None


def test_is_count_line() -> None:
    """The count line is recognised."""
    assert is_count_line("You have completed 3 campaigns today.") is True
    assert is_count_line("You receive 15 quest points bonus") is False


def test_event_descriptions_format() -> None:
    """The descriptions go through str.format, so they hold no raw braces."""
    assert len(EVENTS) == 4
    for info in EVENTS.values():
        for text in info["description"]:
            text.format()
