"""Tests for the mapper web pages: rows match the text commands and links are well formed."""

import html
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from mapper_support import Env, build_env, room

from aardwolf.mapper.libs import CEXIT_COLUMNS, PLACE_COLUMNS, PORTAL_COLUMNS

Page = dict[str, Any]


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """A plugin with a stateful fake mapper."""
    yield build_env(monkeypatch, tmp_path)


def request(
    query: dict[str, str] | None = None,
    *,
    sort: str | None = None,
    descending: bool = False,
    filters: dict[str, str | int | float] | None = None,
    offset: int = 0,
    count: int = 50,
) -> SimpleNamespace:
    """Return a stand-in for the web request of a table route."""
    table = SimpleNamespace(
        sort=sort, descending=descending, filters=filters or {}, offset=offset, count=count
    )
    return SimpleNamespace(query=query or {}, table=table)


def text(cell: object) -> str:
    """Return the text of a cell."""
    return str(cell["text"]) if isinstance(cell, dict) else str(cell)


def texts(page: Page) -> list[str]:
    """Return a table page as the ' | ' lines of the text commands, links read by their text."""
    return [" | ".join(text(cell) for cell in row) for row in page["rows"]]


def add_rooms(env: Env) -> None:
    """Rooms 1 to 3 in area a, 9 in area b, with details and notes, standing in room 1."""
    for uid, area, name, details in (
        ("10", "a", "Bank of A", "bank,safe"),
        ("2", "a", "Smith", "shop"),
        ("3", "a", "Trainer Hall", "trainer"),
        ("9", "b", "Quest Hut", "questor"),
    ):
        env.fake.rooms[uid] = {**room(uid, area, name), "details": {"details": details}}
    env.fake.rooms["1"] = room("1", "a", "Start")
    env.fake.notes["3"] = "mind the step"
    env.fake.exit_add("1", "n", "2")
    env.fake.exit_add("1", "open door;wait(2);e", "3", 1, {"level": 50})
    env.fake.exit_add("3", "pull lever", "9")
    env.fake.exit_add("9", "squeeze", "1", 1, {"level": 7})
    env.fake.exit_add("*", "enter", "2", 1, {"level": 20})
    env.fake.exit_add("**", "recall", "3")
    env.fake.current = "1"


@pytest.fixture
def mapped(env: Env) -> Env:
    """The plugin with rooms, exits, portals and notes."""
    add_rooms(env)
    return env


def test_columns_are_valid() -> None:
    """Names are lower case words, unique, and the types are text or int."""
    for columns in (PORTAL_COLUMNS, CEXIT_COLUMNS, PLACE_COLUMNS):
        names = [column["name"] for column in columns]
        assert len(names) == len(set(names))
        assert all(name.replace("_", "").isalnum() and name.islower() for name in names)
        assert {column["type"] for column in columns} <= {"text", "int"}


def test_portals_match_the_command(mapped: Env) -> None:
    """The page lists the rows of the portals command; the numbers are ints."""
    assert mapped.run("portals", filter="").success
    command = [" | ".join(cells) for cells in mapped.table_cells()]
    page = mapped.plugin._web_portals(request())
    assert page["kind"] == "table"
    assert page["total"] == 2
    assert texts(page) == [line.replace("#", "") for line in command]
    assert [row[0] for row in page["rows"]] == [1, 2]
    assert [row[6] for row in page["rows"]] == [20, 0]


def test_portals_links(mapped: Env) -> None:
    """The area and the name link to the core mapper pages; the cells are exactly text and href."""
    row = mapped.plugin._web_portals(request())["rows"][0]
    assert row[2] == {"text": "a", "href": "/client/mapper/area?uid=a"}
    assert row[3] == {"text": "Smith", "href": "/client/mapper/room?uid=2"}
    assert row[4] == "2"


def test_portal_to_an_unknown_room_has_no_link(env: Env) -> None:
    """A portal into a room that is not mapped gets plain empty cells, not a link."""
    env.fake.exit_add("*", "enter", "55")
    row = env.plugin._web_portals(request())["rows"][0]
    assert row[2] == ""
    assert row[3] == ""
    assert row[4] == "55"


def test_cexits_default_to_the_current_area(mapped: Env) -> None:
    """Without `area` the page lists the custom exits of the current room's area."""
    assert mapped.run("cexits", where="here").success
    command = [" | ".join(cells) for cells in mapped.table_cells()]
    page = mapped.plugin._web_cexits(request())
    assert page["title"] == "Custom exits in a"
    assert texts(page) == command
    assert page["total"] == 2


