"""The statdb command output, as pure functions over a ``StatStore``.

Ported from the old plugin's ``cmd_*`` and ``show_*`` methods with the same SQL aggregates
and line formats. The helpers bastproxy provides come in through ``Formatters``, so the
functions read nothing but the database.

The row lists (milestones, the milestone comparison, quests, levels and mob kills) print
through ``Formatters.table``, the ``plugins.core.utils:table.format`` API, with the column lists
and the pure row builders of this module.

Differences from the old output: an unknown row number reports "no such ..." instead of
failing, a campaign or global quest without mobs counts 0 mobs, an empty table shows zeros
and blanks instead of failing, and the finish and start times are compared to the number -1
(the old code compared them to the text ``'-1'``, which was always true).
"""

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, NamedTuple, cast

from aardwolf._libs.aardu import convert_level

from ._db import ReadDb
from ._store import StatStore

FIELDSTOCOMP = [
    "totallevels",
    "qpearned",
    "questscomplete",
    "questsfailed",
    "campaignsdone",
    "campaignsfld",
    "gquestswon",
    "duelswon",
    "duelslost",
    "timeskilled",
    "monsterskilled",
    "combatmazewins",
    "combatmazedeaths",
    "powerupsall",
    "totaltrivia",
]

NO_STATS = "No stats available"
NO_KILLS = "No kills recorded"
# the message of a report whose table has no rows
EMPTY_MESSAGES = {
    "quests": "No quests stats are available",
    "levels": "No levels/pups stats available",
    "campaigns": "No campaign stats available",
    "gquests": "No gq stats available",
    "mobkills": "No mob stats available",
}
DEFAULT_MOBKILL_COUNT = 10
# the names of the settings that default to the constants of this module
SETTING_MOBKILL_COUNT = "mobkillcount"
SETTING_TIME_FORMAT = "timeformat"
SPECIAL_FLAGS = (
    ("banishment", "B"),
    ("vorpal", "V"),
    ("assassinate", "A"),
    ("slit", "S"),
    ("deathblow", "D"),
    ("disintegrate", "I"),
)
TIME_FORMAT = "%a, %d %b %Y %H:%M:%S"


@dataclass(frozen=True)
class Formatters:
    """The bastproxy helpers the reports use.

    Attributes:
        format_time: Turns a number of seconds into text, ``plugins.core.utils:timelength.format``.
        readable: Shortens a number such as 1500000 to ``1.50 M``,
            ``plugins.core.utils:number.to.readable``.
        table: Formats a table, ``plugins.core.utils:table.format``: a title, the rows as dicts
            and the columns as ``{"name", "key"}`` dicts give the lines.
        line_length: The width of the divider lines.
        time_format: The ``strftime`` pattern of the dates a report shows.
    """

    format_time: Callable[[float], str]
    readable: Callable[[float], str]
    table: Callable[[str, list[dict[str, str]], list[dict[str, str]]], list[str]]
    line_length: int = 80
    time_format: str = TIME_FORMAT


def format_float(item: float | None, addto: str = "") -> str | int:
    """Format a number with three decimals and a suffix; 0 for a missing or zero value."""
    if item:
        return f"{item:.03f}{addto}"
    return 0


def format_row(
    rowname: str, data1: object, data2: object, datacolor: str = "@W", headercolor: str = "@C"
) -> str:
    """Format a row of a report: a name and two values."""
    return f"{headercolor}{rowname:<14} : {datacolor}{data1!s:<12} {datacolor}{data2!s:<12}"


def report_guard(db: ReadDb, table: str) -> str | None:
    """Return why a report of ``table`` has nothing to show, or None when it has data.

    The stats table must have a row, and so must the table itself.
    """
    if db.getlastrowid("stats") <= 0:
        return NO_STATS
    if db.getlastrowid(table) <= 0:
        return EMPTY_MESSAGES[table]
    return None


def _n(value: float | None) -> float:
    """Return value, or 0 when it is None."""
    return value or 0


def _divider(fmt: Formatters) -> str:
    """Return the divider line."""
    return "@B" + "-" * fmt.line_length


def _time_text(fmt: Formatters, row: dict[str, Any]) -> str:
    """Return the time a row took, or an empty string when its times are not known."""
    if row["finishtime"] != -1 and row["starttime"] != -1:
        return fmt.format_time(row["finishtime"] - row["starttime"])
    return ""


def _level_text(level: int) -> str:
    """Return a total level as ``T<tier> R<remort> L<level>``."""
    parts = convert_level(level)
    return f"T{parts['tier']} R{parts['remort']} L{parts['level']}"


# milestones


MILESTONE_COLUMNS: list[dict[str, str]] = [
    {"name": "Milestone", "key": "first"},
    {"name": "", "key": "second"},
    {"name": "", "key": "third"},
]
MILESTONE_TITLE = "Milestones"
COMPARE_TITLE = "Compare milestones"


class MilestoneList(NamedTuple):
    """The milestones of a database.

    Attributes:
        level_range: ``Levels between A and B``, or "" when there is no range.
        names: The names of the named milestones, in order.
    """

    level_range: str
    names: list[str]


def read_milestones(db: ReadDb) -> MilestoneList:
    """Read the level range and the named milestones of a database."""
    rows = db.select("SELECT milestone FROM stats")
    levels = db.select(
        "SELECT MIN(totallevels) as MIN, MAX(totallevels) as MAX FROM stats "
        "WHERE stats.totallevels == stats.milestone"
    )
    level_range = ""
    for row in levels:
        if row["MAX"] and row["MIN"]:
            level_range = f"Levels between {row['MIN']} and {row['MAX']}"

    names: list[str] = []
    for row in rows:
        try:
            int(row["milestone"])
        except (TypeError, ValueError):
            names.append(str(row["milestone"]))
    return MilestoneList(level_range, names)


def milestone_data(names: Sequence[str]) -> list[dict[str, str]]:
    """Group milestone names three to a row, under the keys of ``MILESTONE_COLUMNS``."""
    keys = [column["key"] for column in MILESTONE_COLUMNS]
    return [
        dict(zip(keys, names[start : start + len(keys)], strict=False))
        for start in range(0, len(names), len(keys))
    ]


