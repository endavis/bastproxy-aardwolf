"""Tests for the statdb command output, over a made-up old database."""

from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from statdb_old_db import build_old_database
from statdb_support import TableRecorder, formatters, make_db

if TYPE_CHECKING:
    from aardwolf.statdb.libs import StatStore


@pytest.fixture(autouse=True)
def home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Importing bastproxy needs an existing BASTPROXY_HOME."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setenv("BASTPROXY_HOME", str(home_dir))


@pytest.fixture
def full(tmp_path: Path) -> "Iterator[StatStore]":
    """A store over an old-style database with a few rows in every table."""
    from aardwolf.statdb.libs import StatStore

    directory = tmp_path / "full"
    directory.mkdir()
    build_old_database(directory / "stats.sqlite")
    db = make_db(directory)
    yield StatStore(db)
    db.close()


@pytest.fixture
def empty(tmp_path: Path) -> "Iterator[StatStore]":
    """A store over a new, empty database."""
    from aardwolf.statdb.libs import StatStore

    db = make_db(tmp_path / "empty")
    yield StatStore(db)
    db.close()


def _recorded(rec: TableRecorder, index: int = 0) -> list[dict[str, str]]:
    """Return the rows of one recorded table.format call."""
    return rec.calls[index][1]


def _text(lines: list[str]) -> str:
    return "\n".join(lines)


def test_format_float_and_row() -> None:
    """Float formatting gives three decimals and 0 for nothing; rows pad their columns."""
    from aardwolf.statdb.libs import format_float, format_row

    assert format_float(None) == 0
    assert format_float(0) == 0
    assert format_float(1.23456, "/x") == "1.235/x"
    assert format_row("Name", 1, "b") == "@CName           : @W1            @Wb           "
    assert format_row("N", "", 0, "@G", "@R") == "@RN              : @G             @G0           "


def test_commands_report_no_stats_on_an_empty_database(empty: "StatStore") -> None:
    """Every report says there are no stats when the stats table is empty."""
    from aardwolf.statdb.libs import cp_report, gq_report, level_report, mob_report, quest_report

    fmt = formatters()
    assert quest_report(empty, 0, None, fmt) == ["No stats available"]
    assert level_report(empty, 0, None, fmt) == ["No stats available"]
    assert cp_report(empty, 0, None, fmt) == ["No stats available"]
    assert gq_report(empty, 0, None, fmt) == ["No stats available"]
    assert mob_report(empty, 0, fmt) == ["No stats available"]


def test_commands_report_no_rows_for_an_empty_table(empty: "StatStore") -> None:
    """With stats but no rows, each report names its table."""
    from aardwolf.statdb.libs import cp_report, gq_report, level_report, mob_report, quest_report

    empty.save_whois({"name": "Tester"})
    fmt = formatters()
    assert quest_report(empty, 0, None, fmt) == ["No quests stats are available"]
    assert level_report(empty, 0, None, fmt) == ["No levels/pups stats available"]
    assert cp_report(empty, 0, None, fmt) == ["No campaign stats available"]
    assert gq_report(empty, 0, None, fmt) == ["No gq stats available"]
    assert mob_report(empty, 0, fmt) == ["No mob stats available"]


def test_list_milestones(full: "StatStore") -> None:
    """The list shows the level range and a table of the named milestones."""
    from aardwolf.statdb.libs import MILESTONE_COLUMNS, MILESTONE_TITLE, list_milestones

    rec = TableRecorder()
    lines = list_milestones(full, formatters(table=rec))
    assert lines == ["Levels between 3 and 5", MILESTONE_TITLE]
    ((title, data, columns),) = rec.calls
    assert title == MILESTONE_TITLE
    assert columns == MILESTONE_COLUMNS
    assert data == [{"first": "current", "second": "start", "third": "t0r1l5"}]


def test_list_milestones_three_to_a_row(empty: "StatStore") -> None:
    """Named milestones are three to a row of the table; without names there is no table."""
    from aardwolf.statdb.libs import list_milestones

    rec = TableRecorder()
    fmt = formatters(table=rec)
    assert list_milestones(empty, fmt) == ["No milestones"]
    assert rec.calls == []
    empty.save_whois({"name": "Tester"})
    empty.add_milestone("a")
    list_milestones(empty, fmt)
    assert _recorded(rec, -1) == [{"first": "current", "second": "start", "third": "a"}]
    for extra in ("b", "c"):
        empty.add_milestone(extra)
    list_milestones(empty, fmt)
    assert len(_recorded(rec, -1)) == 2
    assert _recorded(rec, -1)[1] == {"first": "b", "second": "c", "third": ""}
    empty.add_milestone("d")
    list_milestones(empty, fmt)
    assert _recorded(rec, -1)[1] == {"first": "b", "second": "c", "third": "d"}


