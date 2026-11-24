"""Item tables and the item data line parser for Aardwolf.

Ported from the old ``plugins/aardwolf/itemu.py``. There is no plugin class and no API
registration, so this module imports nothing from bastproxy. The six old getter APIs are now
module constants, and the colour API the old ``dataparse`` called is replaced by an optional
``strip_color`` callable.

Changes from the old behaviour:

* ``objecttypes(rev=True)`` is ``OBJECTTYPESREV`` and ``wearlocs(rev=True)`` is
  ``WEARLOCSREV``. ``itemflags``, ``itemflagscolors`` and ``itemflagsname`` are
  ``ITEMFLAGS``, ``ITEMFLAGSCOLORS`` and ``ITEMFLAGSNAME``. The ``invlayout`` instance
  attribute is ``INVLAYOUT``.
* ``dataparse`` is ``parse_item_data``. It no longer calls ``colors.stripcolor``: pass
  ``strip_color`` for the ``eqdata`` layout.
* The old code logged errors and carried on. A line with fewer fields than its layout used to
  return a partial dict after a bare ``except`` sent a traceback; it now raises
  ``ValueError``. An unknown layout used to return ``None``; it now raises ``ValueError``.
  ``eqdata`` without ``strip_color`` raises ``ValueError``. Extra trailing fields are still
  ignored.
* The old branch for ``layoutname == 'invheader' and name == 'type'`` never ran, because the
  field is called ``itype``. It was the conversion Aardwolf needs: real ``{invheader}`` lines
  carry the type as a name (``Weapon``), so ``parse_item_data`` maps it through
  ``OBJECTTYPESREV``, case-insensitively, to the number. An unknown name stays a string.
* ``xrange`` (Python 2) is gone.
"""

from collections.abc import Callable

# object types, indexed by the number the MUD sends
OBJECTTYPES: list[str] = [
    "none",
    "light",
    "scroll",
    "wand",
    "staff",
    "weapon",
    "treasure",
    "armor",
    "potion",
    "furniture",
    "trash",
    "container",
    "drink",
    "key",
    "food",
    "boat",
    "mobcorpse",
    "corpse",
    "fountain",
    "pill",
    "portal",
    "beacon",
    "giftcard",
    "gold",
    "raw material",
    "campfire",
]

# the reverse of OBJECTTYPES
OBJECTTYPESREV: dict[str, int] = {name: i for i, name in enumerate(OBJECTTYPES)}

# wear locations, indexed by the number the MUD sends
WEARLOCS: list[str] = [
    "light",
    "head",
    "eyes",
    "lear",
    "rear",
    "neck1",
    "neck2",
    "back",
    "medal1",
    "medal2",
    "medal3",
    "medal4",
    "torso",
    "body",
    "waist",
    "arms",
    "lwrist",
    "rwrist",
    "hands",
    "lfinger",
    "rfinger",
    "legs",
    "feet",
    "shield",
    "wielded",
    "second",
    "hold",
    "float",
    "tattoo1",
    "tattoo2",
    "above",
    "portal",
    "sleeping",
]

# the reverse of WEARLOCS
WEARLOCSREV: dict[str, int] = {name: i for i, name in enumerate(WEARLOCS)}

# item flag letters
ITEMFLAGS: list[str] = ["K", "G", "H", "I", "M"]

# item flag letters to the colour code letter used to show them
ITEMFLAGSCOLORS: dict[str, str] = {
    "K": "R",
    "M": "B",
    "G": "W",
    "H": "C",
    "I": "w",
}

# item flag letters to their names
ITEMFLAGSNAME: dict[str, str] = {
    "K": "kept",
    "M": "magic",
    "G": "glow",
    "H": "hum",
    "I": "invis",
}

# layout name to the field names of a line in that layout
INVLAYOUT: dict[str, list[str]] = {
    "invheader": [
        "serial",
        "level",
        "itype",
        "worth",
        "weight",
        "wearable",
        "flags",
        "owner",
        "fromclan",
        "timer",
        "u1",
        "u2",
        "u3",
        "score",
    ],
    "container": [
        "capacity",
        "heaviestitem",
        "holding",
        "itemsinside",
        "totalweight",
        "itemburden",
        "itemweightpercent",
    ],
    "statmod": ["name", "value"],
    "resistmod": ["name", "value"],
    "weapon": ["wtype", "avedam", "inflicts", "damtype", "special"],
    "skillmod": ["name", "value"],
    "spells": ["uses", "level", "sn1", "sn2", "sn3", "sn4", "u1"],
    "food": ["percent"],
    "drink": [
        "servings",
        "liquid",
        "liquidmax",
        "liquidleft",
        "thirstpercent",
        "hungerpercent",
        "u1",
    ],
    "furniture": ["hpregen", "manaregen", "u1"],
    "eqdata": ["serial", "shortflags", "cname", "level", "itype", "unique", "wearslot", "timer"],
    "light": ["duration"],
    "portal": ["uses"],
    "tempmod": ["sn", "u1", "u2", "statmod", "duration"],
    "enchant": ["spell", "etype", "stat", "mod", "char", "removable"],
}

# layouts whose fields are comma separated; every other layout uses ``|``
COMMA_LAYOUTS: frozenset[str] = frozenset({"eqdata", "tempmod", "enchant"})


def parse_item_data(
    line: str,
    layout: str,
    strip_color: Callable[[str], str] | None = None,
) -> dict[str, int | str]:
    """Parse a line from invheader, invdata, eqdata or invdetails output.

    Args:
        line: The line to parse.
        layout: A key of ``INVLAYOUT``.
        strip_color: Removes colour codes from a string. Required for ``eqdata``, which
            adds a ``name`` key with the colour codes of ``cname`` removed.

    Returns:
        A dict of field name to value. A field that parses as an int is an int, the rest
        stay strings. Fields beyond the layout are ignored.

    Raises:
        ValueError: The layout is unknown, the line has fewer fields than the layout, or
            the layout is ``eqdata`` and ``strip_color`` is None.
    """
    names = INVLAYOUT.get(layout)
    if names is None:
        msg = f"layout {layout!r} not found"
        raise ValueError(msg)
    if layout == "eqdata" and strip_color is None:
        msg = "layout 'eqdata' needs a strip_color callable"
        raise ValueError(msg)

    fields = line.split("," if layout in COMMA_LAYOUTS else "|")
    if len(fields) < len(names):
        msg = (
            f"line {line!r} has {len(fields)} fields, layout {layout!r} needs {len(names)}: {names}"
        )
        raise ValueError(msg)

    item: dict[str, int | str] = {}
    for name, raw in zip(names, fields, strict=False):
        try:
            item[name] = int(raw)
        except ValueError:
            item[name] = raw

    if layout == "invheader":
        itype = item["itype"]
        if isinstance(itype, str):
            item["itype"] = OBJECTTYPESREV.get(itype.strip().lower(), itype)

    if layout == "eqdata" and strip_color is not None:
        item["name"] = strip_color(str(item["cname"]))

    return item
