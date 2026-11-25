"""Tests for the pure helpers of the su plugin."""

import re
from typing import Any

import pytest

from aardwolf.move.libs import EVENT_DISCONNECT as MOVE_DISCONNECT
from aardwolf.move.libs import SUFFIX_ROOM as MOVE_ROOM
from aardwolf.skills.libs import FAILREASON, TRIGGERS, fail_payload
from aardwolf.skills.libs import SUFFIX_AFFECTED_UPDATE as SK_AFFECTED_UPDATE
from aardwolf.skills.libs import SUFFIX_AFFOFF as SK_AFFOFF
from aardwolf.skills.libs import SUFFIX_AFFON as SK_AFFON
from aardwolf.skills.libs import SUFFIX_FAIL as SK_FAIL
from aardwolf.skills.libs import SUFFIX_GAIN as SK_GAIN
from aardwolf.skills.libs import SUFFIX_RECOFF as SK_RECOFF
from aardwolf.skills.libs import SUFFIX_UPTODATE as SK_UPTODATE
from aardwolf.su.libs import (
    ACTION_BLOCK,
    ACTION_CLEAR,
    ACTION_DISABLE,
    ACTION_IGNORE,
    ACTION_NOCASTROOM,
    ACTION_NOMANA,
    ACTION_NOMOVES,
    ACTION_RESEND,
    ACTION_STOP,
    DISABLE_REASONS,
    EVENT_AFFECTED_UPDATE,
    EVENT_AFFOFF,
    EVENT_AFFON,
    EVENT_DISCONNECT,
    EVENT_FAIL,
    EVENT_GAIN,
    EVENT_MOVE_ROOM,
    EVENT_RECOFF,
    EVENT_UPTODATE,
    ORDER_KEY,
    PRACTICED_ABOVE,
    SELF_KEY,
    SpellupList,
    cast_blockers,
    check_lines,
    fail_action,
    is_active_state,
    list_header,
    list_row,
    next_spell,
    parse_spell_arg,
    room_key,
    to_int,
)


def test_constants_equal_those_of_the_other_plugins() -> None:
    assert f"ev_plugins.aardwolf.skills_{SK_AFFON}" == EVENT_AFFON
    assert f"ev_plugins.aardwolf.skills_{SK_AFFOFF}" == EVENT_AFFOFF
    assert f"ev_plugins.aardwolf.skills_{SK_RECOFF}" == EVENT_RECOFF
    assert f"ev_plugins.aardwolf.skills_{SK_GAIN}" == EVENT_GAIN
    assert f"ev_plugins.aardwolf.skills_{SK_FAIL}" == EVENT_FAIL
    assert f"ev_plugins.aardwolf.skills_{SK_AFFECTED_UPDATE}" == EVENT_AFFECTED_UPDATE
    assert f"ev_plugins.aardwolf.skills_{SK_UPTODATE}" == EVENT_UPTODATE
    assert EVENT_DISCONNECT == MOVE_DISCONNECT
    assert f"ev_plugins.aardwolf.move_{MOVE_ROOM}" == EVENT_MOVE_ROOM


@pytest.mark.parametrize(
    ("value", "expected"),
    [(3, 3), ("3", 3), (" 12 ", 12), (True, None), ("x", None), (None, None), ("-1", None)],
)
def test_to_int(value: object, expected: int | None) -> None:
    assert to_int(value) == expected


@pytest.mark.parametrize(
    ("state", "expected"),
    [(3, True), ("3", True), (8, False), (True, False), (None, False), ("", False)],
)
def test_is_active_state(state: object, expected: bool) -> None:
    assert is_active_state(state) is expected


@pytest.mark.parametrize(
    ("room", "expected"),
    [({"num": 5}, "5"), ({"num": "7"}, "7"), ({}, None), ({"num": None}, None), (None, None)],
)
def test_room_key(room: object, expected: str | None) -> None:
    assert room_key(room) == expected


