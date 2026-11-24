"""Pure helpers for the statmn plugin: the names, the SQL, and the messages and report text.

The helpers import nothing from bastproxy. The plugin hands in a ``Select`` that runs a query
against the statdb database, and ``Formatters`` for the bastproxy helpers the text needs.
"""

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, NamedTuple

PREFIX = "ev_plugins.aardwolf."
# the events statmn listens to; copied, because a plugin never imports another
EVENT_QUEST_COMP = f"{PREFIX}quest_comp"
EVENT_CP_COMP = f"{PREFIX}cp_comp"
EVENT_GQ_WON = f"{PREFIX}gq_won"
EVENT_GQ_COMPLETED = f"{PREFIX}gq_completed"
EVENT_GQ_DONE = f"{PREFIX}gq_done"
EVENT_LEVEL_GAIN = f"{PREFIX}level_gain"
EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"
# the core trigger that fires on an empty line
EMPTYLINE_ID = "t_plugins.core.triggers_emptyline"
# the statdb API that runs a select
SELECT_API = "plugins.aardwolf.statdb:stats.select"

NO_DB = "The stats database is not available"

LINE_LENGTH = 50
# the priority of the completion callbacks: after statdb saves the event at priority 50
CALLBACK_PRIORITY = 60

DEFAULT_STATCOLOR = "@W"
DEFAULT_INFOCOLOR = "@x33"
DEFAULT_SHOW = "5m"
DEFAULT_REPORTMINUTES = "60m"
DEFAULT_EXPPERMIN = 20

QUEST_WINDOW_SQL = (
    "SELECT COUNT(*) AS total, COALESCE(SUM(totqp), 0) AS qp, COALESCE(SUM(gold), 0) AS gold, "
    "COALESCE(SUM(tp), 0) AS tp FROM quests WHERE finishtime > ? AND failed = 0"
)
CP_WINDOW_SQL = (
    "SELECT COUNT(*) AS total, COALESCE(SUM(qp + bonusqp), 0) AS qp, "
    "COALESCE(SUM(gold), 0) AS gold, COALESCE(SUM(tp), 0) AS tp "
    "FROM campaigns WHERE finishtime > ? AND failed = 0"
)
GQ_WINDOW_SQL = (
    "SELECT COUNT(*) AS total, COALESCE(SUM(qp + qpmobs), 0) AS qp, "
    "COALESCE(SUM(gold), 0) AS gold, COALESCE(SUM(tp), 0) AS tp "
    "FROM gquests WHERE finishtime > ?"
)
MOB_WINDOW_SQL = (
    "SELECT COUNT(*) AS total, COALESCE(SUM(totalxp), 0) AS xp, COALESCE(SUM(gold), 0) AS gold, "
    "COALESCE(SUM(tp), 0) AS tp FROM mobkills WHERE time > ?"
)
QUEST_AVERAGE_SQL = (
    "SELECT COUNT(*) AS count, COALESCE(AVG(totqp), 0) AS average FROM quests WHERE failed = 0"
)
LEVEL_PREVIOUS_SQL = (
    "SELECT MAX(starttime) AS prev FROM levels WHERE starttime > 0 AND starttime < ?"
)
LEVEL_KILLS_SQL = (
    "SELECT COUNT(*) AS count, COALESCE(AVG(totalxp), 0) AS average FROM mobkills "
    "WHERE time > ? AND time < ? AND xp > 0"
)

# the order of the stats on a level message
LEVEL_STATS = ("str", "dex", "con", "luc", "int", "wis")

# the rows of the select, by column name
Rows = Sequence[Mapping[str, Any]]
# runs a select with bound parameters; None when the database is not available or the select failed
Select = Callable[[str, tuple[Any, ...]], Rows | None]


class Colors(NamedTuple):
    """The two colour codes of the text: ``info`` for labels, ``stat`` for the numbers."""

    info: str
    stat: str


@dataclass(frozen=True)
class Formatters:
    """The bastproxy helpers the text needs.

    Attributes:
        format_time: Turns seconds into text, ``plugins.core.utils:timelength.format``; the second
            argument leaves the seconds out.
        center: Centres text between filler characters, ``(text, filler, length, filler_color)``,
            ``plugins.core.utils:string.center.colored``.
    """

    format_time: Callable[[float, bool], str]
    center: Callable[[str, str, int, str], str]


class StatRow(NamedTuple):
    """The totals of one kind of event in a report."""

    label: str
    total: int
    xp: int
    qp: int
    tp: int
    gold: int


def _n(record: Mapping[str, Any], key: str) -> int:
    """Return a number of a record as an int; a missing or non-numeric value is 0."""
    value = record.get(key, 0)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0
    return int(value)


def _f(row: Mapping[str, Any], key: str) -> float:
    """Return a number of a database row as a float; a missing or NULL value is 0."""
    value = row.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0.0
    return float(value)


def color_time(text: str, colors: Colors) -> str:
    """Colour a formatted time: the numbers in the stat colour, the rest in the info colour."""
    body = re.sub(r"\d+", lambda match: f"{colors.stat}{match.group()}{colors.info}", text)
    return f"{colors.info}{body}"


