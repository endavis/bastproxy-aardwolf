"""Constants, regexes and state helpers of the gq plugin. No bastproxy imports."""

from collections.abc import Callable
from typing import Any, NamedTuple

from aardwolf._libs import aardu

# the suffixes of the events this plugin raises; the plugin builds the full names from its
# plugin id
SUFFIX_DECLARED = "declared"
SUFFIX_JOINED = "joined"
SUFFIX_STARTED = "started"
SUFFIX_CANCELLED = "cancelled"
SUFFIX_MOBSLEFT = "mobsleft"
SUFFIX_WON = "won"
SUFFIX_COMPLETED = "completed"
SUFFIX_DONE = "done"
SUFFIX_AVAILABLE = "available"
SUFFIX_NOTAVAILABLE = "notavailable"

EVENT_MOBK_KILL = "ev_plugins.aardwolf.mobk_kill"
EVENT_CHAR_ACTIVE = "ev_libs.api_character_active"
EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"

CMDTYPE = "gqcheck"
CMD = "gq check"
CMD_REGEX = "^gq check$"

WATCH_NAME = "gq_check"
WATCH_REGEX = r"^(gq|gqu|gque|gques|gquest) (c|ch|che|chec|check)$"  # codespell:ignore chec

GROUP_CHECK = "gqcheck"
GROUP_IN = "gqin"
GROUP_REW = "gqrew"

_STATE_KEYS = {
    "mobs": "the mobs of the gquest when it was first checked, each with name, location and num",
    "trains": "the trains rewarded",
    "pracs": "the practices rewarded",
    "gold": "the gold rewarded",
    "tp": "the trivia points rewarded",
    "qp": "the quest points rewarded",
    "qpmobs": "the quest points earned for the mobs killed",
    "level": "the total level of the character when the gquest was joined",
    "starttime": "the time the gquest started, in seconds since the epoch",
    "finishtime": "the time the gquest finished, 0 until then",
    "length": "the length of the gquest",
    "won": "1 when the character won, else 0",
    "completed": "1 when the character finished in extended time, else 0",
    "extended": "1 when the gquest went into extended time, else 0",
}

_MOBSLEFT = "the mobs left, each with name, nocolorname, location and num"

EVENTS: dict[str, dict[str, Any]] = {
    SUFFIX_DECLARED: {
        "description": ["raised when a global quest is declared"],
        "arg_descriptions": {
            "gqnum": "the number of the global quest",
            "lowlev": "the lowest level that may join",
            "highlev": "the highest level that may join",
        },
    },
    SUFFIX_JOINED: {
        "description": ["raised when the character joins a global quest"],
        "arg_descriptions": {"gqnum": "the number of the global quest"},
    },
    SUFFIX_STARTED: {
        "description": ["raised when a global quest starts"],
        "arg_descriptions": {"gqnum": "the number of the global quest"},
    },
    SUFFIX_CANCELLED: {
        "description": ["raised when a global quest is cancelled"],
        "arg_descriptions": {"gqnum": "the number of the global quest"},
    },
    SUFFIX_MOBSLEFT: {
        "description": ["raised after a gq check and when a target mob is killed"],
        "arg_descriptions": {"mobsleft": _MOBSLEFT},
    },
    SUFFIX_WON: {
        "description": ["raised when the character wins a global quest, with a copy of the state"],
        "arg_descriptions": dict(_STATE_KEYS),
    },
    SUFFIX_COMPLETED: {
        "description": [
            "raised when the character finishes a global quest in extended time,",
            "with a copy of the state",
        ],
        "arg_descriptions": dict(_STATE_KEYS),
    },
    SUFFIX_DONE: {
        "description": [
            "raised when a global quest ends otherwise, after mobs were killed,",
            "with a copy of the state",
        ],
        "arg_descriptions": dict(_STATE_KEYS),
    },
    SUFFIX_AVAILABLE: {
        "description": ["raised when a global quest is declared and not over"],
        "arg_descriptions": {},
    },
    SUFFIX_NOTAVAILABLE: {
        "description": ["raised when no global quest is declared any more"],
        "arg_descriptions": {},
    },
}


class TriggerSpec(NamedTuple):
    """A trigger the plugin adds: its name, regex, group suffix, state and argtypes."""

    name: str
    regex: str
    group: str | None
    enabled: bool
    argtypes: dict[str, Callable[[str], Any]] | None


