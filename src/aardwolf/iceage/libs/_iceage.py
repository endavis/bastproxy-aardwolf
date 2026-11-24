"""Constants, regexes and helpers of the iceage plugin. No bastproxy imports."""

from typing import Any, NamedTuple

PLUGIN_ID = "plugins.aardwolf.iceage"
PREFIX = "ev_plugins.aardwolf.iceage_"
EVENT_ICEAGE = f"{PREFIX}iceage"
EVENT_REBOOT = f"{PREFIX}reboot"

ICEAGE_REGEX = r"^.* An Ice Age Approaches - (?P<minutes>\d+) minutes?.*$"
REBOOT_REGEX = r"^.* Aardwolf will [rR]eboot (?:.* )?in (?P<minutes>\d+) minutes?.*$"

_MINUTES = {"minutes": "the minutes left before it happens"}

EVENTS: dict[str, dict[str, Any]] = {
    EVENT_ICEAGE: {
        "description": ["raised for each Ice Age countdown line, with the minutes left"],
        "arg_descriptions": dict(_MINUTES),
    },
    EVENT_REBOOT: {
        "description": ["raised for each reboot countdown line, with the minutes left"],
        "arg_descriptions": dict(_MINUTES),
    },
}


class TriggerSpec(NamedTuple):
    """A trigger the plugin adds: its name, regex and the event its match raises."""

    name: str
    regex: str
    event: str


TRIGGERS: tuple[TriggerSpec, ...] = (
    TriggerSpec("iceage", ICEAGE_REGEX, EVENT_ICEAGE),
    TriggerSpec("reboot", REBOOT_REGEX, EVENT_REBOOT),
)


def minutes(value: object) -> int | None:
    """Return ``value`` when it is an int of 0 or more (not a bool), else None."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value
