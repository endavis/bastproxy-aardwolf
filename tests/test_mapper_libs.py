"""Tests for the pure helpers of the mapper plugin."""

from typing import Any

import pytest

from aardwolf.mapper.libs import (
    SEARCHES,
    area_from_gmcp,
    detail_matches,
    mismatch_lines,
    requirement_allowed,
    room_from_gmcp,
    room_uid,
    search_lines,
    steps_to_commands,
    stored_room_with_flags,
    to_int,
)

ROOM: dict[str, Any] = {
    "num": 1234,
    "name": "A Room",
    "zone": "aylor",
    "terrain": "city",
    "details": "bank,safe",
    "exits": {"n": 1235, "s": -1},
    "coord": {"id": 0, "x": 30, "y": 19, "cont": 0},
}


def step(direction: str, fromuid: str = "1") -> dict[str, Any]:
    """Return a walk step."""
    return {"fromuid": fromuid, "touid": "2", "dir": direction, "cost": 1, "requirement": None}


@pytest.mark.parametrize(
    ("info", "expected"),
    [
        ({"num": 1234}, "1234"),
        ({"num": "1234"}, "1234"),
        ({"num": -1}, None),
        ({"num": "-1"}, None),
        ({"num": 0}, None),
        ({}, None),
        ({"num": "abc"}, None),
        (None, None),
        ([1234], None),
    ],
)
def test_room_uid(info: object, expected: str | None) -> None:
    """Only a real room num gives a uid."""
    assert room_uid(info) == expected


def test_to_int() -> None:
    """Numbers convert; anything else is 0."""
    assert to_int("5") == 5
    assert to_int("x") == 0
    assert to_int(None) == 0


def test_room_from_gmcp_full() -> None:
    """A full payload maps to the core room dict."""
    room = room_from_gmcp(ROOM, "A Room", ["noportal"])
    assert room == {
        "uid": "1234",
        "name": "A Room",
        "area": "aylor",
        "terrain": "city",
        "x": 30,
        "y": 19,
        "z": 0,
        "details": {"details": "bank,safe", "coord_id": 0, "cont": 0},
        "flags": ["noportal"],
        "exits": {"n": "1235", "s": "-1"},
    }


def test_room_from_gmcp_sparse() -> None:
    """Missing coord and exits, bad coordinates and bad exit values are handled."""
    room = room_from_gmcp({"num": 5, "exits": {"n": "x", "e": 0}}, "R", [])
    assert room["x"] is None
    assert room["y"] is None
    assert room["exits"] == {"n": "-1", "e": "-1"}
    bad = room_from_gmcp({"num": 5, "coord": {"x": "a", "y": None}}, "R", [])
    assert bad["x"] is None
    assert bad["y"] is None
    assert bad["exits"] == {}


def test_area_from_gmcp() -> None:
    """A room.area message maps to the area.add arguments."""
    data = {"id": "aylor", "name": "Aylor", "col": "@W", "texture": "x", "flags": "virtual,foo"}
    assert area_from_gmcp(data) == {
        "uid": "aylor",
        "name": "Aylor",
        "flags": ["virtual", "foo"],
        "details": {"col": "@W", "texture": "x"},
    }
    empty = area_from_gmcp({"id": "a", "flags": ""})
    assert empty is not None
    assert empty["flags"] == []
    assert area_from_gmcp({"name": "x"}) is None
    assert area_from_gmcp("x") is None


@pytest.mark.parametrize(("level", "allowed"), [(99, False), (100, True), (101, True)])
def test_requirement_level(level: int, allowed: bool) -> None:
    """The level must reach the one required."""
    assert requirement_allowed({"level": 100}, step("n"), level, 0) is allowed


@pytest.mark.parametrize(("tier", "allowed"), [(0, False), (1, True), (2, True)])
def test_requirement_tier(tier: int, allowed: bool) -> None:
    """The tier must reach the one required."""
    assert requirement_allowed({"tier": 1}, step("n"), 200, tier) is allowed


def test_requirement_empty_and_bad() -> None:
    """An empty dict allows the exit; a bad requirement blocks it."""
    assert requirement_allowed({}, step("n"), 1, 0)
    assert not requirement_allowed("x", step("n"), 201, 0)
    assert not requirement_allowed(None, step("n"), 201, 0)
    assert not requirement_allowed({"level": "5"}, step("n"), 201, 0)
    assert not requirement_allowed({"tier": True}, step("n"), 201, 0)


