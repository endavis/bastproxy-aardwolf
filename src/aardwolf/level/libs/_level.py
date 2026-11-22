"""Constants, regexes and record helpers of the level plugin. No bastproxy imports."""

import re
from collections.abc import Callable, Mapping
from typing import Any, NamedTuple

PREFIX = "ev_plugins.aardwolf.level_"
EVENT_GAIN = f"{PREFIX}gain"
EVENT_HERO = f"{PREFIX}hero"
EVENT_SUPERHERO = f"{PREFIX}superhero"
EVENT_REMORT = f"{PREFIX}remort"
EVENT_TIER = f"{PREFIX}tier"
EVENT_PREREMORT = f"{PREFIX}preremort"

EVENT_GMCP_STATUS = "ev_libs.net.mud_gmcp_char.status"
EVENT_GMCP_BASE = "ev_libs.net.mud_gmcp_char.base"
EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"
# the id of the core empty line trigger, which belongs to plugins.core.triggers
EMPTYLINE_ID = "t_plugins.core.triggers_emptyline"

STATS = ("str", "int", "wis", "dex", "con", "luc")

GROUP_LINFO = "linfo"
GROUP_SUPERHERO = "superhero"
GROUP_REMORT = "remort"

_GAIN_KEYS = {
    "type": "level for a level, pup for a powerup",
    "level": "the level reached, or the level of the character for a powerup",
    "totallevels": "the total level of the character",
    "starttime": "the time the level started, in seconds since the epoch",
    "finishtime": "the time the level finished, in seconds since the epoch",
    "str": "1 when a bonus strength point was gained, else 0",
    "int": "1 when a bonus intelligence point was gained, else 0",
    "wis": "1 when a bonus wisdom point was gained, else 0",
    "dex": "1 when a bonus dexterity point was gained, else 0",
    "con": "1 when a bonus constitution point was gained, else 0",
    "luc": "1 when a bonus luck point was gained, else 0",
    "hp": "the hit points gained",
    "mp": "the mana gained",
    "mv": "the moves gained",
    "pracs": "the practices gained",
    "trains": "the trains gained",
    "bonustrains": "the bonus trains gained",
    "blessingtrains": "the trains gained from the daily blessing",
    "battlelearntrains": "the trains gained from enhanced battle learning",
}

EVENTS: dict[str, dict[str, Any]] = {
    EVENT_GAIN: {
        "description": ["raised when a level or a powerup finished, with a copy of the record"],
        "arg_descriptions": dict(_GAIN_KEYS),
    },
    EVENT_HERO: {
        "description": ["raised after level_gain when level 200 is reached by levelling"],
        "arg_descriptions": {},
    },
    EVENT_SUPERHERO: {
        "description": ["raised after level_gain when level 201 is reached"],
        "arg_descriptions": {},
    },
    EVENT_REMORT: {
        "description": ["raised after level_gain when a remort is complete, back at level 1"],
        "arg_descriptions": {},
    },
    EVENT_TIER: {
        "description": ["raised after level_gain when a tier is complete, back at level 1"],
        "arg_descriptions": {},
    },
    EVENT_PREREMORT: {
        "description": ["raised when the character is flagged as remorting"],
        "arg_descriptions": {},
    },
}

# watch name to the regex of the command; the names are global, so they carry a prefix
WATCHES: dict[str, str] = {
    "level_sh": r"^superhero$",
    "level_shsilent": r"^superhero silent$",
    "level_shloud": r"^superhero loud$",
    "level_shconfirm": r"^superhero confirm$",
    "level_shloudconfirm": r"^superhero loud confirm$",
}


class TriggerSpec(NamedTuple):
    """A trigger the plugin adds: its name, regex, group suffix, state and argument types."""

    name: str
    regex: str
    group: str | None
    enabled: bool
    argtypes: dict[str, Callable[[str], Any]] | None


_STARS = re.escape("*" * 71)

