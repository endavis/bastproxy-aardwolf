"""Tests for the pure helpers of the statmn plugin."""

from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from statdb_support import make_db

from aardwolf.statmn.libs import (
    Colors,
    Formatters,
    Select,
    StatRow,
    color_time,
    cp_message,
    gq_message,
    level_kills,
    level_message,
    level_window,
    quest_average,
    quest_message,
    report_lines,
    window_stats,
    xp_per_min,
)

if TYPE_CHECKING:
    from bastproxy.plugins.core.sqldb.libs._sqlite import Sqldb

COLORS = Colors("@i", "@s")


def _time(seconds: float, nosec: bool) -> str:
    """A stand-in for timelength.format: 3 minutes 5 seconds as ``03m:05s``."""
    whole = int(seconds)
    return f"{whole // 60:02d}m" if nosec else f"{whole // 60:02d}m:{whole % 60:02d}s"


def _center(text: str, filler: str, length: int, filler_color: str) -> str:
    return f"[{filler_color}{filler}{filler}]  {text}  [{length}]"


FMT = Formatters(format_time=_time, center=_center)


def test_color_time_colors_the_numbers() -> None:
    assert color_time("01h:00m", COLORS) == "@i@s01@ih:@s00@im"


def test_quest_message_shows_the_optional_parts_only_when_set() -> None:
    record = {"qp": 10, "totqp": 10, "starttime": 100, "finishtime": 280}
    msg = quest_message(record, COLORS, FMT)
    assert msg == (
        "@iStatMonitor: Quest finished for @s10 @i= @s10@iqp. It took @i@s03@im:@s00@is@i."
    )


def test_quest_message_lists_every_bonus_and_extra() -> None:
    record = {
        "qp": 10,
        "lucky": 2,
        "mccp": 1,
        "tierqp": 3,
        "opk": 4,
        "hardcore": 5,
        "daily": 1,
        "double": 1,
        "totqp": 26,
        "tp": 1,
        "trains": 2,
        "pracs": 3,
        "starttime": 0,
        "finishtime": 60,
    }
    msg = quest_message(record, COLORS, FMT, (4, 12.5))
    assert "@s10@i+@s2@i+@s1@i+@s3@i+@s4@i+@s5@i+@sE@i+@sD" in msg
    assert "@s26@iqp @s1@iTP @s2@itr @s3@ipr" in msg
    assert msg.endswith(" @iAvg: @s12.50 @iqp/quest over @s4@i quests.")


def test_quest_message_skips_the_average_for_one_quest() -> None:
    record = {"qp": 1, "totqp": 1, "starttime": 0, "finishtime": 1}
    assert "Avg" not in quest_message(record, COLORS, FMT, (1, 1.0))
    assert "Avg" not in quest_message(record, COLORS, FMT, None)


def test_cp_message_with_and_without_bonus() -> None:
    record = {"qp": 20, "bonusqp": 5, "tp": 2, "starttime": 0, "finishtime": 60}
    assert cp_message(record, COLORS, FMT) == (
        "@iStatMonitor: CP finished for @s20@i+@s5B@i=@s25qp @s2@iTP. "
        "@iIt took @i@s01@im:@s00@is@i."
    )
    plain = cp_message({"qp": 20, "starttime": 0, "finishtime": 60}, COLORS, FMT)
    assert "@s20@iqp. @iIt took" in plain
    assert "B" not in plain


def test_gq_message() -> None:
    record = {"qp": 30, "qpmobs": 7, "trains": 1, "starttime": 0, "finishtime": 60}
    assert gq_message(record, COLORS, FMT) == (
        "@iStatMonitor: GQ finished for @s30@i+@s7@iqp @s1@itr. @iIt took @i@s01@im:@s00@is@i."
    )


def _gain(**kwargs: int | str) -> dict[str, int | str]:
    base: dict[str, int | str] = {
        "type": "level",
        "hp": 10,
        "mp": 11,
        "mv": 12,
        "pracs": 5,
        "trains": 3,
        "blessingtrains": 0,
        "bonustrains": 0,
        "battlelearntrains": 0,
        "str": 0,
        "dex": 0,
        "con": 0,
        "luc": 0,
        "int": 0,
        "wis": 0,
    }
    return base | kwargs


def test_level_message_basics() -> None:
    msg = level_message(_gain(), COLORS, FMT)
    assert msg == (
        "@iStatMonitor: Gained a level: @s10@ihp @s11@imn @s12@imv @s3 @itrains @s5 @ipracs "
    )


