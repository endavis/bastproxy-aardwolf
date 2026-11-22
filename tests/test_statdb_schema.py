"""Tests for the statdb schema: tables, version 17, upgrades and old databases."""

import sqlite3
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import statdb_old_db
from statdb_old_db import build_old_database
from statdb_support import make_db

if TYPE_CHECKING:
    from bastproxy.plugins.core.sqldb.libs._sqlite import Sqldb

TABLE_NAMES = {
    "stats",
    "quests",
    "classes",
    "levels",
    "campaigns",
    "cpmobs",
    "mobkills",
    "gquests",
    "gqmobs",
}
FULL_CLASSES = {"mage", "thief", "paladin", "warrior", "psionicist", "cleric", "ranger"}


@pytest.fixture(autouse=True)
def home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Importing bastproxy needs an existing BASTPROXY_HOME."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setenv("BASTPROXY_HOME", str(home_dir))


@pytest.fixture
def db(tmp_path: Path) -> "Iterator[Sqldb]":
    """A fresh statdb database."""
    database = make_db(tmp_path / "fresh")
    yield database
    database.close()


def _columns(path: Path, table: str) -> list[str]:
    connection = sqlite3.connect(path)
    try:
        return [row[1] for row in connection.execute(f"PRAGMA table_info({table})")]
    finally:
        connection.close()


def _user_version(path: Path) -> int:
    connection = sqlite3.connect(path)
    try:
        return int(connection.execute("PRAGMA user_version").fetchone()[0])
    finally:
        connection.close()


def test_fresh_database(db: "Sqldb") -> None:
    """A new file is version 17, with every table and the seven full class names."""
    assert db.getversion() == 17
    names = {row["name"] for row in db.select("SELECT name FROM sqlite_master WHERE type='table'")}
    assert names >= TABLE_NAMES
    classes = db.select("SELECT * FROM classes")
    assert {row["class"] for row in classes} == FULL_CLASSES
    assert {row["remort"] for row in classes} == {-1}


@pytest.mark.parametrize(
    ("table", "old_sql"),
    [
        ("stats", statdb_old_db.STATS),
        ("quests", statdb_old_db.QUESTS_17),
        ("classes", statdb_old_db.CLASSES),
        ("levels", statdb_old_db.LEVELS_17),
        ("campaigns", statdb_old_db.CAMPAIGNS),
        ("cpmobs", statdb_old_db.CPMOBS),
        ("mobkills", statdb_old_db.MOBKILLS_17),
        ("gquests", statdb_old_db.GQUESTS_17),
        ("gqmobs", statdb_old_db.GQMOBS),
    ],
)
def test_declared_sql_is_the_old_version_17_text(table: str, old_sql: str) -> None:
    """The declared CREATE statement is the old one, so columns keep their order."""
    from aardwolf.statdb.libs import TABLES

    declared = next(item["sql"] for item in TABLES if item["name"] == table)
    assert " ".join(declared.split()).rstrip(";") == " ".join(old_sql.split()).rstrip(";")


def test_old_version_17_database_opens_unchanged(tmp_path: Path) -> None:
    """An old file at version 17 opens without a rebuild, a backup or touching other tables."""
    directory = tmp_path / "old"
    directory.mkdir()
    path = build_old_database(directory / "stats.sqlite")
    db = make_db(directory)
    try:
        assert db.getversion() == 17
        assert not (directory / "archive").exists()
        assert db.select("SELECT * FROM skills") == [{"sn": 1, "name": "bash", "percent": 75}]
        assert db.select("SELECT * FROM recoveries") == [{"rid": 1, "name": "sleep"}]
        assert len(db.select("SELECT * FROM quests")) == 2
        assert db.select("SELECT remort FROM classes WHERE class = 'mage'") == [{"remort": 1}]
        # a positional insert into every table proves the column order matches
        from aardwolf.statdb.libs import StatStore

        store = StatStore(db)
        assert store.save_quest({"totqp": 5, "tp": 0, "failed": 0}) == 3
        assert store.save_cp({"qp": 1, "tp": 0, "mobs": [{"name": "x", "location": "y"}]}) == 3
        assert store.save_gq({"qp": 1, "qpmobs": 1, "tp": 0, "won": 0, "mobs": []}) == 3
        assert store.save_level({"type": "pup", "totallevels": 5, "starttime": 9}) == 4
        assert store.save_mobkill({"name": "z", "tp": 0}) == 4
    finally:
        db.close()
    assert _user_version(path) == 17


