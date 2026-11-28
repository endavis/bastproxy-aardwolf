"""Tests for the statdb web page library, over made-up databases.

bastproxy is imported only inside functions: the library itself never imports it.
"""

import sqlite3
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from statdb_old_db import build_old_database
from statdb_support import TableRecorder, formatters, make_db

if TYPE_CHECKING:
    from aardwolf.statdb.libs import StatStore


@dataclass(frozen=True)
class Params:
    """A stand-in for the web plugin's validated table query."""

    sort: str | None = None
    descending: bool = False
    filters: dict[str, str | int | float] = field(default_factory=dict)
    count: int = 50
    page: int = 1

    @property
    def offset(self) -> int:
        """The number of rows before the page."""
        return (self.page - 1) * self.count


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """A statdb file with a few made-up rows in every table."""
    return build_old_database(tmp_path / "stats.sqlite")


@pytest.fixture
def empty_path(tmp_path: Path) -> Path:
    """A statdb file with the tables and no rows."""
    return build_old_database(tmp_path / "empty.sqlite", rows=False)


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> "Iterator[StatStore]":
    """A store over a copy of the made-up database, as the text reports use it."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("BASTPROXY_HOME", str(home))
    from aardwolf.statdb.libs import StatStore

    directory = tmp_path / "store"
    directory.mkdir()
    build_old_database(directory / "stats.sqlite")
    db = make_db(directory)
    yield StatStore(db)
    db.close()


def _rows(path: Path, route: str, params: Params | None = None) -> list[list[Any]]:
    from aardwolf.statdb.libs import TABLE_PAGES, read_table

    result = read_table(path, TABLE_PAGES[route], params or Params())
    assert result.rows is not None
    return result.rows


# the table pages


EXPECTED_ROWS: dict[str, list[list[Any]]] = {
    "quests": [
        [2, 0, 0, 0, 0, 0, 0, "", 0, 0, 0, 0, 0, 5, 0.17, "Failed", "a bat", "A ledge", "Cave"],
        [1, 20, 3, 2, 0, 0, 0, "D", 25, 1, 1, 2, 300, 5, 1.0, "Done", "a rat", "A pipe", "Sewer"],
    ],
    "levels": [
        [3, 5, "L", 4, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None],
        [2, 3, "P", 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 8.33],
        [1, 3, "L", 3, 0, 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 8.33],
    ],
    "cps": [
        [2, "T0 R1 L4", 0, 0, 0, 0, 0, 0, 0, 0.17, "Failed"],
        [1, "T0 R1 L4", 30, 0, 1, 0, 0, 500, 2, 1.0, "Done"],
    ],
    "cpmobs": [[1, "an orc", "Hills"], [1, "a goblin", "Forest"]],
    "gqs": [
        [2, "T0 R1 L5", 0, 2, 0, 0, 0, 0, 0, 0.33, 0],
        [1, "T0 R1 L5", 40, 10, 0, 0, 0, 0, 3, 1.0, 1],
    ],
    "gqmobs": [[1, 3, "a troll", "Cave"]],
    "mobs": [
        ["1970-01-01 00:43", 5, "a bat", 0, 0, 0, "", 0, "", 0, None],
        [
            "1970-01-01 00:28",
            3,
            "a very long named monster of the deep",
            25,
            20,
            5,
            "",
            0,
            "",
            5,
            None,
        ],
        ["1970-01-01 00:26", 3, "a rat", 12, 10, 0, "D", 1, "V", 50, None],
    ],
}


@pytest.mark.parametrize("route", sorted(EXPECTED_ROWS))
def test_each_table_page_returns_the_rows_of_its_data(db_path: Path, route: str) -> None:
    """A page lists the made-up rows, newest first, with each column's fixed expression."""
    assert _rows(db_path, route) == EXPECTED_ROWS[route]


