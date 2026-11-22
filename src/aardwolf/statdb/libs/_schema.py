"""The statdb schema: tables, version 17 and the upgrade steps from older files.

The CREATE statements are the old proxy's version 17 text, in the same column order, because
a database written by the old plugin is opened as is and the store inserts by position. The
steps for versions 13 to 17 are ports of the old rebuilds. A file older than version 12 cannot
be upgraded; the old plugin could not either.
"""

import sqlite3
from collections.abc import Callable
from typing import Any

from aardwolf.libs.aardu import CLASSABBREV

from ._db import StatsDb

DB_NAME = "stats"
DB_VERSION = 17

STATS_SQL = """CREATE TABLE stats(
            stat_id INTEGER NOT NULL PRIMARY KEY autoincrement,
            name TEXT NOT NULL,
            level INT default 1,
            totallevels INT default 1,
            remorts INT default 1,
            tiers INT default 0,
            race TEXT default "",
            sex TEXT default "",
            subclass TEXT default "",
            qpearned INT default 0,
            questscomplete INT default 0 ,
            questsfailed INT default 0,
            campaignsdone INT default 0,
            campaignsfld INT default 0,
            gquestswon INT default 0,
            duelswon INT default 0,
            duelslost INT default 0,
            timeskilled INT default 0,
            monsterskilled INT default 0,
            combatmazewins INT default 0,
            combatmazedeaths INT default 0,
            powerupsall INT default 0,
            totaltrivia INT default 0,
            time INT default 0,
            milestone TEXT,
            redos INT default 0
          );"""

QUESTS_SQL = """CREATE TABLE quests(
            quest_id INTEGER NOT NULL PRIMARY KEY autoincrement,
            starttime INT default 0,
            finishtime INT default 0,
            mobname TEXT default "Unknown",
            mobarea TEXT default "Unknown",
            mobroom TEXT default "Unknown",
            qp INT default 0,
            double INT default 0,
            daily INT default 0,
            totqp INT default 0,
            gold INT default 0,
            tierqp INT default 0,
            mccp INT default 0,
            lucky INT default 0,
            opk INT default 0,
            hardcore INT default 0,
            tp INT default 0,
            trains INT default 0,
            pracs INT default 0,
            level INT default -1,
            failed INT default 0
          );"""

CLASSES_SQL = """CREATE TABLE classes(
              class TEXT NOT NULL PRIMARY KEY,
              remort INTEGER
            );"""

LEVELS_SQL = """CREATE TABLE levels(
            level_id INTEGER NOT NULL PRIMARY KEY autoincrement,
            type TEXT default "level",
            level INT default -1,
            str INT default 0,
            int INT default 0,
            wis INT default 0,
            dex INT default 0,
            con INT default 0,
            luc INT default 0,
            starttime INT default -1,
            finishtime INT default -1,
            hp INT default 0,
            mp INT default 0,
            mv INT default 0,
            pracs INT default 0,
            trains INT default 0,
            bonustrains INT default 0,
            blessingtrains INT default 0,
            battlelearntrains INT default 0
          )"""

CAMPAIGNS_SQL = """CREATE TABLE campaigns(
            cp_id INTEGER NOT NULL PRIMARY KEY autoincrement,
            starttime INT default 0,
            finishtime INT default 0,
            qp INT default 0,
            bonusqp INT default 0,
            gold INT default 0,
            tp INT default 0,
            trains INT default 0,
            pracs INT default 0,
            level INT default -1,
            failed INT default 0
          );"""

CPMOBS_SQL = """CREATE TABLE cpmobs(
            cpmob_id INTEGER NOT NULL PRIMARY KEY autoincrement,
            cp_id INT NOT NULL,
            name TEXT default "Unknown",
            location TEXT default "Unknown"
          )"""

MOBKILLS_SQL = """CREATE TABLE mobkills(
            mk_id INTEGER NOT NULL PRIMARY KEY autoincrement,
            name TEXT default "Unknown",
            xp INT default 0,
            rarexp INT default 0,
            bonusxp INT default 0,
            blessingxp INT default 0,
            totalxp INT default 0,
            noexp INT default 0,
            gold INT default 0,
            tp INT default 0,
            time INT default -1,
            vorpal INT default 0,
            banishment INT default 0,
            assassinate INT default 0,
            slit INT default 0,
            disintegrate INT default 0,
            deathblow INT default 0,
            wielded_weapon TEXT default '',
            second_weapon TEXT default '',
            room_id INT default 0,
            level INT default -1
          )"""

GQUESTS_SQL = """CREATE TABLE gquests(
            gq_id INTEGER NOT NULL PRIMARY KEY autoincrement,
            starttime INT default 0,
            finishtime INT default 0,
            qp INT default 0,
            qpmobs INT default 0,
            gold INT default 0,
            tp INT default 0,
            trains INT default 0,
            pracs INT default 0,
            level INT default -1,
            extended INT default 0,
            won INT default 0,
            completed INT default 0
          )"""

