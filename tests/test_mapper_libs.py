"""Tests for the pure helpers of the mapper plugin."""

import re
from typing import Any

import pytest

from aardwolf.mapper.libs import (
    CEXIT_TEXT_COLUMNS,
    EXIT_TEXT_COLUMNS,
    MAX_AREA_ARG,
    NORECALL_REGEX,
    PLACE_KINDS,
    PLACE_TEXT_COLUMNS,
    PORTAL_PREFIX,
    PORTAL_TEXT_COLUMNS,
    SEARCHES,
    PortalStep,
    area_arg,
    area_from_gmcp,
    area_link,
    detail_matches,
    is_cexit,
    is_recall_command,
    mismatch_lines,
    movement_chunks,
    movement_plan,
    parse_command,
    portal_marker,
    portal_requirement,
    portal_serial,
    portal_sort_key,
    requirement_allowed,
    requirement_level,
    resolve_portal,
    room_from_gmcp,
    room_link,
    room_uid,
    serial_arg,
    split_command,
    steps_to_commands,
    table_data,
    table_view,
    to_int,
    total_wait,
)

ROOM: dict[str, Any] = {
    "num": 1234,
    "name": "A Room",
    "zone": "aylor",
    "terrain": "city",
    "details": "bank,safe",
    "exits": {"n": 1235, "s": -1},
    "coord": {"id": 0, "x": 30, "y": 19, "cont": 1},
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
        "details": {"details": "bank,safe", "coord_id": 0, "cont": 1},
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


def test_room_from_gmcp_non_continent_has_no_coords() -> None:
    """A room whose coord cont is 0 shares its area's coordinates, so x and y are unset."""
    info = {"num": 7, "coord": {"id": 3, "x": 40, "y": 12, "cont": 0}}
    room = room_from_gmcp(info, "R", [])
    assert room["x"] is None
    assert room["y"] is None
    assert room["details"]["coord_id"] == 3
    assert room["details"]["cont"] == 0


def test_room_from_gmcp_missing_cont_has_no_coords() -> None:
    """A coord without cont gives no x and y."""
    room = room_from_gmcp({"num": 7, "coord": {"id": 3, "x": 40, "y": 12}}, "R", [])
    assert room["x"] is None
    assert room["y"] is None


def test_room_from_gmcp_continent_keeps_coords() -> None:
    """A room whose coord cont is 1 keeps its x and y."""
    room = room_from_gmcp({"num": 7, "coord": {"id": 0, "x": 40, "y": 12, "cont": 1}}, "R", [])
    assert room["x"] == 40
    assert room["y"] == 12


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
    assert not any("purge -r" in line for line in lines)
    assert any("#bp.client.mapper.accept 12" in line for line in lines)


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
    # a retargeted or removed exit is held by the core, so it gets the accept and ignore hints
    assert any("mapper.accept 12" in line for line in lines)
    assert any("mapper.ignoreexits 12" in line for line in lines)
    # a new direction is written at once and needs no hint
    fresh = mismatch_lines("12", {"exits": {"n": (None, "5")}})
    assert any("exit n: none -> 5" in line for line in fresh)
    assert not any("mapper." in line for line in fresh)


@pytest.mark.parametrize("key", ["name", "terrain"])
def test_mismatch_lines_single_change(key: str) -> None:
    """A name or terrain change alone is shown, with no hint."""
    lines = mismatch_lines("12", {key: ("Old", "New")})
    assert lines == ["Mapper: room 12 differs from the map", f"  {key}: Old -> New"]


def test_mismatch_lines_coordinates_and_details() -> None:
    """Coordinates and detail changes are shown; a missing side is none."""
    lines = mismatch_lines(
        "12",
        {"x": (None, 4), "y": (1, 2), "z": (0, -1), "details": {"details": ("bank", "bank,shop")}},
    )
    assert "  x: none -> 4" in lines
    assert "  y: 1 -> 2" in lines
    assert "  z: 0 -> -1" in lines
    assert "  details details: bank -> bank,shop" in lines


def test_mismatch_lines_escape() -> None:
    """Every shown value goes through the escape callable."""
    lines = mismatch_lines(
        "12", {"name": ("a", "b"), "exits": {"n": ("c", None)}}, escape=lambda s: s.upper()
    )
    assert "  name: A -> B" in lines
    assert "  exit N: C -> none" in lines


@pytest.mark.parametrize(
    "differences",
    [{"area": "x"}, {"exits": [1]}, {"details": "y"}, {"exits": {"n": 5}}, {"name": ("a",)}],
)
def test_mismatch_lines_malformed(differences: dict[str, Any]) -> None:
    """A malformed payload entry is ignored."""
    assert mismatch_lines("12", differences) == ["Mapper: room 12 differs from the map"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("You cannot recall from this room.", True),
        ("You cannot return home from this room.", True),
        ("You cannot recall from this room. You feel trapped.", True),
        ("You cannot return home from this room. Try later.", True),
        ("You cannot recall.", False),
        ("You can recall from this room.", False),
        ("Bob says 'You cannot recall from this room.'", False),
        ("You cannot portal from this room.", False),
    ],
)
def test_norecall_regex(text: str, expected: bool) -> None:
    """The norecall message matches with text after the period, like the trigger engine."""
    assert bool(re.match(NORECALL_REGEX, text)) is expected


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


