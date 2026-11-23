"""Tests for the statdb command output, over a made-up old database."""

from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from statdb_old_db import build_old_database
from statdb_support import formatters, make_db

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
    """The list shows the level range and the named milestones."""
    from aardwolf.statdb.libs import list_milestones

    lines = list_milestones(full)
    assert lines[0] == "Levels between 3 and 5"
    assert lines[1].split() == ["current", "start", "t0r1l5"]


def test_list_milestones_line_widths(empty: "StatStore") -> None:
    """Named milestones are three to a line, each padded to 15 characters."""
    from aardwolf.statdb.libs import list_milestones

    assert list_milestones(empty) == ["No milestones"]
    empty.save_whois({"name": "Tester"})
    empty.add_milestone("a")
    assert list_milestones(empty) == [f"{'current':<15} {'start':<15} {'a':<15}"]
    for extra in ("b", "c"):
        empty.add_milestone(extra)
    lines = list_milestones(empty)
    assert len(lines) == 2
    assert lines[1] == f"{'b':<15} {'c':<15}"
    empty.add_milestone("d")
    assert list_milestones(empty)[1] == f"{'b':<15} {'c':<15} {'d':<15}"


def test_compare_defaults_to_start_and_current(full: "StatStore") -> None:
    """With no names it compares start to current, with the difference of each stat."""
    from aardwolf.statdb.libs import compare_milestones

    lines = compare_milestones(full, "", "", formatters(), now=5000)
    assert lines[0].split() == ["Milestone", "start", "current", "Difference"]
    assert "Now" in lines[2]
    assert "4000s" in lines[2]
    levels = next(line for line in lines if line.startswith("totallevels"))
    assert levels.split() == ["totallevels", "1", "5", "4"]
    kills = next(line for line in lines if line.startswith("monsterskilled"))
    assert kills.split() == ["monsterskilled", "0", "4", "4"]