def test_level_message_trains_total_includes_battle_learn() -> None:
    record = _gain(blessingtrains=1, bonustrains=2, battlelearntrains=4)
    msg = level_message(record, COLORS, FMT)
    assert " @s3@i+@s1E@i+@s2B@i+@s4L@i=@s10 @itrains " in msg


def test_level_message_lists_the_bonus_stats() -> None:
    msg = level_message(_gain(luc=1, wis=1), COLORS, FMT)
    assert "@sluc@i+@swis @ibonus " in msg


def test_pup_message_has_no_level_only_parts() -> None:
    record = _gain(type="pup")
    msg = level_message(record, COLORS, FMT)
    assert "hp" not in msg
    assert "pracs" not in msg
    assert msg.startswith("@iStatMonitor: Gained a pup:")


def test_level_message_with_kills_and_xp_per_min() -> None:
    msg = level_message(_gain(), COLORS, FMT, 600, (7, 12.345), 2000, 20)
    assert msg.endswith("@i@s10@im:@s00@is @s7 @imobs killed (@s12.35@ixp/mob @s200@ixp/min)")


def test_level_message_skips_a_low_xp_per_min() -> None:
    msg = level_message(_gain(), COLORS, FMT, 6000, (7, 12.0), 2000, 20)
    assert msg.endswith("@ixp/mob)")


def test_level_message_without_perlevel_does_not_fail() -> None:
    msg = level_message(_gain(), COLORS, FMT, 600, (7, 12.0), None, 20)
    assert msg.endswith("@ixp/mob)")


def test_level_message_without_kills_has_no_mob_part() -> None:
    assert "mobs killed" not in level_message(_gain(), COLORS, FMT, 600, (0, 0.0), 2000, 20)
    assert "mobs killed" not in level_message(_gain(), COLORS, FMT, 600, None, 2000, 20)


@pytest.mark.parametrize(
    ("perlevel", "window", "expected"),
    [
        (2000, 600, 200),
        (2000, 6000, None),
        (2000, 0, None),
        (0, 600, None),
        (-5, 600, None),
        (None, 600, None),
        ("x", 600, None),
        (True, 600, None),
    ],
)
def test_xp_per_min(perlevel: object, window: float, expected: int | None) -> None:
    assert xp_per_min(perlevel, window, 20) == expected


def test_report_lines_layout() -> None:
    rows = [
        StatRow("Quests", 1, 0, 12, 0, 2899),
        StatRow("CPs", 0, 0, 0, 0, 0),
        StatRow("GQs", 0, 0, 0, 0, 0),
        StatRow("Mobs", 4, 72, 0, 0, 1104),
    ]
    lines = report_lines(rows, 3600, COLORS, FMT)
    assert lines[0] == ""
    assert lines[1] == "@i[@i--]  @iStats for @i@s60@im@i  [50]"
    assert lines[2] == "@iType       |  Total     XP    QP    TP       Gold"
    assert lines[3] == "@i" + "-" * 50
    assert lines[4] == "@sQuests     @i| @s     1      0    12     0       2899"
    assert lines[7] == "@sMobs       @i| @s     4     72     0     0       1104"
    assert lines[8] == lines[3]
    assert lines[9] == "@sTotal      @i| @s           72    12     0       4003"
    assert lines[10] == ""


class FakeSelect:
    """A select that returns canned rows and records the calls."""

    def __init__(self, rows: list[dict[str, Any]] | None) -> None:
        self.rows = rows
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def __call__(self, sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]] | None:
        self.calls.append((sql, params))
        return self.rows


def test_helpers_return_none_without_a_result() -> None:
    nothing = FakeSelect(None)
    assert window_stats(nothing, 1.0) is None
    assert quest_average(nothing) is None
    assert level_kills(nothing, 1.0, 2.0) is None
    assert level_window(nothing, 5.0) is None


def test_level_window_needs_a_previous_level_and_a_start() -> None:
    assert level_window(FakeSelect([{"prev": None}]), 5.0) is None
    assert level_window(FakeSelect([{"prev": 2}]), 0) is None
    assert level_window(FakeSelect([{"prev": 2}]), 5.0) == 3.0


