"""Pure helpers for the itemid plugin: the specs, the two readers and the item box."""

import copy
import re
import textwrap
from collections.abc import Callable, Mapping
from typing import Any, NamedTuple

from aardwolf._libs.itemu import OBJECTTYPES, OBJECTTYPESREV, WEARLOCS, parse_item_data

# the APIs of the plugins itemid calls, by name: a plugin never imports another plugin
API_EQ_ITEM_GET = "plugins.aardwolf.eq:item.get"
API_EQ_ITEM_FETCH = "plugins.aardwolf.eq:item.fetch"
API_EQ_ITEM_PUT = "plugins.aardwolf.eq:item.put"
API_EQ_IDENTIFY_ADD = "plugins.aardwolf.eq:item.identify.add"
# eqdb and skills are optional: they are called only when the API exists
API_EQDB_ITEM_GET = "plugins.aardwolf.eqdb:item.get"
API_EQDB_ITEM_SAVE = "plugins.aardwolf.eqdb:item.save"
API_SKILL_GET = "plugins.aardwolf.skills:skill.get"

EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"
EVENT_EQ_PUT = "ev_plugins.aardwolf.eq_put"
EVENT_EQ_WORN = "ev_plugins.aardwolf.eq_worn"
EVENT_EQ_INVENTORY_REMOVED = "ev_plugins.aardwolf.eq_inventory_removed"
SUFFIX_IDENTIFIED = "identified"

EVENTS: dict[str, dict[str, Any]] = {
    SUFFIX_IDENTIFIED: {
        "description": ["raised when an item has been identified and put back where it was"],
        "arg_descriptions": {
            "serial": "the serial of the item, as an int",
            "item": "the identified item as a dict, in the shape eqdb saves",
        },
    },
}

INVENTORY = "Inventory"
WORN = "Worn"

# the most lines hidden after the opening line; mudcmds counts the opening line too
HIDE_MAX = 200

GROUP_INVDETAILS = "invdetails"
GROUP_IDENTIFY = "identify"

TYPE_INVDETAILS = "itemid_invdetails"
TYPE_IDENTIFY = "itemid_identify"
TIMEOUT_EVENT = "cmd_{}_timeout"


class TypeSpec(NamedTuple):
    """A mudcmds command type: its name, command, regex and the first line of its output.

    No type has a hide_end: the window closes at the prompt after the command finishes, so the
    prompt is hidden too, as eq does.
    """

    cmdtype: str
    cmd: str
    regex: str
    hide_start: str


TYPES: tuple[TypeSpec, ...] = (
    TypeSpec(TYPE_INVDETAILS, "invdetails", r"^invdetails \d+$", r"^\{invdetails\}$"),
    TypeSpec(TYPE_IDENTIFY, "identify", r"^identify \d+$", r"^\+-+\+\s*$"),
)


class TriggerSpec(NamedTuple):
    """A trigger the plugin adds: its name, regex and the group it is in."""

    name: str
    regex: str
    group: str


# the group of each is off until a queued command starts
TRIGGERS: tuple[TriggerSpec, ...] = (
    TriggerSpec("itemid_invdetails_start", r"^\{invdetails\}$", GROUP_INVDETAILS),
    TriggerSpec(
        "itemid_invdetails_line",
        r"^\{(?P<header>[^/}][^}]*)\}(?P<data>.+)$",
        GROUP_INVDETAILS,
    ),
    TriggerSpec("itemid_invdetails_end", r"^\{/invdetails\}$", GROUP_INVDETAILS),
    TriggerSpec("itemid_identify_line", r"^(?P<line>.*)$", GROUP_IDENTIFY),
)

# invdetails headers whose data is a name and a value
_MOD_HEADERS = ("statmod", "resistmod", "skillmod")
# invdetails headers that can come more than once
_LIST_HEADERS = ("enchant", "tempmod")


def to_int(value: object) -> int:
    """Return a value as an int, or raise ValueError."""
    if isinstance(value, bool):
        raise ValueError(value)
    if isinstance(value, int):
        return value
    return int(str(value).strip())


