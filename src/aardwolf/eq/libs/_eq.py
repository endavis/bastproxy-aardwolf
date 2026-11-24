"""Constants, regexes, parsers and command builders of the eq plugin. No bastproxy imports."""

import re
from collections.abc import Callable
from typing import Any, NamedTuple

from aardwolf.libs.itemu import OBJECTTYPESREV

PREFIX = "ev_plugins.aardwolf.eq_"
EVENT_WORN = f"{PREFIX}worn"
EVENT_REMOVED = f"{PREFIX}removed"
EVENT_INVENTORY_ADDED = f"{PREFIX}inventory_added"
EVENT_INVENTORY_REMOVED = f"{PREFIX}inventory_removed"
EVENT_PUT = f"{PREFIX}put"
EVENT_TAKEN = f"{PREFIX}taken"

# the disconnect event, listened to by name
EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"

# the eqdb plugin is optional: its API is used by name, and only when it exists
API_EQDB_SAVE = "plugins.aardwolf.eqdb:item.save"
API_A102_TOGGLE = "plugins.aardwolf.a102:option.toggle"
# Aardwolf option 102 feature 20: the {invmon} and {invitem} tags,
# the setting the "invmon" command toggles
INVMON_OPTION = "INVMONTAGS"

# the most lines hidden after the opening line, without an end tag; a big inventory can run to
# several hundred lines. mudcmds counts the opening line too, so the types get HIDE_MAX_LINES + 2
HIDE_MAX_LINES = 2000

# the names of the containers that are not a bag; a bag is named by the serial of its item
INVENTORY = "Inventory"
WORN = "Worn"
KEYRING = "Keyring"
VAULT = "Vault"
CONTAINER_ITYPE = OBJECTTYPESREV["container"]

# the keys eq keeps for where an item is; an identify never overwrites them, and eqdb reads
# "container" as the container detail, so the saved copy leaves them out
PLACE_KEYS = frozenset({"container", "origcontainer", "hasbeenided"})

GROUP_DATA = "data"

_ITEM = "the item as a dict, or None when the item is not known"
_SERIAL = "the serial of the item"
_CONTAINER = "the container: Inventory, Keyring, Vault, or the serial of a bag, as text"
_NO_ITEM_KEY = "the item as a dict"

EVENTS: dict[str, dict[str, Any]] = {
    EVENT_WORN: {
        "description": ["raised when an item is worn"],
        "arg_descriptions": {"item": _NO_ITEM_KEY, "location": "the wear slot it went to"},
    },
    EVENT_REMOVED: {
        "description": ["raised when an item is taken off and goes to the inventory"],
        "arg_descriptions": {"item": _NO_ITEM_KEY, "location": "the wear slot it came from"},
    },
    EVENT_INVENTORY_ADDED: {
        "description": ["raised when an item known to the plugin is added to the inventory"],
        "arg_descriptions": {"item": _NO_ITEM_KEY},
    },
    EVENT_INVENTORY_REMOVED: {
        "description": ["raised when an item leaves the inventory, or is consumed"],
        "arg_descriptions": {"item": _NO_ITEM_KEY},
    },
    EVENT_PUT: {
        "description": [
            "raised when an item is put into a container, or added to the inventory",
        ],
        "arg_descriptions": {"serial": _SERIAL, "container": _CONTAINER, "item": _ITEM},
    },
    EVENT_TAKEN: {
        "description": ["raised when an item is taken out of a container, a vault or the keyring"],
        "arg_descriptions": {"serial": _SERIAL, "container": _CONTAINER, "item": _ITEM},
    },
}


class TriggerSpec(NamedTuple):
    """A trigger the plugin adds: its name, regex, group suffix, state, omit and argtypes."""

    name: str
    regex: str
    group: str | None
    enabled: bool
    omit: bool
    argtypes: dict[str, Callable[[str], Any]] | None


_TAGS = "invdata|eqdata|keyring|vault"
# what Aardwolf answers to "vault data" for a character with no vault, instead of a vault block
NO_VAULT_REGEX = r"^You do not have a vault\. See 'help vault' for how to acquire one\.$"

TRIGGERS: tuple[TriggerSpec, ...] = (
    TriggerSpec(
        "eq_invmon",
        r"^\{invmon\}(?P<action>\d+),(?P<serial>\d+),(?P<container>-?\d+),(?P<location>-?\d+)$",
        None,
        True,
        True,
        {"action": int, "serial": int, "container": int, "location": int},
    ),
    # the invmon and invitem tags are for the plugin, so they are kept from the client
    TriggerSpec("eq_invitem", r"^\{invitem\}(?P<data>.*)$", None, True, True, None),
    TriggerSpec(
        "eq_data_start",
        rf"^\{{(?P<tag>{_TAGS})(?: (?P<cid>\d+))?\}}$",
        None,
        True,
        False,
        None,
    ),
    TriggerSpec("eq_data_end", rf"^\{{/(?P<tag>{_TAGS})\}}$", None, True, False, None),
    TriggerSpec(
        "eq_vaultcounts",
        r"^\{vaultcounts\}(?P<items>\d+),(?P<total>\d+),(?P<max>\d+)\{/vaultcounts\}$",
        None,
        True,
        False,
        {"items": int, "total": int, "max": int},
    ),
    TriggerSpec("eq_no_vault", NO_VAULT_REGEX, None, True, False, None),
    TriggerSpec("eq_data_line", r"^(?P<data>\s*\d+,.*)$", GROUP_DATA, False, False, None),
)


