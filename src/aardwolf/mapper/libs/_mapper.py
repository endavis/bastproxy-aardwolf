"""Constants and helpers of the mapper plugin. No bastproxy imports."""

from collections.abc import Iterable, Mapping
from typing import Any

PLUGIN_ID = "plugins.aardwolf.mapper"
MAPPER = "plugins.client.mapper"
EVENT_GMCP_ROOM = "ev_libs.net.mud_gmcp_room.info"
EVENT_GMCP_AREA = "ev_libs.net.mud_gmcp_room.area"
EVENT_MOVE_ROOM = "ev_plugins.aardwolf.move_room"
EVENT_ROOM_MISMATCH = "ev_plugins.client.mapper_room_mismatch"
EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"
GMCP_ROOM = "room.info"
GMCP_LEVEL = "char.status.level"
GMCP_TIER = "char.base.tier"
NOPORTAL_REGEX = r"^Magic walls bounce you back\.$"
NORECALL_REGEX = r"^You cannot (recall|return home) from this room\.$"
FLAG_NOPORTAL = "noportal"
FLAG_NORECALL = "norecall"
PLAIN_DIRECTIONS = ("n", "s", "e", "w", "u", "d")
ANYWHERE = ("*", "**")
UNKNOWN_UID = "-1"
DEFAULT_LEVEL = 201
DEFAULT_TIER = 0
TIER_LEVELS = 10
SEARCHES: dict[str, tuple[str, ...]] = {
    "shops": ("shop", "bank"),
    "train": ("trainer",),
    "quest": ("questor",),
}
IMPORT_SLICE = 0.05
IMPORT_PROGRESS = 2000


def to_int(value: object) -> int:
    """Return a value as an int, or 0 when it is missing or not numeric."""
    if isinstance(value, (bool, int, float, str, bytes)):
        try:
            return int(value)
        except (ValueError, OverflowError):
            return 0
    return 0


