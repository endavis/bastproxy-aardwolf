"""Read the statdb tables for the web pages.

Everything here runs in a worker thread on its own read-only connection, and nothing imports
bastproxy: the plugin passes in the table query the web plugin validated and gets plain data
back. A request value is only ever a bound parameter. A column name from the request only picks
one of the fixed SQL fragments of ``TABLE_PAGES``; an unknown name raises ``ValueError`` before
any SQL is built.
"""

import sqlite3
from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlencode

from aardwolf._libs.aardu import LEVELS_PER_REMORT, LEVELS_PER_TIER, MAX_TIER, convert_level

from ._report import (
    FIELDSTOCOMP,
    SPECIAL_FLAGS,
    Formatters,
    MilestoneList,
    cp_stats,
    cp_summary,
    gq_stats,
    gq_summary,
    level_stats,
    level_summary,
    milestone_text,
    mob_stats,
    mob_summary,
    quest_stats,
    quest_summary,
    read_milestones,
    report_guard,
)

UNKNOWN_AREA = "Unknown"
MOBKILL_DATE_FORMAT = "%Y-%m-%d %H:%M"
# the defaults of the chart settings, and the names of those settings
CHART_DAYS = 30
CHART_LEVELS = 50
CHART_AREAS = 20
SETTING_CHART_DAYS = "chartdays"
SETTING_CHART_LEVELS = "chartlevels"
SETTING_CHART_AREAS = "chartareas"
AREA_CHART_TITLE = "Kills per area"


class TableParams(Protocol):
    """The table query the web plugin validated (``TableQuery`` in bastproxy)."""

    @property
    def sort(self) -> str | None:
        """The column to sort by, or None."""
        ...

    @property
    def descending(self) -> bool:
        """True to sort high to low."""
        ...

    @property
    def filters(self) -> Mapping[str, str | int | float]:
        """The filter value of each filtered column."""
        ...

    @property
    def count(self) -> int:
        """The number of rows on a page."""
        ...

    @property
    def offset(self) -> int:
        """The number of rows before the page."""
        ...


class WebRequest(Protocol):
    """The part of the web plugin's ``Request`` the handlers read."""

    @property
    def query(self) -> Mapping[str, str]:
        """The first value of each query key."""
        ...

    @property
    def table(self) -> TableParams | None:
        """The validated table query of a table route."""
        ...


@dataclass(frozen=True)
class WebColumn:
    """One column of a table page.

    ``expr`` is the one SQL expression the column is displayed, filtered and sorted by.
    """

    name: str
    label: str
    type: str
    expr: str
    link: str = ""


@dataclass(frozen=True)
class TablePage:
    """A table page: its fixed SQL and the command whose rows it shows.

    Attributes:
        route: The subpath of the page.
        title: The page title.
        source: The FROM clause.
        key: The key column, which orders the rows (newest first unless ``newest_first`` is
            False) and breaks ties.
        columns: The columns, in display order.
        summary: The report whose summary the page shows above the table, or "".
        guard: The table whose emptiness the text report reports, or "".
        newest_first: Order the rows by the key from high to low.
    """

    route: str
    title: str
    source: str
    key: str
    columns: tuple[WebColumn, ...]
    summary: str = ""
    guard: str = ""
    newest_first: bool = True

    def route_columns(self) -> list[dict[str, str]]:
        """Return the column declarations ``web.route.add`` takes."""
        return [{"name": c.name, "label": c.label, "type": c.type} for c in self.columns]


# fixed SQL fragments


def _level_of(column: str) -> str:
    """Return the SQL for the level of a total level, as ``convert_level`` gives it."""
    return f"CASE WHEN {column} < 1 THEN -1 ELSE ({column} - 1) % {LEVELS_PER_REMORT} + 1 END"


def _level_text(column: str) -> str:
    """Return the SQL for ``T<tier> R<remort> L<level>`` of a total level."""
    n = f"({column} - 1)"
    return (
        f"CASE WHEN {column} < 1 THEN 'T-1 R-1 L-1' ELSE "
        f"'T' || MIN({n} / {LEVELS_PER_TIER}, {MAX_TIER}) "
        f"|| ' R' || ({n} % {LEVELS_PER_TIER} / {LEVELS_PER_REMORT} + 1) "
        f"|| ' L' || ({n} % {LEVELS_PER_REMORT} + 1) END"
    )


