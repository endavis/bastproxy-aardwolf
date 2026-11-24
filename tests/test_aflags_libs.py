"""Tests for the pure helpers of the aflags plugin."""

import re

import pytest

from aardwolf.aflags.libs import (
    CMD_REGEX,
    EVENT_AFFECTED_UPDATE,
    EVENT_AFFOFF,
    EVENT_AFFON,
    EVENT_UPTODATE,
    HEADER_REGEX,
    AflagsReader,
    FlagLearner,
    flag_diff,
    split_flags,
)
from aardwolf.skills.libs import EVENT_AFFECTED_UPDATE as SKILLS_AFFECTED_UPDATE
from aardwolf.skills.libs import EVENT_AFFOFF as SKILLS_AFFOFF
from aardwolf.skills.libs import EVENT_AFFON as SKILLS_AFFON
from aardwolf.skills.libs import EVENT_UPTODATE as SKILLS_UPTODATE

PROMPT = "<100/100hp 50/50mn 90/90mv> "


def test_event_names_match_the_skills_plugin() -> None:
    assert EVENT_AFFON == SKILLS_AFFON
    assert EVENT_AFFOFF == SKILLS_AFFOFF
    assert EVENT_AFFECTED_UPDATE == SKILLS_AFFECTED_UPDATE
    assert EVENT_UPTODATE == SKILLS_UPTODATE


def test_regexes() -> None:
    assert re.match(CMD_REGEX, "aflags")
    assert not re.match(CMD_REGEX, "aflags now")
    match = re.match(HEADER_REGEX, "Affect Flags: Sanctuary, Haste")
    assert match
    assert match.group("flags") == "Sanctuary, Haste"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Sanctuary, Haste", ["sanctuary", "haste"]),
        ("  Fly ,, ", ["fly"]),
        ("", []),
        (" , ", []),
    ],
)
def test_split_flags(text: str, expected: list[str]) -> None:
    assert split_flags(text) == expected


def test_reader_ignores_lines_before_the_header() -> None:
    reader = AflagsReader()
    assert not reader.feed("")
    assert not reader.feed(PROMPT, is_prompt=True)
    assert not reader.feed("some other line, with commas")
    assert not reader.started
    assert reader.flags == set()


def test_reader_reads_the_header_and_continuation_lines() -> None:
    reader = AflagsReader()
    reader.feed("Affect Flags: Sanctuary, Haste")
    assert reader.started
    assert not reader.feed("      Fly, Detect Magic")
    assert reader.flags == {"sanctuary", "haste", "fly", "detect magic"}


def test_reader_ends_on_a_blank_line() -> None:
    reader = AflagsReader()
    reader.feed("Affect Flags: Fly")
    assert reader.feed("")
    assert reader.finished
    assert not reader.feed("Later, line")
    assert reader.flags == {"fly"}


def test_reader_ends_on_a_prompt() -> None:
    reader = AflagsReader()
    reader.feed("Affect Flags: Fly")
    assert reader.feed(PROMPT, is_prompt=True)
    assert reader.flags == {"fly"}


def test_reader_skips_tag_lines() -> None:
    reader = AflagsReader()
    reader.feed("Affect Flags: Fly")
    assert not reader.feed("{affon}12,100")
    assert reader.flags == {"fly"}


def test_reader_header_with_no_flags() -> None:
    reader = AflagsReader()
    reader.feed("Affect Flags: ")
    assert reader.feed("")
    assert reader.flags == set()


def test_reader_start_resets() -> None:
    reader = AflagsReader()
    reader.feed("Affect Flags: Fly")
    reader.feed("")
    reader.start()
    assert (reader.flags, reader.started, reader.finished) == (set(), False, False)


def test_flag_diff_is_sorted_and_disjoint() -> None:
    added, removed = flag_diff({"fly", "haste"}, {"haste", "sanctuary", "invis"})
    assert added == ["invis", "sanctuary"]
    assert removed == ["fly"]
    assert flag_diff({"a"}, {"a"}) == ([], [])


def test_learner_stores_the_flags_of_one_sn() -> None:
    learner = FlagLearner()
    learner.change(12)
    learner.start()
    assert learner.learn(["sanctuary"], []) == 12
    assert learner.table == {12: ["sanctuary"]}


def test_learner_stores_the_union_of_added_and_removed() -> None:
    learner = FlagLearner()
    learner.change(3)
    learner.start()
    assert learner.learn(["b"], ["a"]) == 3
    assert learner.table == {3: ["a", "b"]}


def test_learner_ignores_two_sns() -> None:
    learner = FlagLearner()
    learner.change(1)
    learner.change(2)
    learner.start()
    assert learner.learn(["a"], []) is None
    assert learner.table == {}


def test_learner_ignores_an_empty_diff_and_no_sn() -> None:
    learner = FlagLearner()
    learner.change(1)
    learner.start()
    assert learner.learn([], []) is None
    learner.start()
    assert learner.learn(["a"], []) is None
    assert learner.table == {}


def test_learner_keeps_a_change_after_start_for_the_next_read() -> None:
    learner = FlagLearner()
    learner.change(1)
    learner.start()
    learner.change(2)
    assert learner.learn(["a"], []) == 1
    learner.start()
    assert learner.learn(["b"], []) == 2
    assert learner.table == {1: ["a"], 2: ["b"]}


def test_learner_reset_drops_the_changes_but_not_the_table() -> None:
    learner = FlagLearner()
    learner.change(1)
    learner.start()
    learner.learn(["a"], [])
    learner.change(2)
    learner.reset()
    learner.start()
    assert learner.learn(["b"], []) is None
    assert learner.table == {1: ["a"]}