def test_cexits_of_a_named_area_ignore_case(mapped: Env) -> None:
    """`area` picks the area, in any case, like the command."""
    assert mapped.run("cexits", where="b").success
    command = [" | ".join(cells) for cells in mapped.table_cells()]
    page = mapped.plugin._web_cexits(request({"area": " B "}))
    assert texts(page) == command
    assert command == ["9 | Quest Hut | b | squeeze | 1 | 7"]


def test_cexit_row_cells(mapped: Env) -> None:
    """The name links to the room, the area to the area, the level is an int."""
    row = mapped.plugin._web_cexits(request())["rows"][0]
    assert row == [
        "1",
        {"text": "Start", "href": "/client/mapper/room?uid=1"},
        {"text": "a", "href": "/client/mapper/area?uid=a"},
        "open door;wait(2);e",
        "3",
        50,
    ]


def test_cexits_locks(mapped: Env) -> None:
    """show=locks lists every exit of the area with a level above 0, plain exits too."""
    mapped.fake.exit_add("2", "e", "3", 1, {"level": 5})
    page = mapped.plugin._web_cexits(request({"show": "locks"}))
    assert page["title"] == "Locked exits in a"
    assert texts(page) == [
        "1 | Start | a | open door;wait(2);e | 3 | 50",
        "2 | Smith | a | e | 3 | 5",
    ]
    other = mapped.plugin._web_cexits(request({"show": "locks", "area": "b"}))
    assert texts(other) == ["9 | Quest Hut | b | squeeze | 1 | 7"]


def test_cexits_locks_leave_out_free_exits(mapped: Env) -> None:
    """An area whose exits have no requirement lists nothing."""
    mapped.fake.exits.clear()
    mapped.fake.exit_add("1", "n", "2")
    page = mapped.plugin._web_cexits(request({"show": "locks"}))
    assert page["rows"] == []
    assert page["total"] == 0


def test_cexits_errors(mapped: Env) -> None:
    """An unknown area is 404, a bad show 400, an unknown current room 404."""
    unknown = mapped.plugin._web_cexits(request({"area": "nowhere"}))
    assert unknown == {
        "kind": "error",
        "status": 404,
        "message": "area nowhere has no mapped rooms",
    }
    assert mapped.plugin._web_cexits(request({"show": "x"}))["status"] == 400
    assert mapped.plugin._web_cexits(request({"area": "a" * 101}))["status"] == 400
    mapped.fake.current = None
    page = mapped.plugin._web_cexits(request())
    assert page["kind"] == "error"
    assert page["status"] == 404
    assert mapped.plugin._web_cexits(request({"area": "a"}))["kind"] == "table"


@pytest.mark.parametrize("kind", ["shops", "train", "quest", "notes"])
def test_places_match_the_command(mapped: Env, kind: str) -> None:
    """Each kind lists the rows of its text command."""
    assert mapped.search(kind, "a").success
    # a kind with no match prints no table, so there are no command rows
    cells = mapped.table_cells() if mapped.fake.tables else []
    command = [" | ".join(row) for row in cells]
    page = mapped.plugin._web_places(request({"kind": kind, "area": "a"}))
    assert page["kind"] == "table"
    assert texts(page) == command
    assert page["total"] == len(command)


def test_places_default_kind_and_area(mapped: Env) -> None:
    """Without a query the page lists shops of the current area, in room number order."""
    page = mapped.plugin._web_places(request())
    assert page["title"] == "Mapper shops in a"
    assert texts(page) == ["2 | Smith | a | Shop", "10 | Bank of A | a | Bank"]
    assert page["rows"][0][1] == {"text": "Smith", "href": "/client/mapper/room?uid=2"}


def test_places_errors(mapped: Env) -> None:
    """A bad kind is 400, an unknown area 404."""
    bad = mapped.plugin._web_places(request({"kind": "pubs"}))
    assert bad["kind"] == "error"
    assert bad["status"] == 400
    assert mapped.plugin._web_places(request({"area": "nowhere"}))["status"] == 404
    mapped.fake.current = None
    assert mapped.plugin._web_places(request())["status"] == 404