def test_compare_defaults_to_start_and_current(full: "StatStore") -> None:
    """With no names it compares start to current, with the difference of each stat."""
    from aardwolf.statdb.libs import COMPARE_TITLE, compare_milestones

    rec = TableRecorder()
    lines = compare_milestones(full, "", "", formatters(table=rec), now=5000)
    assert lines == [COMPARE_TITLE]
    ((title, data, columns),) = rec.calls
    assert title == COMPARE_TITLE
    assert [c["name"] for c in columns] == ["Milestone", "start", "current", "Difference"]
    assert data[0]["field"] == "Date"
    assert data[0]["second"] == "Now"
    assert data[0]["difference"] == "4000s"
    rows = {row["field"]: row for row in data}
    assert rows["Total levels"] == {
        "field": "Total levels",
        "first": "1",
        "second": "5",
        "difference": "4",
    }
    assert rows["Monsters killed"] == {
        "field": "Monsters killed",
        "first": "0",
        "second": "4",
        "difference": "4",
    }


def test_compare_one_and_two_names_in_either_order(full: "StatStore") -> None:
    """One name compares to current, and two names are put in time order."""
    from aardwolf.statdb.libs import compare_milestones

    rec = TableRecorder()
    fmt = formatters(table=rec)
    compare_milestones(full, "3", "", fmt, now=5000)
    assert [c["name"] for c in rec.calls[0][2]] == ["Milestone", "3", "current", "Difference"]
    compare_milestones(full, "5", "3", fmt, now=5000)
    assert [c["name"] for c in rec.calls[1][2]] == ["Milestone", "3", "5", "Difference"]
    rows = {row["field"]: row for row in _recorded(rec, 1)}
    assert rows["Total levels"] == {
        "field": "Total levels",
        "first": "3",
        "second": "5",
        "difference": "2",
    }
    assert rows["Date"]["difference"] == "1000s"


def test_compare_headers_match_the_column_data_in_either_order(full: "StatStore") -> None:
    """The header over each column names the milestone whose values sit in it."""
    from aardwolf.statdb.libs import compare_milestones

    rec = TableRecorder()
    fmt = formatters(table=rec)
    compare_milestones(full, "3", "5", fmt, now=5000)
    compare_milestones(full, "5", "3", fmt, now=5000)
    for index in (0, 1):
        names = [c["name"] for c in rec.calls[index][2]]
        rows = {row["field"]: row for row in _recorded(rec, index)}
        assert names[1:3] == ["3", "5"]
        assert rows["Total levels"]["first"] == "3"
        assert rows["Total levels"]["second"] == "5"


def test_compare_names_a_missing_milestone(full: "StatStore") -> None:
    """A milestone that does not exist is named in the message."""
    from aardwolf.statdb.libs import compare_milestones

    fmt = formatters()
    assert compare_milestones(full, "nope", "", fmt) == ["milestone nope does not exist"]
    assert compare_milestones(full, "nope", "gone", fmt) == [
        "milestone nope does not exist",
        "milestone gone does not exist",
    ]


def test_compare_with_no_stats(empty: "StatStore") -> None:
    """With no stats, the default milestones are both missing."""
    from aardwolf.statdb.libs import compare_milestones

    assert compare_milestones(empty, "", "", formatters()) == [
        "milestone start does not exist",
        "milestone current does not exist",
    ]


def test_quest_report(full: "StatStore") -> None:
    """The quest report shows the totals, averages and a table of the last quests."""
    from aardwolf.statdb.libs import QUEST_COLUMNS, QUEST_LIST_TITLE, quest_report

    text = _text(quest_report(full, 5, None, formatters()))
    assert "Quests                 : @W4            @W2" in text
    assert "20.000/level" in text
    assert "Gold                   : @W<300>        @W300/quest" in text
    rec = TableRecorder()
    lines = quest_report(full, 5, None, formatters(table=rec))
    assert lines[-1] == QUEST_LIST_TITLE
    ((title, data, columns),) = rec.calls
    assert title == QUEST_LIST_TITLE
    assert columns == QUEST_COLUMNS
    keys = [c["key"] for c in columns]
    assert [data[-1][key] for key in keys] == [
        "1",
        "20",
        "3",
        "2",
        "0",
        "0",
        "0",
        "D",
        "25",
        "1",
        "1",
        "2",
        "300",
        "5",
        "60s",
    ]
    assert data[-2]["time"] == "Failed"
    assert len(quest_report(full, 0, None, formatters())) == len(lines) - 2