def _took(record: Mapping[str, Any], colors: Colors, fmt: Formatters) -> str:
    """Return the coloured time an event took, from its start and finish times."""
    return color_time(
        fmt.format_time(_n(record, "finishtime") - _n(record, "starttime"), False), colors
    )


def _extras(record: Mapping[str, Any], colors: Colors) -> list[str]:
    """Return the tp, trains and pracs parts of a message, each only when it is above zero."""
    parts: list[str] = []
    for key, unit in (("tp", "TP"), ("trains", "tr"), ("pracs", "pr")):
        value = _n(record, key)
        if value > 0:
            parts.append(f" {colors.stat}{value}{colors.info}{unit}")
    return parts


def quest_message(
    record: Mapping[str, Any],
    colors: Colors,
    fmt: Formatters,
    average: tuple[int, float] | None = None,
) -> str:
    """Return the message for a finished quest.

    Args:
        record: The ``quest_comp`` event data.
        colors: The colours of the text.
        fmt: The bastproxy helpers.
        average: The number of quests and the average qp of them, or None when not known; shown
            when there is more than one quest.
    """
    info, stat = colors
    msg = [f"{info}StatMonitor: Quest finished for ", f"{stat}{_n(record, 'qp')}"]
    for key in ("lucky", "mccp", "tierqp", "opk", "hardcore"):
        if _n(record, key) > 0:
            msg.append(f"{info}+{stat}{_n(record, key)}")
    if _n(record, "daily") == 1:
        msg.append(f"{info}+{stat}E")
    if _n(record, "double") == 1:
        msg.append(f"{info}+{stat}D")
    msg.append(f" {info}= ")
    msg.append(f"{stat}{_n(record, 'totqp')}{info}qp")
    msg.extend(_extras(record, colors))
    msg.append(f". It took {_took(record, colors, fmt)}{info}.")
    if average is not None and average[0] > 1:
        count, mean = average
        msg.append(f" {info}Avg: {stat}{mean:.2f} {info}qp/quest over {stat}{count}{info} quests.")
    return "".join(msg)


def cp_message(record: Mapping[str, Any], colors: Colors, fmt: Formatters) -> str:
    """Return the message for a finished campaign."""
    info, stat = colors
    msg = [f"{info}StatMonitor: CP finished for "]
    qp = _n(record, "qp")
    bonus = _n(record, "bonusqp")
    if bonus > 0:
        msg.append(f"{stat}{qp}{info}+{stat}{bonus}B{info}={stat}{qp + bonus}qp")
    else:
        msg.append(f"{stat}{qp}{info}qp")
    msg.extend(_extras(record, colors))
    msg.append(f". {info}It took {_took(record, colors, fmt)}{info}.")
    return "".join(msg)


def gq_message(record: Mapping[str, Any], colors: Colors, fmt: Formatters) -> str:
    """Return the message for a finished global quest."""
    info, stat = colors
    msg = [f"{info}StatMonitor: GQ finished for ", f"{stat}{_n(record, 'qp')}{info}"]
    msg.append(f"+{stat}{_n(record, 'qpmobs')}{info}qp")
    msg.extend(_extras(record, colors))
    msg.append(".")
    msg.append(f" {info}It took {_took(record, colors, fmt)}{info}.")
    return "".join(msg)


def xp_per_min(perlevel: object, window: float, threshold: int) -> int | None:
    """Return the xp per minute over a window, or None when it is not known or too low.

    Args:
        perlevel: The xp a level takes, from GMCP; only a positive number counts.
        window: The length of the window in seconds.
        threshold: The xp per minute that must be exceeded to show it.
    """
    if isinstance(perlevel, bool) or not isinstance(perlevel, int | float) or perlevel <= 0:
        return None
    if window <= 0:
        return None
    rate = perlevel / (window / 60)
    return int(rate) if int(rate) > threshold else None


