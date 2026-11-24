"""Pure helpers for Aardwolf levels, classes and combat damage lines.

Ported from the old ``plugins/aardwolf/aardu.py``. There is no plugin class, no API
registration and no GMCP access: callers pass every value in. The one exception is
``actual_level_from_gmcp``, which takes a plain ``gmcp_get`` callable, so this module still
imports nothing from bastproxy.

Correction to the old behaviour: the old ``convert_level`` computed the remort as
``floor((total - tier * 1407) / 202) + 1``. A remort spans 201 levels, so the divisor 202
mis-converted 45 totals in 1..4220 (``convert_level(403)`` gave remort 2 instead of 3).
This port uses integer arithmetic on ``total - 1`` and matches the old results everywhere
else. The old ``classabb()`` with no argument returned the full-name to abbreviation
table; use ``CLASSABBREV`` for that.
"""

import re
from collections.abc import Callable
from typing import TypedDict

LEVELS_PER_REMORT = 201
REMORTS_PER_TIER = 7
LEVELS_PER_TIER = LEVELS_PER_REMORT * REMORTS_PER_TIER
MAX_TIER = 9

# class abbreviations
CLASSABB: dict[str, str] = {
    "mag": "mage",
    "thi": "thief",
    "pal": "paladin",
    "war": "warrior",
    "psi": "psionicist",
    "cle": "cleric",
    "ran": "ranger",
}

# the reverse of CLASSABB
CLASSABBREV: dict[str, str] = {name: abb for abb, name in CLASSABB.items()}

# reward names to their abbreviations
REWARDTABLE: dict[str, str] = {
    "quest": "qp",
    "training": "trains",
    "gold": "gold",
    "trivia": "tp",
    "practice": "pracs",
}

# damage verbs, weakest first
DAMAGES: list[str] = [
    "misses",
    "tickles",
    "bruises",
    "scratches",
    "grazes",
    "nicks",
    "scars",
    "hits",
    "injures",
    "wounds",
    "mauls",
    "maims",
    "mangles",
    "mars",
    "LACERATES",
    "DECIMATES",
    "DEVASTATES",
    "ERADICATES",
    "OBLITERATES",
    "EXTIRPATES",
    "INCINERATES",
    "MUTILATES",
    "DISEMBOWELS",
    "MASSACRES",
    "DISMEMBERS",
    "RENDS",
    "- BLASTS -",
    "-= DEMOLISHES =-",
    "** SHREDS **",
    "**** DESTROYS ****",
    "***** PULVERIZES *****",
    "-=- VAPORIZES -=-",
    "<-==-> ATOMIZES <-==->",
    "<-:-> ASPHYXIATES <-:->",
    "<-*-> RAVAGES <-*->",
    "<>*<> FISSURES <>*<>",
    "<*><*> LIQUIDATES <*><*>",
    "<*><*><*> EVAPORATES <*><*><*>",
    "<-=-> SUNDERS <-=->",
    "<=-=><=-=> TEARS INTO <=-=><=-=>",
    "<->*<=> WASTES <=>*<->",
    "<-+-><-*-> CREMATES <-*-><-+->",
    "<*><*><*><*> ANNIHILATES <*><*><*><*>",
    "<--*--><--*--> IMPLODES <--*--><--*-->",
    "<-><-=-><-> EXTERMINATES <-><-=-><->",
    "<-==-><-==-> SHATTERS <-==-><-==->",
    "<*><-:-><*> SLAUGHTERS <*><-:-><*>",
    "<-*-><-><-*-> RUPTURES <-*-><-><-*->",
    "<-*-><*><-*-> NUKES <-*-><*><-*->",
    "-<[=-+-=]<:::<>:::> GLACIATES <:::<>:::>[=-+-=]>-",
    "<-=-><-:-*-:-><*--*> METEORITES <*--*><-:-*-:-><-=->",
    "<-:-><-:-*-:-><-*-> SUPERNOVAS <-*-><-:-*-:-><-:->",
    "does UNSPEAKABLE things to",
    "does UNTHINKABLE things to",
    "does UNIMAGINABLE things to",
    "does UNBELIEVABLE things to",
    "pimpslaps",
]


