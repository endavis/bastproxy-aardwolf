"""Constants, regexes and kill helpers of the mobk plugin. No bastproxy imports."""

from collections.abc import Callable, Mapping
from typing import Any, NamedTuple

# the suffixes of the events this plugin raises; the plugin builds the full names from its
# plugin id
SUFFIX_KILL = "kill"

EVENT_GMCP_STATUS = "ev_libs.net.mud_gmcp_char.status"

# the API of an eq plugin, which does not exist yet: it returns the item worn in a slot
EQ_WORN_API = "plugins.aardwolf.eq:eq.worn.get"
WIELDED_SLOT = 24
SECOND_SLOT = 25

_KILL_KEYS = {
    "name": "the name of the mob, Unknown when it was not seen",
    "xp": "the experience of the kill; a sum such as 123+45 is added up",
    "rarexp": "the rare kill bonus experience",
    "bonusxp": "the bonus experience",
    "blessingxp": "the bonus experience from the daily blessing",
    "totalxp": "the sum of xp, rarexp, bonusxp and blessingxp",
    "noexp": "1 when the character did not receive the experience, else 0",
    "gold": "the gold taken from the corpse",
    "tp": "1 for a trivia point mob, else 0",
    "time": "the time of the kill, in seconds since the epoch",
    "vorpal": "1 for a vorpal kill, else 0",
    "banishment": "1 for a banishment, else 0",
    "assassinate": "1 for an assassination, else 0",
    "slit": "1 when the throat was slit, else 0",
    "disintegrate": "1 for a disintegration, else 0",
    "deathblow": "1 for a death blow, else 0",
    "wielded_weapon": "the serial of the wielded weapon, empty when unknown",
    "second_weapon": "the serial of the second weapon, empty when unknown",
    "room_id": "the room of the kill, -1 when unknown",
    "level": "the total level of the character",
    "damage": "the damage done, by damage type, each with hits, misses and damage",
    "immunities": "the immunities seen, always empty for now",
    "starttime": "the time of the first damage line, or None",
    "finishtime": "the time the kill finished, in seconds since the epoch",
}

EVENTS: dict[str, dict[str, Any]] = {
    SUFFIX_KILL: {
        "description": ["raised once for each kill, when the corpse is gone, with a copy"],
        "arg_descriptions": dict(_KILL_KEYS),
    },
}


class TriggerSpec(NamedTuple):
    """A trigger the plugin adds: its name, regex and argument types."""

    name: str
    regex: str
    argtypes: dict[str, Callable[[str], Any]] | None


TRIGGERS: tuple[TriggerSpec, ...] = (
    TriggerSpec(
        "mobk_xp",
        r"^You (?P<dont>don't )?receive (?P<xp>\d+(?:\+\d+)*) experience points?\.$",
        None,
    ),
    TriggerSpec(
        "mobk_rarexp",
        r"^You (don't )?receive (?P<xp>\d+) 'rare kill' experience bonus.$",
        {"xp": int},
    ),
    TriggerSpec(
        "mobk_blessxp",
        r"^You (don't )?receive (?P<xp>\d+) bonus experience points from your daily blessing.$",
        {"xp": int},
    ),
    # the lookahead keeps the blessing line out; no priority or stop evaluating is needed
    TriggerSpec(
        "mobk_bonusxp",
        r"^You (don't )?receive (?P<xp>\d+) bonus experience points"
        r"(?! from your daily blessing).+$",
        {"xp": int},
    ),
    TriggerSpec("mobk_xpptless", r"^That was a pointless no experience kill!$", None),
    TriggerSpec(
        "mobk_switch", r"^You switch targets and direct your attacks at (?P<name>.*).\.$", None
    ),
    TriggerSpec("mobk_flee", r"^You flee from combat!$", None),
    TriggerSpec("mobk_retreat", r"^You retreat from the combat!$", None),
    TriggerSpec(
        "mobk_gold", r"^You get (?P<gold>.+) gold coins from .+ corpse of (?P<name>.+)\.$", None
    ),
    TriggerSpec(
        "mobk_splitgold", r"^\w+ splits? \d+ gold coins?. Your share is (?P<gold>\d+) gold\.$", None
    ),
    TriggerSpec("mobk_corpseget", r"^You get .+ corpse of (?P<name>.+)\.$", None),
    TriggerSpec(
        "mobk_sac",
        r"^.* gives you (?P<sacgold>.+) gold coins? for the .* ?corpse of (?P<name>.+)\.$",
        None,
    ),
    TriggerSpec(
        "mobk_consume",
        r"^You bury your fangs deep into the .* ?corpse of (?P<name>.+), drinking thirstily.$",
        None,
    ),
    TriggerSpec("mobk_trivia", r"^You killed a Triv bonus mob!! Triv point added\.$", None),
    TriggerSpec(
        "mobk_trivia2", r"^You killed a Trivia Point bonus mob!! Trivia point added\.$", None
    ),
    TriggerSpec(
        "mobk_vorpal",
        r"^Deep magic stirs within your weapon. It seems to have a life of its own.$",
        None,
    ),
    TriggerSpec("mobk_assassin", r"^You assassinate (?P<name>.*) with cold efficiency.$", None),
    TriggerSpec("mobk_deathblow", r"^Your death blow CLEAVES (?P<name>.*) in two!$", None),
    TriggerSpec("mobk_slit", r"^You sneak behind (?P<name>.*) and slit .* throat.$", None),
    TriggerSpec("mobk_disintegrate", r"^You have disintegrated (?P<name>.*)!$", None),
    TriggerSpec("mobk_banish", r"^You look at (?P<name>.*) very strangely.$", None),
    TriggerSpec("mobk_damage", r"^\*?\[(.*)\] \*?Your (.*) \[(.*)\]$", None),
    TriggerSpec("mobk_damage2", r"^\*?Your (.*) \[(.*)\]$", None),
    TriggerSpec(
        "mobk_bsincombat",
        r"^You spin around (.*), catching (.*) off guard, and execute a vicious double backstab.$",
        None,
    ),
)