def _letters(pairs: Sequence[tuple[str, str]]) -> str:
    """Return the SQL that joins the letter of every column that is 1."""
    return " || ".join(
        f"(CASE WHEN {column} = 1 THEN '{letter}' ELSE '' END)" for column, letter in pairs
    )


def _first_letter(pairs: Sequence[tuple[str, str]]) -> str:
    """Return the SQL for the letter of the first column that is 1."""
    whens = " ".join(f"WHEN {column} = 1 THEN '{letter}'" for column, letter in pairs)
    return f"CASE {whens} ELSE '' END"


def _mins(start: str, finish: str) -> str:
    """Return the SQL for the minutes between two times, NULL when either is unknown."""
    return (
        f"CASE WHEN {finish} != -1 AND {start} != -1 THEN ROUND(({finish} - {start}) / 60.0, 2) END"
    )


def _utc(column: str) -> str:
    """Return the SQL for a time as UTC text."""
    return f"strftime('{MOBKILL_DATE_FORMAT}', {column}, 'unixepoch')"


def _col(name: str, label: str, kind: str, expr: str = "", link: str = "") -> WebColumn:
    """Return a column; a plain column is its own SQL expression.

    ``link`` names the target the column's cells link to, a key of ``LINK_QUERY_KEYS``.
    """
    return WebColumn(name, label, kind, expr or name, link)


_RESULT = "CASE WHEN failed = 1 THEN 'Failed' ELSE 'Done' END"
_LEVEL_MINS = (
    "CASE WHEN starttime > 0 AND nextstart > 0 THEN ROUND((nextstart - starttime) / 60.0, 2) END"
)