def milestone_text(milestones: MilestoneList, fmt: Formatters) -> list[str]:
    """Return the lines of the milestone list: the level range, then a table of the names."""
    msg: list[str] = []
    if milestones.level_range:
        msg.append(milestones.level_range)
    if milestones.names:
        msg.extend(fmt.table(MILESTONE_TITLE, milestone_data(milestones.names), MILESTONE_COLUMNS))
    return msg or ["No milestones"]


def list_milestones(store: StatStore, fmt: Formatters) -> list[str]:
    """List the milestones: the level range, then a table of the named milestones."""
    return milestone_text(read_milestones(store.db), fmt)


def _when(row: dict[str, Any], now: float) -> None:
    """Add the ``dates`` and ``times`` of a milestone row, with 0 meaning now."""
    if row["time"] == 0:
        row["dates"] = "Now"
        row["times"] = ""
        row["time"] = now
    else:
        row["dates"] = time.strftime("%x", time.localtime(row["time"]))
        row["times"] = time.strftime("%X", time.localtime(row["time"]))


def comparison_columns(first: object, second: object) -> list[dict[str, str]]:
    """Return the columns of a comparison, headed by the names of the two milestones."""
    return [
        {"name": "Milestone", "key": "field"},
        {"name": str(first), "key": "first"},
        {"name": str(second), "key": "second"},
        {"name": "Difference", "key": "difference"},
    ]


def _comparison_row(
    field: str, first: object, second: object, difference: object
) -> dict[str, str]:
    """Return one row of a comparison, every cell as text."""
    return {
        "field": field,
        "first": str(first),
        "second": str(second),
        "difference": str(difference),
    }


def format_comparison(
    first: dict[str, Any], second: dict[str, Any], fmt: Formatters, now: float | None = None
) -> list[str]:
    """Format two milestone rows side by side, the earlier one first."""
    left = dict(first)
    right = dict(second)
    stamp = time.time() if now is None else now
    columns = comparison_columns(left["milestone"], right["milestone"])
    _when(left, stamp)
    _when(right, stamp)
    if right["time"] < left["time"]:
        left, right = right, left
    data = [
        _comparison_row(
            "Date", left["dates"], right["dates"], fmt.format_time(right["time"] - left["time"])
        ),
        _comparison_row("Time", left["times"], right["times"], ""),
    ]
    for field in FIELDSTOCOMP:
        one = _n(left[field])
        two = _n(right[field])
        data.append(_comparison_row(field, one, two, two - one))
    return list(fmt.table(COMPARE_TITLE, data, columns))


def milestone_names(first: str, second: str) -> tuple[str, str]:
    """Return the two milestone names to compare.

    With no names it is ``start`` and ``current``; with one name, that milestone and
    ``current``.
    """
    if first and second:
        return (first, second)
    if first:
        return (first, "current")
    return ("start", "current")


def comparison_lines(
    names: tuple[str, str],
    rows: Sequence[dict[str, Any] | None],
    fmt: Formatters,
    now: float | None = None,
) -> list[str]:
    """Compare two milestone rows, or say which of them does not exist."""
    missing = [
        f"milestone {name} does not exist" for name, row in zip(names, rows, strict=True) if not row
    ]
    if missing:
        return missing
    one, two = rows
    assert one is not None
    assert two is not None
    return format_comparison(one, two, fmt, now)


def compare_milestones(
    store: StatStore, first: str, second: str, fmt: Formatters, now: float | None = None
) -> list[str]:
    """Compare two milestones.

    With no names it compares ``start`` to ``current``; with one name, that milestone to
    ``current``.
    """
    names = milestone_names(first, second)
    return comparison_lines(names, [store.get_milestone(name) for name in names], fmt, now)


# quests


QUEST_COLUMNS: list[dict[str, str]] = [
    {"name": "ID", "key": "id"},
    {"name": "QP", "key": "qp"},
    {"name": "MC", "key": "mc"},
    {"name": "TR", "key": "tr"},
    {"name": "LK", "key": "lk"},
    {"name": "PK", "key": "pk"},
    {"name": "HC", "key": "hc"},
    {"name": "DBL", "key": "dbl"},
    {"name": "TL", "key": "tl"},
    {"name": "TP", "key": "tp"},
    {"name": "TN", "key": "tn"},
    {"name": "PR", "key": "pr"},
    {"name": "Gold", "key": "gold"},
    {"name": "Lvl", "key": "lvl"},
    {"name": "Time", "key": "time"},
]
# the columns of the single quest report, which has no PK and HC
QUEST_SHOW_COLUMNS = [column for column in QUEST_COLUMNS if column["key"] not in ("pk", "hc")]
QUEST_MOB_COLUMNS: list[dict[str, str]] = [
    {"name": "Mob", "key": "mob"},
    {"name": "Room", "key": "room"},
    {"name": "Area", "key": "area"},
]
QUEST_LIST_TITLE = "Recent quests"
QUEST_MOB_TITLE = "Quest mob"


def _quest_cells(item: dict[str, Any], fmt: Formatters) -> dict[str, str]:
    """Return the cells of a quest row, every column."""
    dbl = ""
    if int(item["double"]) == 1:
        dbl += "D"
    if int(item["daily"]) == 1:
        dbl += "E"
    ttime = fmt.format_time(item["finishtime"] - item["starttime"])
    if int(item["failed"]) == 1:
        ttime = "Failed"
    cells = {
        "id": item["quest_id"],
        "qp": item["qp"],
        "mc": item["mccp"],
        "tr": item["tierqp"],
        "lk": item["lucky"],
        "pk": item["opk"],
        "hc": item["hardcore"],
        "dbl": dbl,
        "tl": item["totqp"],
        "tp": item["tp"],
        "tn": item["trains"],
        "pr": item["pracs"],
        "gold": item["gold"],
        "lvl": convert_level(item["level"])["level"],
        "time": ttime,
    }
    return {key: str(value) for key, value in cells.items()}


def quest_data(
    items: Sequence[dict[str, Any]], fmt: Formatters, columns: list[dict[str, str]]
) -> list[dict[str, str]]:
    """Return the quests as table rows holding only the keys of ``columns``."""
    keys = [column["key"] for column in columns]
    rows = [_quest_cells(item, fmt) for item in items]
    return [{key: row[key] for key in keys} for row in rows]