def test_split_command() -> None:
    """A command splits on ; into text and waits; empty parts go and long waits are capped."""
    assert split_command("open north;wait(2);north") == ["open north", 2.0, "north"]
    assert split_command(" a ; ;b; ") == ["a", "b"]
    assert split_command("wait(0.5)") == [0.5]
    assert split_command("wait(100)") == [40.0]
    assert split_command("wait(x);go") == ["wait(x)", "go"]
    assert split_command("") == []


@pytest.mark.parametrize(
    "text", ["", " ; ", "wait(0)", "wait(41)", "wait(x)", "go;wait(-1)", "go;wait()"]
)
def test_parse_command_refuses(text: str) -> None:
    """An empty command or a bad wait cannot be stored."""
    assert parse_command(text) is None


def test_parse_command_accepts() -> None:
    """A good command parses like split_command; the limits are allowed."""
    assert parse_command("open north;wait(2);north") == ["open north", 2.0, "north"]
    assert parse_command("wait(40)") == [40.0]
    assert parse_command("wait(0.5)") == [0.5]
    assert total_wait(["a", 2.0, "b", 0.5]) == 2.5


def test_movement_chunks_plain() -> None:
    """Plain steps still make one speedwalk in one chunk with no delay."""
    steps = [step(d) for d in ("n", "n", "n", "e", "e")]
    assert movement_chunks(steps) == [(0.0, ["run 3n2e"])]
    assert steps_to_commands(steps) == ["run 3n2e"]
    assert movement_chunks([]) == []


def test_movement_chunks_cexit_waits() -> None:
    """A cexit splits the walk; each wait starts a chunk with its delay."""
    steps = [
        step("n"),
        step("n"),
        step("open door;wait(2);e"),
        step("s"),
        step("s"),
    ]
    assert movement_chunks(steps) == [(0.0, ["run 2n", "open door"]), (2.0, ["e", "run 2s"])]
    assert steps_to_commands(steps) == ["run 2n", "open door", "e", "run 2s"]


def test_movement_chunks_portal_and_leading_wait() -> None:
    """A portal command is split on ;, and a wait first leaves an empty first chunk."""
    portal = step("hold amulet;enter;hold sword", fromuid="*")
    assert movement_chunks([portal]) == [(0.0, ["hold amulet", "enter", "hold sword"])]
    assert movement_chunks([step("wait(3);go")]) == [(0.0, []), (3.0, ["go"])]
    assert movement_chunks([step("n", fromuid="*")]) == [(0.0, ["n"])]


def test_is_cexit() -> None:
    """Only a non-plain direction from a real room is a custom exit."""
    assert is_cexit({"fromuid": "1", "dir": "open door;n"})
    assert not is_cexit({"fromuid": "1", "dir": "n"})
    assert not is_cexit({"fromuid": "*", "dir": "enter"})
    assert not is_cexit({"fromuid": "**", "dir": "recall"})


def test_is_recall_command() -> None:
    """recall, home and hom are recalls, in any case."""
    assert all(is_recall_command(c) for c in ("recall", " Home ", "HOM"))
    assert not is_recall_command("enter portal")


def test_requirement_level_for_display() -> None:
    """The level of a requirement, or 0."""
    assert requirement_level({"level": 50}) == 50
    assert requirement_level({"tier": 1}) == 0
    assert requirement_level(None) == 0


