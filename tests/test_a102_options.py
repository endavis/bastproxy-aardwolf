"""Tests for the pure option 102 helpers."""

import pytest

from aardwolf.a102.libs import (
    A102_OPTION,
    OFF,
    ON,
    OPTION_NAMES,
    OPTIONS,
    apply_toggle,
    off_payloads,
    option_number,
    parse_pair,
    parse_toggle,
    state_payloads,
)


def test_constants() -> None:
    """The option and the flags have Aardwolf's values."""
    assert (A102_OPTION, ON, OFF) == (102, 1, 2)


def test_table_has_the_24_options() -> None:
    """The table holds every option from the issue."""
    assert len(OPTIONS) == 24
    assert OPTIONS["STATMON"] == 1
    assert OPTIONS["SPELLUPTAGS"] == 7
    assert OPTIONS["SCORETAGS"] == 11
    assert OPTIONS["SHORTMAP"] == 55
    assert len(set(OPTIONS.values())) == 24


def test_reverse_table() -> None:
    """The reverse table maps every number back to its name."""
    assert len(OPTION_NAMES) == 24
    assert all(OPTIONS[name] == number for number, name in OPTION_NAMES.items())


@pytest.mark.parametrize("name", ["SPELLUPTAGS", "spellUptags", "  prompt "])
def test_option_number_is_case_insensitive(name: str) -> None:
    """Names match without regard to case."""
    assert option_number(name) == OPTIONS[name.strip().upper()]


@pytest.mark.parametrize("name", ["NOPE", "", 7, None, b"PROMPT"])
def test_option_number_unknown(name: object) -> None:
    """Unknown and non-str names give None."""
    assert option_number(name) is None


def test_apply_toggle_sequence() -> None:
    """Only the 0 to 1 and 1 to 0 changes ask for a message."""
    counts: dict[int, int] = {}
    results = [apply_toggle(counts, 7, enable) for enable in (True, True, False, False, False)]
    assert results == [ON, None, None, OFF, None]
    assert counts == {7: 0}


def test_lone_off_creates_no_entry() -> None:
    """An off at 0 changes nothing and adds no entry."""
    counts: dict[int, int] = {}
    assert apply_toggle(counts, 7, False) is None
    assert counts == {}


def test_state_payloads_sorted() -> None:
    """Counted options come out sorted: on above 0, off at 0."""
    assert state_payloads({52: 1, 7: 0, 5: 3}) == [bytes([5, 1]), bytes([7, 2]), bytes([52, 1])]
    assert state_payloads({}) == []


@pytest.mark.parametrize(
    ("data", "expected"),
    [(bytes([100, 3]), (100, 3)), (b"", None), (b"\x01", None), (b"\x01\x01\x01", None)],
)
def test_parse_pair(data: bytes, expected: tuple[int, int] | None) -> None:
    """Only two bytes make a pair, with any flag."""
    assert parse_pair(data) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (bytes([7, 1]), (7, True)),
        (bytes([7, 2]), (7, False)),
        (bytes([7, 3]), None),
        (bytes([7, 0]), None),
        (bytes([100, 1]), None),
        (bytes([7]), None),
        (bytes([7, 1, 1]), None),
    ],
)
def test_parse_toggle(data: bytes, expected: tuple[int, bool] | None) -> None:
    """A toggle needs a known option and a flag of 1 or 2."""
    assert parse_toggle(data) == expected


def test_off_payloads_only_counted_options() -> None:
    """Only options with a count above 0 get an off payload, sorted by number."""
    assert off_payloads({52: 1, 7: 0, 5: 3}) == [bytes([5, OFF]), bytes([52, OFF])]
    assert off_payloads({}) == []
