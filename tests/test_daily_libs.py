"""Tests for the pure helpers of the Aardwolf daily plugin."""

import re
import time

import pytest

from aardwolf.daily.libs import (
    ACTIVE_STATE,
    EVENTS,
    READY_REGEX,
    SUFFIX_AVAILABLE,
    TIME_FORMAT,
    TOOK_REGEX,
    TRIGGERS,
    WAIT_REGEX,
    is_active_state,
    next_message,
    parse_wait,
)


@pytest.mark.parametrize(
    ("text", "seconds"),
    [
        ("3 hours, 5 minutes and 7 seconds", 3 * 3600 + 5 * 60 + 7),
        ("1 hour, 1 minute and 1 second", 3661),
        ("5 minutes and 7 seconds", 307),
        ("45 seconds", 45),
        ("1 second", 1),
        ("2 hours and 10 seconds", 7210),
        ("2 hours", 7200),
        ("0 seconds", 0),
        ("0 hours, 0 minutes and 0 seconds", 0),
    ],
)
def test_parse_wait_shapes(text: str, seconds: int) -> None:
    """The old three shapes and the shapes with a unit missing are read."""
    assert parse_wait(text) == seconds


@pytest.mark.parametrize(
    "text",
    [
        "",
        "soon",
        "hours",
        " minutes",
        "5 hourss",
        "5 fortnights",
        "1 hour, 1 hour",
        "5",
        "-5 seconds",
        None,
        5,
        b"5 seconds",
        ["5 seconds"],
    ],
)
def test_parse_wait_rejects_bad_input(text: object) -> None:
    """Bad text, a repeated unit and a non-str give None."""
    assert parse_wait(text) is None


def test_wait_regex_reads_the_whole_line() -> None:
    """The wait regex captures the wait and needs the escaped final period."""
    line = "You can receive a new daily blessing in 2 hours, 3 minutes and 4 seconds."
    found = re.match(WAIT_REGEX, line)
    assert found is not None
    assert parse_wait(found["wait"]) == 2 * 3600 + 3 * 60 + 4
    assert re.match(WAIT_REGEX, line[:-1] + "X") is None
    assert re.match(WAIT_REGEX, "You can receive a new daily blessing in .") is None


def test_ready_and_took_regexes_escape_the_period() -> None:
    """The two fixed lines match and a period wildcard does not."""
    assert re.match(READY_REGEX, "You are ready to receive a new daily blessing.")
    assert not re.match(READY_REGEX, "You are ready to receive a new daily blessingX")
    assert re.match(TOOK_REGEX, "You bow your head to Ayla and receive your daily blessing.")
    assert not re.match(TOOK_REGEX, "You bow your head to Ayla and receive your daily blessingX")


def test_triggers_have_unique_names() -> None:
    """Three triggers with distinct names."""
    assert len({spec.name for spec in TRIGGERS}) == len(TRIGGERS) == 3


@pytest.mark.parametrize(
    ("state", "expected"),
    [(ACTIVE_STATE, True), (3.0, True), (True, False), (1, False), (None, False), ("3", False)],
)
def test_is_active_state(state: object, expected: bool) -> None:
    """Only the active state number counts, never a bool."""
    assert is_active_state(state) is expected


def test_next_message_branches() -> None:
    """Ready wins, then nothing known, then the time."""
    when = 1_700_000_000.0
    shown = time.strftime(TIME_FORMAT, time.localtime(when))
    assert next_message(when, False) == f"Your next daily is at: {shown}"
    assert next_message(None, False) == "Please type daily to update plugin"
    assert next_message(None, True) == "Your daily blessing is ready"
    assert next_message(when, True) == "Your daily blessing is ready"


def test_event_is_declared() -> None:
    """The available event has a description."""
    assert set(EVENTS) == {SUFFIX_AVAILABLE}
    assert SUFFIX_AVAILABLE == "available"
    assert EVENTS[SUFFIX_AVAILABLE]["description"]


def test_next_message_time_format_parameter() -> None:
    """The time is shown in the format given, the module constant by default."""
    when = 86400.0
    assert next_message(when, False, "%Y") == "Your next daily is at: " + time.strftime(
        "%Y", time.localtime(when)
    )
    assert next_message(when, False) == next_message(when, False, TIME_FORMAT)