TABLE_PAGES: dict[str, TablePage] = {
    page.route: page
    for page in (
        TablePage(
            "milestones",
            "Milestones",
            "stats",
            "stat_id",
            (
                _col("milestone", "Milestone", "text"),
                _col(
                    "date",
                    "Date (UTC)",
                    "text",
                    f"CASE WHEN time = 0 THEN 'Now' ELSE {_utc('time')} END",
                ),
                *(_col(field, field, "int") for field in FIELDSTOCOMP),
            ),
            summary="milestones",
            newest_first=False,
        ),
        TablePage(
            "quests",
            "Quests",
            "quests",
            "quest_id",
            (
                _col("id", "ID", "int", "quest_id", "quests"),
                _col("qp", "QP", "int"),
                _col("mc", "MC", "int", "mccp"),
                _col("tr", "TR", "int", "tierqp"),
                _col("lk", "LK", "int", "lucky"),
                _col("pk", "PK", "int", "opk"),
                _col("hc", "HC", "int", "hardcore"),
                _col(
                    "dbl",
                    "DBL",
                    "text",
                    _letters((("double", "D"), ("daily", "E"))),
                ),
                _col("tl", "TL", "int", "totqp"),
                _col("tp", "TP", "int"),
                _col("tn", "TN", "int", "trains"),
                _col("pr", "PR", "int", "pracs"),
                _col("gold", "Gold", "int"),
                _col("lvl", "Lvl", "int", _level_of("level")),
                _col("mins", "Mins", "float", "ROUND((finishtime - starttime) / 60.0, 2)"),
                _col("result", "Result", "text", _RESULT),
                _col("mob", "Mob", "text", "mobname"),
                _col("room", "Room", "text", "mobroom"),
                _col("area", "Area", "text", "mobarea"),
            ),
            summary="quests",
            guard="quests",
        ),
        TablePage(
            "levels",
            "Levels and pups",
            "(SELECT *, LEAD(starttime) OVER (ORDER BY level_id) AS nextstart FROM levels)",
            "level_id",
            (
                _col("id", "ID", "int", "level_id", "levels"),
                _col("lvl", "Lvl", "int", _level_of("level")),
                _col("type", "T", "text", "CASE WHEN type = 'level' THEN 'L' ELSE 'P' END"),
                _col("tr", "TR", "int", "trains"),
                _col("bt", "BT", "int", "MAX(bonustrains, 0) + MAX(blessingtrains, 0)"),
                _col("pr", "PR", "int", "pracs"),
                _col("hp", "HP", "int"),
                _col("mn", "MN", "int", "mp"),
                _col("mv", "MV", "int"),
                _col("s", "S", "int", "str"),
                _col("i", "I", "int", "int"),
                _col("w", "W", "int", "wis"),
                _col("c", "C", "int", "con"),
                _col("d", "D", "int", "dex"),
                _col("l", "L", "int", "luc"),
                _col("mins", "Mins", "float", _LEVEL_MINS),
            ),
            summary="levels",
            guard="levels",
        ),
        TablePage(
            "cps",
            "Campaigns",
            "campaigns",
            "cp_id",
            (
                _col("id", "ID", "int", "cp_id", "cpmobs"),
                _col("lvl", "Lvl", "text", _level_text("level")),
                _col("qp", "QP", "int"),
                _col("bn", "BN", "int", "bonusqp"),
                _col("tp", "TP", "int"),
                _col("tn", "TN", "int", "trains"),
                _col("pr", "PR", "int", "pracs"),
                _col("gold", "Gold", "int"),
                _col(
                    "mobs",
                    "Mobs",
                    "int",
                    "(SELECT COUNT(*) FROM cpmobs WHERE cpmobs.cp_id = campaigns.cp_id)",
                ),
                _col("mins", "Mins", "float", _mins("starttime", "finishtime")),
                _col("result", "Result", "text", _RESULT),
            ),
            summary="cps",
            guard="campaigns",
        ),
        TablePage(
            "cpmobs",
            "Campaign mobs",
            "cpmobs",
            "cpmob_id",
            (
                _col("cp_id", "CP", "int"),
                _col("name", "Name", "text"),
                _col("location", "Location", "text"),
            ),
        ),
        TablePage(
            "gqs",
            "Global quests",
            "gquests",
            "gq_id",
            (
                _col("id", "ID", "int", "gq_id", "gqmobs"),
                _col("lvl", "Lvl", "text", _level_text("level")),
                _col("qp", "QP", "int"),
                _col("qm", "QM", "int", "qpmobs"),
                _col("tp", "TP", "int"),
                _col("tn", "TN", "int", "trains"),
                _col("pr", "PR", "int", "pracs"),
                _col("gold", "Gold", "int"),
                _col(
                    "mobs",
                    "Mobs",
                    "int",
                    "COALESCE((SELECT SUM(num) FROM gqmobs WHERE gqmobs.gq_id = gquests.gq_id), 0)",
                ),
                _col("mins", "Mins", "float", _mins("starttime", "finishtime")),
                _col("won", "Won", "int"),
            ),
            summary="gqs",
            guard="gquests",
        ),
        TablePage(
            "gqmobs",
            "Global quest mobs",
            "gqmobs",
            "gqmob_id",
            (
                _col("gq_id", "GQ", "int"),
                _col("num", "Num", "int"),
                _col("name", "Name", "text"),
                _col("location", "Location", "text"),
            ),
        ),
        TablePage(
            "mobs",
            "Mob kills",
            "mobkills",
            "mk_id",
            (
                _col("lvl", "Lvl", "int", _level_of("level")),
                _col("mob", "Mob", "text", "name"),
                _col("txp", "TXP", "int", "totalxp"),
                _col("xp", "XP", "int"),
                _col("rxp", "RXP", "int", "rarexp"),
                _col(
                    "oxp",
                    "OXP",
                    "text",
                    "(CASE WHEN noexp = 0 AND bonusxp != 0 THEN 'D' ELSE '' END) "
                    "|| (CASE WHEN noexp = 0 AND blessingxp != 0 THEN 'E' ELSE '' END)",
                ),
                _col("tp", "TP", "int", "CASE WHEN tp = 1 THEN 1 ELSE 0 END"),
                _col("s", "S", "text", _first_letter(SPECIAL_FLAGS)),
                _col("gold", "Gold", "int"),
            ),
            summary="mobs",
            guard="mobkills",
        ),
        TablePage(
            "mobkills",
            "Mob kills, newest first",
            "mobkills",
            "mk_id",
            (
                _col("time", "Time (UTC)", "text", f"CASE WHEN time != -1 THEN {_utc('time')} END"),
                _col("name", "Name", "text"),
                _col(
                    "lvl", "Lvl", "int", "CASE WHEN level >= 1 THEN " + _level_of("level") + " END"
                ),
                _col("txp", "TXP", "int", "totalxp"),
                _col("gold", "Gold", "int"),
                _col(
                    "room", "Room", "int", "CASE WHEN room_id != 0 THEN room_id END", "mapper-room"
                ),
                _col("flags", "Flags", "text", _letters(SPECIAL_FLAGS)),
            ),
        ),
    )
}

