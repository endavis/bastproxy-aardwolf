"""Constants, regexes and state helpers of the cp plugin. No bastproxy imports."""

import re
from collections.abc import Callable, Iterable
from typing import Any, NamedTuple

from aardwolf.libs import aardu

PREFIX = "ev_plugins.aardwolf.cp_"
EVENT_MOBSORIG = f"{PREFIX}mobsorig"
EVENT_MOBSLEFT = f"{PREFIX}mobsleft"
EVENT_COMP = f"{PREFIX}comp"
EVENT_FAILED = f"{PREFIX}failed"

EVENT_MOBK_KILL = "ev_plugins.aardwolf.mobk_kill"
EVENT_CHAR_ACTIVE = "ev_libs.api_character_active"
EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"
# the questmasters come from the aardwolf config plugin; its API and event are used by name,
# because a plugin never imports another plugin's package
EVENT_QUESTMASTERS_CHANGED = "ev_plugins.aardwolf.config_questmasters_changed"
API_QUESTMASTERS_GET = "plugins.aardwolf.config:questmasters.get"
# the id of the core trigger that fires for every line, which belongs to plugins.core.triggers
ALL_LINES_ID = "t_plugins.core.triggers_all"

CMDTYPE = "cpcheck"
CMD = "campaign check"
CMD_REGEX = "^campaign check$"

GROUP_CHECK = "cpcheck"
GROUP_IN = "cpin"
GROUP_REW = "cprew"
GROUP_DONE = "cpdone"

BONUS_REGEX = (
    r"^You receive (?P<bonus>\d+) quest points bonus for your first campaign completed today.$"
)
COUNT_REGEX = r"^You have completed (\d*) campaigns today.$"

_STATE_KEYS = {
    "oncp": "True while the character is on a campaign",
    "cantake": "True when the character may take a campaign at this level",
    "shtime": "the time until the next campaign can be taken, or None",
    "mobs": "the mobs of the campaign when it was first checked",
    "mobsleft": "the mobs left, each with name, nocolorname, location and mobdead",
    "trains": "the trains rewarded",
    "pracs": "the practices rewarded",
    "gold": "the gold rewarded",
    "tp": "the trivia points rewarded",
    "qp": "the quest points rewarded",
    "bonusqp": "the bonus quest points for the first campaign of the day, else 0",
    "failed": "1 when the campaign was cleared, else 0",
    "starttime": "the time the campaign started, in seconds since the epoch",
    "finishtime": "the time the campaign finished, 0 until then",
    "level": "the total level of the character when the campaign started",
}

EVENTS: dict[str, dict[str, Any]] = {
    EVENT_MOBSORIG: {
        "description": ["raised the first time the mobs of a campaign are known, with a copy"],
        "arg_descriptions": {"mobsleft": _STATE_KEYS["mobsleft"]},
    },
    EVENT_MOBSLEFT: {
        "description": ["raised when the mobs left of a campaign are known or change"],
        "arg_descriptions": {"mobsleft": _STATE_KEYS["mobsleft"]},
    },
    EVENT_COMP: {
        "description": ["raised when a campaign is complete and its rewards are known"],
        "arg_descriptions": dict(_STATE_KEYS),
    },
    EVENT_FAILED: {
        "description": ["raised when a campaign is cleared, with a copy of the state"],
        "arg_descriptions": dict(_STATE_KEYS),
    },
}


NEW_TRIGGER = "cp_new"
# matches nothing: used when there are no questmasters
NEVER_REGEX = r"(?!)"
_NEW_TEXT = r" tells you 'Type 'campaign info' to see what you must kill\.'$"
_DEFAULT_QUESTMASTERS = ("Commander Barcett", "A QuestoR", "Questor")


def new_campaign_regex(questmasters: Iterable[str]) -> str:
    """Return the regex of the new-campaign tell, which only the given questmasters send."""
    names = [re.escape(name) for name in questmasters if name]
    if not names:
        return NEVER_REGEX
    return "^(?:" + "|".join(names) + ")" + _NEW_TEXT


class TriggerSpec(NamedTuple):
    """A trigger the plugin adds: its name, regex, group suffix, state, omit and argtypes."""

    name: str
    regex: str
    group: str | None
    enabled: bool
    omit: bool
    argtypes: dict[str, Callable[[str], Any]] | None