class InvdetailsReader:
    """Collect the ``{header}data`` lines of one invdetails reply into a dict."""

    def __init__(self) -> None:
        """Start empty."""
        self._item: dict[str, Any] = {}

    def start(self) -> None:
        """Begin a new reply; nothing of the one before is kept."""
        self._item = {}

    def line(self, header: str, data: str) -> None:
        """Add one line.

        Raises:
            ValueError: the header is unknown, or the data does not fit the header.
        """
        if header == "eqdata":
            msg = "layout 'eqdata' is not an invdetails layout"
            raise ValueError(msg)
        parsed = parse_item_data(data, header)
        if header == "invheader":
            self._item.update(parsed)
        elif header in _MOD_HEADERS:
            self._item.setdefault(header, {})[parsed["name"]] = to_int(parsed["value"])
        elif header in _LIST_HEADERS:
            self._item.setdefault(header, []).append(parsed)
        else:
            self._item[header] = parsed

    @property
    def has_header(self) -> bool:
        """True when the invheader line was read."""
        return "serial" in self._item

    def result(self) -> dict[str, Any]:
        """Return a copy of what was read."""
        return copy.deepcopy(self._item)


_DIVIDER = re.compile(r"^\+-+\+\s*$")
_BOX = re.compile(r"^\|(?P<data>.*)\|\s*$")
# what an identify has that invdetails does not
NEEDED = ("keywords", "foundat", "material", "leadsto", "affectmod", "reward")
# the labels that invdetails already gave
SKIP = frozenset(
    {
        "name",
        "serial",
        "itype",
        "level",
        "weight",
        "worth",
        "wearable",
        "score",
        "flags",
        "ownedby",
        "statmods",
        "resistmods",
        "weapontype",
        "inflicts",
        "specials",
        "capacity",
        "holding",
        "totweight",
        "clanitem",
        "spells",
        "healrate",
        "duration",
    }
)
_ALIASES = {"type": "itype", "id": "serial", "affectmods": "affectmod"}


class IdentifyReader:
    """Read the box an identify prints, and say when it ends.

    Every line before the first divider is ignored, so a prompt left over from the command
    before cannot start or end it. After it a divider or a ``|...|`` line is data, and any
    other line, a blank line or a prompt, ends the read.
    """

    def __init__(self) -> None:
        """Start empty."""
        self.reset()

    def reset(self) -> None:
        """Forget everything read."""
        self._dividers = 0
        self._section = ""
        self.fields: dict[str, str] = {}
        self.notes: list[str] = []
        self.unknown: list[str] = []

    @property
    def started(self) -> bool:
        """True after the first divider."""
        return self._dividers > 0

    def feed(self, text: str) -> bool:
        """Read one plain text line; return True when the identify has ended."""
        if _DIVIDER.match(text):
            self._dividers += 1
            self._section = ""
            return False
        if not self._dividers:
            return False
        box = _BOX.match(text)
        if box is None:
            return True
        self._data(box.group("data"))
        return False

    def _data(self, data: str) -> None:
        """Read the text between the two bars of a line."""
        value = data.strip()
        # a label has a character right after the space that follows the bar
        if ":" in data and len(data) > 1 and data[1] != " ":
            head, _, rest = data.partition(":")
            label = "".join(head.split()).lower().rstrip(".")
            if label:
                self._section = _ALIASES.get(label, label)
                value = rest.strip()
        elif value.startswith(":"):
            # a continuation line may repeat the colon of the label column
            value = value[1:].strip()
        section = self._section
        if section in NEEDED:
            if value:
                self.fields[section] = (
                    f"{self.fields[section]} {value}" if section in self.fields else value
                )
            return
        if not section:
            if value:
                self.notes.append(value)
            return
        if section not in SKIP and section not in self.unknown:
            self.unknown.append(section)

    def result(self) -> dict[str, Any]:
        """Return the fields read, with the notes as a list when there are any."""
        out: dict[str, Any] = dict(self.fields)
        if self.notes:
            out["notes"] = list(self.notes)
        return out


def _split(text: object, separator: str | None) -> list[str]:
    """Split text into its non-empty, stripped parts; a list is returned as it is."""
    if isinstance(text, list | tuple):
        return [str(part).strip() for part in text if str(part).strip()]
    return [part.strip() for part in str(text or "").split(separator) if part.strip()]


