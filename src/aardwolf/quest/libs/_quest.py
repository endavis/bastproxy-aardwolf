"""Constants and the state helper of the quest plugin. No bastproxy imports."""

from collections.abc import Mapping
from typing import Any

EVENT_GMCP_QUEST = "ev_libs.net.mud_gmcp_comm.quest"
PREFIX = "ev_plugins.aardwolf.quest_"

ACTION_EVENTS: dict[str, str] = {
    "ready": f"{PREFIX}ready",
    "start": f"{PREFIX}start",
    "killed": f"{PREFIX}killed",
    "comp": f"{PREFIX}comp",
    "fail": f"{PREFIX}failed",
    "timeout": f"{PREFIX}failed",
    "status": f"{PREFIX}status",
    "reset": f"{PREFIX}reset",
}

_STATE_KEYS = {
    "starttime": "the time the quest started, in seconds since the epoch",
    "finishtime": "the time the quest ended, or -1",
    "killedtime": "the time the target was killed, or -1",
    "mobname": "the name of the target",
    "mobarea": "the area of the target",
    "mobroom": "the room of the target",
    "stimer": "the timer of the quest from the start message, in minutes",
    "level": "the total level of the character when the quest started",
    "failed": "1 when the quest failed, else 0",
}

EVENTS: dict[str, dict[str, Any]] = {
    f"{PREFIX}ready": {
        "description": ["raised when the MUD says a quest can be taken"],
        "arg_descriptions": {},
    },
    f"{PREFIX}start": {
        "description": ["raised when a quest starts, with the reset quest state"],
        "arg_descriptions": dict(_STATE_KEYS),
    },
    f"{PREFIX}killed": {
        "description": ["raised when the target of the quest is killed, with the quest state"],
        "arg_descriptions": dict(_STATE_KEYS),
    },
    f"{PREFIX}comp": {
        "description": ["raised when a quest is completed, with the quest state"],
        "arg_descriptions": {
            **_STATE_KEYS,
            "...": "plus every key of the GMCP comp message, such as qp, totqp, tp and gold",
        },
    },
    f"{PREFIX}failed": {
        "description": ["raised when a quest fails or times out, with the quest state"],
        "arg_descriptions": dict(_STATE_KEYS),
    },
    f"{PREFIX}status": {
        "description": ["raised with the GMCP status message of the quest"],
        "arg_descriptions": {"...": "the keys of the GMCP comm.quest status message"},
    },
    f"{PREFIX}reset": {
        "description": ["raised when the MUD resets the quest timer"],
        "arg_descriptions": {},
    },
}


def start_state(data: Mapping[str, Any], now: float, level: int) -> dict[str, Any]:
    """Return the quest state for a start message, without changing the message."""
    return {
        "starttime": now,
        "finishtime": -1,
        "killedtime": -1,
        "mobname": data.get("targ", ""),
        "mobarea": data.get("area", ""),
        "mobroom": data.get("room", ""),
        "stimer": data.get("timer", -1),
        "level": level,
        "failed": 0,
    }
