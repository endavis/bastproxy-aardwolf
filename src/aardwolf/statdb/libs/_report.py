"""The statdb command output, as pure functions over a ``StatStore``.

Ported from the old plugin's ``cmd_*`` and ``show_*`` methods with the same SQL aggregates
and line formats. The helpers bastproxy provides come in through ``Formatters``, so the
functions read nothing but the database.

Differences from the old output: an unknown row number reports "no such ..." instead of
failing, a campaign or global quest without mobs counts 0 mobs, an empty table shows zeros
and blanks instead of failing, and the finish and start times are compared to the number -1
(the old code compared them to the text ``'-1'``, which was always true).
"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from aardwolf.libs.aardu import convert_level

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
DEFAULT_MOBKILL_COUNT = 10
SPECIAL_FLAGS = (
    ("banishment", "B"),
    ("vorpal", "V"),
    ("assassinate", "A"),
    ("slit", "S"),
    ("deathblow", "D"),
    ("disintegrate", "I"),
)
TIME_FORMAT = "%a, %d %b %Y %H:%M:%S +0000"


@dataclass(frozen=True)
class Formatters:
    """The bastproxy helpers the reports use.

    Attributes:
        format_time: Turns a number of seconds into text, ``plugins.core.utils:timelength.format``.
        readable: Shortens a number such as 1500000 to ``1.50 M``,
            ``plugins.core.utils:number.to.readable``.
        line_length: The width of the divider lines.
    """

    format_time: Callable[[float], str]
    readable: Callable[[float], str]
    line_length: int = 80


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


def list_milestones(store: StatStore) -> list[str]:
    """List the milestones: the level range, then the named milestones three to a line."""
    msg: list[str] = []
    rows = store.db.select("SELECT milestone FROM stats")
    levels = store.db.select(
        "SELECT MIN(totallevels) as MIN, MAX(totallevels) as MAX FROM stats "
        "WHERE stats.totallevels == stats.milestone"
    )
    for row in levels:
        if row["MAX"] and row["MIN"]:
            msg.append(f"Levels between {row['MIN']} and {row['MAX']}")

    items: list[str] = []
    for row in rows:
        try:
            int(row["milestone"])
        except (TypeError, ValueError):
            items.append(str(row["milestone"]))
        if len(items) == 3:
            msg.append(" ".join(f"{item:<15}" for item in items))
            items = []
    if items:
        msg.append(" ".join(f"{item:<15}" for item in items))

    return msg or ["No milestones"]


def _when(row: dict[str, Any], now: float) -> None:
    """Add the ``dates`` and ``times`` of a milestone row, with 0 meaning now."""
    if row["time"] == 0:
        row["dates"] = "Now"
        row["times"] = ""
        row["time"] = now
    else:
        row["dates"] = time.strftime("%x", time.localtime(row["time"]))
        row["times"] = time.strftime("%X", time.localtime(row["time"]))


def format_comparison(
    first: dict[str, Any], second: dict[str, Any], fmt: Formatters, now: float | None = None
) -> list[str]:
    """Format two milestone rows side by side, the earlier one first."""
    left = dict(first)
    right = dict(second)
    stamp = time.time() if now is None else now
    row_format = "{:<17} {:<15} {:<15} {:<10}"
    msg = [row_format.format("Milestone", left["milestone"], right["milestone"], "Difference")]
    msg.append("@g" + "-" * 60)
    _when(left, stamp)
    _when(right, stamp)
    if right["time"] < left["time"]:
        left, right = right, left
    msg.append(
        row_format.format(
            "Date", left["dates"], right["dates"], fmt.format_time(right["time"] - left["time"])
        )
    )
    msg.append(row_format.format("Time", left["times"], right["times"], ""))
    msg.append("@g" + "-" * 60)
    for field in FIELDSTOCOMP:
        one = _n(left[field])
        two = _n(right[field])
        msg.append(row_format.format(field, one, two, two - one))
    return msg


def compare_milestones(
    store: StatStore, first: str, second: str, fmt: Formatters, now: float | None = None
) -> list[str]:
    """Compare two milestones.

    With no names it compares ``start`` to ``current``; with one name, that milestone to
    ``current``.
    """
    if first and second:
        names = (first, second)
    elif first:
        names = (first, "current")
    else:
        names = ("start", "current")
    rows = [store.get_milestone(name) for name in names]
    missing = [
        f"milestone {name} does not exist" for name, row in zip(names, rows, strict=True) if not row
    ]
    if missing:
        return missing
    one, two = rows
    assert one is not None
    assert two is not None
    return format_comparison(one, two, fmt, now)


# quests


def _quest_row(item: dict[str, Any], fmt: Formatters, extra: bool) -> str:
    """Format a quest as a line of the quest list, or of the single quest report."""
    dbl = ""
    if int(item["double"]) == 1:
        dbl += "D"
    if int(item["daily"]) == 1:
        dbl += "E"
    level = convert_level(item["level"])["level"]
    ttime = fmt.format_time(item["finishtime"] - item["starttime"])
    if int(item["failed"]) == 1:
        ttime = "Failed"
    if extra:
        return "%-6s %2s %2s %2s %2s %2s %2s %3s %2s %2s %2s %2s %4s %3s %8s" % (  # noqa: UP031  # %-formats keep the old column layout
            item["quest_id"],
            item["qp"],
            item["mccp"],
            item["tierqp"],
            item["lucky"],
            item["opk"],
            item["hardcore"],
            dbl,
            item["totqp"],
            item["tp"],
            item["trains"],
            item["pracs"],
            item["gold"],
            level,
            ttime,
        )
    return "%-6s %2s %2s %2s %2s %3s %2s %2s %2s %2s %4s %3s %8s" % (  # noqa: UP031  # %-formats keep the old column layout
        item["quest_id"],
        item["qp"],
        item["mccp"],
        item["tierqp"],
        item["lucky"],
        dbl,
        item["totqp"],
        item["tp"],
        item["trains"],
        item["pracs"],
        item["gold"],
        level,
        ttime,
    )


def show_quest(store: StatStore, number: int, fmt: Formatters) -> list[str]:
    """Show one quest."""
    rows = store.db.getrow(number, "quests")
    if not rows or not isinstance(rows, list):
        return [f"No such quest: {number}"]
    item = rows[0]
    div = _divider(fmt)
    return [
        "@G%-6s %-2s %-2s %-2s %-2s %-3s %-2s %-2s %-2s %-2s %-4s %-3s   %s"  # noqa: UP031  # %-formats keep the old column layout
        % ("ID", "QP", "MC", "TR", "LK", "DBL", "TL", "TP", "TN", "PR", "Gold", "Lvl", "Time"),
        div,
        _quest_row(item, fmt, extra=False),
        div,
        f"{item['mobname']:<25} {item['mobroom']:<25} {item['mobarea']:<20}",
        div,
    ]


def quest_report(store: StatStore, count: int, number: int | None, fmt: Formatters) -> list[str]:
    """Show quest statistics, the last ``count`` quests, or the quest ``number``."""
    if store.db.getlastrowid("stats") <= 0:
        return [NO_STATS]
    if store.db.getlastrowid("quests") <= 0:
        return ["No quests stats are available"]
    if number:
        return show_quest(store, number, fmt)

    div = _divider(fmt)
    stats = store.db.select(
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
    stats.update(store.db.select("SELECT COUNT(*) as failedindb FROM quests where failed != 0")[0])
    current = store.db.select(
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

    if count > 0:
        last = store.db.getlast("quests", count)
        if last and isinstance(last, list):
            msg.append("")
            msg.append(
                "@G%-6s %-2s %-2s %-2s %-2s %-2s %-2s %-3s %-2s %-2s %-2s %-2s %-4s %-3s   %s"  # noqa: UP031  # %-formats keep the old column layout
                % (
                    "ID",
                    "QP",
                    "MC",
                    "TR",
                    "LK",
                    "PK",
                    "HC",
                    "DBL",
                    "TL",
                    "TP",
                    "TN",
                    "PR",
                    "Gold",
                    "Lvl",
                    "Time",
                )
            )
            msg.append(div)
            msg.extend(_quest_row(item, fmt, extra=True) for item in last)
    return msg


# levels


def _level_bonus(item: dict[str, Any]) -> int:
    """Return the bonus and blessing trains of a level."""
    return max(int(item["bonustrains"]), 0) + max(int(item["blessingtrains"]), 0)


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
    ttime = _time_text(fmt, item)
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

    kills = store.db.select(
        "SELECT count(*) as count, AVG(totalxp) as average FROM "
        "mobkills where time > ? and time < ? and xp > 0",
        (item["starttime"], item["finishtime"]),
    )[0]
    count = kills["count"]
    average = kills["average"]

    if item["starttime"] or item["finishtime"]:
        msg.append(div)
        if item["starttime"]:
            msg.append(
                "Started  : " + time.strftime(TIME_FORMAT, time.localtime(item["starttime"]))
            )
        if item["finishtime"]:
            if item["finishtime"] == -1:
                finished = "Current"
            else:
                finished = time.strftime(TIME_FORMAT, time.localtime(item["finishtime"]))
            msg.append(f"Finished : {finished}")

    if count > 0 and average and average > 0:
        msg.append(div)
        length = item["finishtime"] - item["starttime"]
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
    if store.db.getlastrowid("stats") <= 0:
        return [NO_STATS]
    if store.db.getlastrowid("levels") <= 0:
        return ["No levels/pups stats available"]
    if number:
        return show_level(store, number, fmt, perlevel)

    div = _divider(fmt)
    current = store.db.select("SELECT totallevels, qpearned FROM stats WHERE milestone = 'current'")
    levels: dict[str, Any] = dict(current[0]) if current else {"totallevels": 0, "qpearned": 0}
    pups: dict[str, Any] = dict(
        store.db.select("SELECT MAX(powerupsall) as powerupsall FROM stats")[0]
    )

    levels.update(
        store.db.select(
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
        store.db.select(
            """SELECT AVG(finishtime - starttime) as avetime FROM levels
             where type = 'level' and finishtime <> -1 and trains > 0"""
        )[0]
    )
    pups.update(
        store.db.select(
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
        store.db.select(
            """SELECT AVG(finishtime - starttime) as avetime FROM levels
             where type = 'pup' and finishtime <> -1"""
        )[0]
    )

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

    if count > 0:
        last = store.db.getlast("levels", count)
        if last and isinstance(last, list):
            msg.append("")
            msg.append(
                "@G%-6s %-3s %2s %2s %2s %-2s %-2s %-2s %-2s %-1s %-1s %-1s %-1s %-1s %-1s   %s"  # noqa: UP031  # %-formats keep the old column layout
                % (
                    "ID",
                    "Lvl",
                    "T",
                    "TR",
                    "BT",
                    "PR",
                    "HP",
                    "MN",
                    "MV",
                    "S",
                    "I",
                    "W",
                    "C",
                    "D",
                    "L",
                    "Time",
                )
            )
            msg.append(div)
            for item in last:
                msg.append(
                    "%-6s %-3s %2s %2s %2s %-2s %-2s %-2s %-2s %-1s %-1s %-1s %-1s %-1s %-1s   %s"  # noqa: UP031  # %-formats keep the old column layout
                    % (
                        item["level_id"],
                        convert_level(item["level"])["level"],
                        "L" if item["type"] == "level" else "P",
                        item["trains"],
                        _level_bonus(item),
                        item["pracs"],
                        item["hp"],
                        item["mp"],
                        item["mv"],
                        item["str"],
                        item["int"],
                        item["wis"],
                        item["con"],
                        item["dex"],
                        item["luc"],
                        _time_text(fmt, item),
                    )
                )
    return msg


# campaigns


def _cp_line(item: dict[str, Any], mobs: object, fmt: Formatters) -> str:
    """Format a campaign as a line of a report."""
    ttime = _time_text(fmt, item)
    if int(item["failed"]) == 1:
        ttime = "Failed"
    return "%-6s %-12s %-2s %2s %2s %2s %2s %6s  %-3s  %s" % (  # noqa: UP031  # %-formats keep the old column layout
        item["cp_id"],
        _level_text(item["level"]),
        item["qp"],
        item["bonusqp"],
        item["tp"],
        item["trains"],
        item["pracs"],
        item["gold"],
        mobs,
        ttime,
    )


CP_HEADER = "@G%-6s %-12s %-2s %-2s %-2s %-2s %-2s %6s %-4s  %s" % (  # noqa: UP031  # %-formats keep the old column layout
    "ID",
    "Lvl",
    "QP",
    "BN",
    "TP",
    "TN",
    "PR",
    "Gold",
    "Mobs",
    "Time",
)


def show_cp(store: StatStore, number: int, fmt: Formatters) -> list[str]:
    """Show one campaign and its mobs."""
    rows = store.db.getrow(number, "campaigns")
    if not rows or not isinstance(rows, list):
        return [f"No such campaign: {number}"]
    mobs = store.db.select("SELECT * FROM cpmobs WHERE cp_id = ?", (number,))
    div = _divider(fmt)
    msg = [CP_HEADER, div, _cp_line(rows[0], len(mobs), fmt), div]
    msg.append("@G%-30s %-30s" % ("Name", "Location"))  # noqa: UP031  # %-formats keep the old column layout
    msg.append(div)
    msg.extend("@G%-30s %-30s" % (mob["name"], mob["location"]) for mob in mobs)  # noqa: UP031  # %-formats keep the old column layout
    msg.append(div)
    return msg


def cp_report(store: StatStore, count: int, number: int | None, fmt: Formatters) -> list[str]:
    """Show campaign statistics, the last ``count`` campaigns, or the campaign ``number``."""
    if store.db.getlastrowid("stats") <= 0:
        return [NO_STATS]
    if store.db.getlastrowid("campaigns") <= 0:
        return ["No campaign stats available"]
    if number:
        return show_cp(store, number, fmt)

    div = _divider(fmt)
    current = store.db.select(
        "SELECT campaignsdone, campaignsfld, totallevels FROM stats WHERE milestone = 'current'"
    )
    stats: dict[str, Any] = (
        dict(current[0]) if current else {"campaignsdone": 0, "campaignsfld": 0, "totallevels": 0}
    )
    stats.update(
        store.db.select(
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
    stats.update(
        store.db.select("SELECT COUNT(*) as failedindb FROM campaigns where failed != 0")[0]
    )
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

    if count > 0:
        last = store.db.getlast("campaigns", count)
        counts = store.db.selectbykeyword(
            "SELECT cp_id, count(*) as mobcount from cpmobs group by cp_id", "cp_id"
        )
        if last and isinstance(last, list):
            msg.append("")
            msg.append(CP_HEADER)
            msg.append(div)
            msg.extend(
                _cp_line(item, counts.get(item["cp_id"], {}).get("mobcount", 0), fmt)
                for item in last
            )
    return msg


# global quests

GQ_HEADER = "@G%-6s %-12s %-2s %-2s %-2s %-2s %-2s %6s %-4s  %s" % (  # noqa: UP031  # %-formats keep the old column layout
    "ID",
    "Lvl",
    "QP",
    "QM",
    "TP",
    "TN",
    "PR",
    "Gold",
    "Mobs",
    "Time",
)


def _gq_line(item: dict[str, Any], mobs: object, fmt: Formatters) -> str:
    """Format a global quest as a line of a report."""
    return "%-6s %-12s %2s %2s %2s %2s %2s %6s  %-3s  %s" % (  # noqa: UP031  # %-formats keep the old column layout
        item["gq_id"],
        _level_text(item["level"]),
        item["qp"],
        item["qpmobs"],
        item["tp"],
        item["trains"],
        item["pracs"],
        item["gold"],
        mobs,
        _time_text(fmt, item),
    )


def show_gq(store: StatStore, number: int, fmt: Formatters) -> list[str]:
    """Show one global quest and its mobs."""
    rows = store.db.getrow(number, "gquests")
    if not rows or not isinstance(rows, list):
        return [f"No such global quest: {number}"]
    mobs = store.db.select("SELECT * FROM gqmobs WHERE gq_id = ?", (number,))
    div = _divider(fmt)
    msg = [GQ_HEADER, div, _gq_line(rows[0], len(mobs), fmt), div]
    msg.append("@G%-5s %-30s %-30s" % ("Num", "Name", "Location"))  # noqa: UP031  # %-formats keep the old column layout
    msg.append(div)
    msg.extend(
        "@G%-5s %-30s %-30s" % (mob["num"], mob["name"], mob["location"])  # noqa: UP031  # %-formats keep the old column layout
        for mob in mobs
    )
    msg.append(div)
    return msg


def gq_report(store: StatStore, count: int, number: int | None, fmt: Formatters) -> list[str]:
    """Show global quest statistics, the last ``count`` or the global quest ``number``."""
    if store.db.getlastrowid("stats") <= 0:
        return [NO_STATS]
    if store.db.getlastrowid("gquests") <= 0:
        return ["No gq stats available"]
    if number:
        return show_gq(store, number, fmt)

    div = _divider(fmt)
    won = store.db.select(
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
    current = store.db.select("SELECT gquestswon FROM stats WHERE milestone = 'current'")
    gquestswon = _n(current[0]["gquestswon"]) if current else 0
    lost = store.db.select(
        """SELECT AVG(finishtime - starttime) as avetime,
                 SUM(qpmobs) as totalqp,
                 AVG(qpmobs) as aveqp,
                 COUNT(*) as indb
                 FROM gquests where won != 1"""
    )[0]
    overall = store.db.select(
        """SELECT SUM(qpmobs + qp) as overallqp,
                 AVG(qpmobs + qp) as aveoverallqp
                 FROM gquests"""
    )[0]
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

    if count > 0:
        last = store.db.getlast("gquests", count)
        counts = store.db.selectbykeyword(
            "SELECT gq_id, SUM(num) as mobcount from gqmobs group by gq_id", "gq_id"
        )
        if last and isinstance(last, list):
            msg.append("")
            msg.append(GQ_HEADER)
            msg.append(div)
            msg.extend(
                _gq_line(item, counts.get(item["gq_id"], {}).get("mobcount", 0), fmt)
                for item in last
            )
    return msg


# mob kills


def mob_report(store: StatStore, count: int, fmt: Formatters) -> list[str]:
    """Show mob kill statistics and the last ``count`` kills."""
    if store.db.getlastrowid("stats") <= 0:
        return [NO_STATS]
    if store.db.getlastrowid("mobkills") <= 0:
        return ["No mob stats available"]

    div = _divider(fmt)
    current = store.db.select("SELECT monsterskilled FROM stats WHERE milestone = 'current'")
    stats: dict[str, Any] = dict(current[0]) if current else {"monsterskilled": 0}
    stats.update(
        store.db.select(
            """SELECT SUM(xp) AS xp,
                  SUM(rarexp) as rarexp,
                  SUM(bonusxp) AS bonusxp,
                  SUM(blessingxp) AS blessingxp,
                  SUM(totalxp) as totalxp,
                  AVG(xp) AS avexp,
                  AVG(totalxp) AS avetotalxp,
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
        store.db.select(
            """SELECT AVG(bonusxp) as avebonusxp,
                 COUNT(*) as bonusmobsindb
                 FROM mobkills where bonusxp > 0"""
        )[0]
    )
    stats.update(
        store.db.select(
            """SELECT AVG(blessingxp) as aveblessxp,
                 COUNT(*) as blessmobsindb
                 FROM mobkills where blessingxp > 0"""
        )[0]
    )
    stats.update(
        store.db.select(
            """SELECT AVG(rarexp) as averarexp,
                 COUNT(*) as raremobsindb
                 FROM mobkills where rarexp > 0"""
        )[0]
    )
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

    if count > 0:
        last = store.db.getlast("mobkills", count)
        if last and isinstance(last, list):
            msg.append("")
            msg.append(
                "@G%3s %-18s %-3s %-3s %-3s %-3s %2s %1s %s"  # noqa: UP031  # %-formats keep the old column layout
                % ("Lvl", "Mob", "TXP", "XP", "RXP", "OXP", "TP", "S", "Gold")
            )
            msg.append(div)
            msg.extend(_mob_line(item) for item in last)
    return msg