# the numbers of each summary, read in the thread, and its text, built on the event loop
STATS_READERS: dict[str, Callable[[Any], Any]] = {
    "quests": quest_stats,
    "levels": level_stats,
    "cps": cp_stats,
    "gqs": gq_stats,
    "mobs": mob_stats,
}
SUMMARIES: dict[str, Callable[[Any, Formatters], list[str]]] = {
    "quests": quest_summary,
    "levels": level_summary,
    "cps": cp_summary,
    "gqs": gq_summary,
    "mobs": mob_summary,
}


# the SQL of a table page


@dataclass(frozen=True)
class Queries:
    """The two statements of a table page and their bound values."""

    count_sql: str
    count_args: tuple[Any, ...]
    rows_sql: str
    rows_args: tuple[Any, ...]


def escape_like(value: str) -> str:
    """Escape the LIKE wildcards of a value, for ``LIKE ? ESCAPE '\\'``."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _select(select: str, page: TablePage, clause: str, tail: str = "") -> str:
    """Return a select statement. Every part is a fixed fragment of ``TABLE_PAGES``."""
    return "SELECT {} FROM {}{}{}".format(select, page.source, clause, tail)  # noqa: UP032  # nosec B608  # fixed fragments


def build_queries(page: TablePage, table: TableParams) -> Queries:
    """Build the count and page statements for a table query.

    Raises:
        ValueError: The sort or a filter names a column the page does not have.
    """
    by_name = {column.name: column for column in page.columns}
    where: list[str] = []
    args: list[Any] = []
    for name, value in table.filters.items():
        column = by_name.get(name)
        if column is None:
            msg = f"unknown column {name!r}"
            raise ValueError(msg)
        if column.type == "text":
            where.append(f"{column.expr} LIKE ? ESCAPE '\\'")
            args.append(f"%{escape_like(str(value))}%")
        else:
            where.append(f"{column.expr} = ?")
            args.append(value)
    clause = (" WHERE " + " AND ".join(where)) if where else ""

    key_direction = "DESC" if page.newest_first else "ASC"
    if table.sort is None:
        order = f"{page.key} {key_direction}"
    else:
        sort_column = by_name.get(table.sort)
        if sort_column is None:
            msg = f"unknown column {table.sort!r}"
            raise ValueError(msg)
        direction = "DESC" if table.descending else "ASC"
        order = f"{sort_column.expr} {direction}, {page.key} {key_direction}"
    select = ", ".join(column.expr for column in page.columns)
    return Queries(
        _select("COUNT(*)", page, clause),
        tuple(args),
        _select(select, page, clause, f" ORDER BY {order} LIMIT ? OFFSET ?"),
        (*args, table.count, table.offset),
    )


# the read-only connection

_LAST_ROW_SQL = {
    "stats": "SELECT MAX(stat_id) FROM stats",
    "quests": "SELECT MAX(quest_id) FROM quests",
    "levels": "SELECT MAX(level_id) FROM levels",
    "campaigns": "SELECT MAX(cp_id) FROM campaigns",
    "gquests": "SELECT MAX(gq_id) FROM gquests",
    "mobkills": "SELECT MAX(mk_id) FROM mobkills",
}


class ReadOnlyDb:
    """A read-only connection with the two methods the report queries use."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Keep the connection."""
        self._connection = connection

    def rows(self, sql: str, params: Sequence[Any] = ()) -> list[tuple[Any, ...]]:
        """Run a select and return its rows as tuples."""
        return [tuple(row) for row in self._connection.execute(sql, params).fetchall()]

    def select(
        self, sql: str, params: Sequence[Any] | Mapping[str, Any] = ()
    ) -> list[dict[str, Any]]:
        """Run a select and return its rows as dicts."""
        cursor = self._connection.execute(sql, params)
        names = [item[0] for item in cursor.description]
        return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]

    def getlastrowid(self, table: str) -> int:
        """Return the highest key of a table, or -1 when it is empty."""
        sql = _LAST_ROW_SQL.get(table)
        if sql is None:
            msg = f"no key known for table {table!r}"
            raise ValueError(msg)
        value = self.rows(sql)[0][0]
        return -1 if value is None else int(value)

    def close(self) -> None:
        """Close the connection."""
        self._connection.close()