def test_show_quest(full: "StatStore") -> None:
    """One quest shows its row, its mob and where it was."""
    from aardwolf.statdb.libs import (
        QUEST_MOB_COLUMNS,
        QUEST_MOB_TITLE,
        QUEST_SHOW_COLUMNS,
        quest_report,
    )

    rec = TableRecorder()
    lines = quest_report(full, 0, 1, formatters(table=rec))
    assert lines == ["Quest 1", QUEST_MOB_TITLE]
    (shown, mob) = rec.calls
    assert shown[0] == "Quest 1"
    assert shown[2] == QUEST_SHOW_COLUMNS
    keys = [c["key"] for c in QUEST_SHOW_COLUMNS]
    assert [shown[1][0][key] for key in keys] == [
        "1",
        "20",
        "3",
        "2",
        "0",
        "D",
        "25",
        "1",
        "1",
        "2",
        "300",
        "5",
        "60s",
    ]
    assert mob[2] == QUEST_MOB_COLUMNS
    assert mob[1] == [{"mob": "a rat", "room": "A pipe", "area": "Sewer"}]
    assert quest_report(full, 0, 99, formatters()) == ["No such quest: 99"]


def test_level_report(full: "StatStore") -> None:
    """The level report totals levels and pups and tables the last rows."""
    from aardwolf.statdb.libs import LEVEL_COLUMNS, LEVEL_LIST_TITLE, level_report

    rec = TableRecorder()
    lines = level_report(full, 5, None, formatters(table=rec))
    text = _text(lines)
    assert "Total Overall           : @W5            @W1" in text
    assert "Total In Database       : @W2            @W1" in text
    assert "Ave Bonus Trains        : @W0.500" in text
    assert lines[-1] == LEVEL_LIST_TITLE
    ((title, data, columns),) = rec.calls
    assert title == LEVEL_LIST_TITLE
    assert columns == LEVEL_COLUMNS
    assert [data[-1][k] for k in ("id", "lvl", "t")] == ["1", "3", "L"]
    assert data[-1]["time"] == "500s"
    assert [data[-3][k] for k in ("id", "lvl", "t", "tr", "bt", "pr")] == [
        "3",
        "5",
        "L",
        "4",
        "1",
        "0",
    ]


def test_show_level(full: "StatStore") -> None:
    """One level shows its numbers, its actual level and its times."""
    from aardwolf.statdb.libs import level_report

    lines = level_report(full, 0, 3, formatters(), 300.0)
    assert lines[1].split() == ["3", "lev", "5", "re0t0r1l5"]
    assert lines[5].split() == ["4", "1", "0", "0"]
    assert any(line.startswith("Started  : ") for line in lines)
    assert lines[-1] == "Finished : Current"
    assert level_report(full, 0, 99, formatters()) == ["No such level: 99"]


def test_show_level_uses_the_time_format_of_the_formatters(full: "StatStore") -> None:
    """The start and finish times follow the format, with no +0000 in the default."""
    import dataclasses

    from aardwolf.statdb.libs import TIME_FORMAT, level_report

    default = level_report(full, 0, 3, formatters())
    assert "+0000" not in TIME_FORMAT
    assert all("+0000" not in line for line in default)
    year = dataclasses.replace(formatters(), time_format="Y%Y")
    started = next(x for x in level_report(full, 0, 3, year) if x.startswith("Started  : "))
    assert started == "Started  : Y1970"


def test_show_level_with_kills_in_its_time(full: "StatStore") -> None:
    """A finished level shows how long it took and the mobs killed in it."""
    from aardwolf.statdb.libs import level_report

    lines = level_report(full, 0, 1, formatters(), 6000.0)
    assert lines[-2] == ("It took 500s with @G2@w mobs killed (@G18.50@w xp/mob) @G720@w xp/min")


def test_campaign_report(full: "StatStore") -> None:
    """The campaign report counts mobs, and a campaign without mobs counts 0."""
    from aardwolf.statdb.libs import CP_COLUMNS, CP_LIST_TITLE, cp_report

    rec = TableRecorder()
    lines = cp_report(full, 5, None, formatters(table=rec))
    assert "Overall        : @W3            @W2" in _text(lines)
    assert lines[-1] == CP_LIST_TITLE
    ((title, data, columns),) = rec.calls
    assert (title, columns) == (CP_LIST_TITLE, CP_COLUMNS)
    assert [row["mobs"] for row in data[-2:]] == ["0", "2"]
    assert [row["time"] for row in data[-2:]] == ["Failed", "60s"]