def show_quest(store: StatStore, number: int, fmt: Formatters) -> list[str]:
    """Show one quest."""
    rows = store.db.getrow(number, "quests")
    if not rows or not isinstance(rows, list):
        return [f"No such quest: {number}"]
    item = rows[0]
    mob = {
        "mob": str(item["mobname"]),
        "room": str(item["mobroom"]),
        "area": str(item["mobarea"]),
    }
    return [
        *fmt.table(
            f"Quest {number}", quest_data([item], fmt, QUEST_SHOW_COLUMNS), QUEST_SHOW_COLUMNS
        ),
        *fmt.table(QUEST_MOB_TITLE, [mob], QUEST_MOB_COLUMNS),
    ]


def quest_report(store: StatStore, count: int, number: int | None, fmt: Formatters) -> list[str]:
    """Show quest statistics, the last ``count`` quests, or the quest ``number``."""
    guard = report_guard(store.db, "quests")
    if guard:
        return [guard]
    if number:
        return show_quest(store, number, fmt)

    msg = quest_summary(quest_stats(store.db), fmt)

    if count > 0:
        last = store.db.getlast("quests", count)
        if last and isinstance(last, list):
            msg.append("")
            msg.extend(
                fmt.table(QUEST_LIST_TITLE, quest_data(last, fmt, QUEST_COLUMNS), QUEST_COLUMNS)
            )
    return msg


def quest_stats(db: ReadDb) -> dict[str, Any]:
    """Return the numbers of the quest report: sums, averages and the current stats."""
    stats = db.select(
        """SELECT AVG(finishtime - starttime) as avetime,
                  SUM(qp) as qp,
                  AVG(qp) as qpquestave,
                  AVG(tierqp) as tierqpave,
                  SUM(tierqp) as tierqp,
                  AVG(mccp) as mccpave,
                  SUM(mccp) as mccp,
                  AVG(lucky) as luckyave,
                  SUM(lucky) as lucky,
                  AVG(opk) as opkave,
                  SUM(opk) as opk,
                  AVG(hardcore) as hardcoreave,
                  SUM(hardcore) as hardcore,
                  SUM(tp) as tp,
                  AVG(tp) as tpave,
                  SUM(trains) as trains,
                  AVG(trains) as trainsave,
                  SUM(pracs) as pracs,
                  AVG(pracs) as pracsave,
                  COUNT(*) as qindb,
                  SUM(totqp) as dboverall,
                  AVG(totqp) as dboverallave,
                  SUM(gold) as gold,
                  AVG(gold) as avegold FROM quests where failed = 0"""
    )[0]
    stats.update(db.select("SELECT COUNT(*) as failedindb FROM quests where failed != 0")[0])
    current = db.select(
        """SELECT qpearned, questscomplete, questsfailed,
            totallevels FROM stats WHERE milestone = 'current'"""
    )
    stats.update(
        current[0]
        if current
        else {"qpearned": 0, "questscomplete": 0, "questsfailed": 0, "totallevels": 0}
    )
    stats["indb"] = stats["failedindb"] + stats["qindb"]
    levels = _n(stats["totallevels"])
    stats["qplevelave"] = _n(stats["qpearned"]) / float(levels) if levels else 0
    return stats


def quest_summary(stats: dict[str, Any], fmt: Formatters) -> list[str]:
    """Format the numbers of ``quest_stats``."""
    div = _divider(fmt)

    def row(name: str, total: float | None, key: str, unit: str) -> str:
        return format_row(name, _n(total), format_float(stats[key], unit))

    msg = [
        format_row("DB Stats", "Total", "In DB", "@G", "@G"),
        div,
        format_row("Quests", stats["questscomplete"] + stats["questsfailed"], stats["indb"]),
        format_row("Quests Comp", stats["questscomplete"], stats["qindb"]),
        format_row("Quests Failed", stats["questsfailed"], stats["failedindb"]),
        "",
        format_row("QP Stats", "Total", "Average", "@G", "@G"),
        div,
        format_row("Overall QP", stats["qpearned"], format_float(stats["qplevelave"], "/level")),
        row("Quest QP", stats["qp"], "qpquestave", "/quest"),
        row("MCCP", stats["mccp"], "mccpave", "/quest"),
        row("Lucky", stats["lucky"], "luckyave", "/quest"),
        row("Tier", stats["tierqp"], "tierqpave", "/quest"),
        row("OPK", stats["opk"], "opkave", "/quest"),
        row("Hardcore", stats["hardcore"], "hardcoreave", "/quest"),
        format_row("QP Per Quest", "", format_float(stats["dboverallave"], "/quest")),
        format_row(
            "Gold",
            fmt.readable(_n(stats["gold"])),
            "%d/quest" % _n(stats["avegold"]),  # noqa: UP031  # %-formats keep the old column layout
        ),
        format_row("Time", "", fmt.format_time(stats["avetime"]) if stats["avetime"] else ""),
        "",
        format_row("Bonus Rewards", "Total", "Average", "@G", "@G"),
        div,
        row("TP", stats["tp"], "tpave", "/quest"),
        row("Trains", stats["trains"], "trainsave", "/quest"),
        row("Pracs", stats["pracs"], "pracsave", "/quest"),
    ]
    return msg


# levels


def _level_bonus(item: dict[str, Any]) -> int:
    """Return the bonus and blessing trains of a level."""
    return max(int(item["bonustrains"]), 0) + max(int(item["blessingtrains"]), 0)


def _next_level_start(store: StatStore, level_id: int) -> float | None:
    """Return the starttime of the row after ``level_id``, or None for the last row."""
    rows = store.db.select(
        "SELECT starttime FROM levels WHERE level_id > ? ORDER BY level_id LIMIT 1",
        (level_id,),
    )
    if not rows:
        return None
    return cast("float | None", rows[0]["starttime"])


def _gap_text(fmt: Formatters, start: object, nextstart: object) -> str:
    """Return the time between a row's start and the next row's start, or "" when unknown."""
    if (
        isinstance(start, (int, float))
        and isinstance(nextstart, (int, float))
        and start > 0
        and nextstart > 0
    ):
        return fmt.format_time(nextstart - start)
    return ""


