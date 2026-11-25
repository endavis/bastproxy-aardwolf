"""Tests for the pure helpers of the cp plugin."""

import re

import pytest

from aardwolf.cp.libs import (
    CHECK_HIDE_START,
    CP_DURATION,
    EVENTS,
    INFO_HIDE_START,
    NEVER_REGEX,
    SUFFIX_COMP,
    TRIGGERS,
    bonus_qp,
    info_mobs,
    info_starttime,
    is_count_line,
    name_has_several_locations,
    new_campaign_regex,
    new_mob,
    new_state,
    parse_time_left,
    remove_mob,
    reward_key,
)

SPECS = {spec.name: spec for spec in TRIGGERS}


def groups(name: str, line: str) -> dict[str, str]:
    """Return the groups a trigger extracts from a line."""
    match = re.match(SPECS[name].regex, line)
    assert match is not None, f"{name} did not match {line!r}"
    return match.groupdict()


def test_there_are_26_triggers_with_prefixed_names() -> None:
    """Every trigger name is unique and carries the cp_ prefix."""
    assert len(TRIGGERS) == 26
    assert len(SPECS) == 26
    assert all(name.startswith("cp_") for name in SPECS)


def test_only_cp_new_and_cp_mobdead_are_enabled_without_a_group() -> None:
    """The new campaign tell and the campaign mob kill are always on; the rest sit in groups."""
    assert [s.name for s in TRIGGERS if s.enabled] == ["cp_new", "cp_mobdead"]
    assert SPECS["cp_new"].group is None
    assert SPECS["cp_mobdead"].group is None
    assert all(s.group for s in TRIGGERS if s.name not in {"cp_new", "cp_mobdead"})


def test_check_triggers_are_omitted() -> None:
    """The triggers of the check output hide it from the client."""
    omitted = {s.name for s in TRIGGERS if s.omit and s.group == "cpcheck"}
    assert omitted == {"cp_none", "cp_time", "cp_mob", "cp_scramble"}


def test_info_triggers_are_in_the_info_group_and_omitted() -> None:
    """The campaign info output is hidden, except the may-take lines, which the client keeps."""
    info = {s.name for s in TRIGGERS if s.group == "cpinfo"}
    assert info == {name for name in SPECS if name.startswith("cp_info_")}
    assert {s.name for s in TRIGGERS if s.omit and s.group == "cpinfo"} == info - {
        "cp_info_cantake",
        "cp_info_needtolevel",
    }
    assert not any(SPECS[name].enabled for name in info)


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


TELL = " tells you 'Type 'campaign info' to see what you must kill.'"


@pytest.mark.parametrize("speaker", ["Commander Barcett", "A QuestoR", "Questor"])
def test_new_matches_the_default_questmasters(speaker: str) -> None:
    """The new-campaign line matches the default questmasters."""
    groups("cp_new", f"{speaker}{TELL}")


def test_new_matches_questor_and_not_a_player() -> None:
    """Questor starts a campaign by default; a player's tell of the same text does not."""
    assert re.match(SPECS["cp_new"].regex, "Questor" + TELL)
    assert re.match(SPECS["cp_new"].regex, "Bob" + TELL) is None


@pytest.mark.parametrize(
    "line", ["Bob" + TELL, "Bob Commander Barcett" + TELL, "Commander Barcett" + TELL + " x"]
)
def test_new_does_not_match_players_or_emotes(line: str) -> None:
    """A player's tell, an emote or trailing text is not a campaign."""
    assert re.match(SPECS["cp_new"].regex, line) is None


def test_new_campaign_regex_escapes_and_anchors() -> None:
    """Names are escaped, alternated and anchored at both ends."""
    regex = new_campaign_regex(["A.B", "C+D"])
    assert regex.startswith(r"^(?:A\.B|C\+D) tells you")
    assert regex.endswith("$")
    assert re.match(regex, "A.B" + TELL)
    assert re.match(regex, "C+D" + TELL)
    assert re.match(regex, "AxB" + TELL) is None
    assert re.match(regex, "xA.B" + TELL) is None