def test_show_campaign(full: "StatStore") -> None:
    """One campaign lists its mobs; a campaign without mobs lists none."""
    from aardwolf.statdb.libs import CP_COLUMNS, CP_MOB_COLUMNS, CP_MOB_TITLE, cp_report

    rec = TableRecorder()
    lines = cp_report(full, 0, 1, formatters(table=rec))
    assert lines == ["Campaign 1", CP_MOB_TITLE]
    (_, one, columns), (_, mobs, mob_columns) = rec.calls
    assert columns == CP_COLUMNS
    assert mob_columns == CP_MOB_COLUMNS
    assert len(one) == 1
    assert one[0]["mobs"] == "2"
    assert [(mob["name"], mob["location"]) for mob in mobs] == [
        ("a goblin", "Forest"),
        ("an orc", "Hills"),
    ]
    rec_none = TableRecorder()
    cp_report(full, 0, 2, formatters(table=rec_none))
    assert _recorded(rec_none)[0]["time"] == "Failed"
    assert _recorded(rec_none)[0]["mobs"] == "0"
    assert _recorded(rec_none, 1) == []
    assert cp_report(full, 0, 99, formatters()) == ["No such campaign: 99"]


def test_gquest_report(full: "StatStore") -> None:
    """The global quest report shows won and lost, and the mob count of each."""
    from aardwolf.statdb.libs import GQ_COLUMNS, GQ_LIST_TITLE, gq_report

    rec = TableRecorder()
    lines = gq_report(full, 5, None, formatters(table=rec))
    text = _text(lines)
    assert "Won                     : @W1            @W1" in text
    assert "Lost                    : @W             @W1" in text
    assert lines[-1] == GQ_LIST_TITLE
    ((title, data, columns),) = rec.calls
    assert (title, columns) == (GQ_LIST_TITLE, GQ_COLUMNS)
    assert [row["mobs"] for row in data[-2:]] == ["0", "3"]
    assert [row["time"] for row in data[-2:]] == ["20s", "60s"]


def test_show_gquest(full: "StatStore") -> None:
    """One global quest lists its mobs."""
    from aardwolf.statdb.libs import GQ_COLUMNS, GQ_MOB_COLUMNS, GQ_MOB_TITLE, gq_report

    rec = TableRecorder()
    lines = gq_report(full, 0, 1, formatters(table=rec))
    assert lines == ["Global quest 1", GQ_MOB_TITLE]
    (_, one, columns), (_, mobs, mob_columns) = rec.calls
    assert columns == GQ_COLUMNS
    assert mob_columns == GQ_MOB_COLUMNS
    assert len(one) == 1
    assert mobs == [{"num": "3", "name": "a troll", "location": "Cave"}]
    rec_none = TableRecorder()
    gq_report(full, 0, 2, formatters(table=rec_none))
    assert [_recorded(rec_none)[0][key] for key in ("mobs", "time")] == ["0", "20s"]
    assert _recorded(rec_none, 1) == []
    assert gq_report(full, 0, 99, formatters()) == ["No such global quest: 99"]


def test_mob_report(full: "StatStore") -> None:
    """The mob report totals the kills and lists the last ones with their marks."""
    from aardwolf.statdb.libs import MOB_COLUMNS, MOB_LIST_TITLE, mob_report

    rec = TableRecorder()
    lines = mob_report(full, 5, formatters(table=rec))
    text = _text(lines)
    assert "Overall             : @W4            @W3" in text
    assert "Vorpal              : @W1            @W0.333/kill" in text
    assert lines[-1] == MOB_LIST_TITLE
    ((title, data, columns),) = rec.calls
    assert (title, columns) == (MOB_LIST_TITLE, MOB_COLUMNS)
    last = data[-1]
    assert [last[key] for key in ("lvl", "mob", "txp", "xp", "rxp")] == [
        "3",
        "a rat",
        "12",
        "10",
        "0",
    ]
    assert [last[key] for key in ("tp", "s", "gold")] == ["1", "V", "50"]
    assert data[-2]["lvl"] == "3"
    assert data[-2]["mob"].startswith("a very long named")
    assert "monster" not in data[-2]["mob"]
    assert "@R0" in data[-3]["txp"]


def test_mobkill_list(full: "StatStore") -> None:
    """The kill list shows the newest first with time, level, gold and flags."""
    from aardwolf.statdb.libs import MOBKILL_COLUMNS, MOBKILL_TITLE, mobkill_list

    rec = TableRecorder()
    assert mobkill_list(full, 10, formatters(table=rec)) == [MOBKILL_TITLE]
    ((title, data, columns),) = rec.calls
    assert title == MOBKILL_TITLE
    assert columns == MOBKILL_COLUMNS
    assert len(data) == 3
    assert "a bat" in data[0]["name"]
    assert "very long named" in data[1]["name"]
    assert "monster" not in data[1]["name"]
    last = data[2]
    assert [last[k] for k in ("time", "name", "lvl", "txp", "gold", "flags")] == [
        "1970-01-01 00:26",
        "a rat",
        "3",
        "12",
        "<50>",
        "V",
    ]
    rec_one = TableRecorder()
    mobkill_list(full, 1, formatters(table=rec_one))
    assert len(_recorded(rec_one)) == 1