@pytest.mark.parametrize(
    ("arg", "expected"),
    [
        ("bless", ("bless", -1)),
        ("bless:2", ("bless", 2)),
        ("bless:0", ("bless", 0)),
        ("bless:x", None),
        ("bless:", None),
        (":3", None),
        ("", None),
    ],
)
def test_parse_spell_arg(arg: str, expected: tuple[str, int] | None) -> None:
    assert parse_spell_arg(arg) == expected


def test_next_spell() -> None:
    enabled = {1: True, 2: False, 3: True, 4: True}
    usable = {1: False, 3: True, 4: True}
    order = [1, 2, 3, 4]
    args = (lambda sn: enabled[sn], lambda sn: usable.get(sn, False))
    assert next_spell(order, *args) == 3
    assert next_spell(order, *args, skip={3}) == 4
    assert next_spell(order, *args, skip={3, 4}) is None
    assert next_spell([], *args) is None


def blockers(**changes: object) -> list[str]:
    """cast_blockers with everything allowing a cast, except the changes."""
    values: dict[str, Any] = {
        "enabled": True,
        "connected": True,
        "active": True,
        "state": 3,
        "up_to_date": True,
        "waiting": None,
        "nocast": False,
        "nomana": False,
        "nomoves": False,
    }
    values.update(changes)
    return cast_blockers(**values)


def test_nothing_blocks_when_all_holds() -> None:
    assert blockers() == []


@pytest.mark.parametrize(
    "change",
    [
        {"enabled": False},
        {"connected": False},
        {"active": False},
        {"state": 8},
        {"state": True},
        {"up_to_date": False},
        {"waiting": 5},
        {"waiting": 0},
        {"nocast": True},
        {"nomana": True},
        {"nomoves": True},
    ],
)
def test_each_blocker_alone_blocks(change: dict[str, Any]) -> None:
    assert len(blockers(**change)) == 1


@pytest.mark.parametrize(
    ("reason", "sn", "waiting", "action"),
    [
        ("nomana", 1, None, ACTION_NOMANA),
        ("nomana", 1, 2, ACTION_NOMANA),
        ("nomoves", 1, None, ACTION_NOMOVES),
        ("nocastroom", 9, 1, ACTION_NOCASTROOM),
        ("fighting", 1, None, ACTION_STOP),
        ("notactive", 3, 1, ACTION_STOP),
        ("lostconc", 1, 1, ACTION_RESEND),
        ("lostconc", 1, 2, ACTION_IGNORE),
        ("lostconc", 1, None, ACTION_IGNORE),
        ("alreadyaff", 1, 1, ACTION_DISABLE),
        ("disabled", 1, 1, ACTION_DISABLE),
        ("wrongtarget", 1, 1, ACTION_DISABLE),
        ("alreadyaff", 1, 2, ACTION_IGNORE),
        ("recblock", 1, 1, ACTION_BLOCK),
        ("recblock", 1, None, ACTION_IGNORE),
        ("dontknow", 1, 1, ACTION_CLEAR),
        ("17", 1, 1, ACTION_CLEAR),
        ("dontknow", 1, 2, ACTION_IGNORE),
        (5, 1, 1, ACTION_CLEAR),
    ],
)
def test_fail_action(reason: object, sn: int, waiting: int | None, action: str) -> None:
    assert fail_action(reason, sn, waiting) == action


def test_every_disable_reason_is_a_skills_reason() -> None:
    assert set(DISABLE_REASONS) <= set(FAILREASON.values())


def test_a_sfail_line_gives_the_nomana_reason() -> None:
    spec = next(t for t in TRIGGERS if t.name == "skills_sfail")
    match = re.match(spec.regex, "{sfail}14,0,4,-1")
    assert match
    groups = {k: int(v) for k, v in match.groupdict().items()}
    payload = fail_payload(**groups)
    assert payload["reason"] == "nomana"
    assert fail_action(payload["reason"], payload["sn"], None) == ACTION_NOMANA