def build_item(details: Mapping[str, Any], idfields: Mapping[str, Any]) -> dict[str, Any]:
    """Join the invdetails result and the identify fields into one dict in eqdb's shape.

    Keywords are split on whitespace, flags and affect mods on ``", "``, the reward and the
    notes are wrapped in the dicts eqdb saves. A missing keywords or flags field is not an error.
    """
    item = copy.deepcopy(dict(details))
    item["keywords"] = _split(idfields.get("keywords"), None)
    item["flags"] = _split(item.get("flags"), ",")
    for key in ("foundat", "material", "leadsto"):
        if idfields.get(key):
            item[key] = str(idfields[key])
    if idfields.get("reward"):
        item["reward"] = {"rtext": str(idfields["reward"])}
    notes = idfields.get("notes")
    if notes:
        item["notes"] = {"ntext": " ".join(notes) if isinstance(notes, list) else str(notes)}
    affects = _split(idfields.get("affectmod"), ",")
    if affects:
        item["affectmod"] = affects
    return item


# the item box

WIDTH = 67
DIVIDER = "+" + "-" * (WIDTH - 2) + "+"
_LINELEN = 50
_STATS = (
    "Damage roll",
    "Hit roll",
    "Strength",
    "Intelligence",
    "Wisdom",
    "Dexterity",
    "Constitution",
    "Luck",
    "Saves",
    "Hit points",
    "Mana",
    "Moves",
)
_PHYSICAL = ("Bash", "Pierce", "Slash", "All physical", "All magic", "Disease", "Poison")
_MAGICAL = (
    "Acid",
    "Air",
    "Cold",
    "Earth",
    "Electric",
    "Energy",
    "Fire",
    "Holy",
    "Light",
    "Magic",
    "Mental",
    "Negative",
    "Shadow",
    "Sonic",
    "Water",
)

Strip = Callable[[str], str]


def _extra(text: str, strip: Strip) -> int:
    """Return how many characters of the text are colour codes."""
    return len(text) - len(strip(text))


def _single(strip: Strip, name: str, colour: str, data: object, datacolour: str = "@W") -> str:
    """One data line: ``| Keywords   : aylorian dagger |``."""
    text = f"| {colour}{name:<11}@w: {datacolour}{data}"
    pad = max(WIDTH - 1 - len(strip(text)), 0)
    return f"{text}{'':{pad}}@w|"


def _double(strip: Strip, name: str, colour: str, data: object, name2: str, data2: object) -> str:
    """Two data on a line: ``| Worth      : 20          Weight : 4 |``."""
    left, right = str(data), str(data2)
    width1 = 24 + _extra(left, strip)
    width2 = 17 + _extra(right, strip)
    return (
        f"| {colour}{name:<11}@w: @W{left:<{width1}} {colour}{name2:<7}@w: @W{right:<{width2}}@w|"
    )


def _special(
    strip: Strip, name: str, colour: str, data: object, name2: str = "", data2: object = ""
) -> str:
    """A line of text, or of two: ``| Weapon Type : Dagger    Average Dam :  17 |``."""
    left = str(data)
    text = f"| {colour}{name:<11}@w: @W{left:<{20 + _extra(left, strip)}}"
    if name2:
        right = str(data2)
        return f"{text} {colour}{name2:<13}:  @W{right:<{14 + _extra(right, strip)}}@w|"
    pad = max(WIDTH - 1 - len(strip(text)), 0)
    return f"{text}{'':{pad}}@w|"


def _colour(value: int) -> str:
    """Green above zero, red below it, plain at zero."""
    if value > 0:
        return "@G"
    return "@R" if value < 0 else "@w"


def _mods(values: object) -> dict[str, int]:
    """Return a mod mapping as ``{name: int}``, leaving the original alone."""
    if not isinstance(values, Mapping):
        return {}
    out: dict[str, int] = {}
    for name, amount in values.items():
        try:
            out[str(name)] = to_int(amount)
        except ValueError:
            continue
    return out