LEVEL_COLUMNS: list[dict[str, str]] = [
    {"name": "ID", "key": "id"},
    {"name": "Lvl", "key": "lvl"},
    {"name": "T", "key": "t"},
    {"name": "TR", "key": "tr"},
    {"name": "BT", "key": "bt"},
    {"name": "PR", "key": "pr"},
    {"name": "HP", "key": "hp"},
    {"name": "MN", "key": "mn"},
    {"name": "MV", "key": "mv"},
    {"name": "S", "key": "s"},
    {"name": "I", "key": "i"},
    {"name": "W", "key": "w"},
    {"name": "C", "key": "c"},
    {"name": "D", "key": "d"},
    {"name": "L", "key": "l"},
    {"name": "Time", "key": "time"},
]
LEVEL_LIST_TITLE = "Recent levels"


def level_data(items: Sequence[dict[str, Any]], fmt: Formatters) -> list[dict[str, str]]:
    """Return the levels, newest first, as table rows.

    The time of a row is the gap to the start of the row before it, which started later.
    """
    data: list[dict[str, str]] = []
    for index, item in enumerate(items):
        nextstart = items[index - 1]["starttime"] if index > 0 else None
        cells = {
            "id": item["level_id"],
            "lvl": convert_level(item["level"])["level"],
            "t": "L" if item["type"] == "level" else "P",
            "tr": item["trains"],
            "bt": _level_bonus(item),
            "pr": item["pracs"],
            "hp": item["hp"],
            "mn": item["mp"],
            "mv": item["mv"],
            "s": item["str"],
            "i": item["int"],
            "w": item["wis"],
            "c": item["con"],
            "d": item["dex"],
            "l": item["luc"],
            "time": _gap_text(fmt, item["starttime"], nextstart),
        }
        data.append({key: str(value) for key, value in cells.items()})
    return data


def show_level(
    store: StatStore, number: int, fmt: Formatters, perlevel: float | None = None
) -> list[str]:
    """Show one level or pup."""
    rows = store.db.getrow(number, "levels")
    if not rows or not isinstance(rows, list):
        return [f"No such level: {number}"]
    item = rows[0]
    div = _divider(fmt)
    parts = convert_level(item["level"])
    actual = f"re{parts['redos']}t{parts['tier']}r{parts['remort']}l{parts['level']}"
    nextstart = _next_level_start(store, int(item["level_id"]))
    ttime = _gap_text(fmt, item["starttime"], nextstart)
    ltype = "lev" if item["type"] == "level" else "pup"

    msg = [
        "@G%-6s %-5s %-7s %-s" % ("ID", "Type", "TotLvl", "Actual"),  # noqa: UP031  # %-formats keep the old column layout
        "%-6s %-5s %-7s %-s" % (item["level_id"], ltype, item["level"], actual),  # noqa: UP031  # %-formats keep the old column layout
        "@G%-6s %2s %2s %-2s %-2s " % ("", "HP", "MN", "MV", "PR"),  # noqa: UP031  # %-formats keep the old column layout
        "%-6s %2s %2s %-2s %-2s" % ("", item["hp"], item["mp"], item["mv"], item["pracs"]),  # noqa: UP031  # %-formats keep the old column layout
        "@G%-6s %-2s %-2s %-2s %-2s" % ("", "TR", "BO", "BL", "BT"),  # noqa: UP031  # %-formats keep the old column layout
        "%-6s %-2s %-2s %-2s %-2s"  # noqa: UP031  # %-formats keep the old column layout
        % (
            "",
            item["trains"],
            item["bonustrains"],
            item["blessingtrains"],
            item["battlelearntrains"],
        ),
        "@G%-6s %-1s %-1s %-1s %-1s %-1s %-1s" % ("", "S", "I", "W", "C", "D", "L"),  # noqa: UP031  # %-formats keep the old column layout
        "%-6s %-1s %-1s %-1s %-1s %-1s %-1s"  # noqa: UP031  # %-formats keep the old column layout
        % ("", item["str"], item["int"], item["wis"], item["con"], item["dex"], item["luc"]),
    ]

    count = 0
    average = None
    if nextstart is not None:
        kills = store.db.select(
            "SELECT count(*) as count, AVG(totalxp) as average FROM "
            "mobkills where time > ? and time < ? and xp > 0 and noexp = 0",
            (item["starttime"], nextstart),
        )[0]
        count = kills["count"]
        average = kills["average"]

    if item["starttime"]:
        msg.append(div)
        msg.append(
            "Started  : " + time.strftime(fmt.time_format, time.localtime(item["starttime"]))
        )
        if nextstart is None:
            finished = "Current"
        else:
            finished = time.strftime(fmt.time_format, time.localtime(nextstart))
        msg.append(f"Finished : {finished}")

    if count > 0 and average and average > 0:
        msg.append(div)
        length = (nextstart or 0) - item["starttime"]
        text = f"It took {ttime} with " if ttime else ""
        text += f"@G{count}@w mobs killed"
        text += f" (@G{average:02.02f}@w xp/mob)"
        if length > 0 and perlevel:
            text += f" @G{int(perlevel / (length / 60)):02d}@w xp/min"
        msg.append(text)
        msg.append(div)
    return msg


def level_report(
    store: StatStore,
    count: int,
    number: int | None,
    fmt: Formatters,
    perlevel: float | None = None,
) -> list[str]:
    """Show level statistics, the last ``count`` levels, or the level ``number``."""
    guard = report_guard(store.db, "levels")
    if guard:
        return [guard]
    if number:
        return show_level(store, number, fmt, perlevel)

    msg = level_summary(level_stats(store.db), fmt)

    if count > 0:
        last = store.db.getlast("levels", count)
        if last and isinstance(last, list):
            msg.append("")
            msg.extend(fmt.table(LEVEL_LIST_TITLE, level_data(last, fmt), LEVEL_COLUMNS))
    return msg