def to_int(value: object) -> int:
    """Return a value as an int, or 0 when it is missing or not numeric."""
    if isinstance(value, (bool, int, float, str, bytes)):
        try:
            return int(value)
        except (ValueError, OverflowError):
            return 0
    return 0


def damage_default() -> dict[str, int]:
    """Return a default damage entry."""
    return {"hits": 0, "misses": 0, "damage": 0}


def add_to_damage(
    tdam: Mapping[str, Any], table: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Add a parsed damage line to a damage table, by damage type, and return the table.

    An empty damage type is ``Unknown``. A ``misses`` verb adds its hits to the misses; any other
    verb adds its hits and its damage.
    """
    damtype = tdam.get("damtype") or "Unknown"
    entry = table.setdefault(damtype, damage_default())
    if tdam.get("damverb") == "misses":
        entry["misses"] += tdam.get("hits", 0)
    else:
        entry["hits"] += tdam.get("hits", 0)
        entry["damage"] += tdam.get("damage", 0)
    return table


# the columns of the damage table: the header of a column and the key of its cell
DAMAGE_COLUMNS: list[dict[str, str]] = [
    {"name": "Damage type", "key": "damtype"},
    {"name": "Hits", "key": "hits"},
    {"name": "Misses", "key": "misses"},
    {"name": "Damage", "key": "damage"},
]


def damage_table_data(damage: Mapping[str, Mapping[str, Any]]) -> list[dict[str, str]]:
    """Return the damage table as one dict of text cells per damage type, in insertion order.

    A missing count is ``0``.
    """
    return [
        {
            "damtype": damtype,
            "hits": str(to_int(entry.get("hits", 0))),
            "misses": str(to_int(entry.get("misses", 0))),
            "damage": str(to_int(entry.get("damage", 0))),
        }
        for damtype, entry in damage.items()
    ]


def sum_xp(text: str) -> int:
    """Return the experience of text such as ``123`` or ``123+45``, 0 when it is not numeric."""
    try:
        return sum(int(part) for part in text.split("+"))
    except ValueError:
        return 0


def parse_gold(text: str) -> int | None:
    """Return the gold of text such as ``1,234``, or None when it is not numeric."""
    try:
        return int(text.replace(",", ""))
    except ValueError:
        return None


def new_kill() -> dict[str, Any]:
    """Return a fresh kill: every count at 0 and no name, times or damage."""
    return {
        "name": "",
        "tp": 0,
        "vorpal": 0,
        "assassinate": 0,
        "deathblow": 0,
        "slit": 0,
        "disintegrate": 0,
        "banishment": 0,
        "xp": 0,
        "bonusxp": 0,
        "blessingxp": 0,
        "rarexp": 0,
        "totalxp": 0,
        "noexp": 0,
        "gold": 0,
        "wielded_weapon": "",
        "second_weapon": "",
        "room_id": -1,
        "level": -1,
        "time": None,
        "damage": {},
        "immunities": {},
        "starttime": None,
        "finishtime": None,
    }


def total_xp(kill: Mapping[str, Any]) -> int:
    """Return the sum of the experience, rare, bonus and blessing experience of a kill."""
    return int(kill["xp"]) + int(kill["rarexp"]) + int(kill["bonusxp"]) + int(kill["blessingxp"])