def test_a_uid_is_percent_encoded(env: Env) -> None:
    """A room uid with query characters cannot add a key to the link."""
    env.fake.rooms["a&b=c d"] = room("a&b=c d", "z&y", "Odd")
    env.fake.notes["a&b=c d"] = "x"
    row = env.plugin._web_places(request({"kind": "notes", "area": "z&y"}))["rows"][0]
    assert row[1] == {"text": "Odd", "href": "/client/mapper/room?uid=a%26b%3Dc+d"}
    assert row[2] == {"text": "z&y", "href": "/client/mapper/area?uid=z%26y"}
    assert set(row[1]) == {"text", "href"}


def test_mud_text_is_escaped_by_colorcode_not_html(mapped: Env) -> None:
    """Names, notes and commands go through colorcode.escape; no html escaping happens."""
    mapped.fake.rooms["2"]["name"] = "@RFire & <b>"
    mapped.fake.notes["2"] = "@Gnote"
    original = mapped.plugin.api

    def escaping(name: str) -> Callable[..., Any]:
        if name == "plugins.core.colors:colorcode.escape":
            return lambda value: value.replace("@", "@@")
        return original(name)

    mapped.plugin.api = MagicMock(side_effect=escaping)
    shops = mapped.plugin._web_places(request({"kind": "shops"}))
    assert shops["rows"][0][1] == {
        "text": "@@RFire & <b>",
        "href": "/client/mapper/room?uid=2",
    }
    notes = mapped.plugin._web_places(request({"kind": "notes"}))
    assert notes["rows"][0][3] == "@@Gnote"


def test_the_core_renderer_shows_the_escaped_text(mapped: Env) -> None:
    """A name with colour codes and markup reaches the page as visible, html-escaped text."""
    from bastproxy.plugins.core.colors.libs._spans import line_spans
    from bastproxy.plugins.core.colors.libs._tokenizer import escape_at, tokenize
    from bastproxy.plugins.core.colors.plugin._colors import _spans_html
    from bastproxy.plugins.core.web.libs._render import _cell_html

    def to_html(value: str) -> str:
        return "\n".join(
            _spans_html(line_spans(tokenize(line.rstrip()))) for line in value.splitlines()
        )

    mapped.fake.rooms["2"]["name"] = "@RFire & <b>"
    original = mapped.plugin.api

    def escaping(name: str) -> Callable[..., Any]:
        if name == "plugins.core.colors:colorcode.escape":
            return escape_at
        return original(name)

    mapped.plugin.api = MagicMock(side_effect=escaping)
    cell = mapped.plugin._web_places(request({"kind": "shops"}))["rows"][0][1]
    assert _cell_html(cell, to_html) == (
        f"<a href='/client/mapper/room?uid=2'>{html.escape('@RFire & <b>')}</a>"
    )


def test_paging_sorting_and_filters(mapped: Env) -> None:
    """The page honours sort, direction, filters, offset and count; a sort is stable."""
    for uid in ("20", "21", "22"):
        mapped.fake.rooms[uid] = {**room(uid, "a", f"Shop {uid}"), "details": {"details": "shop"}}
    base = {"kind": "shops", "area": "a"}
    everything = mapped.plugin._web_places(request(base))
    assert everything["total"] == 5
    by_name = mapped.plugin._web_places(request(base, sort="name", descending=True))
    assert [text(row[1]) for row in by_name["rows"]] == [
        "Smith",
        "Shop 22",
        "Shop 21",
        "Shop 20",
        "Bank of A",
    ]
    paged = mapped.plugin._web_places(request(base, sort="uid", offset=1, count=2))
    assert [row[0] for row in paged["rows"]] == ["10", "20"]
    assert paged["total"] == 5
    same = mapped.plugin._web_places(request(base, sort="area", descending=True))
    assert [row[0] for row in same["rows"]] == [row[0] for row in everything["rows"]]
    filtered = mapped.plugin._web_places(request(base, filters={"name": "SHOP"}))
    assert [row[0] for row in filtered["rows"]] == ["20", "21", "22"]
    assert filtered["total"] == 3
    past = mapped.plugin._web_places(request(base, offset=50))
    assert past["rows"] == []
    assert past["total"] == 5


def test_portals_filter_and_sort_by_int(mapped: Env) -> None:
    """An int column sorts by value and filters by equality."""
    descending = mapped.plugin._web_portals(request(sort="level", descending=True))
    assert [row[6] for row in descending["rows"]] == [20, 0]
    only = mapped.plugin._web_portals(request(filters={"level": 20}))
    assert [row[5] for row in only["rows"]] == ["enter"]
    assert only["total"] == 1