def _grid(lead: int, widths: tuple[int, ...], cells: list[tuple[str, str]]) -> str:
    """One row of the stat and resist tables: ``(colour, text)`` cells in fixed columns."""
    body = "".join(
        f"{colour}{text:<{width}}" for width, (colour, text) in zip(widths, cells, strict=True)
    )
    return f"|{'':{lead}}{body}@w{'':{WIDTH - 2 - lead - sum(widths)}}|"


def _head(lead: int, widths: tuple[int, ...], names: tuple[str, ...]) -> str:
    """A header row of a table."""
    return _grid(lead, widths, [("@w", name) for name in names])


_STAT_WIDTHS = (5, 5, 4, 4, 4, 4, 4, 4, 6, 5, 5, 5)
_STAT_NAMES = ("DR", "HR", "Str", "Int", "Wis", "Dex", "Con", "Luc", "Sav", "HP", "MN", "MV")
_PHYSICAL_WIDTHS = (9, 9, 8, 8, 8, 7, 7)
_PHYSICAL_NAMES = ("All Phys", "All Mag", "Bash", "Pierce", "Slash", "Diss", "Poisn")
_PHYSICAL_KEYS = ("All physical", "All magic", "Bash", "Pierce", "Slash", "Disease", "Poison")
_MAGICAL_ROWS = (
    (
        ("Acid", "Air", "Cold", "Earth", "Electric", "Energy", "Fire", "Holy"),
        ("Acid", "Air", "Cold", "Earth", "Eltrc", "Enrgy", "Fire", "Holy"),
    ),
    (
        ("Light", "Magic", "Mental", "Negative", "Shadow", "Sonic", "Water"),
        ("Light", "Magic", "Mntl", "Ngtv", "Shdw", "Sonic", "Water"),
    ),
)


def stats_header() -> str:
    """The header of the stat table."""
    return _head(5, _STAT_WIDTHS, _STAT_NAMES)


def format_stats(stats: Mapping[str, Any]) -> str:
    """The stat row; a stat that is zero or missing shows as ``-``. The input is not changed."""
    mods = _mods(stats)
    cells = [(_colour(mods.get(name, 0)), str(mods.get(name, 0) or "-")) for name in _STATS]
    return _grid(5, _STAT_WIDTHS, cells)


def format_resist(resists: Mapping[str, Any]) -> list[str]:
    """The resist rows: the physical ones, and the magical ones when any is not zero.

    The input is not changed. A magical resist that is negative counts as not zero.
    """
    mods = _mods(resists)

    def cells(keys: tuple[str, ...]) -> list[tuple[str, str]]:
        return [(_colour(mods.get(key, 0)), str(mods.get(key, 0) or "-")) for key in keys]

    rows: list[str] = []
    if any(name in mods for name in _PHYSICAL):
        rows.append(_head(5, _PHYSICAL_WIDTHS, _PHYSICAL_NAMES))
        rows.append(_grid(5, _PHYSICAL_WIDTHS, cells(_PHYSICAL_KEYS)))
    if any(mods.get(name, 0) != 0 for name in _MAGICAL):
        if rows:
            rows.append(DIVIDER)
        for keys, names in _MAGICAL_ROWS:
            widths = (7,) * len(keys)
            rows.append(_head(5, widths, names))
            rows.append(_grid(5, widths, cells(keys)))
    return rows


def _has(item: Mapping[str, Any], key: str) -> bool:
    """True when the item has a value for the key; zero counts as a value."""
    return item.get(key) not in (None, "", [], {})


def _as_int(value: object, default: int = 0) -> int:
    """Return a value as an int, or the default."""
    try:
        return to_int(value)
    except ValueError:
        return default


def _wrapped(text: str, width: int = _LINELEN) -> list[str]:
    """Wrap text for a box line."""
    return textwrap.wrap(text, width, break_on_hyphens=False)


def item_type_name(item: Mapping[str, Any]) -> str | None:
    """Return the capitalised object type name of an item, or None."""
    itype = item.get("itype")
    if isinstance(itype, int) and not isinstance(itype, bool) and 0 <= itype < len(OBJECTTYPES):
        return OBJECTTYPES[itype].capitalize()
    return None