def test_new_campaign_regex_without_questmasters_never_matches() -> None:
    """An empty list gives a regex that matches nothing."""
    assert new_campaign_regex([]) == NEVER_REGEX
    assert new_campaign_regex([""]) == NEVER_REGEX
    assert re.match(NEVER_REGEX, "Commander Barcett" + TELL) is None
    assert re.match(NEVER_REGEX, "") is None


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


def test_name_has_several_locations() -> None:
    """The name is ambiguous only when its mobs are at more than one distinct location."""
    left = [
        new_mob("A rat", "Sewers", ""),
        new_mob("A bat", "Cave", ""),
        new_mob("A rat", "Kitchen", ""),
    ]
    assert name_has_several_locations(left, "A rat") is True
    assert name_has_several_locations(left, "A bat") is False
    assert name_has_several_locations(left, "A cat") is False
    assert name_has_several_locations([], "A rat") is False


def test_name_has_several_locations_ignores_same_location_duplicates() -> None:
    """Two mobs with the name at the same location are not ambiguous."""
    assert name_has_several_locations(mobs("A rat", "A rat"), "A rat") is False


def test_remove_mob_removes_the_first_of_several_locations() -> None:
    """The first match goes, even when the same name is at another location."""
    left = [
        new_mob("A rat", "Sewers", ""),
        new_mob("A bat", "Cave", ""),
        new_mob("A rat", "Kitchen", ""),
    ]
    assert remove_mob(left, "A rat") is True
    assert [(m["name"], m["location"]) for m in left] == [("A bat", "Cave"), ("A rat", "Kitchen")]


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


INFO_HEADER = "-" * 26 + "[ YOUR CURRENT CAMPAIGN ]" + "-" * 22


def test_info_header_and_value_lines() -> None:
    """The header and the value lines of campaign info give their values."""
    groups("cp_info_header", INFO_HEADER)
    found = groups("cp_info_completeby", "Complete By........: [ 12:34PM on 30 Nov 2026 ]")
    assert found == {"completeby": "12:34PM on 30 Nov 2026"}
    found = groups("cp_info_timeleft", "Time Left  ........: [ 6 days, 23 hours and 56 minutes ]")
    assert found == {"timeleft": "6 days, 23 hours and 56 minutes"}
    assert groups("cp_info_level", "Level Taken........: [     2 ]") == {"level": "2"}
    assert SPECS["cp_info_level"].argtypes == {"level": int}
    groups("cp_info_rewards", "Quest Points.......: [    27 ]")
    groups("cp_info_rewards", "Gold Coins.........: [  6613 ]")


def test_info_structure_lines() -> None:
    """The victims, targets, dashes and end lines match."""
    groups("cp_info_victims", "-" * 28 + "[ Campaign Victims ]" + "-" * 26)
    groups("cp_info_targets", "The targets for this campaign are:")
    groups("cp_info_dashes", "-" * 74)
    groups("cp_info_end", "Use 'cp check' to see only targets that you still need to kill.")
    assert re.match(SPECS["cp_info_dashes"].regex, "-" * 62) is None


def test_info_mob_line() -> None:
    """The target line gives the count, the name and the location."""
    found = groups("cp_info_mob", "Find and kill 1 * some wicked ale (Gallows Hill)")
    assert found == {"count": "1", "mob": "some wicked ale", "location": "Gallows Hill"}
    found = groups("cp_info_mob", "Find and kill 2 * a black cat (Gallows Hill)")
    assert found["count"] == "2"
    assert SPECS["cp_info_mob"].argtypes == {"count": int}


def test_info_mob_line_with_parentheses_in_the_name() -> None:
    """The location is the last group in parentheses."""
    found = groups("cp_info_mob", "Find and kill 1 * a rat (big) (Sewers)")
    assert found == {"count": "1", "mob": "a rat (big)", "location": "Sewers"}


def test_info_none_and_limit_lines() -> None:
    """The not-on-a-campaign reply and its limit lines match in the info group."""
    groups("cp_info_none", "You are not currently on a campaign.")
    groups("cp_info_cantake", "You may take a campaign at this level.")
    groups("cp_info_needtolevel", "You will have to level before you can go on another campaign.")