def open_readonly(path: Path) -> ReadOnlyDb:
    """Open the database file read-only. Any write on the connection fails.

    Raises:
        sqlite3.Error: The file cannot be opened.
    """
    return ReadOnlyDb(sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True))


# thread entry points


@dataclass
class TableResult:
    """What a table page needs from the database."""

    message: str = ""
    rows: list[list[Any]] | None = None
    total: int = 0
    stats: Any = None
    milestones: MilestoneList | None = None


def read_table(path: Path, page: TablePage, table: TableParams) -> TableResult:
    """Read one page of a table, its total and its summary numbers.

    Raises:
        ValueError: The query names a column the page does not have.
        sqlite3.Error: The database cannot be read.
    """
    queries = build_queries(page, table)
    with closing(open_readonly(path)) as db:
        if page.guard:
            message = report_guard(db, page.guard)
            if message:
                return TableResult(message=message)
        total = int(db.rows(queries.count_sql, queries.count_args)[0][0])
        rows = [list(row) for row in db.rows(queries.rows_sql, queries.rows_args)]
        result = TableResult(rows=rows, total=total)
        if page.summary == "milestones":
            result.milestones = read_milestones(db)
        elif page.summary:
            result.stats = STATS_READERS[page.summary](db)
    return result


def page_lines(page: TablePage, result: TableResult, fmt: Formatters) -> list[str]:
    """Return the lines above a table: the summary of its text report."""
    if page.summary == "milestones":
        if result.milestones is None:
            return []
        return milestone_text(result.milestones, fmt)
    if page.summary:
        return SUMMARIES[page.summary](result.stats, fmt)
    return []


MAPPER_ROOM_PATH = "/client/mapper/room"
LINK_QUERY_KEYS: dict[str, str] = {
    "quests": "f_id",
    "levels": "f_id",
    "cpmobs": "f_cp_id",
    "gqmobs": "f_gq_id",
    "mapper-room": "uid",
}


def link_cell(text: str, path: str, key: str, value: object) -> dict[str, str]:
    """Return a link cell: the text and a same-origin path with one query value."""
    return {"text": text, "href": f"{path}?{urlencode({key: str(value)})}"}


def link_rows(
    page: TablePage, rows: Sequence[Sequence[Any]], paths: Mapping[str, str]
) -> list[list[Any]]:
    """Return the rows with the cells of the page's linked columns as link cells.

    ``paths`` maps a link target to its page path. A cell stays a plain value when its target
    has no path or the value is None.
    """
    linked = [
        (index, column.link, paths[column.link])
        for index, column in enumerate(page.columns)
        if column.link in paths and column.link in LINK_QUERY_KEYS
    ]
    result: list[list[Any]] = []
    for row in rows:
        cells = list(row)
        for index, target, path in linked:
            if cells[index] is not None:
                cells[index] = link_cell(
                    str(cells[index]), path, LINK_QUERY_KEYS[target], cells[index]
                )
        result.append(cells)
    return result


def read_milestone_rows(path: Path, names: Sequence[str]) -> list[dict[str, Any] | None]:
    """Read the stats row of each milestone name, None for a name that does not exist.

    Raises:
        sqlite3.Error: The database cannot be read.
    """
    with closing(open_readonly(path)) as db:
        found = [db.select("SELECT * FROM stats WHERE milestone = ?", (name,)) for name in names]
    return [rows[0] if rows else None for rows in found]


@dataclass(frozen=True)
class ChartSpec:
    """A chart: its title, unit and the fixed SQL that gives ``(label, value)``, newest first.

    Attributes:
        title: The name of the chart, as its page is listed.
        unit: What a bar counts.
        sql: The fixed select; its one parameter is the number of bars.
        setting: The name of the setting that holds the number of bars.
        default_limit: The default of that setting.
        detail: What the number of bars means, with a ``{limit}`` placeholder.
        label: Turns the label column into the text under a bar.
    """

    title: str
    unit: str
    sql: str
    setting: str
    default_limit: int
    detail: str
    label: Callable[[object], str] = str

    def heading(self, limit: int) -> str:
        """Return the title of the chart drawn with ``limit`` bars."""
        return f"{self.title} ({self.detail.format(limit=limit)})"