def test_portal_sort_key() -> None:
    """Portals sort by area, then room number, then command."""
    rooms = {"9": {"area": "a"}, "10": {"area": "a"}, "5": {"area": "b"}}
    portals = [
        {"touid": "5", "dir": "x"},
        {"touid": "10", "dir": "y"},
        {"touid": "9", "dir": "z"},
        {"touid": "9", "dir": "a"},
        {"touid": "77", "dir": "q"},
    ]
    ordered = sorted(portals, key=lambda p: portal_sort_key(p, rooms.get(p["touid"])))
    assert [(p["touid"], p["dir"]) for p in ordered] == [
        ("77", "q"),
        ("9", "a"),
        ("9", "z"),
        ("10", "y"),
        ("5", "x"),
    ]


def test_resolve_portal() -> None:
    """A portal is found by #N or by its exact command."""
    portals = [{"dir": "one"}, {"dir": "two"}]
    assert resolve_portal(portals, "#2") == {"dir": "two"}
    assert resolve_portal(portals, "#9") is None
    assert resolve_portal(portals, "#0") is None
    assert resolve_portal(portals, "#x") is None
    assert resolve_portal(portals, "one") == {"dir": "one"}
    assert resolve_portal(portals, "three") is None


def test_table_data() -> None:
    """Rows become dicts keyed by the column keys, in row order."""
    assert table_data(EXIT_TEXT_COLUMNS, [("n", "1", "0"), ("s", "2", "5")]) == [
        {"exit": "n", "to": "1", "level": "0"},
        {"exit": "s", "to": "2", "level": "5"},
    ]
    assert table_data(EXIT_TEXT_COLUMNS, []) == []
    with pytest.raises(ValueError):
        table_data(EXIT_TEXT_COLUMNS, [("n", "1")])


def test_text_columns() -> None:
    """Each text column list has unique keys, today's headers and exactly name and key."""
    headers = {
        "PLACE": ["uid", "name", "area", "found"],
        "CEXIT": ["uid", "name", "area", "command", "to", "level"],
        "EXIT": ["exit", "to", "level"],
        "PORTAL": ["#", "kind", "area", "name", "to", "command", "level"],
    }
    lists = {
        "PLACE": PLACE_TEXT_COLUMNS,
        "CEXIT": CEXIT_TEXT_COLUMNS,
        "EXIT": EXIT_TEXT_COLUMNS,
        "PORTAL": PORTAL_TEXT_COLUMNS,
    }
    for kind, columns in lists.items():
        assert [c["name"] for c in columns] == headers[kind]
        assert len({c["key"] for c in columns}) == len(columns)
        assert all(set(c) == {"name", "key"} for c in columns)


COLUMNS = [
    {"name": "uid", "label": "Room", "type": "text"},
    {"name": "name", "label": "Name", "type": "text"},
    {"name": "level", "label": "Level", "type": "int"},
]
ROWS: list[list[Any]] = [
    ["10", {"text": "Beta", "href": "/x?uid=10"}, 5],
    ["2", {"text": "alpha", "href": "/x?uid=2"}, 5],
    ["3", "Gamma", 1],
    ["x", "beta two", 9],
]


def view(
    *,
    sort: str | None = None,
    descending: bool = False,
    filters: dict[str, str | int | float] | None = None,
    offset: int = 0,
    count: int = 50,
) -> tuple[list[Any], int]:
    """Run table_view over ROWS; the defaults change nothing."""
    return table_view(
        ROWS,
        COLUMNS,
        sort=sort,
        descending=descending,
        filters=filters or {},
        offset=offset,
        count=count,
    )


def test_links_hold_only_text_and_href() -> None:
    """A link cell is exactly the two keys, with the uid percent-encoded."""
    assert room_link("5", "Inn") == {"text": "Inn", "href": "/client/mapper/room?uid=5"}
    assert area_link("a b&c", "A") == {"text": "A", "href": "/client/mapper/area?uid=a+b%26c"}


def test_area_arg() -> None:
    """The area is trimmed and lower cased, empty is here, too long is refused."""
    assert area_arg("  AyLor ") == "aylor"
    assert area_arg("") == "here"
    assert area_arg("a" * MAX_AREA_ARG) == "a" * MAX_AREA_ARG
    assert area_arg("a" * (MAX_AREA_ARG + 1)) is None


