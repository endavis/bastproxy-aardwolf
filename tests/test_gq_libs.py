"""Tests for the pure helpers of the gq plugin."""

import re

from aardwolf.gq.libs import (
    EVENTS,
    TRIGGERS,
    count_down,
    name_has_several_locations,
    new_mob,
    new_state,
    reward_key,
)

SPECS = {spec.name: spec for spec in TRIGGERS}
ALWAYS_ON = {
    "gq_declared",
    "gq_joined",
    "gq_started",
    "gq_cancelled",
    "gq_quit",
    "gq_note",
    "gq_maxkills",
    "gq_wonannounce",
}


def groups(name: str, line: str) -> dict[str, str]:
    """Return the groups a trigger extracts from a line."""
    match = re.match(SPECS[name].regex, line)
    assert match is not None, f"{name} did not match {line!r}"
    return match.groupdict()


def test_there_are_seventeen_triggers_with_prefixed_names() -> None:
    """Every trigger name is unique and carries the gq_ prefix."""
    assert len(TRIGGERS) == 17
    assert len(SPECS) == 17
    assert all(name.startswith("gq_") for name in SPECS)


def test_only_the_eight_always_on_triggers_are_enabled_without_a_group() -> None:
    """The declare, join, start, cancel, quit, note, maxkills and win triggers are always on."""
    assert {s.name for s in TRIGGERS if s.enabled} == ALWAYS_ON
    assert all(SPECS[name].group is None for name in ALWAYS_ON)
    assert all(s.group is not None for s in TRIGGERS if s.name not in ALWAYS_ON)


def test_groups_hold_the_expected_triggers() -> None:
    """The check, in and rewards groups hold their triggers."""
    by_group: dict[str | None, set[str]] = {}
    for spec in TRIGGERS:
        by_group.setdefault(spec.group, set()).add(spec.name)
    assert by_group["gqcheck"] == {"gq_none", "gq_item", "gq_notstarted", "gq_wins"}
    assert by_group["gqin"] == {
        "gq_mobdead",
        "gq_extended",
        "gq_won",
        "gq_extfin",
    }
    assert by_group["gqrew"] == {"gq_reward"}


def test_declared_joined_started_cancelled_quit_lines() -> None:
    """The always-on lines give the number of the gquest."""
    declared = groups(
        "gq_declared",
        "Global Quest: Global quest # 12 has been declared for levels 10 to 60 - some.",
    )
    assert declared["gqnum"] == "12"
    assert declared["lowlev"] == "10"
    assert declared["highlev"] == "60"
    joined = "You have now joined Global Quest # 12. Type gq info"
    assert groups("gq_joined", joined)["gqnum"] == "12"
    started = "Global Quest: Global quest # 12 for levels 10 to 60 has now started."
    assert groups("gq_started", started)["gqnum"] == "12"
    cancelled = "Global Quest: Global quest # 12 has been cancelled due to lack of activity."
    assert groups("gq_cancelled", cancelled)["gqnum"] == "12"
    quit_line = "You are no longer part of Global Quest # 12 and will be unable to rejoin."
    assert groups("gq_quit", quit_line)["gqnum"] == "12"


def test_note_and_maxkills_lines() -> None:
    """The forum note gives the number; the maxkills line matches."""
    note = "INFO: New post #5 in forum Gquest from Aardwolf Subj: Lvl 10 to 60 - Global quest # 12"
    assert groups("gq_note", note)["gqnum"] == "12"
    line = "You have reached the maximum 20 kills for which you can earn quest points this level."
    assert re.match(SPECS["gq_maxkills"].regex, line)


def test_item_line_with_and_without_a_period() -> None:
    """The target line gives the number, the name and the location."""
    expected = {"num": "3", "mob": "A rat", "location": "Sewers"}
    assert groups("gq_item", "You still have to kill 3 * A rat (Sewers)") == expected
    assert groups("gq_item", "You still have to kill 3 * A rat (Sewers).") == expected


def test_check_end_lines() -> None:
    """The not-in, not-started and wins lines match."""
    assert re.match(SPECS["gq_none"].regex, "You are not in a global quest.")
    started = groups("gq_notstarted", "Global Quest # 12 has not yet started.")
    assert started["gqnum"] == "12"
    assert re.match(SPECS["gq_wins"].regex, "You may win 2 more gquests at this level.")
    assert re.match(SPECS["gq_wins"].regex, "You may win 1 more gquest at this level.")


def test_in_group_lines() -> None:
    """The lines of a gquest in progress match."""
    mobdead = "Congratulations, that was one of the GLOBAL QUEST mobs!"
    assert re.match(SPECS["gq_mobdead"].regex, mobdead)
    extended = "Global Quest: Global Quest # 12 will go into extended time for 3 more minutes."
    assert groups("gq_extended", extended)["gqnum"] == "12"
    assert re.match(SPECS["gq_won"].regex, "You were the first to complete this quest!")
    assert re.match(SPECS["gq_extfin"].regex, "You have finished this global quest.")


