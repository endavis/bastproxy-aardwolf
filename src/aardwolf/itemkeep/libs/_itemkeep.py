"""Pure helpers for the itemkeep plugin: the names, the reply patterns and the keep decision."""

from collections.abc import Callable, Mapping
from typing import NamedTuple

from aardwolf._libs.itemu import OBJECTTYPES

# the names of the eq events itemkeep listens to; copied, because a plugin never imports another
EVENT_EQ_INVENTORY_ADDED = "ev_plugins.aardwolf.eq_inventory_added"
EVENT_EQ_TAKEN = "ev_plugins.aardwolf.eq_taken"
EVENT_EQ_REMOVED = "ev_plugins.aardwolf.eq_removed"
EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"

# the most lines hidden after the opening line; mudcmds counts the opening line too
HIDE_MAX = 10  # a kept reply is 4 lines, plus blank lines and the prompt

TYPE_KEEP = "itemkeep_keep"
KEEP_CMD = "keep"
KEEP_REGEX = r"^keep \d+$"
TIMEOUT_EVENT = "cmd_{}_timeout"
GROUP_REPLY = "reply"

# The first line Aardwolf answers a keep with, recorded on a live character: kept, already kept,
# and a serial the character does not have. A reply that matches none is shown, and the command
# timeout frees the queue.
KEEP_REPLIES: tuple[str, ...] = (
    r"^Keep status added to .+\.$",
    r"^Your .+ is already kept\. Use 'unkeep' to remove it\.$",
    r"^You do not have that item\.$",
)
# the first line of the reply opens the hide window
KEEP_HIDE_START = "(?:" + "|".join(KEEP_REPLIES) + ")"


class TriggerSpec(NamedTuple):
    """A trigger the plugin adds: its name, regex and the group it is in."""

    name: str
    regex: str
    group: str


# the group is off until a queued keep starts
TRIGGERS: tuple[TriggerSpec, ...] = (TriggerSpec("itemkeep_reply", KEEP_HIDE_START, GROUP_REPLY),)

# every type but "none", which is itype 0 and is not an item type
KEEP_TYPES: tuple[str, ...] = tuple(name for name in OBJECTTYPES if name != "none")


def setting_name(type_name: str) -> str:
    """Return the setting name of a type; a space cannot be named in the set command."""
    return type_name.replace(" ", "_")


# setting name to its help text
SETTINGS: dict[str, str] = {setting_name(name): f"autokeep {name}" for name in KEEP_TYPES}


def type_name(itype: object) -> str | None:
    """Return the name of an item type, or None for a bool, a non-int, 0 or out of range."""
    if isinstance(itype, bool) or not isinstance(itype, int):
        return None
    if itype <= 0 or itype >= len(OBJECTTYPES):
        return None
    return OBJECTTYPES[itype]


def is_kept(item: Mapping[str, object]) -> bool:
    """Return True when the item's short flags show it is kept."""
    return "K" in str(item.get("shortflags") or "")


def keep_serial(item: Mapping[str, object]) -> int | None:
    """Return the item's serial when it is a positive int, else None."""
    serial = item.get("serial")
    if isinstance(serial, bool) or not isinstance(serial, int) or serial <= 0:
        return None
    return serial


def should_keep(item: Mapping[str, object], enabled: Callable[[str], bool]) -> int | None:
    """Return the serial to keep, or None when the item needs no keep.

    ``enabled`` takes a setting name and says whether autokeep is on for it.
    """
    name = type_name(item.get("itype"))
    if name is None or not enabled(setting_name(name)):
        return None
    if is_kept(item):
        return None
    return keep_serial(item)
