"""Build a database the way the old proxy's statdb plugin wrote it, for tests.

Not a test module. It imports only ``sqlite3``, and writes the old CREATE statements as its own
literals instead of importing them from the plugin, so a drift in the plugin's schema fails a
test. All the data is made up.
"""

import sqlite3
from pathlib import Path
from typing import Any

STATS = """CREATE TABLE stats(
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

QUESTS_17 = """CREATE TABLE quests(
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

QUESTS_12 = """CREATE TABLE quests(
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
            tier INT default 0,
            mccp INT default 0,
            lucky INT default 0,
            tp INT default 0,
            trains INT default 0,
            pracs INT default 0,
            level INT default -1,
            failed INT default 0
          );"""

CLASSES = """CREATE TABLE classes(
              class TEXT NOT NULL PRIMARY KEY,
              remort INTEGER
            );"""

LEVELS_17 = """CREATE TABLE levels(
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

LEVELS_12 = """CREATE TABLE levels(
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
            blessingtrains INT default 0
          )"""

CAMPAIGNS = """CREATE TABLE campaigns(
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

CPMOBS = """CREATE TABLE cpmobs(
            cpmob_id INTEGER NOT NULL PRIMARY KEY autoincrement,
            cp_id INT NOT NULL,
            name TEXT default "Unknown",
            location TEXT default "Unknown"
          )"""

MOBKILLS_17 = """CREATE TABLE mobkills(
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

MOBKILLS_12 = """CREATE TABLE mobkills(
            mk_id INTEGER NOT NULL PRIMARY KEY autoincrement,
            name TEXT default "Unknown",
            xp INT default 0,
            bonusxp INT default 0,
            blessingxp INT default 0,
            totalxp INT default 0,
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

GQUESTS_17 = """CREATE TABLE gquests(
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

GQUESTS_12 = """CREATE TABLE gquests(
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
            won INT default 0,
            completed INT default 0
          )"""

GQMOBS = """CREATE TABLE gqmobs(
            gqmob_id INTEGER NOT NULL PRIMARY KEY autoincrement,
            gq_id INT NOT NULL,
            num INT,
            name TEXT default "Unknown",
            location TEXT default "Unknown"
          )"""

# tables another old plugin wrote into the same file; statdb must leave them alone
SKILLS = "CREATE TABLE skills(sn INTEGER NOT NULL PRIMARY KEY, name TEXT, percent INT)"
RECOVERIES = "CREATE TABLE recoveries(rid INTEGER NOT NULL PRIMARY KEY, name TEXT)"

CLASS_NAMES = ["mage", "thief", "paladin", "warrior", "psionicist", "cleric", "ranger"]


def _stats(milestone: str, time: int, totallevels: int, monsters: int) -> dict[str, Any]:
    return {
        "name": "Tester",
        "level": 5,
        "totallevels": totallevels,
        "remorts": 1,
        "qpearned": 100,
        "questscomplete": 3,
        "questsfailed": 1,
        "campaignsdone": 2,
        "campaignsfld": 1,
        "gquestswon": 1,
        "monsterskilled": monsters,
        "powerupsall": 1,
        "totaltrivia": 10,
        "time": time,
        "milestone": milestone,
    }


def _insert(connection: sqlite3.Connection, table: str, row: dict[str, Any]) -> None:
    """Insert the columns of row the table has."""
    columns = {item[1] for item in connection.execute(f"PRAGMA table_info({table})")}
    kept = {key: value for key, value in row.items() if key in columns}
    names = ", ".join(f'"{key}"' for key in kept)
    marks = ", ".join(f":{key}" for key in kept)
    connection.execute(f"INSERT INTO {table} ({names}) VALUES ({marks})", kept)  # nosec B608  # fixture tables


def build_old_database(path: Path, version: int = 17, rows: bool = True) -> Path:
    """Write an old-proxy stats database at ``path`` and return the path.

    ``version`` 17 writes the current layouts. Any lower version writes the layouts before
    version 13. The file is in WAL mode like the old proxy's, with a ``skills`` and a
    ``recoveries`` table holding one row each.
    """
    old = version < 13
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        for sql in (
            STATS,
            QUESTS_12 if old else QUESTS_17,
            CLASSES,
            LEVELS_12 if old else LEVELS_17,
            CAMPAIGNS,
            CPMOBS,
            MOBKILLS_12 if old else MOBKILLS_17,
            GQUESTS_12 if old else GQUESTS_17,
            GQMOBS,
            SKILLS,
            RECOVERIES,
        ):
            connection.execute(sql)
        connection.execute("INSERT INTO skills VALUES (1, 'bash', 75)")
        connection.execute("INSERT INTO recoveries VALUES (1, 'sleep')")
        for name in CLASS_NAMES:
            connection.execute(
                "INSERT INTO classes VALUES (?, ?)", (name, 1 if name == "mage" else -1)
            )
        if rows:
            _fill(connection)
        connection.execute(f"PRAGMA user_version={version}")
        connection.commit()
    finally:
        connection.close()
    return path


def _fill(connection: sqlite3.Connection) -> None:
    """Add a few made-up rows to every statdb table."""
    for row in (
        _stats("current", 0, 5, 4),
        _stats("start", 1000, 1, 0),
        _stats("3", 2000, 3, 1),
        _stats("5", 3000, 5, 4),
        _stats("t0r1l5", 3100, 5, 4),
    ):
        _insert(connection, "stats", row)
    quests = (
        {"starttime": 100, "finishtime": 160, "mobname": "a rat", "mobarea": "Sewer",
         "mobroom": "A pipe", "qp": 20, "double": 1, "totqp": 25, "gold": 300, "tier": 2,
         "tierqp": 2, "mccp": 3, "tp": 1, "trains": 1, "pracs": 2, "level": 5, "failed": 0},
        {"starttime": 200, "finishtime": 210, "mobname": "a bat", "mobarea": "Cave",
         "mobroom": "A ledge", "level": 5, "failed": 1},
    )  # fmt: skip
    for quest in quests:
        _insert(connection, "quests", quest)
    for level in (
        {"type": "level", "level": 3, "starttime": 1500, "finishtime": 2000, "trains": 3, "hp": 10},
        {"type": "pup", "level": 3, "starttime": 2000, "finishtime": 2500, "trains": 1},
        {"type": "level", "level": 5, "starttime": 2500, "finishtime": -1, "trains": 4,
         "bonustrains": 1},
    ):  # fmt: skip
        _insert(connection, "levels", level)
    _insert(connection, "campaigns", {"starttime": 10, "finishtime": 70, "qp": 30, "level": 4,
                                      "gold": 500, "tp": 1})  # fmt: skip
    _insert(connection, "campaigns", {"starttime": 80, "finishtime": 90, "level": 4, "failed": 1})
    _insert(connection, "cpmobs", {"cp_id": 1, "name": "a goblin", "location": "Forest"})
    _insert(connection, "cpmobs", {"cp_id": 1, "name": "an orc", "location": "Hills"})
    _insert(connection, "gquests", {"starttime": 5, "finishtime": 65, "qp": 40, "qpmobs": 10,
                                    "level": 5, "won": 1, "completed": 1})  # fmt: skip
    _insert(connection, "gquests", {"starttime": 70, "finishtime": 90, "qpmobs": 2, "level": 5})
    _insert(connection, "gqmobs", {"gq_id": 1, "num": 3, "name": "a troll", "location": "Cave"})
    for kill in (
        {"name": "a rat", "xp": 10, "totalxp": 12, "bonusxp": 2, "gold": 50, "tp": 1,
         "time": 1600, "vorpal": 1, "level": 3},
        {"name": "a very long named monster of the deep", "xp": 20, "rarexp": 5, "totalxp": 25,
         "gold": 5, "time": 1700, "level": 3},
        {"name": "a bat", "xp": 0, "totalxp": 0, "noexp": 1, "time": 2600, "level": 5},
    ):  # fmt: skip
        _insert(connection, "mobkills", kill)