def test_mobkill_list_edges(empty: "StatStore") -> None:
    """No kills, a bad count, unknown values and several flags."""
    from aardwolf.statdb.libs import NO_KILLS, mobkill_list

    rec = TableRecorder()
    fmt = formatters(table=rec)
    assert mobkill_list(empty, 10, fmt) == [NO_KILLS]
    assert mobkill_list(empty, 0, fmt) == ["The count must be at least 1"]
    assert mobkill_list(empty, -1, fmt) == ["The count must be at least 1"]
    assert rec.calls == []
    empty.save_mobkill({"name": "x"})
    mobkill_list(empty, 10, fmt)
    last = _recorded(rec, -1)[-1]
    assert (last["name"], last["txp"], last["gold"]) == ("x", "0", "<0>")
    empty.save_mobkill({"name": "y", "vorpal": 1, "slit": 1})
    mobkill_list(empty, 10, fmt)
    assert _recorded(rec, -1)[0]["flags"] == "VS"


def test_reports_survive_missing_current_row(full: "StatStore") -> None:
    """Reports still run when the current stats row is gone."""
    from aardwolf.statdb.libs import cp_report, gq_report, level_report, mob_report, quest_report

    full.db.modify("DELETE FROM stats WHERE milestone = 'current'")
    fmt = formatters()
    assert quest_report(full, 0, None, fmt)
    assert level_report(full, 0, None, fmt)
    assert cp_report(full, 0, None, fmt)
    assert gq_report(full, 0, None, fmt)
    assert mob_report(full, 0, fmt)


def test_reports_survive_only_failed_rows(empty: "StatStore") -> None:
    """A table with only failed rows has no averages and still reports."""
    from aardwolf.statdb.libs import cp_report, gq_report, quest_report

    empty.save_whois({"name": "Tester"})
    empty.save_quest({"failed": 1})
    empty.save_cp({"failed": 1, "mobs": []})
    empty.save_gq({"won": 0, "mobs": []})
    fmt = formatters()
    assert "Quests Failed          : @W1            @W1" in _text(quest_report(empty, 1, None, fmt))
    assert "Failed         : @W1            @W1" in _text(cp_report(empty, 1, None, fmt))
    assert "Lost                    : @W             @W1" in _text(gq_report(empty, 1, None, fmt))


def _save_new_style(store: "StatStore", rows: list[tuple[str, float, int]]) -> None:
    """Save level or pup rows as the plugin now does: only the time reached."""
    store.save_whois({"name": "Tester"})
    for kind, start, trains in rows:
        store.save_level(
            {"type": kind, "starttime": start, "finishtime": -1, "trains": trains, "totallevels": 5}
        )


def test_level_report_times_from_the_next_start(empty: "StatStore") -> None:
    """Average time is the gap to the next row's start; the last row has none."""
    from aardwolf.statdb.libs import level_report

    _save_new_style(
        empty, [("level", 1000, 3), ("pup", 1300, 0), ("level", 1900, 2), ("level", 2500, 1)]
    )
    rec = TableRecorder()
    lines = level_report(empty, 4, None, formatters(table=rec))
    text = _text(lines)
    assert "Time                    : @W450s" in text
    data = _recorded(rec)
    # newest row first in the list: no time for the current row
    assert data[0]["id"] == "4"
    assert data[0]["time"] == ""
    assert [row["time"] for row in data[1:]] == ["600s", "600s", "300s"]


def test_level_report_filters_after_the_window(empty: "StatStore") -> None:
    """A row without trains is left out of the average but still ends the row before it."""
    from aardwolf.statdb.libs import level_report

    _save_new_style(
        empty, [("level", 1000, 3), ("level", 1100, 0), ("level", 2000, 2), ("pup", 2600, 0)]
    )
    rec = TableRecorder()
    lines = level_report(empty, 4, None, formatters(table=rec))
    # levels with trains: 1000 -> 1100 = 100s and 2000 -> 2600 = 600s
    assert "Time                    : @W350s" in _text(lines)
    assert _recorded(rec)[-1]["time"] == "100s"


