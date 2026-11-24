"""Pure helpers for the aarch plugin: the 50 pieces, counting what is held, listing the rest."""

import re
from collections.abc import Iterable
from typing import NamedTuple

# the eq API that finds items by a part of their name; a copy, because no plugin imports another
API_EQ_FIND_BY_NAME = "plugins.aardwolf.eq:item.find.by.name"

# the tag Aardwolf puts in front of the name of every Aarchaeology item
AARCH_TAG = "(Aarchaeology)"

# the 50 pieces of the set, by their number
AARCH_ITEMS: dict[int, str] = {
    1: "Johnny's Appleseed",
    2: "An Ancient Skull",
    3: "A Golden Truffle",
    4: "An Ancient Game Token",
    5: "Neptune's Retired Staff",
    6: "Percival's Retired Crown",
    7: "Photo of an F1 Tornado",
    8: "A Ring of Thandeld",
    9: "Petrified Volcano Ash",
    10: "An Old Coyote's Tooth",
    11: "Dorothy's Lost Earring",
    12: "A Golden Cross",
    13: "Skeleton of a Goblin",
    14: "A Rusted Coin",
    15: "A Rusted Trumpet",
    16: "A Coffin Lid",
    17: "A Wedding Ring",
    18: "A Dinosaur Bone",
    19: "A Dragon's Tooth",
    20: "Unknown Element",
    21: "A Destroyed Mosaic",
    22: "A Silver Cross",
    23: "Lost Binoculars",
    24: "Pirate's Hat",
    25: "A Rusted Cleaver",
    26: "Wilted Rose",
    27: "Casino Chip",
    28: "Torn Visitor's Pass",
    29: "Ten-year-old Textbook",
    30: "Ivory Tusks",
    31: "An Oasis",
    32: "Skeleton of a Monkey",
    33: "An Ancient Stalactite",
    34: "Shoes of a Gnome",
    35: "A Torn Peace Agreement",
    36: "Chunk of an Iceberg",
    37: "Wings of a Harpy",
    38: "Petrified Tree Branch",
    39: "A Golden Leaf",
    40: "Writings of a Dream",
    41: "An Old Rope",
    42: "A Broken Twig",
    43: "Brick from a Castle",
    44: "A Rusted Belt Buckle",
    45: "A Biblical Textbook",
    46: "Frozen Flames",
    47: "Fox Tooth",
    48: "Picture of a Forest",
    49: "Moon in a Bottle",
    50: "Rotting Reed",
}

PAMPHLET_WORDS = "collectable pamphlet"
PAMPHLET_REGEX = re.compile(r"Collectable Pamphlet\s*#\s*(\d+)", re.IGNORECASE)


def normalise(name: str) -> str:
    """Return a name without the Aarchaeology tag, whitespace collapsed and lower case."""
    return _clean(name).lower()


def _clean(name: str) -> str:
    """Return a name without the Aarchaeology tag, whitespace collapsed, case kept."""
    text = " ".join(name.split())
    if text.lower().startswith(AARCH_TAG.lower()):
        text = text[len(AARCH_TAG) :].strip()
    return text


# the normalised name of a piece to its number
AARCH_BY_NAME: dict[str, int] = {normalise(name): number for number, name in AARCH_ITEMS.items()}


class AarchCount(NamedTuple):
    """What the character holds: items, distinct items, pamphlets, the pieces and unknown names."""

    items: int
    distinct: int
    pamphlets: int
    have: frozenset[int]
    unknown: tuple[str, ...]


def count_items(names: Iterable[object]) -> AarchCount:
    """Count the Aarchaeology items and pamphlets in a list of item names.

    A pamphlet numbered N counts as holding piece N. A name that is not a string is skipped.
    """
    items = 0
    pamphlets = 0
    have: set[int] = set()
    distinct: set[int] = set()
    unknown: list[str] = []
    for name in names:
        if not isinstance(name, str):
            continue
        cleaned = _clean(name)
        if PAMPHLET_WORDS in cleaned.lower():
            pamphlets += 1
            match = PAMPHLET_REGEX.search(cleaned)
            if match and int(match.group(1)) in AARCH_ITEMS:
                have.add(int(match.group(1)))
            continue
        number = AARCH_BY_NAME.get(cleaned.lower())
        if number is None:
            unknown.append(cleaned)
            continue
        items += 1
        distinct.add(number)
        have.add(number)
    return AarchCount(items, len(distinct), pamphlets, frozenset(have), tuple(unknown))


def needed(have: Iterable[int]) -> list[int]:
    """Return the numbers of the pieces not held, in order."""
    held = set(have)
    return [number for number in AARCH_ITEMS if number not in held]


def need_lines(count: AarchCount, text: str = "") -> list[str]:
    """Return the lines of the need command; ``text`` filters the pieces by a part of the name."""
    missing = needed(count.have)
    lines = [
        f"You have {count.items} Aarchaeology items ({count.distinct} different) "
        f"and {count.pamphlets} Pamphlets"
    ]
    if not missing:
        lines.append("Congratulations! You have a full set of Aarchaeology items.")
    else:
        word = "piece" if len(missing) == 1 else "pieces"
        wanted = text.strip().lower()
        shown = [n for n in missing if wanted in AARCH_ITEMS[n].lower()] if wanted else missing
        if not wanted:
            lines.append(f"You need {len(missing)} {word}:")
        elif shown:
            lines.append(f"You need {len(missing)} {word}, {len(shown)} match '{text.strip()}':")
        else:
            lines.append(f"You need {len(missing)} {word}, none match '{text.strip()}'")
        lines.extend(f"{number:<2} - {AARCH_ITEMS[number]}" for number in shown)
    lines.extend(f"Not a known piece: {name}" for name in count.unknown)
    return lines
