"""Read a MUSHclient Aardwolf.db into core mapper data. No bastproxy imports.

The reader only reads: the database is opened read-only, validated, and copied into plain
dicts. Writing them to the core mapper is the plugin's job.
"""

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ._mapper import ANYWHERE, FLAG_NOPORTAL, FLAG_NORECALL, UNKNOWN_UID, to_int

REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    "rooms": ("uid", "name", "area", "terrain", "info", "x", "y", "z"),
    "exits": ("dir", "fromuid", "touid"),
    "areas": ("uid", "name"),
}
OPTIONAL_COLUMNS: dict[str, tuple[str, ...]] = {
    "rooms": ("noportal", "norecall", "notes"),
    "exits": ("level",),
    "areas": ("texture", "color", "flags"),
    "bookmarks": ("uid", "notes"),
}


class MushDbError(Exception):
    """The file cannot be imported; the message is meant for the client."""


@dataclass
class MushMap:
    """What a MUSHclient map database holds, converted to core mapper data."""

    areas: list[dict[str, Any]] = field(default_factory=list)
    rooms: list[dict[str, Any]] = field(default_factory=list)
    exits: dict[str, list[tuple[str, str, dict[str, Any] | None]]] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)
    skipped_rooms: int = 0
    skipped_exits: int = 0


def resolve_import_path(text: str) -> Path:
    """Return the file to import, or raise MushDbError with the reason it is refused."""
    if not text.strip():
        raise MushDbError("give the path of the Aardwolf.db file")
    try:
        path = Path(text).expanduser()
    except RuntimeError as exc:
        raise MushDbError(f"cannot expand {text}: {exc}") from exc
    if not path.is_absolute():
        raise MushDbError("give an absolute path or one starting with ~")
    path = path.resolve()
    if not path.exists():
        raise MushDbError(f"no such file: {path}")
    if path.is_dir():
        raise MushDbError(f"{path} is a directory, give the Aardwolf.db file")
    if not path.is_file():
        raise MushDbError(f"{path} is not a regular file")
    return path


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    """Return the column names of a table; empty when the table does not exist."""
    return {str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})")}


def check_schema(conn: sqlite3.Connection) -> set[str]:
    """Raise MushDbError unless this is a mapper database; return the optional columns present.

    The set holds ``table.column`` names, plus ``bookmarks`` when that table has both its columns.
    """
    present: set[str] = set()
    for table, wanted in REQUIRED_COLUMNS.items():
        columns = _columns(conn, table)
        if not columns:
            raise MushDbError(f"not a MUSHclient mapper database: missing table {table}")
        for column in wanted:
            if column not in columns:
                raise MushDbError(f"not a MUSHclient mapper database: missing {table}.{column}")
        present.update(f"{table}.{c}" for c in OPTIONAL_COLUMNS.get(table, ()) if c in columns)
    bookmarks = _columns(conn, "bookmarks")
    if all(c in bookmarks for c in OPTIONAL_COLUMNS["bookmarks"]):
        present.add("bookmarks")
    return present


def requirement_from_level(value: object) -> dict[str, Any] | None:
    """Return the exit requirement of a MUSH exit level; 0 or less means none."""
    level = to_int(value)
    return {"level": level} if level > 0 else None


def _room_uid(value: object) -> str | None:
    """Return a MUSH room uid when it is a positive integer, else None."""
    number = to_int(value)
    return str(number) if number > 0 else None


def _exit_target(value: object) -> str | None:
    """Return the touid of a MUSH exit: a positive integer or -1; anything else is None."""
    if to_int(value) == -1:
        return UNKNOWN_UID
    return _room_uid(value)


def _text(value: object) -> str:
    """Return a column value as text; NULL is empty."""
    return "" if value is None else str(value)


def _dict_rows(conn: sqlite3.Connection, query: str) -> list[dict[str, Any]]:
    """Run a fixed query and return its rows as dicts keyed by column name."""
    cursor = conn.execute(query)
    names = [d[0] for d in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor]


def _read_areas(conn: sqlite3.Connection, present: set[str]) -> list[dict[str, Any]]:
    extra = [c for c in OPTIONAL_COLUMNS["areas"] if f"areas.{c}" in present]
    areas: list[dict[str, Any]] = []
    for row in _dict_rows(conn, "SELECT * FROM areas ORDER BY uid"):
        data = {k: row.get(k) for k in ("uid", "name", *extra)}
        uid = _text(data["uid"])
        if not uid:
            continue
        flags = [f.strip() for f in _text(data.get("flags")).split(",") if f.strip()]
        details = {k: data[k] for k in ("texture", "color") if data.get(k) not in (None, "")}
        areas.append({"uid": uid, "name": _text(data["name"]), "flags": flags, "details": details})
    return areas


