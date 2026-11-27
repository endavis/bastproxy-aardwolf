"""Constants and the state helper of the quest plugin. No bastproxy imports."""

from collections.abc import Mapping
from typing import Any

EVENT_GMCP_QUEST = "ev_libs.net.mud_gmcp_comm.quest"

# the values are event suffixes; the plugin builds the full names from its plugin id
ACTION_EVENTS: dict[str, str] = {
    "ready": "ready",
    "start": "start",
    "killed": "killed",
    "comp": "comp",
    "fail": "failed",
    "timeout": "failed",
    "status": "status",
    "reset": "reset",
}

# the core web plugin APIs, used by name because a plugin never imports another plugin
WEB_PROVIDER_ADD = "plugins.core.web:web.provider.add"
WEB_PROVIDER_CHANGED = "plugins.core.web:web.provider.changed.raise"
PROVIDER_CURRENT = "current"

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

_COMP_KEYS = {
    "action": "the GMCP action, comp",
    "qp": "the quest points of the comp message",
    "double": "the double quest point part of the comp message",
    "daily": "the daily part of the comp message",
    "totqp": "the total quest points of the comp message",
    "gold": "the gold of the comp message",
    "tierqp": "the tier quest point part of the comp message",
    "mccp": "the MCCP part of the comp message",
    "lucky": "the lucky part of the comp message",
    "opk": "the open PK part of the comp message",
    "hardcore": "the hardcore part of the comp message",
    "tp": "the trivia points of the comp message",
    "trains": "the trains of the comp message",
    "pracs": "the practices of the comp message",
    "completed": "the number of quests the character has completed, from the comp message",
    "wait": "the minutes until the next quest can be taken, from the comp message",
}

EVENTS: dict[str, dict[str, Any]] = {
    "ready": {
        "description": ["raised when the MUD says a quest can be taken"],
        "arg_descriptions": {},
    },
    "start": {
        "description": ["raised when a quest starts, with the reset quest state"],
        "arg_descriptions": dict(_STATE_KEYS),
    },
    "killed": {
        "description": ["raised when the target of the quest is killed, with the quest state"],
        "arg_descriptions": dict(_STATE_KEYS),
    },
    "comp": {
        "description": ["raised when a quest is completed, with the quest state"],
        "arg_descriptions": {**_STATE_KEYS, **_COMP_KEYS},
    },
    "failed": {
        "description": ["raised when a quest fails or times out, with the quest state"],
        "arg_descriptions": dict(_STATE_KEYS),
    },
    "status": {
        "description": ["raised with the GMCP status message of the quest"],
        "arg_descriptions": {
            "action": "the GMCP action, status",
            "status": "the status of the quest, as the MUD reports it",
            "wait": "the minutes until the next quest can be taken, from the status message",
        },
    },
    "reset": {
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


def quest_current(state: Mapping[str, Any], now: float) -> dict[str, Any]:
    """Return the current quest for the web page: target, area, room, end and the outcome.

    ``active`` is True from the start message until the quest is completed or fails. The end
    time is the start plus the timer of the start message, and the time left only counts
    while the quest is active. An empty state gives None values and False flags.
    """
    name = state.get("mobname") or None
    failed = bool(state.get("failed"))
    finished = state.get("finishtime", -1) != -1
    active = name is not None and not finished and not failed
    starttime = state.get("starttime") or None
    stimer = state.get("stimer", -1)
    endtime = None
    if starttime is not None and isinstance(stimer, int | float) and stimer >= 0:
        endtime = starttime + stimer * 60
    return {
        "active": active,
        "target": name,
        "area": (state.get("mobarea") or None) if name else None,
        "room": (state.get("mobroom") or None) if name else None,
        "starttime": starttime,
        "endtime": endtime,
        "timeleft": max(0, int(endtime - now)) if active and endtime is not None else None,
        "killed": state.get("killedtime", -1) != -1,
        "complete": finished and not failed,
        "failed": failed,
    }