TRIGGERS: tuple[TriggerSpec, ...] = (
    TriggerSpec(
        "gq_declared",
        r"^Global Quest: Global quest \# *(?P<gqnum>\d*) has been "
        r"declared for levels (?P<lowlev>\d*) to (?P<highlev>\d*)( - .*)*\.$",
        None,
        True,
        {"gqnum": int},
    ),
    TriggerSpec(
        "gq_joined",
        r"^You have now joined Global Quest \# *(?P<gqnum>\d*)\. .*$",
        None,
        True,
        {"gqnum": int},
    ),
    TriggerSpec(
        "gq_started",
        r"^Global Quest: Global quest \# *(?P<gqnum>\d*) for levels .* "
        r"to .* has now started\.$",
        None,
        True,
        {"gqnum": int},
    ),
    TriggerSpec(
        "gq_cancelled",
        r"^Global Quest: Global quest \# *(?P<gqnum>\d*) has been "
        r"cancelled due to lack of (activity|participants)\.$",
        None,
        True,
        {"gqnum": int},
    ),
    TriggerSpec(
        "gq_quit",
        r"^You are no longer part of Global Quest \# *(?P<gqnum>\d*) "
        r"and will be unable to rejoin.$",
        None,
        True,
        {"gqnum": int},
    ),
    TriggerSpec(
        "gq_note",
        r"^INFO: New post \#(?P<bdnum>.*) in forum Gquest from "
        r"Aardwolf Subj: Lvl (?P<low>.*) to (?P<high>.*) - "
        r"Global quest \# *(?P<gqnum>\d*)$",
        None,
        True,
        {"gqnum": int},
    ),
    TriggerSpec(
        "gq_maxkills",
        r"^You have reached the "
        r"maximum (.*) kills for which you can earn quest points this level\.$",
        None,
        True,
        None,
    ),
    TriggerSpec("gq_none", r"^You are not in a global quest\.$", GROUP_CHECK, False, None),
    TriggerSpec(
        "gq_item",
        r"^You still have to kill (?P<num>[\d]*) \* "
        r"(?P<mob>.*?) \((?P<location>.*?)\)(|\.)$",
        GROUP_CHECK,
        False,
        {"num": int},
    ),
    TriggerSpec(
        "gq_notstarted",
        r"^Global Quest \# *(?P<gqnum>\d*) has not yet started.",
        GROUP_CHECK,
        False,
        {"gqnum": int},
    ),
    TriggerSpec(
        "gq_wins",
        r"^You may win .* more gquests* at this level\.$",
        GROUP_CHECK,
        False,
        None,
    ),
    TriggerSpec(
        "gq_mobdead",
        r"^Congratulations, that was one of the GLOBAL QUEST mobs!$",
        GROUP_IN,
        False,
        None,
    ),
    TriggerSpec(
        "gq_extended",
        r"^Global Quest: Global Quest \# *(?P<gqnum>\d*) will go "
        r"into extended time for 3 more minutes.$",
        GROUP_IN,
        False,
        {"gqnum": int},
    ),
    TriggerSpec(
        "gq_won",
        r"^You were the first to complete this quest!$",
        GROUP_IN,
        False,
        None,
    ),
    TriggerSpec(
        "gq_extfin",
        r"^You have finished this global quest.$",
        GROUP_IN,
        False,
        None,
    ),
    TriggerSpec(
        "gq_wonannounce",
        r"^Global Quest: Global Quest \# *(?P<gqnum>\d+) has been won "
        r"by (?P<winner>.+?) - .+ win.$",
        None,
        True,
        {"gqnum": int},
    ),
    TriggerSpec(
        "gq_reward",
        r"^\s*Reward of (?P<amount>\d+) (?P<type>.+) .+ added\.$",
        GROUP_REW,
        False,
        {"amount": int},
    ),
)


def new_state(level: int) -> dict[str, Any]:
    """Return the state of a new global quest: nothing rewarded, no mobs."""
    return {
        "mobs": [],
        "trains": 0,
        "pracs": 0,
        "gold": 0,
        "tp": 0,
        "qp": 0,
        "qpmobs": 0,
        "level": level,
        "starttime": 0,
        "finishtime": 0,
        "length": 0,
        "won": 0,
        "completed": 0,
        "extended": 0,
    }


def new_mob(name: str, location: str, num: int) -> dict[str, Any]:
    """Return a target mob; the trigger matches the name without colour."""
    return {"name": name, "nocolorname": name, "location": location, "num": num}


def count_down(mobs: list[dict[str, Any]], name: str) -> bool:
    """Count down the first mob called ``name``; return False when there is none.

    A mob with more than one kill left loses one; the last kill removes it. The old plugin
    skipped the mob at index 0 because it tested the index for truth, and counted down every
    mob with the name. The kill carries only the name, not the location, so with the name at
    several locations the first is a guess; the plugin queues a check then (see
    ``name_has_several_locations``), as cp does.
    """
    for index, mob in enumerate(mobs):
        if mob.get("name") != name:
            continue
        if int(mob.get("num", 1)) > 1:
            mob["num"] = int(mob["num"]) - 1
        else:
            del mobs[index]
        return True
    return False


def name_has_several_locations(mobs: list[dict[str, Any]], name: str) -> bool:
    """Return True when the mobs called ``name`` are at more than one distinct location."""
    locations = {str(mob.get("location", "")) for mob in mobs if mob.get("name") == name}
    return len(locations) > 1


def reward_key(rtype: str) -> str | None:
    """Return the state key of a reward type, or None when the type is unknown."""
    return aardu.REWARDTABLE.get(rtype)