class TypeSpec(NamedTuple):
    """A mudcmds command type: its name, command, regex and the first line of its output.

    No type has a hide_end: each data command finishes at its end tag, and the hide window
    closes at the prompt after that, so the prompt is hidden too. Vault needs this anyway,
    since {vaultcounts} follows {/vault}.
    """

    cmdtype: str
    cmd: str
    regex: str
    hide_start: str


TYPE_WORN = TypeSpec("eq_worn", "eqdata", r"^eqdata$", r"^\{eqdata\}$")
TYPE_INVENTORY = TypeSpec("eq_inventory", "invdata", r"^invdata$", r"^\{invdata\}$")
TYPE_KEYRING = TypeSpec("eq_keyring", "keyring data", r"^keyring data$", r"^\{keyring\}$")
# the window also opens on the no-vault answer, which ends the command at once
TYPE_VAULT = TypeSpec(
    "eq_vault",
    "vault data",
    r"^vault data$",
    r"^(?:\{vault\}|You do not have a vault\. See 'help vault' for how to acquire one\.)$",
)
FIXED_TYPES: tuple[TypeSpec, ...] = (TYPE_WORN, TYPE_INVENTORY, TYPE_KEYRING, TYPE_VAULT)
_FIXED_BY_CID = {
    WORN: TYPE_WORN,
    INVENTORY: TYPE_INVENTORY,
    KEYRING: TYPE_KEYRING,
    VAULT: TYPE_VAULT,
}
CONTAINER_TYPE_PREFIX = "eq_container_"


def container_type(serial: int | str) -> TypeSpec:
    """Return the command type that reads the contents of a bag."""
    return TypeSpec(
        f"{CONTAINER_TYPE_PREFIX}{serial}",
        f"invdata {serial}",
        rf"^invdata {serial}$",
        rf"^\{{invdata {serial}\}}$",
    )


def type_for(cid: str) -> TypeSpec:
    """Return the command type that reads a container: a fixed one, or a bag's."""
    return _FIXED_BY_CID.get(cid) or container_type(cid)


def tag_container(tag: str, cid: str | None) -> str | None:
    """Return the container a data block starts for, or None for an unknown tag."""
    if tag == "invdata":
        return cid if cid else INVENTORY
    if cid:
        return None
    return {"eqdata": WORN, "keyring": KEYRING, "vault": VAULT}.get(tag)


# one line of eqdata, invdata, keyring data or vault data; the greedy name keeps its commas
ITEM_LINE_REGEX = re.compile(
    r"^\s*(?P<serial>\d+),(?P<shortflags>\w*),(?P<cname>.*),(?P<level>\d+),(?P<itype>\d+),"
    r"(?P<unique>[01]),(?P<wearslot>-?\d+),(?P<timer>-?\d+)$"
)
_CODES = r"(?:@x\d{1,3}|@[A-Za-z])*"
# the same line as colour coded text: codes may come before and after it, and the tag of an
# {invitem} line may come first
_COLOR_LINE_REGEX = re.compile(
    rf"^{_CODES}(?:\{{invitem\}})?{_CODES}\s*(?P<serial>\d+),(?P<shortflags>\w*),"
    rf"(?P<cname>.*),(?P<level>\d+),(?P<itype>\d+),(?P<unique>[01]),(?P<wearslot>-?\d+),"
    rf"(?P<timer>-?\d+){_CODES}$"
)
_INT_KEYS = ("serial", "level", "itype", "wearslot", "timer")


def parse_item_line(
    noansi: str, colorcoded: object, strip: Callable[[str], str]
) -> dict[str, Any] | None:
    """Parse an item line into a dict, or None when it is not one.

    ``cname`` is taken from the colour coded text when that matches too, else it is the plain
    name. The colour coded text escapes each literal ``@`` as ``@@``, so ``@@`` becomes ``@``
    and Aardwolf's own codes in the name stay codes. ``name`` is ``cname`` with the colour
    codes stripped by ``strip``.
    """
    match = ITEM_LINE_REGEX.match(noansi)
    if not match:
        return None
    item: dict[str, Any] = match.groupdict()
    for key in _INT_KEYS:
        item[key] = int(item[key])
    item["unique"] = item["unique"] == "1"
    if isinstance(colorcoded, str):
        colored = _COLOR_LINE_REGEX.match(colorcoded)
        if colored:
            item["cname"] = colored.group("cname").replace("@@", "@")
    item["name"] = strip(item["cname"])
    return item


def quote_arg(arg: str) -> str:
    """Quote an argument that holds a space, as the MUD wants it."""
    return f"'{arg}'" if " " in arg else arg


def get_command(cid: str, serial: int) -> str | None:
    """Return the command that takes an item out of a container, or None for the inventory."""
    if cid == WORN:
        return f"remove {serial}"
    if cid == KEYRING:
        return f"keyring get {serial}"
    if cid == VAULT:
        return f"vault get {serial}"
    if cid == INVENTORY:
        return None
    return f"get {serial} {cid}"


def put_command(cid: str, serial: int, location: str | None = None) -> str | None:
    """Return the command that puts an item into a container, or None for the inventory.

    ``location`` is the wear location name for Worn.
    """
    if cid == WORN:
        return f"wear {serial} {location}" if location else f"wear {serial}"
    if cid == KEYRING:
        return f"keyring put {serial}"
    if cid == VAULT:
        return f"vault put {serial}"
    if cid == INVENTORY:
        return None
    return f"put {serial} {cid}"


def to_serial(value: object) -> int | None:
    """Return a serial as an int, or None when the value is not a serial."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdecimal():
        return int(value)
    return None