def test_show_level_on_new_style_rows(empty: "StatStore") -> None:
    """A row finishes at the next row's start, and the last row is current."""
    from aardwolf.statdb.libs import level_report

    _save_new_style(empty, [("level", 1000, 3), ("level", 2000, 2)])
    empty.save_mobkill({"name": "a rat", "xp": 5, "totalxp": 20, "time": 1500})
    empty.save_mobkill({"name": "a bat", "xp": 5, "totalxp": 20, "time": 2500})
    first = level_report(empty, 0, 1, formatters(), 6000.0)
    assert any(line.startswith("Finished : ") and "Current" not in line for line in first)
    assert first[-2].startswith("It took 1000s with @G1@w mobs killed")
    last = level_report(empty, 0, 2, formatters())
    assert last[-1] == "Finished : Current"
    assert not any("mobs killed" in line for line in last)


NORMAL_KILL = {
    "name": "a rat",
    "time": 1500,
    "xp": 10,
    "rarexp": 4,
    "bonusxp": 2,
    "blessingxp": 3,
    "totalxp": 19,
    "gold": 5,
}
NOEXP_KILL = {
    "name": "a bat",
    "time": 1600,
    "noexp": 1,
    "xp": 100,
    "rarexp": 50,
    "bonusxp": 20,
    "blessingxp": 30,
    "totalxp": 200,
    "gold": 7,
    "vorpal": 1,
}


def test_mob_stats_leave_noexp_kills_out_of_xp(empty: "StatStore") -> None:
    from aardwolf.statdb.libs import mob_stats

    empty.save_mobkill(dict(NORMAL_KILL))
    empty.save_mobkill(dict(NOEXP_KILL))
    stats = mob_stats(empty.db)
    expected = {
        "xp": 10,
        "rarexp": 4,
        "bonusxp": 2,
        "blessingxp": 3,
        "totalxp": 19,
        "avexp": 10,
        "avetotalxp": 19,
        "averarexp": 4,
        "avebonusxp": 2,
        "aveblessxp": 3,
        "bonusmobsindb": 1,
        "blessmobsindb": 1,
        "raremobsindb": 2,
        "indb": 2,
        "gold": 12,
        "vorpal": 1,
    }
    assert {key: stats[key] for key in expected} == expected


def test_mob_stats_with_only_noexp_kills(empty: "StatStore") -> None:
    from aardwolf.statdb.libs import mob_report, mob_stats

    empty.save_mobkill(dict(NOEXP_KILL))
    stats = mob_stats(empty.db)
    assert stats["indb"] == 1
    assert stats["raremobsindb"] == 1
    assert stats["bonusmobsindb"] == 0
    assert stats["blessmobsindb"] == 0
    assert not stats["xp"]
    assert not stats["totalxp"]
    empty.db.modify("INSERT INTO stats (name, milestone) VALUES ('Tester', 'current')")
    assert mob_report(empty, 5, formatters())


def test_mob_line_has_no_bonus_flags_on_noexp_kills(empty: "StatStore") -> None:
    from aardwolf.statdb.libs import mob_report

    empty.db.modify("INSERT INTO stats (name, milestone) VALUES ('Tester', 'current')")
    empty.save_mobkill(dict(NORMAL_KILL))
    empty.save_mobkill(dict(NOEXP_KILL))
    rec = TableRecorder()
    mob_report(empty, 5, formatters(table=rec))
    normal_row, noexp_row = _recorded(rec)[-1], _recorded(rec)[-2]
    assert "@R" not in "".join(normal_row.values())
    assert normal_row["oxp"] == "DE"
    assert all("@R" in noexp_row[key] for key in ("txp", "xp", "rxp", "oxp"))
    assert noexp_row["oxp"] == "@R@w"
    assert noexp_row["s"] == "V"


def test_show_level_leaves_noexp_kills_out(empty: "StatStore") -> None:
    from aardwolf.statdb.libs import level_report

    _save_new_style(empty, [("level", 1000, 3), ("level", 2000, 2)])
    empty.save_mobkill({"name": "a rat", "xp": 5, "totalxp": 20, "time": 1500})
    empty.save_mobkill({"name": "a bat", "xp": 50, "totalxp": 500, "time": 1600, "noexp": 1})
    lines = level_report(empty, 0, 1, formatters(), 6000.0)
    assert lines[-2].startswith("It took 1000s with @G1@w mobs killed (@G20.00@w xp/mob)")


def test_show_level_with_only_noexp_kills_has_no_mob_line(empty: "StatStore") -> None:
    from aardwolf.statdb.libs import level_report

    _save_new_style(empty, [("level", 1000, 3), ("level", 2000, 2)])
    empty.save_mobkill({"name": "a bat", "xp": 50, "totalxp": 500, "time": 1600, "noexp": 1})
    lines = level_report(empty, 0, 1, formatters(), 6000.0)
    assert not any("mobs killed" in line for line in lines)