def test_list_formatting() -> None:
    header = list_header()
    assert header[0].split() == ["Num", "-", "Name", ":", "A", "P", "B", "D", "NP", "NL"]
    row = list_row(2, "bless", affected=True, pending=True, blocked=True, disabled=True, percent=0)
    assert row.split() == ["2", "-", "bless", ":", "A", "P", "B", "D", "NL"]
    row = list_row(
        0, "sanctuary", affected=False, pending=False, blocked=False, disabled=False, percent=5
    )
    assert row.split() == ["0", "-", "sanctuary", ":", "NP"]
    row = list_row(
        0, "sanctuary", affected=False, pending=False, blocked=False, disabled=False, percent=80
    )
    assert row.split() == ["0", "-", "sanctuary", ":"]


def test_check_lines() -> None:
    lines = check_lines(
        enabled=True,
        connected=False,
        active=True,
        waiting=None,
        nocast=False,
        nomoves=False,
        nomana=True,
        up_to_date=True,
        state=3,
    )
    assert len(lines) == 9
    assert lines[0].startswith("enabled")
    assert "False" in lines[1]
    assert "True" in lines[6]


def make(order: object, entries: object) -> tuple[dict[str, Any], SpellupList]:
    data: dict[str, Any] = {ORDER_KEY: order, SELF_KEY: entries}
    return data, SpellupList(data)


def test_normalize_an_empty_mapping() -> None:
    data: dict[str, Any] = {}
    ups = SpellupList(data)
    assert data == {ORDER_KEY: [], SELF_KEY: {}}
    assert ups.order() == []


def test_normalize_an_old_file() -> None:
    data, ups = make(
        ["3", 5, 3, "x", 7],
        {"3": {"enabled": False}, "5": {"enabled": True}, "99": {"enabled": True}},
    )
    data["oorder"] = []
    data["other"] = {}
    assert ups.normalize() is True
    assert "oorder" not in data
    assert "other" not in data
    assert ups.order() == [3, 5, 7]
    assert data[SELF_KEY] == {3: {"enabled": False}, 5: {"enabled": True}, 7: {"enabled": True}}
    assert ups.normalize() is False


def test_normalize_garbage_does_not_raise() -> None:
    data: dict[str, Any] = {ORDER_KEY: "no", SELF_KEY: ["no"]}
    ups = SpellupList(data)
    assert ups.order() == []


def test_add_remove_and_enable() -> None:
    _, ups = make([], {})
    assert ups.add(10) == 0
    assert ups.add(20) == 1
    assert ups.add(30, 0) == 0
    assert ups.order() == [30, 10, 20]
    assert ups.add(10) is None
    assert ups.contains(20)
    assert ups.is_enabled(20)
    assert ups.set_enabled(20, False) is True
    assert not ups.is_enabled(20)
    assert ups.set_enabled(99, False) is False
    assert not ups.is_enabled(99)
    ups.set_all(False)
    assert not any(ups.is_enabled(sn) for sn in ups.order())
    ups.set_all(True)
    assert all(ups.is_enabled(sn) for sn in ups.order())
    assert ups.remove(10) is True
    assert ups.remove(10) is False
    assert ups.order() == [30, 20]
    ups.clear()
    assert ups.order() == []
    assert not ups.contains(30)


def test_order_returns_a_copy() -> None:
    _, ups = make([1], {1: {"enabled": True}})
    ups.order().append(2)
    assert ups.order() == [1]


def test_list_row_practiced_above_parameter() -> None:
    kwargs = {"affected": False, "pending": False, "blocked": False, "disabled": False}
    assert "NP" not in list_row(0, "bless", percent=50, **kwargs).split()
    assert "NP" in list_row(0, "bless", percent=50, practiced_above=50, **kwargs).split()
    assert "NP" in list_row(0, "bless", percent=PRACTICED_ABOVE, **kwargs).split()