def test_win_announcement_lines() -> None:
    """The announcement matches the old loose forms and not a quoted or malformed line."""
    announce = "Global Quest: Global Quest #12 has been won by Bast - 1st win."
    assert groups("gq_wonannounce", announce) == {"gqnum": "12", "winner": "Bast"}
    spaced = "Global Quest: Global Quest # 12 has been won by Bast - 1st win!"
    assert groups("gq_wonannounce", spaced) == {"gqnum": "12", "winner": "Bast"}
    ordinal = "Global Quest: Global Quest #12 has been won by Bast - first win."
    assert groups("gq_wonannounce", ordinal) == {"gqnum": "12", "winner": "Bast"}
    for line in (
        f"(Gossip) Other: {announce}",
        "Global Quest: Global Quest #x has been won by Bast - 1st win.",
        "Global Quest: Global Quest #12 has been won by Bast - 1st",
    ):
        assert not re.match(SPECS["gq_wonannounce"].regex, line), line


def test_reward_line() -> None:
    """The reward line gives the amount and the type."""
    got = groups("gq_reward", "  Reward of 120 quest points added.")
    assert got == {"amount": "120", "type": "quest"}


def test_argtypes_are_the_old_ones() -> None:
    """The numbers are converted to int by the triggers."""
    assert SPECS["gq_declared"].argtypes == {"gqnum": int}
    assert SPECS["gq_item"].argtypes == {"num": int}
    assert SPECS["gq_reward"].argtypes == {"amount": int}
    assert SPECS["gq_none"].argtypes is None


def test_new_state_has_the_state_keys() -> None:
    """A new state has no rewards and no mobs."""
    state = new_state(120)
    assert set(state) == {
        "mobs",
        "trains",
        "pracs",
        "gold",
        "tp",
        "qp",
        "qpmobs",
        "level",
        "starttime",
        "finishtime",
        "length",
        "won",
        "completed",
        "extended",
    }
    assert state["mobs"] == []
    assert state["level"] == 120
    assert all(state[key] == 0 for key in ("trains", "qp", "qpmobs", "won", "completed"))


def test_new_mob_has_the_nocolorname() -> None:
    """The mob carries the name without colour, as the trigger matches it."""
    assert new_mob("A rat", "Sewers", 2) == {
        "name": "A rat",
        "nocolorname": "A rat",
        "location": "Sewers",
        "num": 2,
    }


def test_count_down_removes_the_first_mob() -> None:
    """The mob at index 0 with one kill left is removed."""
    mobs = [new_mob("A rat", "Sewers", 1), new_mob("A bat", "Cave", 1)]
    assert count_down(mobs, "A rat") is True
    assert [m["name"] for m in mobs] == ["A bat"]


def test_count_down_decrements_a_mob_with_more_kills() -> None:
    """A mob with several kills left loses one and stays."""
    mobs = [new_mob("A rat", "Sewers", 3)]
    assert count_down(mobs, "A rat") is True
    assert mobs[0]["num"] == 2


def test_count_down_unknown_mob() -> None:
    """A name that is not in the list changes nothing."""
    mobs = [new_mob("A rat", "Sewers", 1)]
    assert count_down(mobs, "A bat") is False
    assert len(mobs) == 1
    assert count_down([], "A bat") is False


def test_count_down_acts_on_the_first_of_duplicates() -> None:
    """Only the first mob with the name is counted down."""
    mobs = [new_mob("A rat", "Sewers", 2), new_mob("A rat", "Cave", 2)]
    assert count_down(mobs, "A rat") is True
    assert [m["num"] for m in mobs] == [1, 2]


def test_reward_key() -> None:
    """The reward types map to the state keys; an unknown type is None."""
    assert reward_key("quest") == "qp"
    assert reward_key("training") == "trains"
    assert reward_key("gold") == "gold"
    assert reward_key("trivia") == "tp"
    assert reward_key("practice") == "pracs"
    assert reward_key("bogus") is None


def test_events_are_described() -> None:
    """The ten events carry a suffix, a description and the payload keys."""
    assert set(EVENTS) == {
        "declared",
        "joined",
        "started",
        "cancelled",
        "mobsleft",
        "won",
        "completed",
        "done",
        "available",
        "notavailable",
    }
    assert all(info["description"] for info in EVENTS.values())
    assert set(EVENTS["declared"]["arg_descriptions"]) == {"gqnum", "lowlev", "highlev"}
    assert set(EVENTS["mobsleft"]["arg_descriptions"]) == {"mobsleft"}
    assert EVENTS["available"]["arg_descriptions"] == {}
    assert EVENTS["won"]["arg_descriptions"] == EVENTS["done"]["arg_descriptions"]


def test_event_text_has_no_raw_braces() -> None:
    """The event text goes through str.format, so it holds no braces."""
    for info in EVENTS.values():
        for text in [*info["description"], *info["arg_descriptions"].values()]:
            assert "{" not in text
            assert "}" not in text


def test_name_has_several_locations() -> None:
    """The name is ambiguous only when its mobs are at more than one distinct location."""
    left = [
        new_mob("A rat", "Sewers", 1),
        new_mob("A bat", "Cave", 1),
        new_mob("A rat", "Kitchen", 1),
    ]
    assert name_has_several_locations(left, "A rat") is True
    assert name_has_several_locations(left, "A bat") is False
    assert name_has_several_locations(left, "A cat") is False
    assert name_has_several_locations([], "A rat") is False


def test_name_has_several_locations_ignores_same_location_duplicates() -> None:
    """Two mobs with the name at the same location are not ambiguous."""
    left = [new_mob("A rat", "Sewers", 1), new_mob("A rat", "Sewers", 2)]
    assert name_has_several_locations(left, "A rat") is False
