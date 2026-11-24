"""Build a MUSHclient Aardwolf.db the way the old mapper wrote it, for tests.

Not a test module. It imports only ``sqlite3``, and writes the CREATE statements as its own
literals instead of importing them from the plugin, so a drift in the reader fails a test. All
the data is made up.
"""

import sqlite3
from pathlib import Path

AREAS = """CREATE TABLE areas(
    uid TEXT NOT NULL PRIMARY KEY,
    name TEXT,
    texture TEXT,
    color TEXT,
    flags TEXT NOT NULL DEFAULT ''
)"""
ROOMS = """CREATE TABLE rooms(
    uid TEXT NOT NULL PRIMARY KEY,
    name TEXT,
    area TEXT,
    building TEXT,
    terrain TEXT,
    info TEXT,
    notes TEXT,
    x INTEGER,
    y INTEGER,
    z INTEGER,
    norecall INTEGER NOT NULL DEFAULT 0,
    noportal INTEGER NOT NULL DEFAULT 0
)"""
ROOMS_OLD = """CREATE TABLE rooms(
    uid TEXT NOT NULL PRIMARY KEY,
    name TEXT,
    area TEXT,
    building TEXT,
    terrain TEXT,
    info TEXT,
    notes TEXT,
    x INTEGER,
    y INTEGER,
    z INTEGER
)"""
EXITS = """CREATE TABLE exits(
    dir TEXT NOT NULL,
    fromuid TEXT NOT NULL,
    touid TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT '0',
    PRIMARY KEY(fromuid, dir)
)"""
EXITS_OLD = """CREATE TABLE exits(
    dir TEXT NOT NULL,
    fromuid TEXT NOT NULL,
    touid TEXT NOT NULL,
    PRIMARY KEY(fromuid, dir)
)"""
BOOKMARKS = """CREATE TABLE bookmarks(
    uid TEXT NOT NULL PRIMARY KEY,
    notes TEXT
)"""
STORAGE = "CREATE TABLE storage(name TEXT NOT NULL PRIMARY KEY, data TEXT)"

# uid, name, area, terrain, info, notes, x, y, z, norecall, noportal
ROOM_ROWS: list[tuple[str, str, str, str, str, str, int, int, int, int, int]] = [
    ("100", "The Test Bank", "testarea", "city", "bank,shop", "", 10, 20, 0, 0, 0),
    ("101", "Training Hall", "testarea", "city", "trainer", "", 11, 20, 0, 1, 0),
    ("102", "Quest Office", "testarea", "city", "questor", "old room note", 12, 20, 0, 0, 1),
    ("103", "Plain Road", "testarea", "city", "", "", 13, 20, 0, 0, 0),
    ("200", "Far Hut", "otherarea", "forest", "Shop, Safe", "", 5, 5, 1, 0, 0),
    ("nomap_x", "Nowhere", "testarea", "city", "", "", 0, 0, 0, 0, 0),
]
# dir, fromuid, touid, level
EXIT_ROWS: list[tuple[str, str, str, int]] = [
    ("n", "100", "101", 0),
    ("e", "100", "-1", 0),
    ("s", "101", "100", 0),
    ("n", "101", "102", 50),
    ("w", "102", "103", 0),
    ("e", "200", "nomap_x", 0),
    ("w", "nomap_x", "100", 0),
    ("n", "9999", "100", 0),
    ("enter test", "*", "100", 0),
    ("recall", "**", "100", 0),
    ("enter far", "*", "200", 100),
]
AREA_ROWS: list[tuple[str, str, str, str, str]] = [
    ("testarea", "Test Area", "tex1", "green", "flagone,flagtwo"),
    ("otherarea", "Other Area", "", "", ""),
    ("", "No Id", "", "", ""),
]
BOOKMARK_ROWS: list[tuple[str, str]] = [
    ("100", "bookmark note"),
    ("102", "bookmark wins"),
    ("103", ""),
    ("nomap_x", "ignored"),
]


def build_mush_db(path: Path, *, version: str = "current") -> Path:
    """Write a made-up MUSH map database; ``version`` is ``current`` or ``old``."""
    old = version == "old"
    conn = sqlite3.connect(path)
    try:
        conn.execute(AREAS)
        conn.execute(ROOMS_OLD if old else ROOMS)
        conn.execute(EXITS_OLD if old else EXITS)
        conn.execute(STORAGE)
        conn.executemany("INSERT INTO areas VALUES (?,?,?,?,?)", AREA_ROWS)
        for row in ROOM_ROWS:
            if old:
                conn.execute(
                    "INSERT INTO rooms VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (row[0], row[1], row[2], "", row[3], row[4], row[5], row[6], row[7], row[8]),
                )
            else:
                conn.execute(
                    "INSERT INTO rooms VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (row[0], row[1], row[2], "", row[3], row[4], row[5], *row[6:]),
                )
        for direction, fromuid, touid, level in EXIT_ROWS:
            if old:
                conn.execute("INSERT INTO exits VALUES (?,?,?)", (direction, fromuid, touid))
            else:
                conn.execute(
                    "INSERT INTO exits VALUES (?,?,?,?)", (direction, fromuid, touid, str(level))
                )
        if not old:
            conn.execute(BOOKMARKS)
            conn.executemany("INSERT INTO bookmarks VALUES (?,?)", BOOKMARK_ROWS)
        conn.commit()
    finally:
        conn.close()
    return path
