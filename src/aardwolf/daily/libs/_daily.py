"""Constants, regexes and helpers of the daily plugin. No bastproxy imports."""

import re
import time
from typing import Any, NamedTuple

PLUGIN_ID = "plugins.aardwolf.daily"
EVENT_AVAILABLE = f"ev_{PLUGIN_ID}_available"

EVENTS: dict[str, dict[str, Any]] = {
    EVENT_AVAILABLE: {
        "description": ["raised when the daily blessing can be received"],
        "arg_descriptions": {},
    },
}

WAIT_REGEX = r"^You can receive a new daily blessing in (?P<wait>.+)\.$"
READY_REGEX = r"^You are ready to receive a new daily blessing\.$"
TOOK_REGEX = r"^You bow your head to Ayla and receive your daily blessing\.$"

TRIGGER_WAIT = "dailywait"
TRIGGER_READY = "dailynow"
TRIGGER_TOOK = "tookdaily"

DAILY_CMD = "daily"
ACTIVE_STATE = 3
# the wait after receiving a blessing, from the old plugin (not verified against the mud)
BLESSING_WAIT = 23 * 60 * 60
TIME_FORMAT = "%a, %d %b %Y %H:%M:%S"
TIMER_NAME = "dailyblessing"

_UNIT_SECONDS = {"hour": 3600, "minute": 60, "second": 1}
_PART = re.compile(r"(?P<count>\d+) (?P<unit>hour|minute|second)s?")
_SEPARATOR = re.compile(r",\s*|\s+and\s+")


class TriggerSpec(NamedTuple):
    """A trigger the plugin adds: its name and regex."""

    name: str
    regex: str


TRIGGERS: tuple[TriggerSpec, ...] = (
    TriggerSpec(TRIGGER_WAIT, WAIT_REGEX),
    TriggerSpec(TRIGGER_READY, READY_REGEX),
    TriggerSpec(TRIGGER_TOOK, TOOK_REGEX),
)


def parse_wait(text: object) -> int | None:
    """Return the seconds in a wait such as ``1 hour, 5 minutes and 7 seconds``.

    Any of hours, minutes and seconds may be missing, each is used once, and a bad
    text (or a non-str) gives None.
    """
    if not isinstance(text, str):
        return None
    seen: set[str] = set()
    total = 0
    for part in _SEPARATOR.split(text.strip()):
        found = _PART.fullmatch(part)
        if not found or found["unit"] in seen:
            return None
        seen.add(found["unit"])
        total += int(found["count"]) * _UNIT_SECONDS[found["unit"]]
    return total


def is_active_state(state: object) -> bool:
    """Return True when the GMCP character state is the active one (not a bool)."""
    return not isinstance(state, bool) and state == ACTIVE_STATE


def next_message(next_time: float | None, available: bool) -> str:
    """Return the line the ``next`` command shows."""
    if available:
        return "Your daily blessing is ready"
    if next_time is None:
        return "Please type daily to update plugin"
    return "Your next daily is at: " + time.strftime(TIME_FORMAT, time.localtime(next_time))
