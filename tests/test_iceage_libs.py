"""Tests for the pure helpers of the iceage plugin."""

import re

import pytest

from aardwolf.iceage.libs import (
    EVENT_ICEAGE,
    EVENT_REBOOT,
    EVENTS,
    ICEAGE_REGEX,
    REBOOT_REGEX,
    TRIGGERS,
    minutes,
)

ICEAGE = "INFO: An Ice Age Approaches - 5 minutes - See 'help iceage'."
ICEAGE_ONE = "INFO: An Ice Age Approaches - 1 minute - See 'help iceage'."
REBOOT = "INFO: Aardwolf will Reboot in 3 minutes."
REBOOT_REASON = "INFO: Aardwolf will reboot for a code update in 10 minutes."


def found(regex: str, line: str) -> dict[str, str]:
    """Return the groups a regex extracts from a line."""
    match = re.match(regex, line)
    assert match is not None, line
    return match.groupdict()


def test_iceage_regex_matches_plural_and_singular() -> None:
    """The Ice Age line gives the minutes as a named group."""
    assert found(ICEAGE_REGEX, ICEAGE) == {"minutes": "5"}
    assert found(ICEAGE_REGEX, ICEAGE_ONE) == {"minutes": "1"}


def test_reboot_regex_gives_minutes_not_the_reason() -> None:
    """The old regex's first group was the reason; the named group is the number."""
    assert found(REBOOT_REGEX, REBOOT) == {"minutes": "3"}
    assert found(REBOOT_REGEX, REBOOT_REASON) == {"minutes": "10"}


@pytest.mark.parametrize(
    ("regex", "line"),
    [
        (ICEAGE_REGEX, "An Ice Age Approaches - 5 minutes"),
        (ICEAGE_REGEX, "INFO: An Ice Age Approaches -  minutes - See 'help iceage'."),
        (REBOOT_REGEX, "Aardwolf will reboot in 3 minutes"),
        (REBOOT_REGEX, "INFO: Aardwolf will Reboot in  minutes."),
        (ICEAGE_REGEX, "You kill a rat."),
        (REBOOT_REGEX, "You kill a rat."),
    ],
)
def test_non_matches(regex: str, line: str) -> None:
    """No prefix, an empty number and unrelated lines do not match."""
    assert re.match(regex, line) is None


@pytest.mark.parametrize(("value", "expected"), [(0, 0), (5, 5)])
def test_minutes_accepts_ints(value: int, expected: int) -> None:
    """A non-negative int is returned."""
    assert minutes(value) == expected


@pytest.mark.parametrize("value", [True, False, -1, "5", None, 1.5])
def test_minutes_rejects_others(value: object) -> None:
    """Bools, negatives, strings, None and floats give None."""
    assert minutes(value) is None


def test_events_cover_triggers_and_describe_minutes() -> None:
    """Every trigger event is declared and describes exactly the minutes key."""
    assert {spec.event for spec in TRIGGERS} == {EVENT_ICEAGE, EVENT_REBOOT}
    assert set(EVENTS) == {EVENT_ICEAGE, EVENT_REBOOT}
    for info in EVENTS.values():
        assert set(info["arg_descriptions"]) == {"minutes"}
        assert info["description"]


def test_event_names() -> None:
    """The event names are the documented literals."""
    assert EVENT_ICEAGE == "ev_plugins.aardwolf.iceage_iceage"
    assert EVENT_REBOOT == "ev_plugins.aardwolf.iceage_reboot"
