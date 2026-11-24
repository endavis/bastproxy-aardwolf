"""Tests for the pure helpers of the afk plugin."""

import re
import time

import pytest

from aardwolf.afk.libs import (
    EVENT_CLIENT_DISCONNECTED,
    EVENT_CLIENT_LOGGED_IN,
    EVENT_GMCP_COMM,
    TITLE_REGEX,
    TITLE_SET_REGEX,
    TRIGGERS,
    WATCH_TITLE_REGEX,
    count_active,
    format_tells,
    queue_notice,
    remember_title,
    tell_entry,
    title_to_send,
)


def test_count_active_counts_only_logged_in_players() -> None:
    states = [(True, False), (True, True), (False, False), (True, False)]
    assert count_active(states) == 2


def test_count_active_of_no_clients_is_zero() -> None:
    assert count_active([]) == 0


def test_tell_entry_keeps_a_tell() -> None:
    data = {"chan": "tell", "msg": "hello there", "player": "Zed"}
    assert tell_entry(data, 100.5) == {"timestamp": 100.5, "player": "Zed", "msg": "hello there"}


@pytest.mark.parametrize(
    "data",
    [{"chan": "gossip", "msg": "x", "player": "Zed"}, {}, None, "tell", ["tell"], 5],
)
def test_tell_entry_ignores_what_is_not_a_tell(data: object) -> None:
    assert tell_entry(data, 1.0) is None


def test_tell_entry_tolerates_missing_fields() -> None:
    assert tell_entry({"chan": "tell"}, 1.0) == {"timestamp": 1.0, "player": "", "msg": ""}


@pytest.mark.parametrize(
    ("is_afk", "afk", "last", "expected"),
    [
        (True, "is AFK.", "mine", "is AFK."),
        (False, "is AFK.", "mine", "mine"),
        (False, "is AFK.", "", None),
        (True, "", "mine", None),
    ],
)
def test_title_to_send(is_afk: bool, afk: str, last: str, expected: str | None) -> None:
    assert title_to_send(is_afk, afk, last) == expected


@pytest.mark.parametrize(
    ("typed", "afk", "expected"),
    [
        ("a new title", "is AFK.", "a new title"),
        ("is AFK.", "is AFK.", None),
        ("", "is AFK.", None),
        (None, "is AFK.", None),
    ],
)
def test_remember_title(typed: str | None, afk: str, expected: str | None) -> None:
    assert remember_title(typed, afk) == expected


def test_format_tells_of_nothing_says_the_queue_is_empty() -> None:
    assert format_tells([]) == ["The queue is empty"]


def test_format_tells_lists_rows() -> None:
    stamp = time.mktime((2026, 1, 2, 3, 4, 5, 0, 0, -1))
    entries = [
        {"timestamp": stamp, "player": "Zed", "msg": "hi"},
        {"timestamp": stamp, "player": "", "msg": "no sender"},
    ]
    lines = format_tells(entries)
    assert lines[0] == "Tells received while afk"
    assert lines[1].endswith("Fri Jan 02 2026 03:04:05 - Zed: hi")
    assert lines[2].endswith("Fri Jan 02 2026 03:04:05 - no sender")


@pytest.mark.parametrize("bad", ["text", None, {"msg": "no time"}, {"timestamp": True}])
def test_format_tells_skips_a_bad_entry(bad: object) -> None:
    good = {"timestamp": 1.0, "player": "Zed", "msg": "hi"}
    lines = format_tells([bad, good])
    assert len(lines) == 2
    assert format_tells([bad]) == ["The queue is empty"]


@pytest.mark.parametrize(
    ("count", "expected"),
    [(0, []), (-1, []), (1, "1 tell in"), (3, "3 tells in")],
)
def test_queue_notice(count: int, expected: list[str] | str) -> None:
    lines = queue_notice(count)
    if isinstance(expected, list):
        assert lines == expected
    else:
        assert expected in lines[1]


@pytest.mark.parametrize(
    ("text", "title"),
    [
        ("title a fine title", "a fine title"),
        ("titl a fine title", "a fine title"),
        ("tit a fine title", "a fine title"),
    ],
)
def test_watch_regex_matches_the_abbreviations(text: str, title: str) -> None:
    match = re.match(WATCH_TITLE_REGEX, text)
    assert match is not None
    assert match["title"] == title


@pytest.mark.parametrize("text", ["title", "titles x", "ti x", "say title x"])
def test_watch_regex_ignores_other_input(text: str) -> None:
    assert re.match(WATCH_TITLE_REGEX, text) is None


def test_set_line_regex() -> None:
    match = re.match(TITLE_SET_REGEX, "Title now set to: is AFK.")
    assert match is not None
    assert match["title"] == "is AFK."
    assert re.match(TITLE_SET_REGEX, "Your title is: x") is None


def test_command_regex_matches_a_queued_title() -> None:
    assert re.match(TITLE_REGEX, "title is AFK.")
    assert not re.match(TITLE_REGEX, "title")


def test_trigger_matches_the_set_line() -> None:
    assert [t.regex for t in TRIGGERS] == [TITLE_SET_REGEX]


def test_event_names() -> None:
    assert EVENT_CLIENT_DISCONNECTED.endswith("clients_client_disconnected")
    assert EVENT_CLIENT_LOGGED_IN.endswith("clients_client_logged_in")
    assert EVENT_GMCP_COMM == "ev_libs.net.mud_gmcp_comm.channel"