def level_stats(db: ReadDb) -> dict[str, dict[str, Any]]:
    """Return the numbers of the level report: one dict for levels and one for pups."""
    current = db.select("SELECT totallevels, qpearned FROM stats WHERE milestone = 'current'")
    levels: dict[str, Any] = dict(current[0]) if current else {"totallevels": 0, "qpearned": 0}
    pups: dict[str, Any] = dict(db.select("SELECT MAX(powerupsall) as powerupsall FROM stats")[0])

    levels.update(
        db.select(
            """SELECT AVG(trains) as avetrains,
                    AVG(bonustrains) as avebonustrains,
                    AVG(blessingtrains) as aveblessingtrains,
                    AVG(battlelearntrains) as avebattlelearntrains,
                    SUM(trains + bonustrains + blessingtrains + battlelearntrains) as totaltrains,
                    SUM(pracs) as totalpracs,
                    COUNT(*) as indb
                    FROM levels where type = 'level' and trains > 0"""
        )[0]
    )
    levels.update(
        db.select(
            """WITH timed AS (SELECT *, LEAD(starttime) OVER (ORDER BY level_id) AS nextstart
                 FROM levels)
             SELECT AVG(nextstart - starttime) as avetime FROM timed
             where type = 'level' and trains > 0 and nextstart IS NOT NULL
             and starttime > 0 and nextstart > 0"""
        )[0]
    )
    pups.update(
        db.select(
            """SELECT AVG(trains) as avetrains,
                    AVG(bonustrains) as avebonustrains,
                    AVG(blessingtrains) as aveblessingtrains,
                    AVG(battlelearntrains) as avebattlelearntrains,
                    SUM(trains + bonustrains + blessingtrains + battlelearntrains) as totaltrains,
                    COUNT(*) as indb
                    FROM levels where type = 'pup'"""
        )[0]
    )
    pups.update(
        db.select(
            """WITH timed AS (SELECT *, LEAD(starttime) OVER (ORDER BY level_id) AS nextstart
                 FROM levels)
             SELECT AVG(nextstart - starttime) as avetime FROM timed
             where type = 'pup' and nextstart IS NOT NULL
             and starttime > 0 and nextstart > 0"""
        )[0]
    )
    return {"levels": levels, "pups": pups}


def level_summary(stats: dict[str, dict[str, Any]], fmt: Formatters) -> list[str]:
    """Format the numbers of ``level_stats``."""
    div = _divider(fmt)
    levels = stats["levels"]
    pups = stats["pups"]

    msg = [
        format_row("Type", "Levels", "Pups", "@G", "@G"),
        div,
        format_row("Total Overall", levels["totallevels"], pups["powerupsall"]),
        format_row("Total In DB", levels["indb"], pups["indb"]),
        format_row("Total Trains", _n(levels["totaltrains"]), _n(pups["totaltrains"])),
    ]
    level_sum = 0.0
    pup_sum = 0.0
    for title, key in (
        ("Ave Trains", "avetrains"),
        ("Ave Bon Trains", "avebonustrains"),
        ("Ave Bls Trains", "aveblessingtrains"),
        ("Ave BaL Trains", "avebattlelearntrains"),
    ):
        level_ave = format_float(levels[key])
        pup_ave = format_float(pups[key])
        level_sum += float(level_ave)
        pup_sum += float(pup_ave)
        msg.append(format_row(title, level_ave or 0, pup_ave or 0))
    msg.append(format_row("Ave Overall", level_sum or 0, pup_sum or 0))
    msg.append(format_row("Total Pracs", _n(levels["totalpracs"]), ""))
    msg.append(
        format_row(
            "Time",
            fmt.format_time(levels["avetime"]) if levels["avetime"] else "",
            fmt.format_time(pups["avetime"]) if pups["avetime"] else "",
        )
    )
    return msg


# campaigns


CP_COLUMNS: list[dict[str, str]] = [
    {"name": "ID", "key": "id"},
    {"name": "Lvl", "key": "lvl"},
    {"name": "QP", "key": "qp"},
    {"name": "BN", "key": "bn"},
    {"name": "TP", "key": "tp"},
    {"name": "TN", "key": "tn"},
    {"name": "PR", "key": "pr"},
    {"name": "Gold", "key": "gold"},
    {"name": "Mobs", "key": "mobs"},
    {"name": "Time", "key": "time"},
]
CP_MOB_COLUMNS: list[dict[str, str]] = [
    {"name": "Name", "key": "name"},
    {"name": "Location", "key": "location"},
]
CP_LIST_TITLE = "Recent campaigns"
CP_MOB_TITLE = "Campaign mobs"


def _cp_cells(item: dict[str, Any], mobs: object, fmt: Formatters) -> dict[str, str]:
    """Return the cells of a campaign row."""
    ttime = _time_text(fmt, item)
    if int(item["failed"]) == 1:
        ttime = "Failed"
    cells = {
        "id": item["cp_id"],
        "lvl": _level_text(item["level"]),
        "qp": item["qp"],
        "bn": item["bonusqp"],
        "tp": item["tp"],
        "tn": item["trains"],
        "pr": item["pracs"],
        "gold": item["gold"],
        "mobs": mobs,
        "time": ttime,
    }
    return {key: str(value) for key, value in cells.items()}


def cp_data(
    items: Sequence[dict[str, Any]], counts: dict[Any, dict[str, Any]], fmt: Formatters
) -> list[dict[str, str]]:
    """Return the campaigns as table rows; ``counts`` maps a campaign id to its mob count."""
    return [
        _cp_cells(item, counts.get(item["cp_id"], {}).get("mobcount", 0), fmt) for item in items
    ]


def cp_mob_data(mobs: Sequence[dict[str, Any]]) -> list[dict[str, str]]:
    """Return the mobs of a campaign as table rows."""
    return [{"name": str(mob["name"]), "location": str(mob["location"])} for mob in mobs]


def show_cp(store: StatStore, number: int, fmt: Formatters) -> list[str]:
    """Show one campaign and its mobs."""
    rows = store.db.getrow(number, "campaigns")
    if not rows or not isinstance(rows, list):
        return [f"No such campaign: {number}"]
    mobs = store.db.select("SELECT * FROM cpmobs WHERE cp_id = ?", (number,))
    one = [_cp_cells(rows[0], len(mobs), fmt)]
    return [
        *fmt.table(f"Campaign {number}", one, CP_COLUMNS),
        *fmt.table(CP_MOB_TITLE, cp_mob_data(mobs), CP_MOB_COLUMNS),
    ]