def test_version_12_database_upgrades(tmp_path: Path) -> None:
    """Version 12 is rebuilt to 17, keeping rows and ids, with a backup first."""
    directory = tmp_path / "old"
    directory.mkdir()
    path = build_old_database(directory / "stats.sqlite", version=12)
    db = make_db(directory)
    try:
        assert db.getversion() == 17
        assert (directory / "archive" / "stats_12.sqlite.zip").exists()
        with zipfile.ZipFile(directory / "archive" / "stats_12.sqlite.zip") as archive:
            assert archive.namelist() == ["stats_12.sqlite"]
        for item in (
            ("quests", statdb_old_db.QUESTS_17),
            ("levels", statdb_old_db.LEVELS_17),
            ("mobkills", statdb_old_db.MOBKILLS_17),
            ("gquests", statdb_old_db.GQUESTS_17),
        ):
            expected = _fresh_columns(item[1], item[0])
            assert _columns(path, item[0]) == expected
        quests = db.select("SELECT * FROM quests ORDER BY quest_id")
        assert [row["quest_id"] for row in quests] == [1, 2]
        assert quests[0]["tierqp"] == 2
        assert quests[0]["mobname"] == "a rat"
        assert (quests[0]["opk"], quests[0]["hardcore"]) == (0, 0)
        gquests = db.select("SELECT gq_id, extended, completed FROM gquests ORDER BY gq_id")
        assert [(row["extended"], row["completed"]) for row in gquests] == [(1, 1), (0, 0)]
        mobs = db.select("SELECT * FROM mobkills ORDER BY mk_id")
        assert next(row["name"] for row in mobs) == "a rat"
        assert {row["rarexp"] for row in mobs} == {0}
        assert {row["noexp"] for row in mobs} == {0}
        assert {row["battlelearntrains"] for row in db.select("SELECT * FROM levels")} == {0}
        assert db.select("SELECT * FROM skills") == [{"sn": 1, "name": "bash", "percent": 75}]
        assert len(db.select("SELECT * FROM stats")) == 5
    finally:
        db.close()


def _fresh_columns(sql: str, table: str) -> list[str]:
    from aardwolf.statdb.libs import target_columns

    return target_columns(table, sql)


def test_version_5_database_is_refused(tmp_path: Path) -> None:
    """A file older than version 12 raises a ValueError naming its version and stays as it was."""
    directory = tmp_path / "old"
    directory.mkdir()
    path = build_old_database(directory / "stats.sqlite", version=5)
    with pytest.raises(ValueError, match="from version 5"):
        make_db(directory)
    assert _user_version(path) == 5
    assert _columns(path, "levels") == _fresh_columns(statdb_old_db.LEVELS_12, "levels")


def test_migrations_cover_every_version() -> None:
    """There is a step for each version from 2 to 17, and 2 to 12 refuse."""
    from aardwolf.statdb.libs import MIGRATIONS

    assert sorted(MIGRATIONS) == list(range(2, 18))
    for version in range(2, 13):
        with pytest.raises(ValueError, match=f"from version {version - 1}"):
            MIGRATIONS[version](None)


def test_rebuild_is_idempotent(tmp_path: Path) -> None:
    """A rebuild of a table already in its final layout changes nothing."""
    from aardwolf.statdb.libs import MIGRATIONS, TABLES, rebuild_table

    directory = tmp_path / "old"
    directory.mkdir()
    build_old_database(directory / "stats.sqlite", version=12)
    db = make_db(directory)
    try:
        before = db.select("SELECT * FROM quests ORDER BY quest_id")
        for table in TABLES:
            assert rebuild_table(db, table["name"], table["sql"]) is False
        for step in range(13, 18):
            MIGRATIONS[step](db)
        assert db.select("SELECT * FROM quests ORDER BY quest_id") == before
        db.modifyscript("DROP TABLE gqmobs")
        gqmobs = next(item for item in TABLES if item["name"] == "gqmobs")
        assert rebuild_table(db, "gqmobs", gqmobs["sql"]) is False
    finally:
        db.close()


def test_rebuild_needs_a_matching_create_statement(db: "Sqldb") -> None:
    """A create statement for another table is refused before anything changes."""
    from aardwolf.statdb.libs import rebuild_table

    with pytest.raises(ValueError, match="must start with"):
        rebuild_table(db, "classes", "CREATE TABLE other(a INT, b INT)")
    assert len(db.select("SELECT * FROM classes")) == 7