TRIGGERS: tuple[TriggerSpec, ...] = (
    TriggerSpec(
        "lvlpup", r"^Congratulations, hero. You have increased your powers!$", None, True, None
    ),
    TriggerSpec("lvlpupbless", r"^You gain a powerup\.$", None, True, None),
    TriggerSpec(
        "lvllevel",
        r"^You raise a level! You are now level (?P<level>\d*).$",
        None,
        True,
        {"level": int},
    ),
    TriggerSpec(
        "lvlshloud",
        r"^Congratulations! You are now a superhero!"
        r" You receive (?P<trains>\d+) trains for superhero loud.$",
        None,
        True,
        {"trains": int},
    ),
    TriggerSpec("lvlsh", r"^Congratulations! You are now a superhero!", None, True, None),
    TriggerSpec(
        "lvlbless",
        r"^You gain a level - you are now level (?P<level>\d*).$",
        None,
        True,
        {"level": int},
    ),
    TriggerSpec(
        "lvlgains",
        r"^You gain (?P<hp>\d*) hit points, (?P<mp>\d*) mana, "
        r"(?P<mv>\d*) moves, (?P<pr>\d*) practices and "
        r"(?P<tr>\d*) trains.$",
        GROUP_LINFO,
        False,
        {"hp": int, "mp": int, "mv": int, "pr": int, "tr": int},
    ),
    TriggerSpec(
        "lvlblesstrain",
        r"^You gain (?P<tr>\d*) extra trains? daily blessing bonus.$",
        GROUP_LINFO,
        False,
        {"tr": int},
    ),
    TriggerSpec("lvlpupgains", r"^You gain (?P<tr>\d*) trains.$", GROUP_LINFO, False, {"tr": int}),
    TriggerSpec(
        "lvlbattlelearntrains",
        r"^You gain (?P<tr>\d*) additional training sessions? "
        r"from your enhanced battle learning.$",
        GROUP_LINFO,
        False,
        {"tr": int},
    ),
    TriggerSpec(
        "lvlbonustrains",
        r"^Lucky! You gain an extra (?P<tr>\d*) training sessions?!$",
        GROUP_LINFO,
        False,
        {"tr": int},
    ),
    TriggerSpec(
        "lvlbonusstat", r"^You gain a bonus (?P<stat>.*) point!$", GROUP_LINFO, False, None
    ),
    TriggerSpec("lvlshbadstar", f"^{_STARS}$", GROUP_SUPERHERO, False, None),
    TriggerSpec(
        "lvlshbad",
        r"^Use either: 'superhero loud'   - (?P<mins>.*) mins of "
        r"double xp, (?P<qp>.*)qp and (?P<gold>.*) gold$",
        GROUP_SUPERHERO,
        False,
        None,
    ),
    TriggerSpec(
        "lvlshnogold",
        r"^You must be carrying at least 500,000 gold coins.$",
        GROUP_SUPERHERO,
        False,
        None,
    ),
    TriggerSpec(
        "lvlshnoqp", r"^You must have at least 1000 quest points.$", GROUP_SUPERHERO, False, None
    ),
    TriggerSpec(
        "lvlshnodbl",
        r"^You cannot superhero loud until double exp is over.$",
        GROUP_SUPERHERO,
        False,
        None,
    ),
    TriggerSpec(
        "lvlshnot200", r"^You have to be level 200 to superhero.$", GROUP_SUPERHERO, False, None
    ),
    TriggerSpec("lvlpreremort", r"^You are now flagged as remorting.$", GROUP_REMORT, True, None),
    TriggerSpec("lvlremortcomp", r"^\* Remort transformation complete!$", GROUP_REMORT, True, None),
    TriggerSpec(
        "lvltier",
        r"^## You have already remorted the max number of times.$",
        GROUP_REMORT,
        True,
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


def new_record(kind: str, level: int, totallevels: int, starttime: float) -> dict[str, Any]:
    """Return a fresh level record: every gain 0 and no finish time."""
    record: dict[str, Any] = {"type": kind, "level": level}
    record.update(dict.fromkeys(STATS, 0))
    record.update(
        {
            "starttime": starttime,
            "finishtime": -1,
            "hp": 0,
            "mp": 0,
            "mv": 0,
            "pracs": 0,
            "trains": 0,
            "bonustrains": 0,
            "blessingtrains": 0,
            "battlelearntrains": 0,
            "totallevels": totallevels,
        }
    )
    return record


def next_starttime(old: Mapping[str, Any], now: float) -> float:
    """Return the start time of a new level.

    That is the finish time of the old record. When the old record never finished, such as a
    failed superhero, it is the old record's own start time, which came from the last finish.
    With no usable old record it is ``now``.
    """
    for key in ("finishtime", "starttime"):
        value = old.get(key, 0)
        if isinstance(value, (int, float)) and value > 0:
            return float(value)
    return now


def should_finish(trains: int, remortcomp: bool, tiering: bool) -> bool:
    """Return True when an empty line ends the level.

    A level ends once trains were gained, or when a remort or a tier is completing.
    """
    return trains > 0 or remortcomp or tiering


def bonus_stat_key(stat: str) -> str | None:
    """Return the record key for the stat of a bonus stat line, or None when it is not a stat."""
    key = stat[:3].lower()
    return key if key in STATS else None
