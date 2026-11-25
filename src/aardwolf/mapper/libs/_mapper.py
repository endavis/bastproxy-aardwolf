"""Constants and helpers of the mapper plugin. No bastproxy imports."""

import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

PLUGIN_ID = "plugins.aardwolf.mapper"
MAPPER = "plugins.client.mapper"
EVENT_GMCP_ROOM = "ev_libs.net.mud_gmcp_room.info"
EVENT_GMCP_AREA = "ev_libs.net.mud_gmcp_room.area"
EVENT_MOVE_ROOM = "ev_plugins.aardwolf.move_room"
EVENT_ROOM_MISMATCH = "ev_plugins.client.mapper_room_mismatch"
EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"
EVENT_WALK_FAILED = "ev_plugins.client.mapper_walk_failed"
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
COMMAND_SEPARATOR = ";"
WAIT_REGEX = r"^wait\((\d*\.?\d+)\)$"
WAIT_PREFIX_REGEX = r"^wait\(.*\)$"
CEXIT_TIMEOUT = 5
CEXIT_MIN_TIMEOUT = 2
CEXIT_MAX_TIMEOUT = 40
MAX_WAIT = 40
RECALL_COMMANDS = ("recall", "home", "hom")
IMPORT_SLICE = 0.05
# most rows of one map.batch.add call; mirrors the core mapper's BATCH_LIMIT, which a plugin
# cannot import, and a call over it is refused
IMPORT_BATCH = 1000


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


def _run_command(run: list[str]) -> str:
    """Return the command that walks plain directions: one direction, or a `run` speedwalk."""
    if len(run) == 1:
        return run[0]
    body = ""
    index = 0
    while index < len(run):
        end = index
        while end < len(run) and run[end] == run[index]:
            end += 1
        count = end - index
        body += (str(count) if count > 1 else "") + run[index]
        index = end
    return f"run {body}"


def split_command(text: str) -> list[str | float]:
    """Split a command on `;` into commands and waits; a `wait(N)` becomes the float N.

    This is the lenient form used when walking: a segment that is not a valid wait is sent
    as text, empty segments are dropped, and a wait over MAX_WAIT is capped.
    """
    parts: list[str | float] = []
    for segment in text.split(COMMAND_SEPARATOR):
        segment = segment.strip()
        if not segment:
            continue
        match = re.match(WAIT_REGEX, segment, re.IGNORECASE)
        if match:
            parts.append(min(float(match.group(1)), float(MAX_WAIT)))
        else:
            parts.append(segment)
    return parts


def parse_command(text: str) -> list[str | float] | None:
    """Split a command for storing; None for an empty command or a bad wait.

    A bad wait is any `wait(...)` segment that is not a number over 0 and at most MAX_WAIT.
    """
    parts = split_command(text)
    if not parts:
        return None
    for segment in text.split(COMMAND_SEPARATOR):
        segment = segment.strip()
        if not re.match(WAIT_PREFIX_REGEX, segment, re.IGNORECASE):
            continue
        match = re.match(WAIT_REGEX, segment, re.IGNORECASE)
        if match is None or not 0 < float(match.group(1)) <= MAX_WAIT:
            return None
    return parts


def total_wait(parts: Iterable[str | float]) -> float:
    """Return the seconds a split command waits in total."""
    return sum(part for part in parts if isinstance(part, float))


def command_chunks(parts: Iterable[str | float]) -> list[tuple[float, list[str]]]:
    """Group commands into (delay seconds, commands) chunks; each wait starts a new chunk."""
    chunks: list[tuple[float, list[str]]] = []
    delay = 0.0
    commands: list[str] = []
    seen = False
    for part in parts:
        seen = True
        if isinstance(part, float):
            chunks.append((delay, commands))
            delay, commands = part, []
        else:
            commands.append(part)
    if seen:
        chunks.append((delay, commands))
    return chunks


def movement_chunks(steps: list[dict[str, Any]]) -> list[tuple[float, list[str]]]:
    """Turn walk steps into (delay seconds, commands) chunks.

    Plain directions are joined into `run` speedwalks. Any other direction is split on `;`,
    and each `wait(N)` starts a chunk that is sent N seconds after the one before it.
    """
    parts: list[str | float] = []
    run: list[str] = []
    for step in steps:
        direction = str(step.get("dir", ""))
        if direction in PLAIN_DIRECTIONS and step.get("fromuid") not in ANYWHERE:
            run.append(direction)
            continue
        if run:
            parts.append(_run_command(run))
            run.clear()
        parts.extend(split_command(direction))
    if run:
        parts.append(_run_command(run))
    return command_chunks(parts)


def steps_to_commands(steps: list[dict[str, Any]]) -> list[str]:
    """Turn walk steps into commands, joining plain directions into `run` speedwalks.

    The waits of a custom exit are left out; `movement_chunks` keeps them.
    """
    return [command for _, commands in movement_chunks(steps) for command in commands]


def is_cexit(exit_dict: Mapping[str, Any]) -> bool:
    """Return True for a custom exit: not a plain direction and not a portal or recall."""
    return exit_dict.get("fromuid") not in ANYWHERE and exit_dict.get("dir") not in PLAIN_DIRECTIONS


def requirement_level(requirement: object) -> int:
    """Return the level of an exit requirement for display; 0 when it has none."""
    if not isinstance(requirement, dict):
        return 0
    return to_int(requirement.get("level"))


def is_recall_command(command: str) -> bool:
    """Return True when a portal command is the recall command."""
    return command.strip().lower() in RECALL_COMMANDS


def portal_sort_key(portal: Mapping[str, Any], room: Mapping[str, Any] | None) -> tuple[Any, ...]:
    """Return the sort key of a portal: the area of its room, the room number, the command."""
    area = str(room.get("area") or "") if room else ""
    touid = str(portal.get("touid"))
    return (area, to_int(touid), touid, str(portal.get("dir")))


def resolve_portal(portals: Sequence[Mapping[str, Any]], ref: str) -> Mapping[str, Any] | None:
    """Return the portal a `#N` number or an exact command names, or None."""
    ref = ref.strip()
    if ref.startswith("#"):
        number = _maybe_int(ref[1:])
        if number is None or not 1 <= number <= len(portals):
            return None
        return portals[number - 1]
    for portal in portals:
        if portal.get("dir") == ref:
            return portal
    return None


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


def table_lines(title: str, header: Sequence[str], rows: Iterable[Sequence[str]]) -> list[str]:
    """Return a table: the title, a header line, and one ` | ` joined line per row."""
    return [title, " | ".join(header), *(" | ".join(row) for row in rows)]


def search_lines(title: str, rows: Iterable[tuple[str, str, str, str]]) -> list[str]:
    """Return a search table: the title, a header, and one line per (uid, name, area, found)."""
    return table_lines(title, ("uid", "name", "area", "found"), rows)
