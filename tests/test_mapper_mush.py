"""Tests for the MUSHclient map reader of the mapper plugin."""

import hashlib
import os
import sqlite3
import sys
from pathlib import Path

import pytest
from mush_db import build_mush_db

from aardwolf.mapper.libs import (
    MushDbError,
    check_schema,
    read_mush_db,
    requirement_from_level,
    resolve_import_path,
)


def _digest(path: Path) -> tuple[str, float]:
    return hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime


def test_relative_path_is_refused() -> None:
    """The proxy's working directory means nothing to a client, so a relative path fails."""
    with pytest.raises(MushDbError, match="absolute path"):
        resolve_import_path("Aardwolf.db")


def test_empty_path_is_refused() -> None:
    """A blank path asks for the file."""
    with pytest.raises(MushDbError, match="give the path"):
        resolve_import_path("  ")


def test_tilde_expands(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A path starting with ~ is looked up in the home directory."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    target = tmp_path / "x.db"
    target.write_bytes(b"")
    assert resolve_import_path("~/x.db") == target.resolve()


def test_missing_file_and_directory_are_refused(tmp_path: Path) -> None:
    """A missing file and a directory each get their own message."""
    with pytest.raises(MushDbError, match="no such file"):
        resolve_import_path(str(tmp_path / "none.db"))
    with pytest.raises(MushDbError, match="is a directory"):
        resolve_import_path(str(tmp_path))


def test_valid_file_resolves(tmp_path: Path) -> None:
    """An existing file resolves to itself."""
    path = build_mush_db(tmp_path / "Aardwolf.db")
    assert resolve_import_path(str(path)) == path.resolve()


def test_text_file_is_not_sqlite(tmp_path: Path) -> None:
    """A text file is not an SQLite database."""
    path = tmp_path / "a.db"
    path.write_text("this is not a database, just some text to fill the header " * 4)
    with pytest.raises(MushDbError, match="not an SQLite database"):
        read_mush_db(path)


def test_empty_file_is_not_a_mapper_db(tmp_path: Path) -> None:
    """A 0-byte file is an empty SQLite database, so it lacks the tables."""
    path = tmp_path / "a.db"
    path.write_bytes(b"")
    with pytest.raises(MushDbError, match="not a MUSHclient mapper database"):
        read_mush_db(path)


def test_missing_table_is_named(tmp_path: Path) -> None:
    """A database without exits names the table."""
    path = build_mush_db(tmp_path / "a.db")
    conn = sqlite3.connect(path)
    conn.execute("DROP TABLE exits")
    conn.commit()
    conn.close()
    with pytest.raises(MushDbError, match="missing table exits"):
        read_mush_db(path)


def test_missing_column_is_named(tmp_path: Path) -> None:
    """A rooms table without info names the column."""
    path = tmp_path / "a.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE areas(uid TEXT, name TEXT)")
    conn.execute("CREATE TABLE exits(dir TEXT, fromuid TEXT, touid TEXT)")
    conn.execute(
        "CREATE TABLE rooms(uid TEXT, name TEXT, area TEXT, terrain TEXT, x INT, y INT, z INT)"
    )
    conn.commit()
    conn.close()
    with pytest.raises(MushDbError, match=r"missing rooms\.info"):
        read_mush_db(path)


def test_read_is_read_only(tmp_path: Path) -> None:
    """The file is the same bytes with the same mtime after a read."""
    path = build_mush_db(tmp_path / "a.db")
    os.utime(path, (1_000_000, 1_000_000))
    before = _digest(path)
    read_mush_db(path)
    assert _digest(path) == before


def test_path_with_special_characters(tmp_path: Path) -> None:
    """A path with spaces, #, % and ? is opened as a file path, not as a URI query.

    Windows does not allow ``?`` in a file name, so it is left out there.
    """
    folder = tmp_path / ("my dir #1%" + ("" if sys.platform == "win32" else "?"))
    folder.mkdir()
    path = build_mush_db(folder / "Aardwolf.db")
    assert len(read_mush_db(path).rooms) == 5


def test_read_current_schema(tmp_path: Path) -> None:
    """The current schema converts to core dicts; nomap rooms and orphan exits are skipped."""
    data = read_mush_db(build_mush_db(tmp_path / "a.db"))
    rooms = {r["uid"]: r for r in data.rooms}
    assert list(rooms) == ["100", "101", "102", "103", "200"]
    assert rooms["100"]["details"] == {"details": "bank,shop", "coord_id": None, "cont": None}
    assert rooms["100"]["flags"] == []
    assert rooms["100"]["x"] == 10
    assert rooms["101"]["flags"] == ["norecall"]
    assert rooms["102"]["flags"] == ["noportal"]
    assert data.skipped_rooms == 1
    assert data.skipped_exits == 3
    assert data.exits["101"] == [("n", "102", {"level": 50}), ("s", "100", None)]
    assert data.exits["100"] == [("e", "-1", None), ("n", "101", None)]
    assert data.exits["*"] == [("enter far", "200", {"level": 100}), ("enter test", "100", None)]
    assert data.exits["**"] == [("recall", "100", None)]
    assert "nomap_x" not in data.exits
    assert "9999" not in data.exits
    assert "200" not in data.exits


def test_notes_bookmark_wins(tmp_path: Path) -> None:
    """A bookmark note wins over rooms.notes; an empty note is skipped."""
    data = read_mush_db(build_mush_db(tmp_path / "a.db"))
    assert data.notes == {"100": "bookmark note", "102": "bookmark wins"}


def test_areas(tmp_path: Path) -> None:
    """Area flags are split, texture and color go to details, an empty uid is skipped."""
    data = read_mush_db(build_mush_db(tmp_path / "a.db"))
    assert data.areas == [
        {
            "uid": "otherarea",
            "name": "Other Area",
            "flags": [],
            "details": {},
        },
        {
            "uid": "testarea",
            "name": "Test Area",
            "flags": ["flagone", "flagtwo"],
            "details": {"texture": "tex1", "color": "green"},
        },
    ]


def test_read_old_schema(tmp_path: Path) -> None:
    """An old database has no flags or requirements and keeps notes in rooms.notes."""
    data = read_mush_db(build_mush_db(tmp_path / "a.db", version="old"))
    assert all(r["flags"] == [] for r in data.rooms)
    assert all(req is None for items in data.exits.values() for _, _, req in items)
    assert data.notes == {"102": "old room note"}
    assert len(data.rooms) == 5


def test_check_schema_reports_optional_columns(tmp_path: Path) -> None:
    """The optional columns present are returned."""
    for version, expected in (("current", True), ("old", False)):
        path = build_mush_db(tmp_path / f"{version}.db", version=version)
        conn = sqlite3.connect(path)
        try:
            present = check_schema(conn)
        finally:
            conn.close()
        assert ("rooms.noportal" in present) is expected
        assert ("exits.level" in present) is expected
        assert ("bookmarks" in present) is expected
        assert "rooms.notes" in present


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0", None),
        (0, None),
        ("50", {"level": 50}),
        (100, {"level": 100}),
        ("x", None),
        (None, None),
    ],
)
def test_requirement_from_level(value: object, expected: dict[str, int] | None) -> None:
    """Level 0 or junk is no requirement; above 0 is a level requirement."""
    assert requirement_from_level(value) == expected