def cp_report(store: StatStore, count: int, number: int | None, fmt: Formatters) -> list[str]:
    """Show campaign statistics, the last ``count`` campaigns, or the campaign ``number``."""
    guard = report_guard(store.db, "campaigns")
    if guard:
        return [guard]
    if number:
        return show_cp(store, number, fmt)

    msg = cp_summary(cp_stats(store.db), fmt)

    if count > 0:
        last = store.db.getlast("campaigns", count)
        counts = store.db.selectbykeyword(
            "SELECT cp_id, count(*) as mobcount from cpmobs group by cp_id", "cp_id"
        )
        if last and isinstance(last, list):
            msg.append("")
            msg.extend(fmt.table(CP_LIST_TITLE, cp_data(last, counts, fmt), CP_COLUMNS))
    return msg


def cp_stats(db: ReadDb) -> dict[str, Any]:
    """Return the numbers of the campaign report."""
    current = db.select(
        "SELECT campaignsdone, campaignsfld, totallevels FROM stats WHERE milestone = 'current'"
    )
    stats: dict[str, Any] = (
        dict(current[0]) if current else {"campaignsdone": 0, "campaignsfld": 0, "totallevels": 0}
    )
    stats.update(
        db.select(
            """SELECT AVG(finishtime - starttime) as avetime,
                  SUM(qp) as totalqp,
                  AVG(qp) as aveqp,
                  SUM(tp) as totaltp,
                  AVG(tp) as avetp,
                  SUM(trains) as totaltrains,
                  AVG(trains) as avetrains,
                  SUM(pracs) as totalpracs,
                  AVG(pracs) as avepracs,
                  COUNT(*) as cindb,
                  SUM(gold) as totalgold,
                  AVG(gold) as avegold
                  FROM campaigns where failed = 0"""
        )[0]
    )
    stats.update(db.select("SELECT COUNT(*) as failedindb FROM campaigns where failed != 0")[0])
    return stats


def cp_summary(stats: dict[str, Any], fmt: Formatters) -> list[str]:
    """Format the numbers of ``cp_stats``."""
    div = _divider(fmt)
    indb = int(stats["cindb"]) + int(stats["failedindb"])
    total = int(_n(stats["campaignsdone"])) + int(_n(stats["campaignsfld"]))

    msg = [
        format_row("DB Stats", "Total", "In DB", "@G", "@G"),
        div,
        format_row("Overall", total, indb),
        format_row("Completed", stats["campaignsdone"], stats["cindb"]),
        format_row("Failed", stats["campaignsfld"], stats["failedindb"]),
        "",
        format_row("CP Stats", "Total", "Average", "@G", "@G"),
        div,
        format_row("QP", _n(stats["totalqp"]), format_float(stats["aveqp"], "/CP")),
        format_row(
            "Gold",
            fmt.readable(stats["totalgold"]) if stats["totalgold"] else 0,
            "%d/CP" % _n(stats["avegold"]),  # noqa: UP031  # %-formats keep the old column layout
        ),
        format_row("Time", "", fmt.format_time(stats["avetime"]) if stats["avetime"] else ""),
        "",
        format_row("Bonus Rewards", "Total", "Average", "@G", "@G"),
        div,
        format_row("TP", _n(stats["totaltp"]), format_float(stats["avetp"], "/CP")),
        format_row("Trains", _n(stats["totaltrains"]), format_float(stats["avetrains"], "/CP")),
        format_row("Pracs", _n(stats["totalpracs"]), format_float(stats["avepracs"], "/CP")),
    ]
    return msg


# global quests

GQ_COLUMNS: list[dict[str, str]] = [
    {"name": "ID", "key": "id"},
    {"name": "Lvl", "key": "lvl"},
    {"name": "QP", "key": "qp"},
    {"name": "QM", "key": "qm"},
    {"name": "TP", "key": "tp"},
    {"name": "TN", "key": "tn"},
    {"name": "PR", "key": "pr"},
    {"name": "Gold", "key": "gold"},
    {"name": "Mobs", "key": "mobs"},
    {"name": "Time", "key": "time"},
]
GQ_MOB_COLUMNS: list[dict[str, str]] = [
    {"name": "Num", "key": "num"},
    {"name": "Name", "key": "name"},
    {"name": "Location", "key": "location"},
]
GQ_LIST_TITLE = "Recent global quests"
GQ_MOB_TITLE = "Global quest mobs"


def _gq_cells(item: dict[str, Any], mobs: object, fmt: Formatters) -> dict[str, str]:
    """Return the cells of a global quest row."""
    cells = {
        "id": item["gq_id"],
        "lvl": _level_text(item["level"]),
        "qp": item["qp"],
        "qm": item["qpmobs"],
        "tp": item["tp"],
        "tn": item["trains"],
        "pr": item["pracs"],
        "gold": item["gold"],
        "mobs": mobs,
        "time": _time_text(fmt, item),
    }
    return {key: str(value) for key, value in cells.items()}


def gq_data(
    items: Sequence[dict[str, Any]], counts: dict[Any, dict[str, Any]], fmt: Formatters
) -> list[dict[str, str]]:
    """Return the global quests as table rows; ``counts`` maps a gq id to its mob count."""
    return [
        _gq_cells(item, counts.get(item["gq_id"], {}).get("mobcount", 0), fmt) for item in items
    ]


def gq_mob_data(mobs: Sequence[dict[str, Any]]) -> list[dict[str, str]]:
    """Return the mobs of a global quest as table rows."""
    return [
        {"num": str(mob["num"]), "name": str(mob["name"]), "location": str(mob["location"])}
        for mob in mobs
    ]


def show_gq(store: StatStore, number: int, fmt: Formatters) -> list[str]:
    """Show one global quest and its mobs."""
    rows = store.db.getrow(number, "gquests")
    if not rows or not isinstance(rows, list):
        return [f"No such global quest: {number}"]
    mobs = store.db.select("SELECT * FROM gqmobs WHERE gq_id = ?", (number,))
    one = [_gq_cells(rows[0], len(mobs), fmt)]
    return [
        *fmt.table(f"Global quest {number}", one, GQ_COLUMNS),
        *fmt.table(GQ_MOB_TITLE, gq_mob_data(mobs), GQ_MOB_COLUMNS),
    ]