def format_item(
    item: Mapping[str, Any],
    location: str | None,
    worn_slot: int | None,
    skill_name: Callable[[int | str], str | None],
    strip: Strip,
    bag_name: str | None = None,
) -> list[str]:
    """Return the lines of the item box.

    Args:
        item: The item as eq or eqdb gives it. It is not changed.
        location: Where the item is now, or None when not known.
        worn_slot: The wear slot, used when the location is Worn.
        skill_name: Returns the name of a skill by sn, or None.
        strip: Removes colour codes, to measure a line.
        bag_name: The plain name of the bag the item is in, when location is its serial.
    """
    lines = [DIVIDER]

    def single(name: str, colour: str, data: object, datacolour: str = "@W") -> None:
        lines.append(_single(strip, name, colour, data, datacolour))

    def special(name: str, colour: str, data: object, name2: str = "", data2: object = "") -> None:
        lines.append(_special(strip, name, colour, data, name2, data2))

    def wrapped(name: str, colour: str, text: str, datacolour: str = "@W") -> None:
        header = name
        for part in _wrapped(text):
            single(header, colour, part, datacolour)
            header = ""

    if _has(item, "keywords"):
        keywords = item["keywords"]
        wrapped(
            "Keywords", "@R", " ".join(keywords) if isinstance(keywords, list) else str(keywords)
        )
    if _has(item, "cname"):
        single("Name", "@R", f"@w{item['cname']}")
    single("Id", "@R", f"@w{item.get('serial', '')}")
    if location:
        if location == WORN and worn_slot is not None and 0 <= worn_slot < len(WEARLOCS):
            single("Location", "@R", f"Worn - {WEARLOCS[worn_slot]}")
        elif bag_name:
            wrapped("Location", "@R", f"{bag_name} ({location})")
        else:
            single("Location", "@R", location)

    type_name = item_type_name(item)
    if type_name and _has(item, "level"):
        lines.append(_double(strip, "Type", "@c", type_name, "Level", item["level"]))
    elif _has(item, "level"):
        single("Level", "@c", item["level"])
    if _has(item, "worth") and _has(item, "weight"):
        lines.append(
            _double(strip, "Worth", "@c", f"{_as_int(item['worth']):,}", "Weight", item["weight"])
        )

    light = item.get("light")
    if item.get("itype") == OBJECTTYPESREV["light"] and not light:
        single("Duration", "@c", "permanent")
    if isinstance(light, Mapping) and light:
        single("Duration", "@c", f"{light.get('duration', '')} minutes")
    if _has(item, "wearable"):
        single("Wearable", "@c", item["wearable"])
    if _has(item, "score"):
        single("Score", "@c", item["score"], "@Y")
    if _has(item, "material"):
        single("Material", "@c", item["material"])
    if _has(item, "flags"):
        flags = item["flags"]
        text = ", ".join(flags) if isinstance(flags, list) else str(flags)
        header = "Flags"
        for part in _wrapped(text):
            part = part.replace("precious", "@Yprecious@w").replace("noshare", "@Rnoshare@w")
            single(header, "@c", part.rstrip())
            header = ""
    if _has(item, "owner"):
        single("Owned by", "@c", item["owner"])
    if _has(item, "fromclan"):
        single("Clan Item", "@G", item["fromclan"], "@M")
    if _has(item, "foundat"):
        single("Found at", "@G", item["foundat"], "@M")
    if _has(item, "leadsto"):
        single("Leads to", "@G", item["leadsto"], "@M")

    notes = item.get("notes")
    if isinstance(notes, Mapping) and notes.get("ntext"):
        lines.append(DIVIDER)
        wrapped("Notes", "@W", str(notes["ntext"]), "@w")
    affects = item.get("affectmod")
    if affects:
        lines.append(DIVIDER)
        wrapped("Affects", "@g", ", ".join(str(a) for a in affects), "@w")

    box = item.get("container")
    if isinstance(box, Mapping) and box:
        lines.append(DIVIDER)
        special(
            "Capacity", "@c", box.get("capacity", 0), "Heaviest Item", box.get("heaviestitem", 0)
        )
        special("Holding", "@c", box.get("holding", 0), "Items Inside", box.get("itemsinside", 0))
        special(
            "Tot Weight", "@c", box.get("totalweight", 0), "Item Burden", box.get("itemburden", 0)
        )
        percent = _as_int(box.get("itemweightpercent"))
        special("", "@c", f"@wItems inside weigh @Y{percent}@w%@w of their usual weight")

    weapon = item.get("weapon")
    if isinstance(weapon, Mapping) and weapon:
        lines.append(DIVIDER)
        special(
            "Weapon Type", "@c", weapon.get("wtype", ""), "Average Dam", weapon.get("avedam", "")
        )
        special(
            "Inflicts", "@c", weapon.get("inflicts", ""), "Damage Type", weapon.get("damtype", "")
        )
        if weapon.get("special"):
            special("Specials", "@c", weapon["special"])

    portal = item.get("portal")
    if item.get("itype") == OBJECTTYPESREV["portal"] and isinstance(portal, Mapping) and portal:
        lines.append(DIVIDER)
        single("Portal", "@R", f"@Y{portal.get('uses', '')}@w uses remaining.")

    if _has(item, "statmod"):
        lines.extend([DIVIDER, stats_header(), format_stats(item["statmod"])])
    resist_rows = format_resist(item["resistmod"]) if _has(item, "resistmod") else []
    if resist_rows:
        lines.append(DIVIDER)
        lines.extend(resist_rows)

    skillmods = item.get("skillmod")
    if isinstance(skillmods, Mapping) and skillmods:
        lines.append(DIVIDER)
        header = "Skill Mods"
        for sn, amount in skillmods.items():
            value = _as_int(amount)
            found = skill_name(sn)
            name = found.capitalize() if found else f"sn {sn}"
            colour = "@G" if value > 0 else "@R"
            special(header, "@c", f"Modifies @g{name}@w by {colour}{value:+d}@w")
            header = ""

    enchants = item.get("enchant")
    if enchants:
        lines.append(DIVIDER)
        special("Enchants", "@c", "")
        for enchant in enchants:
            text = f"@W{enchant.get('stat', '')} @G{_as_int(enchant.get('mod')):+d}@w"
            if enchant.get("removable") == "E":
                text = f"{text:<{20 + _extra(text, strip)}}   (removable by enchanter)"
            single(str(enchant.get("spell", "")), "@g", text)

    spells = item.get("spells")
    if isinstance(spells, Mapping) and spells:
        lines.append(DIVIDER)
        header = "Spells"
        uses = _as_int(spells.get("uses"))
        plural = "s" if uses > 1 else ""
        for number in range(1, 5):
            sn = spells.get(f"sn{number}")
            if not sn:
                continue
            name = (skill_name(sn) or f"sn {sn}").lower()
            special(
                header,
                "@c",
                f"{uses} use{plural} of level {_as_int(spells.get('level'))} '@g{name}@w'",
            )
            header = ""

    food = item.get("food")
    if isinstance(food, Mapping) and food:
        lines.append(DIVIDER)
        special("Food", "@c", f"Will replenish hunger by {_as_int(food.get('percent'))}%")

    reward = item.get("reward")
    if isinstance(reward, Mapping) and reward.get("rtext"):
        lines.append(DIVIDER)
        special("Reward", "@Y", reward["rtext"])

    drink = item.get("drink")
    if isinstance(drink, Mapping) and drink:
        lines.append(DIVIDER)
        maximum = _as_int(drink.get("liquidmax")) // 20 or 1
        special(
            "Drink",
            "@c",
            f"@w{_as_int(drink.get('servings'))} servings of {drink.get('liquid', '')}. "
            f"Max: {maximum}",
        )
        special(
            "", "@c", f"@wEach serving replenishes thirst by {_as_int(drink.get('thirstpercent'))}%"
        )
        special(
            "", "@c", f"@wEach serving replenishes hunger by {_as_int(drink.get('hungerpercent'))}%"
        )

    furniture = item.get("furniture")
    if isinstance(furniture, Mapping) and furniture:
        lines.append(DIVIDER)
        special(
            "Heal Rate",
            "@c",
            f"Health @w[@Y{_as_int(furniture.get('hpregen'))}@w]    "
            f"@WMagic @w[@Y{_as_int(furniture.get('manaregen'))}@w]",
        )

    lines.append(DIVIDER)
    return lines