def level_message(
    record: Mapping[str, Any],
    colors: Colors,
    fmt: Formatters,
    window: float | None = None,
    kills: tuple[int, float] | None = None,
    perlevel: object = None,
    threshold: int = DEFAULT_EXPPERMIN,
) -> str:
    """Return the message for a level or a pup.

    Args:
        record: The ``level_gain`` event data.
        colors: The colours of the text.
        fmt: The bastproxy helpers.
        window: The seconds from the previous level's start to this one's, or None when unknown.
        kills: The number of mobs killed in the window and their average xp, or None.
        perlevel: The GMCP ``char.base.perlevel`` value.
        threshold: The xp per minute that must be exceeded to show it.
    """
    info, stat = colors
    is_level = record.get("type") == "level"
    msg = [f"{info}StatMonitor: Gained a {record.get('type')}:"]
    if is_level:
        msg.append(f" {stat}{_n(record, 'hp')}{info}hp")
        msg.append(f" {stat}{_n(record, 'mp')}{info}mn")
        msg.append(f" {stat}{_n(record, 'mv')}{info}mv")
    if "trains" in record:
        base = _n(record, "trains")
        trains = base
        msg.append(f" {stat}{base}")
        for key, suffix in (
            ("blessingtrains", "E"),
            ("bonustrains", "B"),
            ("battlelearntrains", "L"),
        ):
            value = _n(record, key)
            if value > 0:
                trains += value
                msg.append(f"{info}+{stat}{value}{suffix}")
        if trains != base:
            msg.append(f"{info}={stat}{trains}")
        msg.append(f" {info}trains ")
    if is_level:
        msg.append(f"{stat}{_n(record, 'pracs')} {info}pracs ")
    bonus = [name for name in LEVEL_STATS if _n(record, name) > 0]
    if bonus:
        msg.append(f"{stat}{bonus[0]}")
        msg.extend(f"{info}+{stat}{name}" for name in bonus[1:])
        msg.append(f" {info}bonus ")
    if window is not None and window > 0:
        msg.append(color_time(fmt.format_time(window, False), colors))
    if kills is not None and kills[0] > 0 and kills[1] > 0:
        count, mean = kills
        msg.append(f" {stat}{count} {info}mobs killed")
        msg.append(f" ({stat}{mean:.2f}{info}xp/mob")
        rate = xp_per_min(perlevel, window or 0, threshold)
        if rate is not None:
            msg.append(f" {stat}{rate:02d}{info}xp/min")
        msg.append(")")
    return "".join(msg)


def _first(rows: Rows | None) -> Mapping[str, Any] | None:
    """Return the first row of a select, or None."""
    return rows[0] if rows else None


def quest_average(select: Select) -> tuple[int, float] | None:
    """Return the number of quests that did not fail and their average qp; None without a result."""
    row = _first(select(QUEST_AVERAGE_SQL, ()))
    if row is None:
        return None
    return int(_f(row, "count")), _f(row, "average")


def level_window(select: Select, starttime: float) -> float | None:
    """Return the seconds from the previous level's start to ``starttime``, or None.

    The previous level is the ``levels`` row with the latest start before ``starttime``; there is
    none for the first level in the database.
    """
    if starttime <= 0:
        return None
    row = _first(select(LEVEL_PREVIOUS_SQL, (starttime,)))
    previous = _f(row, "prev") if row is not None else 0.0
    if previous <= 0:
        return None
    return starttime - previous


def level_kills(select: Select, start: float, finish: float) -> tuple[int, float] | None:
    """Return the number of mobs killed for xp between two times and their average xp."""
    row = _first(select(LEVEL_KILLS_SQL, (start, finish)))
    if row is None:
        return None
    return int(_f(row, "count")), _f(row, "average")


def window_stats(select: Select, start: float) -> list[StatRow] | None:
    """Return the totals of quests, campaigns, global quests and mob kills after ``start``.

    Failed quests and campaigns are not counted. A kind with nothing in the window is all zeros.
    Returns None when a select returns nothing, as when the database is not available.
    """
    rows: list[StatRow] = []
    for label, sql in (
        ("Quests", QUEST_WINDOW_SQL),
        ("CPs", CP_WINDOW_SQL),
        ("GQs", GQ_WINDOW_SQL),
        ("Mobs", MOB_WINDOW_SQL),
    ):
        row = _first(select(sql, (start,)))
        if row is None:
            return None
        rows.append(
            StatRow(
                label,
                int(_f(row, "total")),
                int(_f(row, "xp")),
                int(_f(row, "qp")),
                int(_f(row, "tp")),
                int(_f(row, "gold")),
            )
        )
    return rows


_ROW_FORMAT = "{stat}{label:<10} {info}| {stat}{total:>6} {xp:>6} {qp:>5} {tp:>5} {gold:>10}"


def report_lines(
    rows: Sequence[StatRow], window: float, colors: Colors, fmt: Formatters
) -> list[str]:
    """Return the lines of the report: a header, a row for each kind and the totals.

    Args:
        rows: The rows of ``window_stats``.
        window: The length of the report window in seconds.
        colors: The colours of the text.
        fmt: The bastproxy helpers.
    """
    info = colors.info
    timestr = color_time(fmt.format_time(window, True), colors)
    divider = info + "-" * LINE_LENGTH
    lines = [
        "",
        info + fmt.center(f"{info}Stats for {timestr}{info}", "-", LINE_LENGTH, info),
        f"{info}{'Type':<10} | {'Total':>6} {'XP':>6} {'QP':>5} {'TP':>5} {'Gold':>10}",
        divider,
    ]
    lines.extend(_format_row(row, colors) for row in rows)
    lines.append(divider)
    total = StatRow(
        "Total",
        0,
        sum(row.xp for row in rows),
        sum(row.qp for row in rows),
        sum(row.tp for row in rows),
        sum(row.gold for row in rows),
    )
    lines.append(_format_row(total, colors, blank_total=True))
    lines.append("")
    return lines


def _format_row(row: StatRow, colors: Colors, blank_total: bool = False) -> str:
    """Format a report row; the totals row shows no count."""
    return _ROW_FORMAT.format(
        stat=colors.stat,
        info=colors.info,
        label=row.label,
        total="" if blank_total else row.total,
        xp=row.xp,
        qp=row.qp,
        tp=row.tp,
        gold=row.gold,
    )
