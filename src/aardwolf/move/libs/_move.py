"""Constants and helpers of the move plugin. No bastproxy imports."""

import copy
from collections.abc import Mapping
from typing import Any

PLUGIN_ID = "plugins.aardwolf.move"
EVENT_GMCP_ROOM = "ev_libs.net.mud_gmcp_room.info"
EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"
EVENT_MOVE_ROOM = "ev_plugins.aardwolf.move_room"
GMCP_ROOM = "room.info"
UNKNOWN = "unknown"

EVENTS: dict[str, dict[str, Any]] = {
    EVENT_MOVE_ROOM: {
        "description": ["raised when the character moves to another room"],
        "arg_descriptions": {
            "from": "the GMCP room.info of the room left",
            "to": "the GMCP room.info of the room entered",
            "direction": "the exit of the old room that leads to the new one, or unknown",
        },
    },
}


def room_num(room: object) -> object | None:
    """Return the num of a room.info message, or None when it is not a dict with a num."""
    if isinstance(room, dict) and "num" in room:
        num: object = room["num"]
        return num
    return None


def find_direction(last: Mapping[str, Any], room: Mapping[str, Any]) -> str:
    """Return the last exit of the old room that leads to the new room, else unknown."""
    exits = last.get("exits")
    direction = UNKNOWN
    if isinstance(exits, dict):
        num = room.get("num")
        for key, value in exits.items():
            if value == num:
                direction = key
    return direction


def move_payload(last: Mapping[str, Any] | None, room: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return the move_room payload, or None when there was no move."""
    if last is None or room_num(last) == room_num(room):
        return None
    return {
        "from": copy.deepcopy(dict(last)),
        "to": copy.deepcopy(dict(room)),
        "direction": find_direction(last, room),
    }