def gq_report(store: StatStore, count: int, number: int | None, fmt: Formatters) -> list[str]:
    """Show global quest statistics, the last ``count`` or the global quest ``number``."""
    guard = report_guard(store.db, "gquests")
    if guard:
        return [guard]
    if number:
        return show_gq(store, number, fmt)

    msg = gq_summary(gq_stats(store.db), fmt)

    if count > 0:
        last = store.db.getlast("gquests", count)
        counts = store.db.selectbykeyword(
            "SELECT gq_id, SUM(num) as mobcount from gqmobs group by gq_id", "gq_id"
        )
        if last and isinstance(last, list):
            msg.append("")
            msg.extend(fmt.table(GQ_LIST_TITLE, gq_data(last, counts, fmt), GQ_COLUMNS))
    return msg


def gq_stats(db: ReadDb) -> dict[str, Any]:
    """Return the numbers of the global quest report."""
    won = db.select(
        """SELECT AVG(finishtime - starttime) as avetime,
                  SUM(qp) as qp,
                  AVG(qp) as qpave,
                  SUM(qpmobs) as qpmobs,
                  AVG(qpmobs) as qpmobsave,
                  SUM(tp) as tp,
                  AVG(tp) as tpave,
                  SUM(trains) as trains,
                  AVG(trains) as trainsave,
                  SUM(pracs) as pracs,
                  AVG(pracs) as pracsave,
                  COUNT(*) as indb,
                  SUM(gold) as gold,
                  AVG(gold) as avegold
                  FROM gquests where won = 1"""
    )[0]
    current = db.select("SELECT gquestswon FROM stats WHERE milestone = 'current'")
    gquestswon = _n(current[0]["gquestswon"]) if current else 0
    lost = db.select(
        """SELECT AVG(finishtime - starttime) as avetime,
                 SUM(qpmobs) as totalqp,
                 AVG(qpmobs) as aveqp,
                 COUNT(*) as indb
                 FROM gquests where won != 1"""
    )[0]
    overall = db.select(
        """SELECT SUM(qpmobs + qp) as overallqp,
                 AVG(qpmobs + qp) as aveoverallqp
                 FROM gquests"""
    )[0]
    return {"won": won, "lost": lost, "overall": overall, "gquestswon": gquestswon}


def gq_summary(stats: dict[str, Any], fmt: Formatters) -> list[str]:
    """Format the numbers of ``gq_stats``."""
    div = _divider(fmt)
    won = stats["won"]
    lost = stats["lost"]
    overall = stats["overall"]
    gquestswon = stats["gquestswon"]
    indb = won["indb"] + lost["indb"]

    msg = [
        format_row("GQ Stats", "Total", "In DB", "@G", "@G"),
        div,
        format_row("Won", gquestswon, won["indb"]),
        format_row("Lost", "", lost["indb"]),
        format_row("Overall", gquestswon + lost["indb"], indb),
        format_row("QP", _n(overall["overallqp"]), format_float(overall["aveoverallqp"], "/GQ")),
        "",
        format_row("GQ Won Stats", "Total", "Average", "@G", "@G"),
        div,
        format_row("GQ QP", _n(won["qp"]), format_float(won["qpave"], "/GQ")),
        format_row("GQ MOB QP", _n(won["qpmobs"]), format_float(won["qpmobsave"], "/GQ")),
        format_row("Time", "", fmt.format_time(won["avetime"]) if won["avetime"] else ""),
        format_row(
            "Gold",
            fmt.readable(_n(won["gold"])),
            "%d/GQ" % _n(won["avegold"]),  # noqa: UP031  # %-formats keep the old column layout
        ),
        format_row("TP", _n(won["tp"]), format_float(won["tpave"], "/GQ")),
        format_row("Trains", _n(won["trains"]), format_float(won["trainsave"], "/GQ")),
        format_row("Pracs", _n(won["pracs"]), format_float(won["pracsave"], "/GQ")),
        "",
        format_row("GQ Lost Stats", "Total", "Average", "@G", "@G"),
        div,
        format_row("GQ MOB QP", _n(lost["totalqp"]), format_float(lost["aveqp"], "/GQ")),
    ]
    return msg


# mob kills


MOB_COLUMNS: list[dict[str, str]] = [
    {"name": "Lvl", "key": "lvl"},
    {"name": "Mob", "key": "mob"},
    {"name": "TXP", "key": "txp"},
    {"name": "XP", "key": "xp"},
    {"name": "RXP", "key": "rxp"},
    {"name": "OXP", "key": "oxp"},
    {"name": "TP", "key": "tp"},
    {"name": "S", "key": "s"},
    {"name": "Gold", "key": "gold"},
]
MOB_LIST_TITLE = "Recent mobs"


def _mob_cells(item: dict[str, Any]) -> dict[str, str]:
    """Return the cells of a mob kill row; a no-xp kill shows its four xp cells in red."""
    bonus = ""
    if int(item["noexp"]) != 1:
        if int(item["bonusxp"]) != 0:
            bonus += "D"
        if int(item["blessingxp"]) != 0:
            bonus += "E"
    special = ""
    for column, letter in SPECIAL_FLAGS:
        if int(item[column]) == 1:
            special = letter
            break
    xp_cells = {
        "txp": str(item["totalxp"]),
        "xp": str(item["xp"]),
        "rxp": str(item["rarexp"]),
        "oxp": bonus,
    }
    if item["noexp"] == 1:
        xp_cells = {key: f"@R{value}@w" for key, value in xp_cells.items()}
    return {
        "lvl": str(convert_level(item["level"])["level"]),
        "mob": str(item["name"])[0:18],
        **xp_cells,
        "tp": "1" if int(item["tp"]) == 1 else "",
        "s": special,
        "gold": str(item["gold"]),
    }


def mob_data(items: Sequence[dict[str, Any]]) -> list[dict[str, str]]:
    """Return the mob kills as table rows; a name is cut to 18 characters."""
    return [_mob_cells(item) for item in items]


def mob_report(store: StatStore, count: int, fmt: Formatters) -> list[str]:
    """Show mob kill statistics and the last ``count`` kills."""
    guard = report_guard(store.db, "mobkills")
    if guard:
        return [guard]

    msg = mob_summary(mob_stats(store.db), fmt)

    if count > 0:
        last = store.db.getlast("mobkills", count)
        if last and isinstance(last, list):
            msg.append("")
            msg.extend(fmt.table(MOB_LIST_TITLE, mob_data(last), MOB_COLUMNS))
    return msg