def _read_notes(
    conn: sqlite3.Connection, present: set[str], rooms: dict[str, dict[str, Any]]
) -> dict[str, str]:
    """Return the notes of the importable rooms; a bookmark wins over rooms.notes."""
    notes: dict[str, str] = {}
    if "rooms.notes" in present:
        for uid, text in conn.execute("SELECT uid, notes FROM rooms"):
            key = _room_uid(uid)
            if key in rooms and _text(text).strip():
                notes[str(key)] = _text(text)
    if "bookmarks" in present:
        for uid, text in conn.execute("SELECT uid, notes FROM bookmarks"):
            key = _room_uid(uid)
            if key in rooms and _text(text).strip():
                notes[str(key)] = _text(text)
    return notes


def _read_exits(
    conn: sqlite3.Connection, present: set[str], rooms: dict[str, dict[str, Any]]
) -> tuple[dict[str, list[tuple[str, str, dict[str, Any] | None]]], int]:
    has_level = "exits.level" in present
    exits: dict[str, list[tuple[str, str, dict[str, Any] | None]]] = {}
    skipped = 0
    for row in _dict_rows(conn, "SELECT * FROM exits ORDER BY fromuid, dir"):
        fromuid, direction, touid = row["fromuid"], row["dir"], row["touid"]
        exit_level = row.get("level") if has_level else 0
        source = _text(fromuid)
        if source not in ANYWHERE:
            source = _room_uid(fromuid) or ""
            if source not in rooms:
                skipped += 1
                continue
        target = _exit_target(touid)
        command = _text(direction)
        if target is None or not command:
            skipped += 1
            continue
        exits.setdefault(source, []).append((command, target, requirement_from_level(exit_level)))
    return exits, skipped


def _read_rooms(
    conn: sqlite3.Connection, present: set[str]
) -> tuple[dict[str, dict[str, Any]], int]:
    has_noportal = "rooms.noportal" in present
    has_norecall = "rooms.norecall" in present
    rooms: dict[str, dict[str, Any]] = {}
    skipped = 0
    for row in _dict_rows(conn, "SELECT * FROM rooms ORDER BY CAST(uid AS INTEGER)"):
        uid, name, area, terrain = row["uid"], row["name"], row["area"], row["terrain"]
        info, x, y, z = row["info"], row["x"], row["y"], row["z"]
        no_portal = row.get("noportal") if has_noportal else 0
        no_recall = row.get("norecall") if has_norecall else 0
        key = _room_uid(uid)
        if key is None:
            skipped += 1
            continue
        flags = []
        if to_int(no_portal) == 1:
            flags.append(FLAG_NOPORTAL)
        if to_int(no_recall) == 1:
            flags.append(FLAG_NORECALL)
        rooms[key] = {
            "uid": key,
            "name": _text(name),
            "area": _text(area),
            "terrain": _text(terrain),
            "x": to_int(x),
            "y": to_int(y),
            "z": to_int(z),
            "details": {"details": _text(info), "coord_id": None, "cont": None},
            "flags": flags,
        }
    return rooms, skipped


def _read(conn: sqlite3.Connection) -> MushMap:
    present = check_schema(conn)
    rooms, skipped_rooms = _read_rooms(conn, present)
    exits, skipped_exits = _read_exits(conn, present, rooms)
    return MushMap(
        areas=_read_areas(conn, present),
        rooms=list(rooms.values()),
        exits=exits,
        notes=_read_notes(conn, present, rooms),
        skipped_rooms=skipped_rooms,
        skipped_exits=skipped_exits,
    )


def read_mush_db(path: Path) -> MushMap:
    """Read a MUSHclient map database, read-only, into core mapper data.

    Raises MushDbError when the file is not a mapper database. Nothing is written anywhere.
    """
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
        return _read(conn)
    except sqlite3.OperationalError as exc:
        raise MushDbError(f"cannot read {path}: {exc}") from exc
    except sqlite3.DatabaseError as exc:
        raise MushDbError(f"not an SQLite database: {path}") from exc
    finally:
        if conn is not None:
            conn.close()