_DASHES = "^" + "-" * 62 + "$"

TRIGGERS: tuple[TriggerSpec, ...] = (
    TriggerSpec(
        NEW_TRIGGER,
        new_campaign_regex(_DEFAULT_QUESTMASTERS),
        None,
        True,
        False,
        None,
    ),
    TriggerSpec(
        "cp_none",
        "^You are not currently on a campaign.$",
        GROUP_CHECK,
        False,
        True,
        None,
    ),
    TriggerSpec(
        "cp_time",
        "^You have (?P<time>.*) to finish this campaign.$",
        GROUP_CHECK,
        False,
        True,
        None,
    ),
    TriggerSpec(
        "cp_mob",
        r"^You still have to kill \* (?P<mob>.*) \((?P<location>.*?)(?P<dead> - Dead|)\)$",
        GROUP_CHECK,
        False,
        True,
        None,
    ),
    TriggerSpec(
        "cp_scramble",
        "Note: One or more target names in this campaign might be slightly scrambled.$",
        GROUP_CHECK,
        False,
        True,
        None,
    ),
    TriggerSpec(
        "cp_needtolevel",
        "^You will have to level before you can go on another campaign.$",
        GROUP_IN,
        False,
        False,
        None,
    ),
    TriggerSpec(
        "cp_cantake",
        "^You may take a campaign at this level.$",
        GROUP_IN,
        False,
        False,
        None,
    ),
    TriggerSpec(
        "cp_shnext",
        "^You cannot take another campaign for (?P<time>.*).$",
        GROUP_IN,
        False,
        False,
        None,
    ),
    TriggerSpec(
        "cp_mobdead",
        "^Congratulations, that was one of your CAMPAIGN mobs!$",
        GROUP_IN,
        False,
        False,
        None,
    ),
    TriggerSpec(
        "cp_complete",
        "^CONGRATULATIONS! You have completed your campaign.$",
        GROUP_IN,
        False,
        False,
        None,
    ),
    TriggerSpec("cp_clear", "^Campaign cleared.$", GROUP_IN, False, False, None),
    TriggerSpec(
        "cp_reward",
        r"^\s*Reward of (?P<amount>\d+) (?P<type>.+) .+ added.$",
        GROUP_REW,
        False,
        False,
        {"amount": int},
    ),
    TriggerSpec("cp_compdone", _DASHES, GROUP_DONE, False, False, None),
)


def new_state(now: float, level: int) -> dict[str, Any]:
    """Return the state of a new campaign: nothing rewarded, no mobs, on a campaign."""
    return {
        "mobs": [],
        "mobsleft": [],
        "trains": 0,
        "pracs": 0,
        "gold": 0,
        "tp": 0,
        "qp": 0,
        "bonusqp": 0,
        "failed": 0,
        "level": level,
        "starttime": now,
        "finishtime": 0,
        "oncp": True,
        "cantake": False,
        "shtime": None,
    }


def new_mob(name: str, location: str, dead: object) -> dict[str, Any]:
    """Return a mob of the campaign; the trigger matches the name without colour."""
    return {"name": name, "nocolorname": name, "location": location, "mobdead": bool(dead)}


def remove_mob(mobs: list[dict[str, Any]], name: str) -> bool:
    """Delete the first mob called ``name``; return False when there is none.

    The old plugin skipped the mob at index 0 because it tested the index for truth.
    """
    found: int | None = None
    for index, mob in enumerate(mobs):
        if mob.get("name") == name:
            found = index
            break
    if found is None:
        return False
    del mobs[found]
    return True


def reward_key(rtype: str) -> str | None:
    """Return the state key of a reward type, or None when the type is unknown."""
    return aardu.REWARDTABLE.get(rtype)


def bonus_qp(line: str) -> int | None:
    """Return the bonus quest points of the first-campaign-of-the-day line, else None."""
    match = re.match(BONUS_REGEX, line)
    return int(match.group("bonus")) if match else None


def is_count_line(line: str) -> bool:
    """Return True for the line that counts the campaigns completed today."""
    return re.match(COUNT_REGEX, line) is not None