def _maybe_int(value: object) -> int | None:
    """Return a value as an int, or None when it is not numeric."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str, bytes)):
        return None
    try:
        return int(value)
    except (ValueError, OverflowError):
        return None


def room_uid(info: object) -> str | None:
    """Return the uid of a room.info message, or None for a nomap room or a bad message."""
    if not isinstance(info, dict):
        return None
    num = _maybe_int(info.get("num"))
    if num is None or num in (0, -1):
        return None
    return str(num)


def _exit_uid(value: object) -> str:
    """Return the uid of an exit target; anything not a real room is unexplored."""
    num = _maybe_int(value)
    if num is None or num in (0, -1):
        return UNKNOWN_UID
    return str(num)


def room_from_gmcp(info: Mapping[str, Any], name: str, flags: list[str]) -> dict[str, Any]:
    """Return the core room dict of a room.info message; name is already stripped of colours."""
    coord = info.get("coord")
    coord = coord if isinstance(coord, dict) else {}
    exits = info.get("exits")
    exits = exits if isinstance(exits, dict) else {}
    return {
        "uid": room_uid(info),
        "name": name,
        "area": info.get("zone"),
        "terrain": info.get("terrain"),
        "x": _maybe_int(coord.get("x")),
        "y": _maybe_int(coord.get("y")),
        "z": 0,
        "details": {
            "details": info.get("details"),
            "coord_id": coord.get("id"),
            "cont": coord.get("cont"),
        },
        "flags": list(flags),
        "exits": {str(direction): _exit_uid(value) for direction, value in exits.items()},
    }


def area_from_gmcp(data: object) -> dict[str, Any] | None:
    """Return the area.add keyword arguments of a room.area message, or None."""
    if not isinstance(data, dict):
        return None
    uid = data.get("id")
    if uid is None or str(uid) == "":
        return None
    flags = data.get("flags")
    flag_list = [f.strip() for f in flags.split(",") if f.strip()] if isinstance(flags, str) else []
    return {
        "uid": str(uid),
        "name": str(data.get("name", "")),
        "flags": flag_list,
        "details": {k: v for k, v in data.items() if k not in ("id", "name", "flags")},
    }


def requirement_allowed(
    requirement: object,
    exit_dict: Mapping[str, Any],
    level: int | None,
    tier: int | None,
) -> bool:
    """Return True when a character of this level and tier may use the exit."""
    if not isinstance(requirement, dict):
        return False
    wanted: list[int] = []
    for key in ("level", "tier"):
        value = requirement.get(key, 0)
        if isinstance(value, bool) or not isinstance(value, int):
            return False
        wanted.append(value)
    wanted_level, wanted_tier = wanted
    have_tier = DEFAULT_TIER if tier is None else tier
    have_level = DEFAULT_LEVEL if level is None else level
    if exit_dict.get("fromuid") in ANYWHERE:
        have_level += TIER_LEVELS * have_tier
    return have_tier >= wanted_tier and have_level >= wanted_level


def steps_to_commands(steps: list[dict[str, Any]]) -> list[str]:
    """Turn walk steps into commands, joining plain directions into `run` speedwalks."""
    commands: list[str] = []
    run: list[str] = []

    def flush() -> None:
        if not run:
            return
        if len(run) == 1:
            commands.append(run[0])
        else:
            body = ""
            index = 0
            while index < len(run):
                end = index
                while end < len(run) and run[end] == run[index]:
                    end += 1
                count = end - index
                body += (str(count) if count > 1 else "") + run[index]
                index = end
            commands.append(f"run {body}")
        run.clear()

    for step in steps:
        direction = str(step.get("dir", ""))
        if direction in PLAIN_DIRECTIONS and step.get("fromuid") not in ANYWHERE:
            run.append(direction)
        else:
            flush()
            commands.append(direction)
    flush()
    return commands


def mismatch_lines(uid: str, differences: Mapping[str, Any]) -> list[str]:
    """Return the client lines that report a room mismatch."""
    lines = [f"Mapper: room {uid} differs from the map"]
    purge_room = f"#bp.client.mapper.purge -r {uid}"
    area = differences.get("area")
    if area:
        old, new = area
        lines.append(f"  area {old} -> {new}")
        lines.append(f"  to drop the old area: #bp.client.mapper.purge -a {old}")
        lines.append(f"  to drop this room: {purge_room}")
    exits = differences.get("exits")
    if exits:
        for direction, (old, new) in exits.items():
            before = "none" if old is None else old
            after = "none" if new is None else new
            lines.append(f"  {direction}: {before} -> {after}")
        lines.append(f"  to drop this room: {purge_room}")
    return lines


def detail_matches(details: object, wanted: Iterable[str]) -> list[str]:
    """Return the capitalised items of a room's detail list that are in wanted.

    The detail list is the comma separated ``details["details"]`` text; items are compared
    stripped and lowercased. Anything that is not a dict with a text value matches nothing.
    """
    if not isinstance(details, dict):
        return []
    text = details.get("details")
    if not isinstance(text, str):
        return []
    wanted_set = {w.lower() for w in wanted}
    items = (item.strip().lower() for item in text.split(","))
    return [item.capitalize() for item in items if item in wanted_set]


def search_lines(title: str, rows: Iterable[tuple[str, str, str, str]]) -> list[str]:
    """Return a search table: the title, a header, and one line per (uid, name, area, found)."""
    return [title, "uid | name | area | found", *(" | ".join(row) for row in rows)]


def stored_room_with_flags(
    stored: Mapping[str, Any], extra_flags: Iterable[str]
) -> dict[str, Any] | None:
    """Return the stored room as a room.add dict with extra_flags added, or None if it has them all.

    The dict has no ``exits`` and no ``note``, so adding it leaves the exits and the mismatch
    check alone.
    """
    flags = list(stored.get("flags") or [])
    missing = [flag for flag in extra_flags if flag not in flags]
    if not missing:
        return None
    return {
        "uid": stored.get("uid"),
        "name": stored.get("name"),
        "area": stored.get("area"),
        "terrain": stored.get("terrain"),
        "x": stored.get("x"),
        "y": stored.get("y"),
        "z": stored.get("z"),
        "details": stored.get("details"),
        "flags": [*flags, *missing],
    }