@pytest.mark.parametrize(
    ("text", "seconds"),
    [
        ("6 days, 23 hours and 59 minutes", 604740),
        ("1 day, 1 hour and 1 minute", 86400 + 3600 + 60),
        ("59 minutes", 3540),
        ("garbage", None),
        ("", None),
    ],
)
def test_parse_time_left(text: str, seconds: int | None) -> None:
    """The time left is summed in seconds, or None when it has no unit."""
    assert parse_time_left(text) == seconds


def test_info_starttime() -> None:
    """The start is the 7 days of a campaign less its time left before now."""
    assert info_starttime(10000.0, 604740) == 10000.0 - 60
    assert info_starttime(10000.0, CP_DURATION) == 10000.0
    assert info_starttime(10000.0, None) == 10000.0


def test_info_mobs_repeats_a_target_by_its_count() -> None:
    """A target with a count of n is n mobs, none of them dead; a count under 1 is one."""
    found = info_mobs(2, "a cat", "Hill")
    assert found == [new_mob("a cat", "Hill", "")] * 2
    assert not any(mob["mobdead"] for mob in found)
    assert len(info_mobs(0, "a cat", "Hill")) == 1


def test_new_state_has_completeby() -> None:
    """The state starts without a Complete By time, and the key is described."""
    assert new_state(5.0, 1)["completeby"] == ""
    assert "completeby" in EVENTS[SUFFIX_COMP]["arg_descriptions"]


CHECK_OPENERS = (
    "You are not currently on a campaign.",
    "You have 30 minutes to finish this campaign.",
    "You still have to kill * A rat (Sewers)",
    "You still have to kill * A bat (Cave - Dead)",
    "Note: One or more target names in this campaign might be slightly scrambled.",
)
INFO_OPENERS = (
    "-" * 26 + "[ YOUR CURRENT CAMPAIGN ]" + "-" * 22,
    "Complete By........: [ 12:34PM on 30 Nov 2026 ]",
    "Time Left  ........: [ 6 days, 23 hours and 56 minutes ]",
    "Level Taken........: [    50 ]",
    "Quest Points.......: [    27 ]",
    "Gold Coins.........: [  6613 ]",
    "-" * 28 + "[ Campaign Victims ]" + "-" * 26,
    "The targets for this campaign are:",
    "Find and kill 1 * A rat (Sewers)",
    "-" * 74,
    "Use 'cp check' to see only targets that you still need to kill.",
    "You are not currently on a campaign.",
)
NOT_OPENERS = (
    "Commander Barcett tells you 'Type 'campaign info' to see what you must kill.'",
    "You may take a campaign at this level.",
    "You will have to level before you can go on another campaign.",
    "[198/201hp 168/176mn 630/630mv 10qt 773tnl] >",
    "",
)


def test_the_check_hide_start_matches_the_omitted_check_lines() -> None:
    """A queued check opens its window on the lines its omit triggers hide, and no other."""
    start = re.compile(CHECK_HIDE_START)
    assert all(start.search(line) for line in CHECK_OPENERS)
    assert not any(start.search(line) for line in NOT_OPENERS[:1] + NOT_OPENERS[3:])
    assert not start.search(INFO_OPENERS[1])


def test_the_info_hide_start_matches_the_omitted_info_lines() -> None:
    """A queued info opens its window on its omitted lines, not on the may-take lines."""
    start = re.compile(INFO_HIDE_START)
    assert all(start.search(line) for line in INFO_OPENERS)
    assert not any(start.search(line) for line in NOT_OPENERS)


@pytest.mark.parametrize("group", ["cpcheck", "cpinfo"])
def test_a_hide_start_has_one_alternative_per_omitted_trigger(group: str) -> None:
    """Every omitted trigger of the group is in the opener, and no other one."""
    start = CHECK_HIDE_START if group == "cpcheck" else INFO_HIDE_START
    omitted = [s for s in TRIGGERS if s.group == group and s.omit]
    assert start.startswith("(?:") and start.endswith(")")
    assert start.count("|") >= len(omitted) - 1
    assert "(?P<" not in start