def test_milestones_page_lists_oldest_first_with_utc_dates(db_path: Path) -> None:
    """The milestones page shows the name, a UTC date or Now, then each compared stat."""
    from aardwolf.statdb.libs import FIELDSTOCOMP

    rows = _rows(db_path, "milestones")
    assert [row[0] for row in rows] == ["current", "start", "3", "5", "t0r1l5"]
    assert [row[1] for row in rows] == [
        "Now",
        "1970-01-01 00:16",
        "1970-01-01 00:33",
        "1970-01-01 00:50",
        "1970-01-01 00:51",
    ]
    assert all(len(row) == 2 + len(FIELDSTOCOMP) for row in rows)
    assert rows[0][2] == 5
    assert rows[1][2] == 1


def test_every_page_declares_its_columns_once() -> None:
    """The column names are unique per page and the declarations match the web plugin's."""
    from aardwolf.statdb.libs import TABLE_PAGES

    assert len(TABLE_PAGES) == 8
    for page in TABLE_PAGES.values():
        names = [column["name"] for column in page.route_columns()]
        assert len(names) == len(set(names))
        assert {column["type"] for column in page.route_columns()} <= {"text", "int", "float"}


def test_paging_and_totals(db_path: Path) -> None:
    """A page of count N is the rows of the text command, and total counts every row."""
    from aardwolf.statdb.libs import TABLE_PAGES, read_table

    page = TABLE_PAGES["quests"]
    first = read_table(db_path, page, Params(count=1))
    second = read_table(db_path, page, Params(count=1, page=2))
    assert first.total == second.total == 2
    assert first.rows == EXPECTED_ROWS["quests"][:1]
    assert second.rows == EXPECTED_ROWS["quests"][1:]
    assert read_table(db_path, page, Params(count=1, page=3)).rows == []


def test_filters(db_path: Path) -> None:
    """A text filter is a case-insensitive part, a number filter is exact, filters combine."""
    from aardwolf.statdb.libs import TABLE_PAGES, read_table

    page = TABLE_PAGES["quests"]
    found = read_table(db_path, page, Params(filters={"mob": "RAT"}))
    assert found.total == 1
    assert found.rows == EXPECTED_ROWS["quests"][1:]
    assert _rows(db_path, "quests", Params(filters={"id": 2})) == EXPECTED_ROWS["quests"][:1]
    assert _rows(db_path, "quests", Params(filters={"id": 2, "mob": "rat"})) == []
    assert _rows(db_path, "quests", Params(filters={"mins": 1.0})) == EXPECTED_ROWS["quests"][1:]
    assert _rows(db_path, "cps", Params(filters={"lvl": "l4"})) == EXPECTED_ROWS["cps"]


def test_detail_filters_replace_the_n_views(db_path: Path) -> None:
    """The ``-n`` detail views are filters on the id columns."""
    assert _rows(db_path, "cpmobs", Params(filters={"cp_id": 1})) == EXPECTED_ROWS["cpmobs"]
    assert _rows(db_path, "cpmobs", Params(filters={"cp_id": 2})) == []
    assert _rows(db_path, "gqmobs", Params(filters={"gq_id": 1})) == EXPECTED_ROWS["gqmobs"]
    assert _rows(db_path, "levels", Params(filters={"id": 1})) == EXPECTED_ROWS["levels"][2:]


def test_sorting_orders_by_the_column_and_breaks_ties_by_key(db_path: Path) -> None:
    """Sorting uses the column's expression, then the key newest first."""
    rows = _rows(db_path, "quests", Params(sort="qp"))
    assert [row[0] for row in rows] == [2, 1]
    rows = _rows(db_path, "quests", Params(sort="qp", descending=True))
    assert [row[0] for row in rows] == [1, 2]
    rows = _rows(db_path, "mobs", Params(sort="lvl"))
    assert rows[0][2] == "a very long named monster of the deep"
    rows = _rows(db_path, "milestones", Params(sort="date", descending=True))
    assert rows[0][1] == "Now"


def test_every_sort_and_filter_fragment_executes(db_path: Path) -> None:
    """Each column of each page sorts both ways and filters, without a SQL error."""
    from aardwolf.statdb.libs import TABLE_PAGES, read_table

    samples: dict[str, str | int | float] = {"text": "a", "int": 1, "float": 1.0}
    for page in TABLE_PAGES.values():
        for column in page.columns:
            for descending in (False, True):
                read_table(db_path, page, Params(sort=column.name, descending=descending))
            read_table(db_path, page, Params(filters={column.name: samples[column.type]}))