def test_column_lists_have_unique_keys_and_both_fields() -> None:
    """Every column list names a header and a key, and no key repeats."""
    from aardwolf.statdb.libs import (
        LEVEL_COLUMNS,
        MILESTONE_COLUMNS,
        MOBKILL_COLUMNS,
        QUEST_COLUMNS,
        QUEST_MOB_COLUMNS,
        QUEST_SHOW_COLUMNS,
        comparison_columns,
    )

    for columns in (
        LEVEL_COLUMNS,
        MILESTONE_COLUMNS,
        MOBKILL_COLUMNS,
        QUEST_COLUMNS,
        QUEST_MOB_COLUMNS,
        QUEST_SHOW_COLUMNS,
        comparison_columns("a", "b"),
    ):
        keys = [column["key"] for column in columns]
        assert len(set(keys)) == len(keys)
        assert all(set(column) == {"name", "key"} for column in columns)
    assert [c["name"] for c in QUEST_COLUMNS if c not in QUEST_SHOW_COLUMNS] == ["PK", "HC"]
    assert [c["name"] for c in comparison_columns("a", 2)] == [
        "Milestone",
        "a",
        "2",
        "Difference",
    ]


def test_milestone_data_groups_names_three_to_a_row() -> None:
    from aardwolf.statdb.libs import milestone_data

    assert milestone_data([]) == []
    assert milestone_data(["a", "b", "c", "d"]) == [
        {"first": "a", "second": "b", "third": "c"},
        {"first": "d", "second": "", "third": ""},
    ]


@pytest.mark.parametrize("count", [1, 2, 4, 5])
def test_milestone_data_rows_have_every_column_key(count: int) -> None:
    """A short last row has every key of the columns, "" for the missing cells."""
    from aardwolf.statdb.libs import MILESTONE_COLUMNS, milestone_data

    names = [f"m{number}" for number in range(count)]
    keys = [column["key"] for column in MILESTONE_COLUMNS]
    data = milestone_data(names)
    assert all(list(row) == keys for row in data)
    cells = [cell for row in data for cell in row.values()]
    assert cells[:count] == names
    assert set(cells[count:]) <= {""}


def test_milestone_text_pads_the_short_row_for_the_table() -> None:
    """The recorded table of four names has a last row with every key."""
    from aardwolf.statdb.libs import MilestoneList, milestone_text

    rec = TableRecorder()
    milestone_text(MilestoneList("", ["a", "b", "c", "d"]), formatters(table=rec))
    assert rec.calls[0][1][1] == {"first": "d", "second": "", "third": ""}


def test_milestone_text_without_names_has_no_table() -> None:
    from aardwolf.statdb.libs import MilestoneList, milestone_text

    rec = TableRecorder()
    fmt = formatters(table=rec)
    assert milestone_text(MilestoneList("", []), fmt) == ["No milestones"]
    assert milestone_text(MilestoneList("Levels between 1 and 2", []), fmt) == [
        "Levels between 1 and 2"
    ]
    assert rec.calls == []


def test_quest_data_keeps_only_the_keys_of_the_columns(full: "StatStore") -> None:
    from aardwolf.statdb.libs import QUEST_COLUMNS, quest_data

    items = full.db.getlast("quests", 2)
    assert isinstance(items, list)
    fmt = formatters()
    assert all(
        set(row) == {c["key"] for c in QUEST_COLUMNS}
        for row in quest_data(items, fmt, QUEST_COLUMNS)
    )
    only = quest_data(items, fmt, [{"name": "ID", "key": "id"}])
    assert all(set(row) == {"id"} for row in only)
    assert len(only) == 2


