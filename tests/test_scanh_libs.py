"""Tests for the pure helpers of the scan highlight plugin."""

import pytest

from aardwolf.scanh.libs import (
    SETTINGS,
    SOURCES,
    highlight,
    matching_sources,
    mob_names,
    name_ends_line,
)


@pytest.mark.parametrize(
    ("line", "name"),
    [
        ("     - a big rat", "a big rat"),
        ("a big rat", "a big rat"),
        ("     - A Big Rat   ", "a big rat"),
        ("   (Hostile) a big rat", "a big rat"),
        ("    rat", "rat"),
    ],
)
def test_name_ends_line_matches(line: str, name: str) -> None:
    """The line ends with the name, which follows the start or a non-letter."""
    assert name_ends_line(line, name)


@pytest.mark.parametrize(
    ("line", "name"),
    [
        ("   - pirat", "rat"),
        ("   - a big rat is here", "a big rat"),
        ("   - a big rat", ""),
        ("   - a big rat", "  "),
        ("   - a big cat", "rat"),
    ],
)
def test_name_ends_line_no_match(line: str, name: str) -> None:
    """A name inside a word, in the middle or empty never matches (bug 1)."""
    assert not name_ends_line(line, name)


def test_matching_sources_in_fixed_order() -> None:
    """Every matching source is returned in CP, GQ, Quest order (bug 2)."""
    targets = {"quest": ["a rat"], "gq": ["a rat"], "cp": ["a rat"]}
    assert [s.key for s in matching_sources("  - a rat", targets)] == ["cp", "gq", "quest"]
    two = {"quest": ["a rat"], "cp": ["a rat"]}
    assert [s.key for s in matching_sources("  - a rat", two)] == ["cp", "quest"]


def test_matching_sources_none() -> None:
    """No targets, or no match, returns nothing."""
    assert matching_sources("  - a rat", {}) == []
    assert matching_sources("  - a rat", {"cp": ["a cat"]}) == []


def test_mob_names() -> None:
    """Names come from nocolorname, then name, lower-cased; junk is skipped."""
    mobs = [
        {"nocolorname": "A Big Rat", "name": "@Ra Big Rat"},
        {"name": "  A Cat "},
        {"name": ""},
        {"nocolorname": "", "name": ""},
        "not a dict",
        None,
    ]
    assert mob_names(mobs) == ["a big rat", "a cat"]
    assert mob_names(None) == []
    assert mob_names("a rat") == []


def test_highlight_one_source() -> None:
    """One source gives its tag."""
    assert highlight(" - a rat", SOURCES[:1], "@x0", "@z14") == "@x0@z14 - a rat - (CP)@x"


def test_highlight_two_sources() -> None:
    """Two sources give both tags with the colours passed in."""
    sources = [SOURCES[0], SOURCES[2]]
    assert highlight(" - a rat", sources, "@x0", "@z14") == "@x0@z14 - a rat - (CP) (Quest)@x"


def test_settings() -> None:
    """The six colour settings keep their names and defaults, and text help says text (bug 5)."""
    defaults = {name: default for name, default, _ in SETTINGS}
    assert defaults == {
        "cpbackcolor": "@z14",
        "gqbackcolor": "@z9",
        "questbackcolor": "@z13",
        "cptextcolor": "@x0",
        "gqtextcolor": "@x0",
        "questtextcolor": "@x0",
    }
    for name, _, help_text in SETTINGS:
        word = "text" if name.endswith("textcolor") else "background"
        assert f"the {word} color for" in help_text
