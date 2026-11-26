"""Pure constants and helpers for the hunger plugin. No bastproxy imports."""

from collections.abc import Mapping, Sequence
from typing import NamedTuple

# the events the plugin listens to; copied, because a plugin never imports another
EVENT_EQ_TAKEN = "ev_plugins.aardwolf.eq_taken"
EVENT_EQ_PUT = "ev_plugins.aardwolf.eq_put"
EVENT_EQ_INVENTORY_ADDED = "ev_plugins.aardwolf.eq_inventory_added"
EVENT_MOVE_ROOM = "ev_plugins.aardwolf.move_room"
EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"
EVENT_WALK_STARTED = "ev_plugins.client.mapper_walk_started"
EVENT_WALK_DONE = "ev_plugins.client.mapper_walk_done"
EVENT_WALK_FAILED = "ev_plugins.client.mapper_walk_failed"

# the APIs of other plugins and of the framework
API_EXISTS = "libs.api:api.exists"
API_ITEM_GET = "plugins.aardwolf.eq:item.get"
API_ITEM_FIND = "plugins.aardwolf.eq:item.find.by.name"
API_ITEM_FETCH = "plugins.aardwolf.eq:item.fetch"
API_ITEM_PUT = "plugins.aardwolf.eq:item.put"
API_WALK_START = "plugins.client.mapper:walk.start"
API_WALK_GET = "plugins.client.mapper:walk.get"
API_ROOM_GET = "plugins.client.mapper:room.get"
GMCP_ROOM_NUM = "room.info.num"

# the names eq gives the places an item can be in
INVENTORY = "Inventory"
SKIPPED_PLACES = frozenset({"Worn", "Vault", "Keyring"})
WALK_BUSY_STATES = frozenset({"searching", "walking"})

SETTING_DRINK = "drink"
SETTING_CONTAINER = "container"
SETTING_COOLDOWN = "cooldown"
SETTING_FILLROOM = "fillroom"
SETTING_FILLOBJECT = "fillobject"
COOLDOWN = 60
GROUP = "Hunger"
GROUP_REPLY = "hunger_reply"
TIMER_FETCH = "hunger_fetch"
TIMER_REPLY = "hunger_reply"
# seconds to wait for eq to take the container out, and for the mud to answer a drink or fill
PENDING_TIMEOUT = 10

DRINK_CMD = "drink {item}"
FILL_CMD = "fill {item}"
# TODO(live check #174): the two argument form of fill is not confirmed on Aardwolf yet
FILL_FROM_CMD = "fill {item} {source}"

TRIGGER_DRANK = "hunger_drank"
TRIGGER_EMPTY = "hunger_empty"
TRIGGER_FILLED = "hunger_filled"
TRIGGER_NOSOURCE = "hunger_nosource"


class TriggerSpec(NamedTuple):
    """A trigger the plugin adds: its name and regex."""

    name: str
    regex: str


# the log shows the "## " after the colour is stripped
_PREFIX = r"^(?:##\s*)?"

# the six stage lines of hunger and thirst, which all mean "drink"
STAGE_TRIGGERS: tuple[TriggerSpec, ...] = (
    TriggerSpec("hunger_stage1", _PREFIX + r"You start to feel (hungry|thirsty)\.$"),
    TriggerSpec(
        "hunger_stage2", _PREFIX + r"You are very (hungry|thirsty); your healing is reduced\.$"
    ),
    TriggerSpec(
        "hunger_stage3",
        _PREFIX + r"You are (starving|dehydrated); your healing is greatly reduced\.$",
    ),
)

# the replies to a drink or fill this plugin sent; on only while one is awaited
REPLY_TRIGGERS: tuple[TriggerSpec, ...] = (
    TriggerSpec(TRIGGER_DRANK, r"^You drink (?P<liquid>.+) from (?P<container>.+)\.$"),
    TriggerSpec(TRIGGER_EMPTY, r"^(?P<container>.+) is empty\.$"),
    TriggerSpec(TRIGGER_FILLED, r"^You fill (?P<container>.+) with (?P<liquid>.+)\.$"),
    TriggerSpec(TRIGGER_NOSOURCE, r"^There is no liquid source here\.$"),
)


def parse_item_setting(value: object) -> int | str | None:
    """Return the container setting as a serial, a name piece, or None when it is empty."""
    text = str(value).strip() if value is not None else ""
    if not text:
        return None
    return int(text) if text.isascii() and text.isdigit() else text


def choose_item(items: Sequence[Mapping[str, object]]) -> int | None:
    """Return the serial of the item to use from the items a name matched, or None.

    An item in the inventory wins, then one in a bag (its container is the serial of the bag, all
    digits). One worn, in the vault or on the keyring is skipped.
    """
    bag: int | None = None
    for item in items:
        serial = item.get("serial")
        if isinstance(serial, bool) or not isinstance(serial, int):
            continue
        place = str(item.get("container") or "")
        if place == INVENTORY:
            return serial
        if bag is None and place.isascii() and place.isdigit():
            bag = serial
    return bag


def room_num(value: object) -> str | None:
    """Return a GMCP room num as the text of the mapper uid, or None when it is not a room."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value) if value > 0 else None
    if isinstance(value, str):
        text = value.strip()
        if text.isascii() and text.isdigit() and int(text) > 0:
            return str(int(text))
    return None


def cooldown_ok(last: float | None, now: float, cooldown: float) -> bool:
    """Return True when no attempt was made yet, or the cooldown has run out."""
    return last is None or now - last >= cooldown


def should_autofill(room: str | None, fillroom: str, empty: bool, busy: bool) -> bool:
    """Return True when entering ``room`` should fill the container.

    That needs a fill room, the character in it, the last drink found the container empty, and no
    fill walk or fill already under way.
    """
    return bool(fillroom) and room == fillroom and empty and not busy


def fill_command(item: int, source: str = "") -> str:
    """Return the fill command for an item, with the source object when there is one."""
    if source:
        return FILL_FROM_CMD.format(item=item, source=source)
    return FILL_CMD.format(item=item)