def test_cp_gq_and_mob_columns_have_unique_keys_and_every_cell_is_text(full: "StatStore") -> None:
    """Each column list has unique keys, and the rows hold exactly those keys as str."""
    from aardwolf.statdb.libs import (
        CP_COLUMNS,
        CP_MOB_COLUMNS,
        GQ_COLUMNS,
        GQ_MOB_COLUMNS,
        MOB_COLUMNS,
        cp_report,
        gq_report,
        mob_report,
    )

    for columns in (CP_COLUMNS, CP_MOB_COLUMNS, GQ_COLUMNS, GQ_MOB_COLUMNS, MOB_COLUMNS):
        keys = [column["key"] for column in columns]
        assert len(keys) == len(set(keys))
    assert [column["name"] for column in CP_COLUMNS] == [
        "ID", "Lvl", "QP", "BN", "TP", "TN", "PR", "Gold", "Mobs", "Time",
    ]  # fmt: skip
    assert [column["name"] for column in GQ_COLUMNS][3] == "QM"
    assert [column["name"] for column in MOB_COLUMNS] == [
        "Lvl", "Mob", "TXP", "XP", "RXP", "OXP", "TP", "S", "Gold",
    ]  # fmt: skip
    for report, columns in (
        (lambda f: cp_report(full, 5, None, f), CP_COLUMNS),
        (lambda f: cp_report(full, 0, 1, f), CP_COLUMNS),
        (lambda f: gq_report(full, 5, None, f), GQ_COLUMNS),
        (lambda f: gq_report(full, 0, 1, f), GQ_COLUMNS),
        (lambda f: mob_report(full, 5, f), MOB_COLUMNS),
    ):
        rec = TableRecorder()
        report(formatters(table=rec))
        for row in _recorded(rec):
            assert list(row) == [column["key"] for column in columns]
            assert all(isinstance(value, str) for value in row.values())


SHORT_SUMMARY_LABELS = (
    "BaL",
    "Bon",
    "Bls",
    "DB",
    "QP",
    "XP",
    "TP",
    "GQ",
    "CP",
    "OPK",
    "Pracs",
    "Comp",
    "Pups",
)


def _summary_labels(lines: list[str]) -> list[str]:
    """Return the label of each row of a summary, colors and values removed."""
    return [line[2:].split(" : ")[0].strip() for line in lines if " : " in line]


def test_summary_labels_are_spelled_out(full: "StatStore") -> None:
    """No summary of a report uses a short label, and every colon lines up."""
    from aardwolf.statdb.libs import (
        cp_report,
        gq_report,
        level_report,
        mob_report,
        quest_report,
    )

    fmt = formatters()
    for lines in (
        quest_report(full, 0, None, fmt),
        level_report(full, 0, None, fmt),
        cp_report(full, 0, None, fmt),
        gq_report(full, 0, None, fmt),
        mob_report(full, 0, fmt),
    ):
        labels = _summary_labels(lines)
        assert labels
        for label in labels:
            words = set(label.split())
            assert not words & set(SHORT_SUMMARY_LABELS), label
        rows = [line for line in lines if " : " in line]
        assert len({line.index(" : ") for line in rows}) == 1


def test_level_summary_names(full: "StatStore") -> None:
    """The level summary says powerups and spells out the train kinds."""
    from aardwolf.statdb.libs import level_report

    labels = _summary_labels(level_report(full, 0, None, formatters()))
    assert "Powerups" not in labels  # a header, not a row label
    for name in (
        "Total In Database",
        "Ave Bonus Trains",
        "Ave Blessing Trains",
        "Ave Battle Learn Trains",
        "Total Practices",
    ):
        assert name in labels


def test_per_unit_suffixes_are_spelled_out(full: "StatStore") -> None:
    """The averages of a campaign and a global quest say /campaign and /global quest."""
    from aardwolf.statdb.libs import cp_report, gq_report

    fmt = formatters()
    cp_text = _text(cp_report(full, 0, None, fmt))
    gq_text = _text(gq_report(full, 0, None, fmt))
    assert "/campaign" in cp_text
    assert "/CP" not in cp_text
    assert "/global quest" in gq_text
    assert "/GQ" not in gq_text


def test_show_level_headers_are_spelled_out(full: "StatStore") -> None:
    """The headers of one level are full names; the battle learn trains sit under theirs."""
    from aardwolf.statdb.libs import level_report

    lines = level_report(full, 0, 3, formatters())
    assert lines[0].split("  ")[0] == "@GID"
    assert "Total Level" in lines[0]
    assert "Hit Points" in lines[2]
    assert "Battle Learn Trains" in lines[4]
    assert "Bonus Strength" in lines[6]
    head = lines[4]
    values = lines[5]
    start = head.index("Battle Learn Trains") - len("@G")
    assert values[start : start + len("Battle Learn Trains")].strip() == "0"


def test_comparison_rows_use_the_full_names(full: "StatStore") -> None:
    """Each comparison row is named by the full name of its field."""
    from aardwolf.statdb.libs import FIELD_NAMES, compare_milestones

    rec = TableRecorder()
    compare_milestones(full, "", "", formatters(table=rec), now=5000)
    fields = [row["field"] for row in _recorded(rec)]
    assert fields == ["Date", "Time", *FIELD_NAMES.values()]


def test_field_names_cover_the_compared_fields() -> None:
    """FIELD_NAMES names every compared field and nothing else."""
    from aardwolf.statdb.libs import FIELD_NAMES, FIELDSTOCOMP

    assert set(FIELD_NAMES) == set(FIELDSTOCOMP)
