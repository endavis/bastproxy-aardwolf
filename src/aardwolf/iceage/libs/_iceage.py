"""Constants, regexes and helpers of the iceage plugin. No bastproxy imports."""

from typing import Any, NamedTuple

# the suffixes of the events this plugin raises; the plugin builds the full names from its
# plugin id
SUFFIX_ICEAGE = "iceage"
SUFFIX_REBOOT = "reboot"

ICEAGE_REGEX = r"^.* An Ice Age Approaches - (?P<minutes>\d+) minutes?.*$"
REBOOT_REGEX = r"^.* Aardwolf will [rR]eboot (?:.* )?in (?P<minutes>\d+) minutes?.*$"

_MINUTES = {"minutes": "the minutes left before it happens"}

EVENTS: dict[str, dict[str, Any]] = {
    SUFFIX_ICEAGE: {
        "description": ["raised for each Ice Age countdown line, with the minutes left"],
        "arg_descriptions": dict(_MINUTES),
    },
    SUFFIX_REBOOT: {
        "description": ["raised for each reboot countdown line, with the minutes left"],
        "arg_descriptions": dict(_MINUTES),
    },
}


class TriggerSpec(NamedTuple):
    """A trigger the plugin adds: its name, regex and the suffix of the event its match raises."""

    name: str
    regex: str
    event: str


TRIGGERS: tuple[TriggerSpec, ...] = (
    TriggerSpec("iceage", ICEAGE_REGEX, SUFFIX_ICEAGE),
    TriggerSpec("reboot", REBOOT_REGEX, SUFFIX_REBOOT),
)


def minutes(value: object) -> int | None:
    """Return ``value`` when it is an int of 0 or more (not a bool), else None."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value