def _level_label(value: object) -> str:
    """Return the level of a total level, as the level text shows it."""
    total = int(value) if isinstance(value, int | float) else 0
    return str(convert_level(total)["level"])


CHARTS: dict[str, ChartSpec] = {
    "qp-per-day": ChartSpec(
        "Quest points per day",
        "QP",
        """SELECT day, SUM(amount) FROM (
               SELECT date(finishtime, 'unixepoch') AS day, totqp AS amount
                 FROM quests WHERE failed = 0 AND finishtime > 0
               UNION ALL
               SELECT date(finishtime, 'unixepoch'), qp
                 FROM campaigns WHERE failed = 0 AND finishtime > 0
               UNION ALL
               SELECT date(finishtime, 'unixepoch'), qp + qpmobs
                 FROM gquests WHERE finishtime > 0
             ) GROUP BY day ORDER BY day DESC LIMIT ?""",
        SETTING_CHART_DAYS,
        CHART_DAYS,
        "newest {limit} days",
    ),
    "gold-per-day": ChartSpec(
        "Gold per day",
        "gold",
        """SELECT day, SUM(amount) FROM (
               SELECT date(finishtime, 'unixepoch') AS day, gold AS amount
                 FROM quests WHERE finishtime > 0
               UNION ALL
               SELECT date(finishtime, 'unixepoch'), gold
                 FROM campaigns WHERE finishtime > 0
               UNION ALL
               SELECT date(finishtime, 'unixepoch'), gold
                 FROM gquests WHERE finishtime > 0
               UNION ALL
               SELECT date(time, 'unixepoch'), gold
                 FROM mobkills WHERE time > 0
             ) GROUP BY day ORDER BY day DESC LIMIT ?""",
        SETTING_CHART_DAYS,
        CHART_DAYS,
        "newest {limit} days",
    ),
    "level-time": ChartSpec(
        "Minutes per level",
        "minutes",
        """SELECT level, mins FROM (
               SELECT level_id, level,
                      CASE WHEN starttime > 0 AND nextstart > 0
                           THEN ROUND((nextstart - starttime) / 60.0, 2) END AS mins
                 FROM (SELECT *, LEAD(starttime) OVER (ORDER BY level_id) AS nextstart
                         FROM levels)
                WHERE type = 'level'
             ) WHERE mins IS NOT NULL ORDER BY level_id DESC LIMIT ?""",
        SETTING_CHART_LEVELS,
        CHART_LEVELS,
        "last {limit} levels",
        _level_label,
    ),
}

ROOM_KILLS_SQL = "SELECT room_id, COUNT(*) FROM mobkills GROUP BY room_id"


def read_chart(path: Path, name: str, limit: int | None = None) -> list[tuple[str, float]]:
    """Read the bars of a chart, oldest first, at most ``limit`` of them.

    ``limit`` defaults to the chart's default number of bars.

    Raises:
        ValueError: The chart name is unknown.
        sqlite3.Error: The database cannot be read.
    """
    spec = CHARTS.get(name)
    if spec is None:
        msg = f"unknown chart {name!r}"
        raise ValueError(msg)
    with closing(open_readonly(path)) as db:
        rows = db.rows(spec.sql, (spec.default_limit if limit is None else limit,))
    return [(spec.label(label), float(value or 0)) for label, value in reversed(rows)]


def read_room_kills(path: Path) -> dict[int, int]:
    """Read the number of kills in each room.

    Raises:
        sqlite3.Error: The database cannot be read.
    """
    with closing(open_readonly(path)) as db:
        return {int(room): int(count) for room, count in db.rows(ROOM_KILLS_SQL)}


def aggregate_areas(
    room_counts: Mapping[int, int], room_areas: Mapping[int, str], limit: int = CHART_AREAS
) -> list[tuple[str, float]]:
    """Add the kills of each area, most first. A room without an area is "Unknown"."""
    totals: dict[str, int] = {}
    for room, count in room_counts.items():
        name = room_areas.get(room) or UNKNOWN_AREA
        totals[name] = totals.get(name, 0) + count
    ordered = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    return [(name, float(count)) for name, count in ordered[:limit]]
