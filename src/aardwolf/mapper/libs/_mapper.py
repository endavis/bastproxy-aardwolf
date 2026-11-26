"""Constants and helpers of the mapper plugin. No bastproxy imports."""

import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlencode

from aardwolf._libs.itemu import OBJECTTYPESREV

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
NORECALL_REGEX = r"^You cannot (recall|return home) from this room\."
# the direction of an exit from * that uses a portal item, followed by the item serial
PORTAL_PREFIX = "eqportal:"
# the wear slot of a portal item the character has bought, and the one a portal is held in
# otherwise; a plain wear puts the portal in the right one. Both are eq's wear location names.
PORTAL_WEARLOC = "portal"
HELD_WEARLOC = "hold"
PORTAL_ITYPE = OBJECTTYPESREV["portal"]
# the eq plugin is a soft dependency: its APIs are used by name, and only when they exist
API_EQ_ITEM_GET = "plugins.aardwolf.eq:item.get"
API_EQ_WORN_GET = "plugins.aardwolf.eq:eq.worn.get"
API_EQ_ITEM_PUT = "plugins.aardwolf.eq:item.put"
API_EQ_ITEM_EQUIP = "plugins.aardwolf.eq:item.equip"
API_EQ_ITEM_UNEQUIP = "plugins.aardwolf.eq:item.unequip"
API_EQ = (
    API_EQ_ITEM_GET,
    API_EQ_WORN_GET,
    API_EQ_ITEM_PUT,
    API_EQ_ITEM_EQUIP,
    API_EQ_ITEM_UNEQUIP,
)
FLAG_NOPORTAL = "noportal"
FLAG_NORECALL = "norecall"
# mirrors the core mapper's IGNORE_EXITS_FLAG, which a plugin cannot import
FLAG_IGNORE_EXITS = "ignoreexits"
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
# the name of the setting that defaults to CEXIT_TIMEOUT
SETTING_CEXIT_TIMEOUT = "cexittimeout"
MAX_WAIT = 40
RECALL_COMMANDS = ("recall", "home", "hom")
IMPORT_SLICE = 0.05
# most rows of one map.batch.add call; mirrors the core mapper's BATCH_LIMIT, which a plugin
# cannot import, and a call over it is refused
IMPORT_BATCH = 1000
WEB_ROUTE_ADD = "plugins.core.web:web.route.add"
WEB_ROUTE_REMOVE = "plugins.core.web:web.route.remove"
# the pages of the core client mapper that a room or area cell links to
CORE_ROOM_PAGE = "/client/mapper/room"
CORE_AREA_PAGE = "/client/mapper/area"
PLACE_KINDS = (*SEARCHES, "notes")
# longest `area` query value a page accepts; a real area id is far shorter
MAX_AREA_ARG = 100
PORTAL_COLUMNS: list[dict[str, str]] = [
    {"name": "number", "label": "#", "type": "int"},
    {"name": "kind", "label": "Kind", "type": "text"},
    {"name": "area", "label": "Area", "type": "text"},
    {"name": "name", "label": "Name", "type": "text"},
    {"name": "to", "label": "To", "type": "text"},
    {"name": "command", "label": "Command", "type": "text"},
    {"name": "level", "label": "Level", "type": "int"},
]
CEXIT_COLUMNS: list[dict[str, str]] = [
    {"name": "uid", "label": "Room", "type": "text"},
    {"name": "name", "label": "Name", "type": "text"},
    {"name": "area", "label": "Area", "type": "text"},
    {"name": "command", "label": "Command", "type": "text"},
    {"name": "to", "label": "To", "type": "text"},
    {"name": "level", "label": "Level", "type": "int"},
]
PLACE_COLUMNS: list[dict[str, str]] = [
    {"name": "uid", "label": "Room", "type": "text"},
    {"name": "name", "label": "Name", "type": "text"},
    {"name": "area", "label": "Area", "type": "text"},
    {"name": "found", "label": "Found", "type": "text"},
]


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


def serial_arg(text: object) -> int | None:
    """Return the serial a portal command names: a single word of digits above 0, else None."""
    if not isinstance(text, str):
        return None
    word = text.strip()
    if not (word.isascii() and word.isdecimal()):
        return None
    serial = int(word)
    return serial if serial > 0 else None


def portal_marker(serial: int) -> str:
    """Return the exit direction that stands for the portal item with this serial."""
    return f"{PORTAL_PREFIX}{serial}"


def portal_serial(direction: object) -> int | None:
    """Return the serial of an item portal direction, or None for any other direction."""
    if not isinstance(direction, str) or not direction.startswith(PORTAL_PREFIX):
        return None
    return serial_arg(direction[len(PORTAL_PREFIX) :])


def portal_requirement(serial: int, level: int) -> dict[str, Any]:
    """Return the requirement of an item portal; the level is left out when 0 or less.

    The serial rides in the requirement because the core mapper asks the requirement
    callback only for an exit that has one.
    """
    requirement: dict[str, Any] = {"serial": serial}
    if level > 0:
        requirement["level"] = level
    return requirement


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


@dataclass(frozen=True)
class PortalStep:
    """A walk step that uses the portal item with this serial."""

    serial: int


def movement_plan(steps: list[dict[str, Any]]) -> list[tuple[float, list[str]] | PortalStep]:
    """Turn walk steps into (delay seconds, commands) chunks and the portal item steps.

    The steps between two item portals are turned into chunks as `movement_chunks` does.
    """
    plan: list[tuple[float, list[str]] | PortalStep] = []
    segment: list[dict[str, Any]] = []
    for step in steps:
        serial = portal_serial(step.get("dir")) if step.get("fromuid") in ANYWHERE else None
        if serial is None:
            segment.append(step)
            continue
        plan.extend(movement_chunks(segment))
        segment = []
        plan.append(PortalStep(serial))
    plan.extend(movement_chunks(segment))
    return plan


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