def test_hostile_filter_text_is_only_ever_a_bound_value(db_path: Path) -> None:
    """Request text never reaches the SQL string, and the table is intact afterwards."""
    from aardwolf.statdb.libs import TABLE_PAGES, build_queries, read_table

    hostile = "x'; DROP TABLE quests; --"
    page = TABLE_PAGES["quests"]
    queries = build_queries(page, Params(filters={"mob": hostile}))
    assert "DROP" not in queries.count_sql
    assert "DROP" not in queries.rows_sql
    assert hostile not in queries.rows_sql
    assert f"%{hostile}%" in queries.rows_args
    assert read_table(db_path, page, Params(filters={"mob": hostile})).total == 0
    assert read_table(db_path, page, Params()).total == 2
    with sqlite3.connect(db_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM quests").fetchone() == (2,)


def test_like_wildcards_in_a_filter_are_literal(db_path: Path) -> None:
    """A percent sign or underscore in a text filter matches itself only."""
    from aardwolf.statdb.libs import escape_like

    assert escape_like(r"50%_off\x") == r"50\%\_off\\x"
    assert _rows(db_path, "quests", Params(filters={"mob": "%"})) == []
    assert _rows(db_path, "quests", Params(filters={"mob": "_"})) == []
    assert len(_rows(db_path, "quests", Params(filters={"mob": "a "}))) == 2


def test_unknown_names_raise_before_any_sql(tmp_path: Path) -> None:
    """An unknown sort or filter column raises ValueError, even for a file that is missing."""
    from aardwolf.statdb.libs import TABLE_PAGES, build_queries, read_table

    page = TABLE_PAGES["quests"]
    with pytest.raises(ValueError, match="unknown column"):
        build_queries(page, Params(sort="nope"))
    with pytest.raises(ValueError, match="unknown column"):
        build_queries(page, Params(filters={"nope": "x"}))
    with pytest.raises(ValueError, match="unknown column"):
        read_table(tmp_path / "missing.sqlite", page, Params(sort="nope"))


def test_level_expressions_equal_convert_level(db_path: Path) -> None:
    """The SQL level of quests, mob kills and campaigns equals ``convert_level``."""
    from aardwolf._libs.aardu import convert_level

    totals = [-1, 0, 1, 2, 200, 201, 202, 1406, 1407, 1408, 14069, 14070, 14071, 15477, 40000]
    with sqlite3.connect(db_path) as connection:
        for total in totals:
            connection.execute(
                "INSERT INTO quests (mobname, level) VALUES (?, ?)", (f"q{total}", total)
            )
            connection.execute("INSERT INTO campaigns (level) VALUES (?)", (total,))
            connection.execute(
                "INSERT INTO mobkills (name, level) VALUES (?, ?)", (f"m{total}", total)
            )
    quests = {row[16]: row[13] for row in _rows(db_path, "quests", Params(count=500))}
    cps = [row[1] for row in _rows(db_path, "cps", Params(count=500))][: len(totals)][::-1]
    mobs = {row[2]: row[1] for row in _rows(db_path, "mobs", Params(count=500))}
    for index, total in enumerate(totals):
        parts = convert_level(total)
        assert quests[f"q{total}"] == parts["level"]
        assert mobs[f"m{total}"] == parts["level"]
        assert cps[index] == f"T{parts['tier']} R{parts['remort']} L{parts['level']}"


def test_mobkill_page_matches_the_text_list(store: "StatStore", db_path: Path) -> None:
    """The mobkills page shows the same time, name, level, xp and flags as ``mobkills``."""
    from aardwolf.statdb.libs import mobkill_list

    rec = TableRecorder()
    mobkill_list(store, 3, formatters(table=rec))
    text = rec.calls[0][1]
    rows = _rows(db_path, "mobs")
    for cells, row in zip(text, rows, strict=True):
        assert cells["time"] == row[0]
        assert cells["name"] == row[2][:18]
        if row[8]:
            assert cells["flags"] == row[8]


def test_empty_pages_have_no_rows(empty_path: Path) -> None:
    """A database without rows gives every page no rows and a total of 0."""
    from aardwolf.statdb.libs import TABLE_PAGES, read_table

    for name in ("cpmobs", "gqmobs", "mobs", "milestones"):
        result = read_table(empty_path, TABLE_PAGES[name], Params())
        if name == "mobs":
            assert result.rows is None
            assert result.message == "No stats available"
        else:
            assert result.rows == []
        assert result.total == 0


# the summaries and guards


def test_summaries_equal_the_text_report_summaries(store: "StatStore", db_path: Path) -> None:
    """The summary above each page is the summary of its text command."""
    from aardwolf.statdb.libs import (
        TABLE_PAGES,
        cp_report,
        gq_report,
        level_report,
        list_milestones,
        mob_report,
        page_lines,
        quest_report,
        read_table,
    )

    fmt = formatters()
    reports = {
        "quests": quest_report(store, 0, None, fmt),
        "levels": level_report(store, 0, None, fmt),
        "cps": cp_report(store, 0, None, fmt),
        "gqs": gq_report(store, 0, None, fmt),
        "mobs": mob_report(store, 0, fmt),
        "milestones": list_milestones(store, fmt),
    }
    for route, text in reports.items():
        page = TABLE_PAGES[route]
        result = read_table(db_path, page, Params())
        assert page_lines(page, result, fmt) == text
    assert (
        page_lines(TABLE_PAGES["cpmobs"], read_table(db_path, TABLE_PAGES["cpmobs"], Params()), fmt)
        == []
    )


def test_guard_messages_match_the_text_reports(empty_path: Path, tmp_path: Path) -> None:
    """An empty stats table or an empty report table gives the text command's message."""
    from aardwolf.statdb.libs import TABLE_PAGES, read_table

    for route in ("quests", "levels", "cps", "gqs", "mobs"):
        result = read_table(empty_path, TABLE_PAGES[route], Params())
        assert result.message == "No stats available"
        assert result.rows is None
    path = build_old_database(tmp_path / "stats_only.sqlite", rows=False)
    with sqlite3.connect(path) as connection:
        connection.execute("INSERT INTO stats (name, milestone) VALUES ('Tester', 'current')")
    expected = {
        "quests": "No quests stats are available",
        "levels": "No levels/pups stats available",
        "cps": "No campaign stats available",
        "gqs": "No gq stats available",
        "mobs": "No mob stats available",
    }
    for route, message in expected.items():
        assert read_table(path, TABLE_PAGES[route], Params()).message == message


def test_comparison_lines_equal_compare_milestones(store: "StatStore", db_path: Path) -> None:
    """The comp page formats the rows of the milestone names as the text command does."""
    from aardwolf.statdb.libs import (
        compare_milestones,
        comparison_lines,
        milestone_names,
        read_milestone_rows,
    )

    fmt = formatters()
    for first, second in (("", ""), ("3", ""), ("start", "5"), ("start", "nope")):
        names = milestone_names(first, second)
        rows = read_milestone_rows(db_path, names)
        assert comparison_lines(names, rows, fmt, now=5000) == compare_milestones(
            store, first, second, fmt, now=5000
        )
    assert milestone_names("", "") == ("start", "current")
    assert milestone_names("a", "") == ("a", "current")
    assert milestone_names("a", "b") == ("a", "b")


# the read-only connection


def test_connection_is_read_only(db_path: Path) -> None:
    """A write on the connection fails and the file is unchanged."""
    from aardwolf.statdb.libs import open_readonly

    db = open_readonly(db_path)
    try:
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            db.select("INSERT INTO quests (mobname) VALUES ('x')")
        assert db.getlastrowid("quests") == 2
        assert db.getlastrowid("stats") == 5
        with pytest.raises(ValueError, match="no key known"):
            db.getlastrowid("classes")
    finally:
        db.close()
    with sqlite3.connect(db_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM quests").fetchone() == (2,)


def test_reads_a_wal_database(tmp_path: Path) -> None:
    """A database in WAL mode, with its writer still open, reads through the connection."""
    from aardwolf.statdb.libs import open_readonly

    path = build_old_database(tmp_path / "wal.sqlite")
    writer = sqlite3.connect(path)
    try:
        assert writer.execute("PRAGMA journal_mode").fetchone() == ("wal",)
        writer.execute("INSERT INTO quests (mobname) VALUES ('wal row')")
        writer.commit()
        db = open_readonly(path)
        try:
            assert db.getlastrowid("quests") == 3
        finally:
            db.close()
    finally:
        writer.close()


def test_missing_file_raises_sqlite_error(tmp_path: Path) -> None:
    """A file that is not there is an sqlite3 error, not a created file."""
    from aardwolf.statdb.libs import open_readonly

    with pytest.raises(sqlite3.Error):
        open_readonly(tmp_path / "missing.sqlite")
    assert not (tmp_path / "missing.sqlite").exists()


# charts


def test_chart_svg_is_well_formed_and_inert() -> None:
    """The chart parses, and has no script, event attribute or link."""
    from aardwolf.statdb.libs import bar_chart_svg

    svg = bar_chart_svg("Per day", [("2020-01-01", 3), ("2020-01-02", 7.5)], "QP")
    root = ET.fromstring(svg)
    tags = {element.tag.split("}")[-1] for element in root.iter()}
    assert "script" not in tags
    assert "a" not in tags
    attributes = {name.split("}")[-1] for element in root.iter() for name in element.attrib}
    assert not [name for name in attributes if name.startswith("on") or name == "href"]
    assert sum(1 for element in root.iter() if element.tag.endswith("rect")) == 3
    assert root.tag.endswith("svg")


def test_chart_labels_are_escaped() -> None:
    """Hostile labels, titles and units are text in the document, never markup."""
    from aardwolf.statdb.libs import bar_chart_svg

    label = '<script>alert(1)</script>"&'
    svg = bar_chart_svg("<b>T</b>", [(label, 2)], "<i>u</i>")
    assert "<script" not in svg
    assert "<b>" not in svg
    root = ET.fromstring(svg)
    texts = [element.text or "" for element in root.iter() if element.tag.endswith("text")]
    assert "<b>T</b>" in texts
    titles = [element.text or "" for element in root.iter() if element.tag.endswith("title")]
    assert any("alert(1)" in title for title in titles)


def test_chart_with_no_data_and_zero_values() -> None:
    """No bars says "No data"; all zero values draw flat bars without dividing by zero."""
    from aardwolf.statdb.libs import bar_chart_svg

    empty = bar_chart_svg("None", [], "QP")
    assert "No data" in empty
    ET.fromstring(empty)
    flat = bar_chart_svg("Zero", [("a", 0), ("b", 0)], "")
    ET.fromstring(flat)
    assert "No data" not in flat
    long = bar_chart_svg("Long", [("x" * 40, 1)], "")
    assert ">" + "x" * 12 + "..<" in long


def _texts(svg: str, text: str, fill: str) -> list[ET.Element]:
    """The <text> elements with this content and fill."""
    return [
        e
        for e in ET.fromstring(svg).iter()
        if e.tag.endswith("text") and e.text == text and e.get("fill") == fill
    ]


def _bar_rects(svg: str) -> list[ET.Element]:
    """The bar rectangles (the ones with a tooltip)."""
    return [e for e in ET.fromstring(svg).iter() if e.tag.endswith("rect") and len(e)]


def test_chart_tall_bar_value_inside_in_white() -> None:
    """A value that fits sits inside its bar near the top, in white."""
    from aardwolf.statdb.libs import bar_chart_svg

    svg = bar_chart_svg("T", [("a", 100), ("b", 50)], "")
    rect = _bar_rects(svg)[1]
    top = float(rect.get("y", "0"))
    bottom = top + float(rect.get("height", "0"))
    value = _texts(svg, "50", "#ffffff")
    assert len(value) == 1
    assert top < float(value[0].get("y", "0")) < bottom
    assert value[0].get("transform") is None


def test_chart_short_bar_value_above_in_dark() -> None:
    """A bar too short for its value shows it just above the bar, in dark text."""
    from aardwolf.statdb.libs import bar_chart_svg

    svg = bar_chart_svg("T", [("a", 1000), ("b", 10)], "")
    rect = _bar_rects(svg)[1]
    value = _texts(svg, "10", "#333333")
    assert len(value) == 1
    assert float(value[0].get("y", "0")) < float(rect.get("y", "0"))


def test_chart_long_value_is_vertical_and_inside_bar() -> None:
    """A value too wide for the bar runs vertically and stays inside a tall bar."""
    from aardwolf.statdb.libs import bar_chart_svg

    svg = bar_chart_svg("T", [("a", 20000), ("b", 12.5)], "")
    rect = _bar_rects(svg)[0]
    top = float(rect.get("y", "0"))
    bottom = top + float(rect.get("height", "0"))
    value = _texts(svg, "20000", "#ffffff")
    assert len(value) == 1
    assert "rotate(-90" in (value[0].get("transform") or "")
    y = float(value[0].get("y", "0"))
    assert top <= y
    assert y + len("20000") * 6 <= bottom
    small = _texts(svg, "12.50", "#333333") + _texts(svg, "12.50", "#ffffff")
    assert len(small) == 1
    assert "rotate(-90" in (small[0].get("transform") or "")


def test_chart_zero_bar_shows_zero_at_baseline() -> None:
    """A zero-value bar shows 0 just above the baseline in dark text."""
    from aardwolf.statdb.libs import bar_chart_svg

    svg = bar_chart_svg("T", [("a", 5), ("b", 0)], "")
    rect = _bar_rects(svg)[1]
    base = float(rect.get("y", "0")) + float(rect.get("height", "0"))
    zero = _texts(svg, "0", "#333333")
    assert len(zero) == 1
    assert base - 6 <= float(zero[0].get("y", "0")) <= base


def test_chart_data_per_day_and_level_time(db_path: Path) -> None:
    """The day charts sum every source of a day; the level chart skips an unknown time."""
    from aardwolf.statdb.libs import read_chart

    assert read_chart(db_path, "qp-per-day") == [("1970-01-01", 107.0)]
    assert read_chart(db_path, "gold-per-day") == [("1970-01-01", 855.0)]
    assert read_chart(db_path, "level-time") == [("3", 8.33)]
    with pytest.raises(ValueError, match="unknown chart"):
        read_chart(db_path, "nope")


def test_day_charts_keep_the_newest_30_days_oldest_first(tmp_path: Path) -> None:
    """With more than 30 days only the newest 30 show, left to right in time."""
    from aardwolf.statdb.libs import read_chart

    path = build_old_database(tmp_path / "days.sqlite", rows=False)
    with sqlite3.connect(path) as connection:
        for day in range(1, 36):
            connection.execute(
                "INSERT INTO quests (finishtime, totqp) VALUES (?, ?)", (day * 86400 + 5, day)
            )
    bars = read_chart(path, "qp-per-day")
    assert len(bars) == 30
    assert bars[0] == ("1970-01-07", 6.0)
    assert bars[-1] == ("1970-02-05", 35.0)


def test_chart_limit_sets_the_number_of_bars(tmp_path: Path) -> None:
    """An explicit limit replaces the default number of bars."""
    from aardwolf.statdb.libs import CHARTS, read_chart

    path = build_old_database(tmp_path / "limit.sqlite", rows=False)
    with sqlite3.connect(path) as connection:
        for day in range(1, 36):
            connection.execute(
                "INSERT INTO quests (finishtime, totqp) VALUES (?, ?)", (day * 86400 + 5, day)
            )
    bars = read_chart(path, "qp-per-day", 5)
    assert [label for label, _ in bars] == [
        "1970-02-01",
        "1970-02-02",
        "1970-02-03",
        "1970-02-04",
        "1970-02-05",
    ]
    assert len(read_chart(path, "qp-per-day", 40)) == 35
    spec = CHARTS["qp-per-day"]
    assert spec.heading(7) == "Quest points per day (newest 7 days)"


def test_level_chart_keeps_the_last_50_levels(tmp_path: Path) -> None:
    """With more than 50 timed levels only the last 50 show, oldest first."""
    from aardwolf.statdb.libs import read_chart

    path = build_old_database(tmp_path / "levels.sqlite", rows=False)
    with sqlite3.connect(path) as connection:
        for number in range(1, 62):
            connection.execute(
                "INSERT INTO levels (type, level, starttime) VALUES ('level', ?, ?)",
                (number, number * 600),
            )
    bars = read_chart(path, "level-time")
    assert len(bars) == 50
    assert bars[0] == ("11", 10.0)
    assert bars[-1] == ("60", 10.0)


def test_room_kills_and_area_totals(db_path: Path) -> None:
    """Kills are counted per room, then added per area with unmapped rooms as Unknown."""
    from aardwolf.statdb.libs import aggregate_areas, read_room_kills

    assert read_room_kills(db_path) == {0: 3}
    counts = {1: 5, 2: 4, 3: 4, 4: 1}
    areas = {1: "Cave", 2: "Sewer", 3: "Sewer"}
    assert aggregate_areas(counts, areas) == [("Sewer", 8.0), ("Cave", 5.0), ("Unknown", 1.0)]
    assert aggregate_areas(counts, areas, limit=1) == [("Sewer", 8.0)]
    assert aggregate_areas({1: 1, 2: 1}, {1: "B", 2: "A"}) == [("A", 1.0), ("B", 1.0)]
    assert aggregate_areas({}, {}) == []


# link cells

LINK_PATHS = {
    "quests": "/aardwolf/statdb/quests",
    "levels": "/aardwolf/statdb/levels",
    "cpmobs": "/aardwolf/statdb/cpmobs",
    "gqmobs": "/aardwolf/statdb/gqmobs",
}


def _linked(db_path: Path, route: str) -> list[list[Any]]:
    from aardwolf.statdb.libs import MAPPER_ROOM_PATH, TABLE_PAGES, link_rows

    paths = {**LINK_PATHS, "mapper-room": MAPPER_ROOM_PATH}
    return link_rows(TABLE_PAGES[route], _rows(db_path, route), paths)


def _link(path: str, key: str, value: int) -> dict[str, str]:
    return {"text": str(value), "href": f"{path}?{key}={value}"}


def test_link_cell_encodes_the_query_value() -> None:
    """The query value is URL-encoded and the text is kept as given."""
    from aardwolf.statdb.libs import link_cell

    assert link_cell("a b", "/p", "k", "a b&c") == {"text": "a b", "href": "/p?k=a+b%26c"}


def test_link_rows_links_each_listed_cell(db_path: Path) -> None:
    """Each linked column's cells are link cells with the target's path and query key."""
    quests = _linked(db_path, "quests")
    assert [row[0] for row in quests] == [
        _link("/aardwolf/statdb/quests", "f_id", 2),
        _link("/aardwolf/statdb/quests", "f_id", 1),
    ]
    assert [row[0] for row in _linked(db_path, "levels")] == [
        _link("/aardwolf/statdb/levels", "f_id", level_id) for level_id in (3, 2, 1)
    ]
    assert [row[0] for row in _linked(db_path, "cps")] == [
        _link("/aardwolf/statdb/cpmobs", "f_cp_id", cp_id) for cp_id in (2, 1)
    ]
    assert [row[0] for row in _linked(db_path, "gqs")] == [
        _link("/aardwolf/statdb/gqmobs", "f_gq_id", gq_id) for gq_id in (2, 1)
    ]


def test_link_rows_links_the_mobkill_room(db_path: Path) -> None:
    """A mob kill's room links to the mapper room page."""
    with closing(sqlite3.connect(db_path)) as db, db:
        db.execute("UPDATE mobkills SET room_id = ? WHERE name = ?", (7, "a bat"))
    rooms = [row[10] for row in _linked(db_path, "mobs")]
    assert rooms == [_link("/client/mapper/room", "uid", 7), None, None]


def test_link_rows_leaves_an_unset_room_plain(db_path: Path) -> None:
    """A mob kill without a room has a None cell, and the link keeps it None."""
    assert [row[10] for row in _linked(db_path, "mobs")] == [None, None, None]


def test_link_rows_without_a_target_path_keeps_plain_values(db_path: Path) -> None:
    """A target the web plugin refused has no path, so its cells stay raw values."""
    from aardwolf.statdb.libs import TABLE_PAGES, link_rows

    for route in ("quests", "levels", "cps", "gqs", "mobs"):
        assert link_rows(TABLE_PAGES[route], _rows(db_path, route), {}) == _rows(db_path, route)


def test_linked_columns_keep_names_and_types() -> None:
    """The column declarations the web plugin gets do not mention links."""
    from aardwolf.statdb.libs import TABLE_PAGES

    for route, name in (
        ("quests", "id"),
        ("levels", "id"),
        ("cps", "id"),
        ("gqs", "id"),
        ("mobs", "room"),
    ):
        columns = {column["name"]: column for column in TABLE_PAGES[route].route_columns()}
        assert set(columns[name]) <= {"name", "label", "type", "long"}
        assert columns[name]["type"] == "int"


def test_mobs_page_shows_no_bonus_flags_on_noexp_kills(empty_path: Path) -> None:
    sql = (
        "INSERT INTO mobkills(name, time, xp, totalxp, bonusxp, blessingxp, noexp) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)"
    )
    with closing(sqlite3.connect(empty_path)) as conn:
        conn.execute("INSERT INTO stats (name, milestone) VALUES ('Tester', 'current')")
        conn.execute(sql, ("a rat", 1000, 10, 15, 2, 3, 0))
        conn.execute(sql, ("a bat", 1001, 100, 150, 20, 30, 1))
        conn.commit()
    flags = {row[2]: row[6] for row in _rows(empty_path, "mobs")}
    assert flags == {"a rat": "DE", "a bat": ""}


# the milestones data provider


def test_latest_milestones_omit_current_and_run_oldest_first(db_path: Path) -> None:
    """The provider rows are the milestones page columns, without the ``current`` row."""
    from aardwolf.statdb.libs import FIELDSTOCOMP, read_latest_milestones

    rows = read_latest_milestones(db_path)
    assert [row[0] for row in rows] == ["start", "3", "5", "t0r1l5"]
    assert all(len(row) == 2 + len(FIELDSTOCOMP) for row in rows)
    assert rows[0][2] == 1
    assert rows[1][2] == 3


def test_latest_milestones_cap_keeps_the_newest(db_path: Path) -> None:
    """A limit keeps the newest rows, still oldest first."""
    from aardwolf.statdb.libs import read_latest_milestones

    assert [row[0] for row in read_latest_milestones(db_path, 2)] == ["5", "t0r1l5"]


def test_latest_milestones_of_an_empty_database(empty_path: Path) -> None:
    from aardwolf.statdb.libs import read_latest_milestones

    assert read_latest_milestones(empty_path) == []


def test_latest_milestones_of_a_missing_file_raise(tmp_path: Path) -> None:
    from aardwolf.statdb.libs import read_latest_milestones

    with pytest.raises(sqlite3.Error):
        read_latest_milestones(tmp_path / "missing.sqlite")


def test_the_provider_columns_are_accepted_by_the_real_route_table() -> None:
    """The real RouteTable takes the route and the provider side by side."""
    pytest.importorskip("bastproxy")
    from bastproxy.plugins.core.web.libs._store import RouteTable

    from aardwolf.statdb.libs import MILESTONES_PROVIDER, TABLE_PAGES

    page = TABLE_PAGES["milestones"]
    table = RouteTable()
    owner = "plugins.aardwolf.statdb"
    assert table.add(owner, page.route, lambda _r: {}, page.title, page.route_columns())
    topic = table.add_provider(
        owner, MILESTONES_PROVIDER, list, page.route_columns(), "table", None, str
    )
    assert topic == "aardwolf.statdb.milestones"
