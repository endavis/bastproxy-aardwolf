"""Tests for the pure helpers of the move plugin."""

from typing import Any

from aardwolf.move.libs import (
    EVENT_MOVE_ROOM,
    EVENTS,
    UNKNOWN,
    find_direction,
    move_payload,
    room_num,
)


def room(num: int, **exits: int) -> dict[str, Any]:
    """Build a room.info message."""
    return {"num": num, "exits": dict(exits)}


def test_find_direction_match() -> None:
    """The exit that leads to the new room is the direction."""
    assert find_direction(room(1, n=2, s=3), room(2)) == "n"


def test_find_direction_unknown() -> None:
    """No match, no exits, or bad exits give unknown."""
    assert find_direction(room(1, n=2), room(9)) == UNKNOWN
    assert find_direction({"num": 1}, room(2)) == UNKNOWN
    assert find_direction({"num": 1, "exits": "x"}, room(2)) == UNKNOWN


def test_find_direction_last_match_wins() -> None:
    """Two exits to the same room give the last one, as the old plugin did."""
    assert find_direction(room(1, n=2, d=2), room(2)) == "d"


def test_move_payload_none() -> None:
    """No last room and the same room give no payload."""
    assert move_payload(None, room(1)) is None
    assert move_payload(room(1, n=2), room(1)) is None


def test_move_payload_move_and_copies() -> None:
    """A move gives from, to and direction, as copies."""
    last, new = room(1, n=2), room(2, s=1)
    payload = move_payload(last, new)
    assert payload is not None
    assert payload == {"from": last, "to": new, "direction": "n"}
    payload["from"]["exits"]["n"] = 99
    payload["to"]["num"] = 99
    assert last == room(1, n=2)
    assert new == room(2, s=1)


def test_room_num() -> None:
    """The num of a dict with one, else None."""
    assert room_num({"num": 5}) == 5
    assert room_num({"x": 1}) is None
    assert room_num("num") is None
    assert room_num(None) is None


def test_events() -> None:
    """One event with the three payload keys described."""
    assert set(EVENTS) == {EVENT_MOVE_ROOM}
    assert set(EVENTS[EVENT_MOVE_ROOM]["arg_descriptions"]) == {"from", "to", "direction"}