def mob_stats(db: ReadDb) -> dict[str, Any]:
    """Return the numbers of the mob kill report."""
    current = db.select("SELECT monsterskilled FROM stats WHERE milestone = 'current'")
    stats: dict[str, Any] = dict(current[0]) if current else {"monsterskilled": 0}
    stats.update(
        db.select(
            """SELECT SUM(CASE WHEN noexp = 0 THEN xp END) AS xp,
                  SUM(CASE WHEN noexp = 0 THEN rarexp END) as rarexp,
                  SUM(CASE WHEN noexp = 0 THEN bonusxp END) AS bonusxp,
                  SUM(CASE WHEN noexp = 0 THEN blessingxp END) AS blessingxp,
                  SUM(CASE WHEN noexp = 0 THEN totalxp END) as totalxp,
                  AVG(CASE WHEN noexp = 0 THEN xp END) AS avexp,
                  AVG(CASE WHEN noexp = 0 THEN totalxp END) AS avetotalxp,
                  SUM(tp) AS tp,
                  SUM(vorpal) AS vorpal,
                  SUM(assassinate) AS assassinate,
                  SUM(disintegrate) AS disintegrate,
                  SUM(banishment) AS banishment,
                  SUM(slit) AS slit,
                  SUM(deathblow) AS deathblow,
                  SUM(gold) AS gold,
                  AVG(gold) AS avegold,
                  COUNT(*) AS indb
                  FROM mobkills"""
        )[0]
    )
    stats.update(
        db.select(
            """SELECT AVG(bonusxp) as avebonusxp,
                 COUNT(*) as bonusmobsindb
                 FROM mobkills where bonusxp > 0 and noexp = 0"""
        )[0]
    )
    stats.update(
        db.select(
            """SELECT AVG(blessingxp) as aveblessxp,
                 COUNT(*) as blessmobsindb
                 FROM mobkills where blessingxp > 0 and noexp = 0"""
        )[0]
    )
    stats.update(
        db.select(
            """SELECT AVG(CASE WHEN noexp = 0 THEN rarexp END) as averarexp,
                 COUNT(*) as raremobsindb
                 FROM mobkills where rarexp > 0"""
        )[0]
    )
    return stats


def mob_summary(stats: dict[str, Any], fmt: Formatters) -> list[str]:
    """Format the numbers of ``mob_stats``."""
    div = _divider(fmt)
    kills = float(stats["indb"])

    msg = [
        format_row("DB Stats", "Total", "In DB", "@G", "@G"),
        div,
        format_row("Overall", stats["monsterskilled"], stats["indb"]),
        format_row("Rare Mobs", "", stats["raremobsindb"]),
        format_row("Bonus Mobs", "", stats["bonusmobsindb"]),
        format_row("Blessing Mobs", "", stats["blessmobsindb"]),
        "",
        format_row("Stats", "Total", "Average", "@G", "@G"),
        div,
        format_row("XP", _n(stats["xp"]), format_float(stats["avexp"], "/kill")),
        format_row("Rare XP", _n(stats["rarexp"]), format_float(stats["averarexp"], "/kill")),
        format_row("Double XP", _n(stats["bonusxp"]), format_float(stats["avebonusxp"], "/kill")),
        format_row(
            "Blessing XP", _n(stats["blessingxp"]), format_float(stats["aveblessxp"], "/kill")
        ),
        format_row("Total XP", _n(stats["totalxp"]), format_float(stats["avetotalxp"], "/kill")),
        format_row(
            "Gold",
            fmt.readable(_n(stats["gold"])),
            "%d/kill" % _n(stats["avegold"]),  # noqa: UP031  # %-formats keep the old column layout
        ),
        format_row("TP", _n(stats["tp"]), format_float(_n(stats["tp"]) / kills, "/kill")),
    ]
    for title, key in (
        ("Vorpal", "vorpal"),
        ("Assassinate", "assassinate"),
        ("Slit", "slit"),
        ("Banishment", "banishment"),
        ("Deathblow", "deathblow"),
        ("Disintegrate", "disintegrate"),
    ):
        total = _n(stats[key])
        msg.append(format_row(title, total, format_float(total / kills, "/kill") or ""))
    return msg


def _flags(item: dict[str, Any]) -> str:
    """Return the letters of every special kill the row has."""
    return "".join(letter for column, letter in SPECIAL_FLAGS if int(item[column]) == 1)


MOBKILL_COLUMNS: list[dict[str, str]] = [
    {"name": "Time", "key": "time"},
    {"name": "Name", "key": "name"},
    {"name": "Lvl", "key": "lvl"},
    {"name": "TXP", "key": "txp"},
    {"name": "Gold", "key": "gold"},
    {"name": "Room", "key": "room"},
    {"name": "Flags", "key": "flags"},
]
MOBKILL_TITLE = "Recent mob kills"


def mobkill_data(items: Sequence[dict[str, Any]], fmt: Formatters) -> list[dict[str, str]]:
    """Return the mob kills as table rows; a name is cut to 18 characters."""
    data: list[dict[str, str]] = []
    for item in items:
        when = int(item["time"])
        level = int(item["level"])
        room = int(item["room_id"])
        data.append(
            {
                "time": time.strftime("%Y-%m-%d %H:%M", time.gmtime(when)) if when != -1 else "",
                "name": str(item["name"])[0:18],
                "lvl": str(convert_level(level)["level"]) if level >= 1 else "",
                "txp": str(item["totalxp"]),
                "gold": str(fmt.readable(item["gold"])),
                "room": str(room) if room else "",
                "flags": _flags(item),
            }
        )
    return data


def mobkill_list(store: StatStore, count: int, fmt: Formatters) -> list[str]:
    """List the last ``count`` mob kills, newest first."""
    if count < 1:
        return ["The count must be at least 1"]
    rows = store.recent_mobkills(count)
    if not rows:
        return [NO_KILLS]
    return list(fmt.table(MOBKILL_TITLE, mobkill_data(rows, fmt), MOBKILL_COLUMNS))