def _pair(value: object) -> tuple[object, object] | None:
    """Return an (old, new) pair, or None when the value is not one."""
    if isinstance(value, (tuple, list)) and len(value) == 2:
        return value[0], value[1]
    return None


def _shown(value: object, escape: Callable[[str], str]) -> str:
    """Return a value as client text: None is ``none``, anything else is escaped."""
    return "none" if value is None else escape(str(value))


def mismatch_lines(
    uid: str, differences: Mapping[str, Any], escape: Callable[[str], str] = str
) -> list[str]:
    """Return the client lines that report a room mismatch.

    ``differences`` is the core mapper's ``room_mismatch`` payload. A malformed entry is
    ignored, since the payload comes from another plugin. ``escape`` makes a value safe to show.
    """
    lines = [f"Mapper: room {uid} differs from the map"]
    for key in ("name", "terrain", "x", "y", "z"):
        pair = _pair(differences.get(key))
        if pair:
            lines.append(f"  {key}: {_shown(pair[0], escape)} -> {_shown(pair[1], escape)}")
    details = differences.get("details")
    if isinstance(details, Mapping):
        for key, value in details.items():
            pair = _pair(value)
            if pair:
                lines.append(
                    f"  details {escape(str(key))}: "
                    f"{_shown(pair[0], escape)} -> {_shown(pair[1], escape)}"
                )
    area = _pair(differences.get("area"))
    if area:
        lines.append(f"  area {_shown(area[0], escape)} -> {_shown(area[1], escape)}")
    held_exit = False
    exits = differences.get("exits")
    if isinstance(exits, Mapping):
        for direction, value in exits.items():
            pair = _pair(value)
            if pair:
                held_exit = held_exit or pair[0] is not None
                lines.append(
                    f"  exit {escape(str(direction))}: "
                    f"{_shown(pair[0], escape)} -> {_shown(pair[1], escape)}"
                )
    if area or held_exit:
        lines.append(f"  to accept the held changes: #bp.client.mapper.accept {uid}")
    if area:
        lines.append(f"  to drop the old area: #bp.client.mapper.purge -a {area[0]}")
    if held_exit:
        lines.append(f"  if this room's exits vary: #bp.client.mapper.ignoreexits {uid}")
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


class WebTableQuery(Protocol):
    """The part of the core web plugin's table query that the pages read."""

    @property
    def sort(self) -> str | None:
        """The column to sort by."""

    @property
    def descending(self) -> bool:
        """True for a descending sort."""

    @property
    def filters(self) -> Mapping[str, str | int | float]:
        """The column filters."""

    @property
    def offset(self) -> int:
        """The rows before the page."""

    @property
    def count(self) -> int:
        """The rows of a page."""


class WebRequest(Protocol):
    """The part of the core web plugin's request that the pages read."""

    @property
    def query(self) -> Mapping[str, str]:
        """The first value of each query key."""

    @property
    def table(self) -> WebTableQuery | None:
        """The validated table query of a table route."""


def room_link(uid: str, text: str) -> dict[str, str]:
    """Return a link cell to the core mapper page of a room; `text` is already escaped."""
    return {"text": text, "href": f"{CORE_ROOM_PAGE}?{urlencode({'uid': uid})}"}


def area_link(uid: str, text: str) -> dict[str, str]:
    """Return a link cell to the core mapper page of an area; `text` is already escaped."""
    return {"text": text, "href": f"{CORE_AREA_PAGE}?{urlencode({'uid': uid})}"}


def area_arg(value: str) -> str | None:
    """Return the `area` query value as an area id, `here` when empty, None when too long."""
    area = value.strip().lower()
    if len(area) > MAX_AREA_ARG:
        return None
    return area or "here"


def _cell_text(cell: object) -> str:
    """Return the text of a cell: the text of a link cell, else the cell as a string."""
    if isinstance(cell, Mapping):
        return str(cell.get("text", ""))
    return str(cell)


def _cell_key(cell: object, kind: str) -> tuple[int, int, str]:
    """Return the sort key of a cell: a number by value, a text of digits (a room number) by
    value before other text, other text by lower case."""
    shown = _cell_text(cell)
    if kind == "int":
        return (0, to_int(cell), "")
    if shown.isascii() and shown.isdigit():
        return (0, int(shown), "")
    return (1, 0, shown.casefold())


def _cell_matches(cell: object, kind: str, wanted: str | int | float) -> bool:
    """Return True when a cell passes a column filter: a number is equal, text is contained."""
    if kind == "text":
        return str(wanted).casefold() in _cell_text(cell).casefold()
    return to_int(cell) == wanted


def table_view(
    rows: Sequence[Sequence[object]],
    columns: Sequence[Mapping[str, str]],
    *,
    sort: str | None,
    descending: bool,
    filters: Mapping[str, str | int | float],
    offset: int,
    count: int,
) -> tuple[list[Sequence[object]], int]:
    """Filter, sort and page rows; return the page and the number of rows that match.

    A link cell is read by its text. The sort is stable, also when descending.
    """
    kinds = {column["name"]: column["type"] for column in columns}
    index = {column["name"]: place for place, column in enumerate(columns)}
    kept = [
        row
        for row in rows
        if all(
            _cell_matches(row[index[name]], kinds[name], wanted) for name, wanted in filters.items()
        )
    ]
    if sort is not None:
        place, kind = index[sort], kinds[sort]
        kept.sort(key=lambda row: _cell_key(row[place], kind), reverse=descending)
    return list(kept[offset : offset + count]), len(kept)