def _flags(item: dict[str, Any]) -> str:
    """Return the letters of every special kill the row has."""
    return "".join(letter for column, letter in SPECIAL_FLAGS if int(item[column]) == 1)


def mobkill_list(store: StatStore, count: int, fmt: Formatters) -> list[str]:
    """List the last ``count`` mob kills, newest first."""
    if count < 1:
        return ["The count must be at least 1"]
    rows = store.recent_mobkills(count)
    if not rows:
        return [NO_KILLS]
    msg = [
        f"@G{'Time':<16} {'Name':<18} {'Lvl':>3} {'TXP':>6} {'Gold':>8} {'Room':>8} Flags",
        _divider(fmt),
    ]
    for item in rows:
        when = int(item["time"])
        time_text = time.strftime("%Y-%m-%d %H:%M", time.gmtime(when)) if when != -1 else ""
        level = int(item["level"])
        level_text = str(convert_level(level)["level"]) if level >= 1 else ""
        room = int(item["room_id"])
        room_text = str(room) if room else ""
        gold = fmt.readable(item["gold"])
        msg.append(
            f"{time_text:<16} {item['name'][0:18]:<18} {level_text:>3} "
            f"{item['totalxp']:>6} {gold:>8} {room_text:>8} {_flags(item)}"
        )
    return msg


def _mob_line(item: dict[str, Any]) -> str:
    """Format a mob kill as a line of the mob list."""
    bonus = ""
    if int(item["bonusxp"]) != 0:
        bonus += "D"
    if int(item["blessingxp"]) != 0:
        bonus += "E"
    special = ""
    for column, letter in SPECIAL_FLAGS:
        if int(item[column]) == 1:
            special = letter
            break
    trivia = "1" if int(item["tp"]) == 1 else ""
    template = "%3s %-18s %-3s %-3s %-3s %-3s %2s %1s %s"
    if item["noexp"] == 1:
        template = "%3s %-18s @R%-3s %-3s %-3s %-3s@w %2s %1s %s"
    return template % (
        convert_level(item["level"])["level"],
        item["name"][0:18],
        item["totalxp"],
        item["xp"],
        item["rarexp"],
        bonus,
        trivia,
        special,
        item["gold"],
    )