def test_requirement_anywhere_counts_tier_levels() -> None:
    """An exit from * adds ten levels per tier."""
    portal = step("enter", "*")
    assert requirement_allowed({"level": 105}, portal, 100, 1)
    assert not requirement_allowed({"level": 105}, step("enter"), 100, 1)
    assert not requirement_allowed({"level": 105}, portal, 100, 0)


def test_requirement_unknown_level_and_tier() -> None:
    """An unknown level counts as 201, an unknown tier as 0."""
    assert requirement_allowed({"level": 201}, step("n"), None, None)
    assert not requirement_allowed({"tier": 1}, step("n"), None, None)


@pytest.mark.parametrize(
    ("dirs", "expected"),
    [
        (["n", "n", "n", "e", "e"], ["run 3n2e"]),
        (["n"], ["n"]),
        (["n", "e"], ["run ne"]),
        (["n", "s", "n"], ["run nsn"]),
        ([], []),
    ],
)
def test_steps_to_commands_plain(dirs: list[str], expected: list[str]) -> None:
    """Plain directions are joined into a run."""
    assert steps_to_commands([step(d) for d in dirs]) == expected


def test_steps_to_commands_special() -> None:
    """A non-direction step splits the run and is sent as it is."""
    steps = [step("n"), step("enter portal"), step("e"), step("e")]
    assert steps_to_commands(steps) == ["n", "enter portal", "run 2e"]
    assert steps_to_commands([step("enter aylor", "*")]) == ["enter aylor"]
    assert steps_to_commands([step("n", "*"), step("e")]) == ["n", "e"]


def test_mismatch_lines_area() -> None:
    """An area change names both areas and both purge hints."""
    lines = mismatch_lines("12", {"area": ("old", "new")})
    assert any("area old -> new" in line for line in lines)
    assert any("purge -a old" in line for line in lines)
    assert any("purge -r 12" in line for line in lines)


def test_mismatch_lines_exits_and_both() -> None:
    """An exit side that is missing shows as none."""
    exits = {"n": (None, "5"), "s": ("6", None), "e": ("7", "8")}
    lines = mismatch_lines("12", {"exits": exits})
    assert any("n: none -> 5" in line for line in lines)
    assert any("s: 6 -> none" in line for line in lines)
    assert any("e: 7 -> 8" in line for line in lines)
    both = mismatch_lines("12", {"area": ("a", "b"), "exits": exits})
    assert any("area a -> b" in line for line in both)
    assert any("n: none -> 5" in line for line in both)


@pytest.mark.parametrize(
    ("details", "expected"),
    [
        ({"details": "Bank, safe"}, ["Bank"]),
        ({"details": " SHOP ,bank,Trainer"}, ["Shop", "Bank"]),
        ({"details": ""}, []),
        ({"details": None}, []),
        ({"details": "shopkeeper"}, []),
        ({}, []),
        (None, []),
        ("bank", []),
        (["bank"], []),
    ],
)
def test_detail_matches(details: object, expected: list[str]) -> None:
    """Items match whole, after strip and lowercase; anything else matches nothing."""
    assert detail_matches(details, SEARCHES["shops"]) == expected


def test_search_lines() -> None:
    """The table has the title, the header and one line per row."""
    assert search_lines("Mapper shops in aylor: 1 rooms", [("1", "A Bank", "aylor", "Bank")]) == [
        "Mapper shops in aylor: 1 rooms",
        "uid | name | area | found",
        "1 | A Bank | aylor | Bank",
    ]


def test_stored_room_with_flags() -> None:
    """Only missing flags are added, and the dict has no exits or note."""
    stored = {
        "uid": "1",
        "name": "R",
        "area": "a",
        "terrain": "t",
        "x": 1,
        "y": 2,
        "z": 3,
        "details": {"details": "bank"},
        "flags": ["noportal"],
        "exits": [{"dir": "n"}],
        "note": "x",
    }
    assert stored_room_with_flags(stored, ["noportal"]) is None
    assert stored_room_with_flags(stored, []) is None
    assert stored_room_with_flags(stored, ["noportal", "norecall"]) == {
        "uid": "1",
        "name": "R",
        "area": "a",
        "terrain": "t",
        "x": 1,
        "y": 2,
        "z": 3,
        "details": {"details": "bank"},
        "flags": ["noportal", "norecall"],
    }
    assert stored_room_with_flags({"uid": "2"}, ["norecall"])["flags"] == ["norecall"]  # type: ignore[index]