GQMOBS_SQL = """CREATE TABLE gqmobs(
            gqmob_id INTEGER NOT NULL PRIMARY KEY autoincrement,
            gq_id INT NOT NULL,
            num INT,
            name TEXT default "Unknown",
            location TEXT default "Unknown"
          )"""


def init_classes(db: StatsDb) -> None:
    """Fill a new ``classes`` table with each full class name and remort -1."""
    db.modifymany(
        "INSERT INTO classes VALUES (:class, -1)",
        [{"class": name} for name in CLASSABBREV],
    )


TABLES: list[dict[str, Any]] = [
    {"name": "stats", "sql": STATS_SQL, "keyfield": "stat_id"},
    {"name": "quests", "sql": QUESTS_SQL, "keyfield": "quest_id"},
    {"name": "classes", "sql": CLASSES_SQL, "keyfield": "class", "postcreate": init_classes},
    {"name": "levels", "sql": LEVELS_SQL, "keyfield": "level_id"},
    {"name": "campaigns", "sql": CAMPAIGNS_SQL, "keyfield": "cp_id"},
    {"name": "cpmobs", "sql": CPMOBS_SQL, "keyfield": "cpmob_id"},
    {"name": "mobkills", "sql": MOBKILLS_SQL, "keyfield": "mk_id"},
    {"name": "gquests", "sql": GQUESTS_SQL, "keyfield": "gq_id"},
    {"name": "gqmobs", "sql": GQMOBS_SQL, "keyfield": "gqmob_id"},
]


def target_columns(table: str, create_sql: str) -> list[str]:
    """Return the column names a CREATE statement gives a table, in order."""
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(create_sql)
        rows = connection.execute("SELECT name FROM pragma_table_info(?)", (table,)).fetchall()
    finally:
        connection.close()
    return [str(row[0]) for row in rows]


def rebuild_table(
    db: StatsDb, table: str, create_sql: str, expressions: dict[str, str] | None = None
) -> bool:
    """Rebuild a table into the layout of ``create_sql``, keeping its rows and ids.

    Does nothing, and returns False, when the table is not in the file or already has the
    target columns in order. A target column the file lacks takes ``expressions[column]``, an
    SQL expression over the old columns, or else its SQL default. The rebuild runs as one
    script, so a failure keeps the old table.
    """
    if not db.checktableexists(table):
        return False
    target = target_columns(table, create_sql)
    existing = [
        str(row["name"]) for row in db.select("SELECT name FROM pragma_table_info(?)", (table,))
    ]
    if existing == target:
        return False
    new_sql = create_sql.strip().rstrip(";")
    header = f"CREATE TABLE {table}("
    if not new_sql.startswith(header):
        msg = f"the create statement for {table} must start with {header!r}"
        raise ValueError(msg)
    new_sql = f"CREATE TABLE {table}_new(" + new_sql[len(header) :]
    columns: list[str] = []
    values: list[str] = []
    for column in target:
        if column in existing:
            columns.append(f'"{column}"')
            values.append(f'"{column}"')
        elif expressions and column in expressions:
            columns.append(f'"{column}"')
            values.append(expressions[column])
    script = ";\n".join(
        [
            f"DROP TABLE IF EXISTS {table}_new",
            new_sql,
            # Table and column names come from the declared schema, never from input.
            "INSERT INTO {0}_new ({1}) SELECT {2} FROM {0}".format(  # nosec B608  # schema
                table, ", ".join(columns), ", ".join(values)
            ),
            f"DROP TABLE {table}",
            f"ALTER TABLE {table}_new RENAME TO {table}",
        ]
    )
    db.modifyscript(script + ";")
    return True


def _refuse_old_version(version: int) -> Callable[[Any], None]:
    """Return the step for ``version``, which refuses to upgrade from the version before it."""

    def refuse(db: StatsDb) -> None:
        del db
        msg = (
            f"cannot upgrade a stats database from version {version - 1}: "
            "the oldest version that can be upgraded is 12"
        )
        raise ValueError(msg)

    return refuse


def _version_13(db: StatsDb) -> None:
    """Add rarexp to mobkills."""
    rebuild_table(db, "mobkills", MOBKILLS_SQL)


def _version_14(db: StatsDb) -> None:
    """Add noexp to mobkills."""
    rebuild_table(db, "mobkills", MOBKILLS_SQL)


def _version_15(db: StatsDb) -> None:
    """Add extended to gquests; a completed global quest was extended."""
    rebuild_table(
        db, "gquests", GQUESTS_SQL, {"extended": "CASE WHEN completed = 1 THEN 1 ELSE 0 END"}
    )


def _version_16(db: StatsDb) -> None:
    """Add tierqp, opk and hardcore to quests; tierqp starts as the old tier."""
    rebuild_table(db, "quests", QUESTS_SQL, {"tierqp": "tier"})


def _version_17(db: StatsDb) -> None:
    """Add battlelearntrains to levels."""
    rebuild_table(db, "levels", LEVELS_SQL)


MIGRATIONS: dict[int, Callable[[Any], Any]] = {
    **{version: _refuse_old_version(version) for version in range(2, 13)},
    13: _version_13,
    14: _version_14,
    15: _version_15,
    16: _version_16,
    17: _version_17,
}