class LevelInfo(TypedDict):
    """The parts of a total level."""

    tier: int
    redos: int
    remort: int
    level: int


class DamageLine(TypedDict):
    """A parsed combat damage line; strings are empty when not found."""

    damage: int
    hits: int
    damtype: str
    damverb: str
    enemy: str


def actual_level(level: int, remort: int, tier: int, redos: int) -> int:
    """Convert level, remort, tier and redos to the total level.

    Args:
        level: The level within the remort (1..201).
        remort: The remort number (1..7).
        tier: The tier.
        redos: The number of redos (only above zero at tier 9).

    Returns:
        The total level.

    """
    return (tier + redos) * LEVELS_PER_TIER + (remort - 1) * LEVELS_PER_REMORT + level


def _gmcp_int(gmcp_get: Callable[[str], object], path: str) -> int:
    """Read a GMCP value as an int, using 0 when it is missing or not numeric."""
    value = gmcp_get(path)
    if not isinstance(value, int | float | str | bytes):
        return 0
    try:
        return int(value)
    except ValueError:
        return 0


def actual_level_from_gmcp(gmcp_get: Callable[[str], object], level: int | None = None) -> int:
    """Return the total level from GMCP char data.

    Reads ``char.status.level`` (unless ``level`` is given), ``char.base.remorts``,
    ``char.base.tier`` and ``char.base.redos``, converting each to ``int``. A missing or
    non-numeric value counts as 0.

    Args:
        gmcp_get: Returns the GMCP value for a path such as ``char.base.tier``, or ``None``.
            Pass bastproxy's ``libs.net.protocols:gmcp.value.get``.
        level: Overrides ``char.status.level`` when not ``None``.

    Returns:
        The total level, as ``actual_level`` computes it.

    """
    if level is None:
        level = _gmcp_int(gmcp_get, "char.status.level")
    return actual_level(
        level,
        _gmcp_int(gmcp_get, "char.base.remorts"),
        _gmcp_int(gmcp_get, "char.base.tier"),
        _gmcp_int(gmcp_get, "char.base.redos"),
    )


def convert_level(total: int) -> LevelInfo:
    """Convert a total level to tier, redos, remort and level.

    Args:
        total: The total level.

    Returns:
        The parts; all four are -1 when ``total`` is below 1.

    """
    if total < 1:
        return {"tier": -1, "redos": -1, "remort": -1, "level": -1}
    n = total - 1
    tier = n // LEVELS_PER_TIER
    remort = (n % LEVELS_PER_TIER) // LEVELS_PER_REMORT + 1
    level = n % LEVELS_PER_REMORT + 1
    redos = 0
    if tier > MAX_TIER:
        redos = tier - MAX_TIER
        tier = MAX_TIER
    return {"tier": tier, "redos": redos, "remort": remort, "level": level}


def parse_damage_line(line: str) -> DamageLine:
    """Parse an Aardwolf combat damage line.

    Args:
        line: The line, optionally prefixed with ``[hits]`` and suffixed with ``[damage]``.
            A critical hit has a leading ``*``, before the hits or before ``Your``.

    Returns:
        The damage, hits, damage type, verb and enemy. Hits defaults to 1, damage to 0 and
        the strings to ``""`` when the line has no recognised damage verb.

    """
    result: DamageLine = {"damage": 0, "hits": 1, "damtype": "", "damverb": "", "enemy": ""}
    words = line.removeprefix("*").split(" ")
    if hits := re.match(r"^\[(?P<hits>\d+)\]$", words[0]):
        result["hits"] = int(hits.group("hits"))
        del words[0]
        if words:
            words[0] = words[0].removeprefix("*")
    if words and words[0] == "Your":
        del words[0]
    if words and (dam := re.match(r"^\[(?P<damage>\d+)\]$", words[-1])):
        result["damage"] = int(dam.group("damage"))
        del words[-1]
    text = " ".join(words)
    for verb in DAMAGES:
        if verb in text:
            match = re.match(rf"^(?P<damtype>.*) ({re.escape(verb)}) (?P<enemy>.*)[!.]$", text)
            if match:
                result["damtype"] = match.group("damtype")
                result["damverb"] = verb
                result["enemy"] = match.group("enemy")
                break
    return result