# against a real database


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> "Iterator[Sqldb]":
    """A new statdb database in a temporary home."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("BASTPROXY_HOME", str(home))
    database = make_db(tmp_path / "db")
    yield database
    database.close()


def _select(database: "Sqldb") -> Select:
    def run(sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
        return database.select(sql, params)

    return run


def test_window_stats_of_an_empty_database_is_all_zeros(db: "Sqldb") -> None:
    rows = window_stats(_select(db), 0)
    assert rows == [
        StatRow("Quests", 0, 0, 0, 0, 0),
        StatRow("CPs", 0, 0, 0, 0, 0),
        StatRow("GQs", 0, 0, 0, 0, 0),
        StatRow("Mobs", 0, 0, 0, 0, 0),
    ]


def test_window_stats_sums_the_window_and_skips_failed(db: "Sqldb") -> None:
    quest = "INSERT INTO quests(finishtime, totqp, gold, tp, failed) VALUES (?, ?, ?, ?, ?)"
    db.modify(quest, (1000, 10, 100, 1, 0))
    db.modify(quest, (1100, 20, 200, 2, 0))
    db.modify(quest, (1200, 50, 500, 5, 1))
    db.modify(quest, (10, 99, 99, 9, 0))
    campaign = (
        "INSERT INTO campaigns(finishtime, qp, bonusqp, gold, tp, failed) VALUES (?, ?, ?, ?, ?, ?)"
    )
    db.modify(campaign, (1000, 5, 2, 30, 1, 0))
    db.modify(campaign, (1000, 7, 2, 30, 1, 1))
    db.modify(
        "INSERT INTO gquests(finishtime, qp, qpmobs, gold, tp) VALUES (?, ?, ?, ?, ?)",
        (1000, 10, 4, 0, 3),
    )
    mob = "INSERT INTO mobkills(time, totalxp, gold, tp) VALUES (?, ?, ?, ?)"
    db.modify(mob, (1000, 25, 10, 0))
    db.modify(mob, (1001, 35, 20, 1))
    db.modify(mob, (5, 1000, 0, 0))
    rows = window_stats(_select(db), 500)
    assert rows == [
        StatRow("Quests", 2, 0, 30, 3, 300),
        StatRow("CPs", 1, 0, 7, 1, 30),
        StatRow("GQs", 1, 0, 14, 3, 0),
        StatRow("Mobs", 2, 60, 0, 1, 30),
    ]


def test_window_stats_leave_noexp_xp_out(db: "Sqldb") -> None:
    mob = "INSERT INTO mobkills(time, totalxp, gold, tp, noexp) VALUES (?, ?, ?, ?, ?)"
    db.modify(mob, (1000, 25, 10, 0, 0))
    db.modify(mob, (1001, 500, 20, 1, 1))
    rows = window_stats(_select(db), 500)
    assert rows is not None
    assert rows[-1] == StatRow("Mobs", 2, 25, 0, 1, 30)


def test_level_kills_leave_noexp_kills_out(db: "Sqldb") -> None:
    level = "INSERT INTO levels(starttime) VALUES (?)"
    for start in (400, 1000):
        db.modify(level, (start,))
    mob = "INSERT INTO mobkills(time, xp, totalxp, noexp) VALUES (?, ?, ?, ?)"
    db.modify(mob, (450, 10, 10, 0))
    db.modify(mob, (500, 50, 90, 1))
    assert level_kills(_select(db), 400, 1000) == (1, 10.0)


def test_quest_average_ignores_failed_quests(db: "Sqldb") -> None:
    assert quest_average(_select(db)) == (0, 0.0)
    quest = "INSERT INTO quests(totqp, failed) VALUES (?, ?)"
    db.modify(quest, (10, 0))
    db.modify(quest, (20, 0))
    db.modify(quest, (90, 1))
    assert quest_average(_select(db)) == (2, 15.0)


def test_level_window_and_kills_use_the_previous_level(db: "Sqldb") -> None:
    level = "INSERT INTO levels(starttime) VALUES (?)"
    for start in (-1, 100, 400, 1000):
        db.modify(level, (start,))
    mob = "INSERT INTO mobkills(time, xp, totalxp) VALUES (?, ?, ?)"
    db.modify(mob, (50, 5, 5))
    db.modify(mob, (450, 10, 10))
    db.modify(mob, (500, 20, 30))
    db.modify(mob, (600, 0, 99))
    db.modify(mob, (1100, 10, 10))
    select = _select(db)
    assert level_window(select, 1000) == 600
    assert level_window(select, 100) is None
    assert level_kills(select, 400, 1000) == (2, 20.0)
    assert level_kills(select, 2000, 3000) == (0, 0.0)


def test_report_lines_line_length_parameter() -> None:
    rows = [StatRow("Quests", 1, 0, 12, 0, 2899)]
    narrow = report_lines(rows, 3600, COLORS, FMT, 20)
    assert narrow[3] == "@i" + "-" * 20
    assert narrow[1].endswith("[20]")
    assert narrow[2] == report_lines(rows, 3600, COLORS, FMT)[2]
    assert report_lines(rows, 3600, COLORS, FMT)[3] == "@i" + "-" * 50