def test_compare_one_and_two_names_in_either_order(full: "StatStore") -> None:
    """One name compares to current, and two names are put in time order."""
    from aardwolf.statdb.libs import compare_milestones

    fmt = formatters()
    one = compare_milestones(full, "3", "", fmt, now=5000)
    assert one[0].split() == ["Milestone", "3", "current", "Difference"]
    two = compare_milestones(full, "5", "3", fmt, now=5000)
    assert two[0].split() == ["Milestone", "5", "3", "Difference"]
    levels = next(line for line in two if line.startswith("totallevels"))
    assert levels.split() == ["totallevels", "3", "5", "2"]
    assert "1000s" in two[2]


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
    """The quest report shows the totals, averages and the last quests."""
    from aardwolf.statdb.libs import quest_report

    text = _text(quest_report(full, 5, None, formatters()))
    assert "Quests         : @W4            @W2" in text
    assert "20.000/level" in text
    assert "Gold           : @W<300>        @W300/quest" in text
    lines = quest_report(full, 5, None, formatters())
    assert lines[-1].split() == [
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
    assert lines[-2].split()[-1] == "Failed"
    assert len(quest_report(full, 0, None, formatters())) == len(lines) - 5


def test_show_quest(full: "StatStore") -> None:
    """One quest shows its row, its mob and where it was."""
    from aardwolf.statdb.libs import quest_report

    lines = quest_report(full, 0, 1, formatters())
    assert lines[2].split() == [
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
    assert lines[4].split() == ["a", "rat", "A", "pipe", "Sewer"]
    assert quest_report(full, 0, 99, formatters()) == ["No such quest: 99"]


def test_level_report(full: "StatStore") -> None:
    """The level report totals levels and pups and lists the last rows."""
    from aardwolf.statdb.libs import level_report

    lines = level_report(full, 5, None, formatters())
    text = _text(lines)
    assert "Total Overall  : @W5            @W1" in text
    assert "Total In DB    : @W2            @W1" in text
    assert "Ave Bon Trains : @W0.500" in text
    assert lines[-1].split()[:3] == ["1", "3", "L"]
    assert lines[-1].endswith("500s")
    assert lines[-3].split()[:6] == ["3", "5", "L", "4", "1", "0"]


def test_show_level(full: "StatStore") -> None:
    """One level shows its numbers, its actual level and its times."""
    from aardwolf.statdb.libs import level_report

    lines = level_report(full, 0, 3, formatters(), 300.0)
    assert lines[1].split() == ["3", "lev", "5", "re0t0r1l5"]
    assert lines[5].split() == ["4", "1", "0", "0"]
    assert any(line.startswith("Started  : ") for line in lines)
    assert lines[-1] == "Finished : Current"
    assert level_report(full, 0, 99, formatters()) == ["No such level: 99"]


def test_show_level_with_kills_in_its_time(full: "StatStore") -> None:
    """A finished level shows how long it took and the mobs killed in it."""
    from aardwolf.statdb.libs import level_report

    lines = level_report(full, 0, 1, formatters(), 6000.0)
    assert lines[-2] == ("It took 500s with @G2@w mobs killed (@G18.50@w xp/mob) @G720@w xp/min")


def test_campaign_report(full: "StatStore") -> None:
    """The campaign report counts mobs, and a campaign without mobs counts 0."""
    from aardwolf.statdb.libs import cp_report

    lines = cp_report(full, 5, None, formatters())
    assert "Overall        : @W3            @W2" in _text(lines)
    assert lines[-1].split()[-2:] == ["2", "60s"]
    assert lines[-2].split()[-2:] == ["0", "Failed"]


def test_show_campaign(full: "StatStore") -> None:
    """One campaign lists its mobs; a campaign without mobs lists none."""
    from aardwolf.statdb.libs import cp_report

    lines = cp_report(full, 0, 1, formatters())
    assert lines[-3].split()[:3] == ["@Ga", "goblin", "Forest"]
    assert lines[-2].split()[:3] == ["@Gan", "orc", "Hills"]
    none = cp_report(full, 0, 2, formatters())
    assert none[2].split()[-1] == "Failed"
    assert none[-1] == none[-2]
    assert cp_report(full, 0, 99, formatters()) == ["No such campaign: 99"]


def test_gquest_report(full: "StatStore") -> None:
    """The global quest report shows won and lost, and the mob count of each."""
    from aardwolf.statdb.libs import gq_report

    lines = gq_report(full, 5, None, formatters())
    text = _text(lines)
    assert "Won            : @W1            @W1" in text
    assert "Lost           : @W             @W1" in text
    assert lines[-1].split()[-2:] == ["3", "60s"]
    assert lines[-2].split()[-2:] == ["0", "20s"]


def test_show_gquest(full: "StatStore") -> None:
    """One global quest lists its mobs."""
    from aardwolf.statdb.libs import gq_report

    lines = gq_report(full, 0, 1, formatters())
    assert lines[-2].split()[:4] == ["@G3", "a", "troll", "Cave"]
    none = gq_report(full, 0, 2, formatters())
    assert none[2].split()[-2:] == ["0", "20s"]
    assert none[-1] == none[-2]
    assert gq_report(full, 0, 99, formatters()) == ["No such global quest: 99"]


def test_mob_report(full: "StatStore") -> None:
    """The mob report totals the kills and lists the last ones with their marks."""
    from aardwolf.statdb.libs import mob_report

    lines = mob_report(full, 5, formatters())
    text = _text(lines)
    assert "Overall        : @W4            @W3" in text
    assert "Vorpal         : @W1            @W0.333/kill" in text
    assert lines[-1].split()[:6] == ["3", "a", "rat", "12", "10", "0"]
    assert lines[-1].split()[-3:] == ["1", "V", "50"]
    assert lines[-2].startswith("  3 a very long named ")
    assert "monster" not in lines[-2]
    assert "@R0" in lines[-3]


def test_mobkill_list(full: "StatStore") -> None:
    """The kill list shows the newest first with time, level, gold and flags."""
    from aardwolf.statdb.libs import mobkill_list

    lines = mobkill_list(full, 10, formatters())
    assert lines[0].startswith("@GTime")
    assert lines[1].startswith("@B-")
    assert len(lines) == 5
    assert "a bat" in lines[2]
    assert "very long named" in lines[3]
    assert "monster" not in lines[3]
    assert lines[4].split() == ["1970-01-01", "00:26", "a", "rat", "3", "12", "<50>", "V"]
    assert len(mobkill_list(full, 1, formatters())) == 3


def test_mobkill_list_edges(empty: "StatStore") -> None:
    """No kills, a bad count, unknown values and several flags."""
    from aardwolf.statdb.libs import NO_KILLS, mobkill_list

    fmt = formatters()
    assert mobkill_list(empty, 10, fmt) == [NO_KILLS]
    assert mobkill_list(empty, 0, fmt) == ["The count must be at least 1"]
    assert mobkill_list(empty, -1, fmt) == ["The count must be at least 1"]
    empty.save_mobkill({"name": "x"})
    assert mobkill_list(empty, 10, fmt)[-1].split() == ["x", "0", "<0>"]
    empty.save_mobkill({"name": "y", "vorpal": 1, "slit": 1})
    assert mobkill_list(empty, 10, fmt)[2].split()[-1] == "VS"


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
    assert "Quests Failed  : @W1            @W1" in _text(quest_report(empty, 1, None, fmt))
    assert "Failed         : @W1            @W1" in _text(cp_report(empty, 1, None, fmt))
    assert "Lost           : @W             @W1" in _text(gq_report(empty, 1, None, fmt))


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
    lines = level_report(empty, 4, None, formatters())
    text = _text(lines)
    assert "Time           : @W450s" in text
    assert text.count("600s") >= 1
    # newest row first in the list: no time for the current row
    assert lines[-4].split()[-1] != "600s"
    assert lines[-4].split()[0] == "4"
    assert len(lines[-4].split()) == 15
    assert lines[-3].endswith("600s")
    assert lines[-2].endswith("600s")
    assert lines[-1].endswith("300s")


def test_level_report_filters_after_the_window(empty: "StatStore") -> None:
    """A row without trains is left out of the average but still ends the row before it."""
    from aardwolf.statdb.libs import level_report

    _save_new_style(
        empty, [("level", 1000, 3), ("level", 1100, 0), ("level", 2000, 2), ("pup", 2600, 0)]
    )
    lines = level_report(empty, 4, None, formatters())
    # levels with trains: 1000 -> 1100 = 100s and 2000 -> 2600 = 600s
    assert "Time           : @W350s" in _text(lines)
    assert lines[-1].endswith("100s")


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