def test_place_kinds_are_the_searches_and_notes() -> None:
    """The places page offers every search command."""
    assert PLACE_KINDS == ("shops", "train", "quest", "notes")


def test_table_view_without_options_keeps_order() -> None:
    """No sort and no filter returns every row in order."""
    rows, total = view()
    assert rows == ROWS
    assert total == 4


def test_table_view_sorts_text_by_link_text_and_room_numbers_by_value() -> None:
    """A link sorts by its text, digits by value before other text; descending reverses."""
    assert [r[0] for r in view(sort="uid")[0]] == ["2", "3", "10", "x"]
    assert [r[0] for r in view(sort="name")[0]] == ["2", "10", "x", "3"]
    assert [r[0] for r in view(sort="name", descending=True)[0]] == ["3", "x", "10", "2"]


def test_table_view_sort_is_stable() -> None:
    """Equal cells keep their order, ascending and descending."""
    assert [r[0] for r in view(sort="level")[0]] == ["3", "10", "2", "x"]
    assert [r[0] for r in view(sort="level", descending=True)[0]] == ["x", "10", "2", "3"]


def test_table_view_filters() -> None:
    """Text matches a part without case, a link by its text; an int matches when equal."""
    assert [r[0] for r in view(filters={"name": "BETA"})[0]] == ["10", "x"]
    assert view(filters={"level": 5})[1] == 2
    assert [r[0] for r in view(filters={"name": "beta", "level": 9})[0]] == ["x"]
    assert view(filters={"name": "zzz"}) == ([], 0)


def test_table_view_pages() -> None:
    """The offset and count pick the page; the total counts all matching rows."""
    rows, total = view(offset=1, count=2)
    assert [r[0] for r in rows] == ["2", "3"]
    assert total == 4
    assert view(offset=10) == ([], 4)


@pytest.mark.parametrize(
    ("text", "serial"),
    [("1234", 1234), (" 7 ", 7), ("0", None), ("-5", None), ("12 34", None), ("enter", None),
     ("hold 5", None), ("", None), ("\u0663", None), (5, None)],
)  # fmt: skip
def test_serial_arg(text: object, serial: int | None) -> None:
    """A single word of ascii digits above 0 is a serial."""
    assert serial_arg(text) == serial


def test_portal_marker_round_trip() -> None:
    """The marker holds the serial and reads back; other directions have none."""
    assert portal_marker(1234) == f"{PORTAL_PREFIX}1234"
    assert portal_serial(portal_marker(1234)) == 1234
    for direction in ("n", "enter portal", f"{PORTAL_PREFIX}x", f"{PORTAL_PREFIX}0", None):
        assert portal_serial(direction) is None


def test_portal_requirement() -> None:
    """The serial is always in the requirement; the level only above 0."""
    assert portal_requirement(5, 40) == {"serial": 5, "level": 40}
    assert portal_requirement(5, 0) == {"serial": 5}
    assert portal_requirement(5, -3) == {"serial": 5}


def test_requirement_allowed_ignores_serial() -> None:
    """The serial key does not change the level check."""
    anywhere = {"fromuid": "*", "dir": portal_marker(5)}
    assert requirement_allowed({"serial": 5}, anywhere, 1, 0)
    assert requirement_allowed({"serial": 5, "level": 40}, anywhere, 40, 0)
    assert not requirement_allowed({"serial": 5, "level": 40}, anywhere, 39, 0)


def test_movement_plan() -> None:
    """Item portal steps split the chunks; no item portal gives the movement chunks."""
    walk = [{"fromuid": "1", "dir": "n"}, {"fromuid": "1", "dir": "n"}]
    assert movement_plan(walk) == movement_chunks(walk)
    assert movement_plan([]) == []
    marker = portal_marker(9)
    steps = [
        {"fromuid": "1", "dir": "n"},
        {"fromuid": "*", "dir": marker},
        {"fromuid": "2", "dir": "e"},
        {"fromuid": "2", "dir": "open;wait(2);w"},
    ]
    assert movement_plan(steps) == [
        (0.0, ["n"]),
        PortalStep(9),
        (0.0, ["e", "open"]),
        (2.0, ["w"]),
    ]
    assert movement_plan(steps[1:2]) == [PortalStep(9)]
    # a marker that is not from * is a plain command
    assert movement_plan([{"fromuid": "1", "dir": marker}]) == [(0.0, [marker])]
