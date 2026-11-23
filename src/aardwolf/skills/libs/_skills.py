"""Constants, regexes and the skill table of the skills plugin. No bastproxy imports."""

import copy
from collections.abc import Callable, Iterable, Mapping
from typing import Any, NamedTuple

PREFIX = "ev_plugins.aardwolf.skills_"
EVENT_AFFON = f"{PREFIX}affon"
EVENT_AFFOFF = f"{PREFIX}affoff"
EVENT_RECON = f"{PREFIX}recon"
EVENT_RECOFF = f"{PREFIX}recoff"
EVENT_GAIN = f"{PREFIX}gain"
EVENT_FAIL = f"{PREFIX}fail"
EVENT_AFFECTED_UPDATE = f"{PREFIX}affected_update"
EVENT_UPTODATE = f"{PREFIX}uptodate"

# the level plugin's events and the disconnect event, listened to by name
EVENT_LEVEL_REMORT = "ev_plugins.aardwolf.level_remort"
EVENT_LEVEL_TIER = "ev_plugins.aardwolf.level_tier"
EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"

# the a102 plugin counts the requests for a tag option; its API is used by name
API_A102_TOGGLE = "plugins.aardwolf.a102:option.toggle"
A102_OPTIONS = ("SPELLUPTAGS", "SKILLGAINTAGS")

# the most lines hidden after the opening line, without an end tag; a full slist can run to
# several hundred lines. mudcmds counts the opening line too, so the type gets HIDE_MAX_LINES + 1
HIDE_MAX_LINES = 1000

CMDTYPE = "slist"
CMD = "slist"
CMD_REGEX = r"^slist\s((?P<type>.*)\s)?noprompt$"
CMDTYPE_SPELLUP = "slistspellup"
CMD_SPELLUP_REGEX = r"^slist\sspellup\snoprompt$"
ARGS_FULL = "noprompt"
ARGS_SPELLUP = "spellup noprompt"

# the hide window of each type: a full slist ends at the end of the recoveries and prints the end
# of the spell headers partway through, a spellup slist ends at the end of the spell headers
HIDE_START_FULL = r"^\{spellheaders noprompt\}$"
HIDE_START_SPELLUP = r"^\{spellheaders spellup noprompt\}$"
HIDE_END_FULL = r"^\{/recoveries\}$"
HIDE_END_SPELLUP = r"^\{/spellheaders\}$"

GROUP_SLIST = "slist"
GROUP_SPELLS = "slist_spells"
GROUP_RECOVERIES = "slist_recoveries"

_SN = "the sn of the skill or spell"
_SN_DURATION: dict[str, str] = {
    "sn": _SN,
    "duration": "the time the affect or recovery ends, in seconds since the epoch",
}
_NO_ARGS: dict[str, None] = {"None": None}

EVENTS: dict[str, dict[str, Any]] = {
    EVENT_AFFON: {
        "description": ["raised when a spell or skill affect starts on the character"],
        "arg_descriptions": dict(_SN_DURATION),
    },
    EVENT_AFFOFF: {
        "description": ["raised when a spell or skill affect ends"],
        "arg_descriptions": {"sn": _SN},
    },
    EVENT_RECON: {
        "description": ["raised when a recovery starts"],
        "arg_descriptions": dict(_SN_DURATION),
    },
    EVENT_RECOFF: {
        "description": ["raised when a recovery ends"],
        "arg_descriptions": {"sn": _SN},
    },
    EVENT_GAIN: {
        "description": ["raised when the percent of a skill or spell changes by practice"],
        "arg_descriptions": {"sn": _SN, "percent": "the new percent learned"},
    },
    EVENT_FAIL: {
        "description": ["raised when a skill or spell fails"],
        "arg_descriptions": {
            "sn": _SN,
            "reason": "the name of the reason, or the code when it is unknown",
            "target": "self or other, or the code when it is unknown",
            "recovery": "the sn of the recovery that blocks it, or -1",
        },
    },
    EVENT_AFFECTED_UPDATE: {
        "description": ["raised when a full or affected slist set the durations of the affects"],
        "arg_descriptions": dict(_NO_ARGS),
    },
    EVENT_UPTODATE: {
        "description": ["raised once the skills are known and the spellups are flagged"],
        "arg_descriptions": dict(_NO_ARGS),
    },
}

FAILREASON = {
    1: "lostconc",  # Regular fail, lost concentration.
    2: "alreadyaff",  # Already affected.
    3: "recblock",  # Cast blocked by a recovery.
    4: "nomana",  # Not enough mana.
    5: "nocastroom",  # You are in a nocast room.
    6: "fighting",  # Fighting or other 'cant concentrate'.
    8: "dontknow",  # You don't know the spell.
    9: "wrongtarget",  # Tried to cast self only on other.
    10: "notactive",  # You are resting / sitting.
    11: "disabled",  # Skill/spell has been disabled.
    12: "nomoves",  # Not enough moves.
}
TARGET = {
    0: "special",  # Target decided in spell (gate etc)
    1: "attack",
    2: "spellup",
    3: "selfonly",
    4: "object",
    5: "other",  # Spell has extended / unique syntax.
}
STYPE = {1: "spell", 2: "skill"}
FAILTARG = {0: "self", 1: "other"}


class TriggerSpec(NamedTuple):
    """A trigger the plugin adds: its name, regex, group suffix, state, omit and argtypes."""

    name: str
    regex: str
    group: str | None
    enabled: bool
    omit: bool
    argtypes: dict[str, Callable[[str], Any]] | None


TRIGGERS: tuple[TriggerSpec, ...] = (
    TriggerSpec("skills_affoff", r"^\{affoff\}(?P<sn>\d+)$", None, True, False, {"sn": int}),
    TriggerSpec(
        "skills_affon",
        r"^\{affon\}(?P<sn>\d+),(?P<duration>\d+)$",
        None,
        True,
        False,
        {"sn": int, "duration": int},
    ),
    TriggerSpec("skills_recoff", r"^\{recoff\}(?P<sn>\d+)$", None, True, False, {"sn": int}),
    TriggerSpec(
        "skills_recon",
        r"^\{recon\}(?P<sn>\d+),(?P<duration>\d+)$",
        None,
        True,
        False,
        {"sn": int, "duration": int},
    ),
    TriggerSpec(
        "skills_skillgain",
        r"^\{skillgain\}(?P<sn>\d+),(?P<percent>\d+)$",
        None,
        True,
        False,
        {"sn": int, "percent": int},
    ),
    TriggerSpec(
        "skills_sfail",
        r"^\{sfail\}(?P<sn>\d+),(?P<target>\d+),(?P<reason>\d+),(?P<recovery>-?\d+)$",
        None,
        True,
        False,
        {"sn": int, "target": int, "reason": int, "recovery": int},
    ),
    TriggerSpec(
        "skills_start",
        r"^\{spellheaders\s((?P<type>.*)\s)?noprompt\}$",
        GROUP_SLIST,
        False,
        True,
        None,
    ),
    TriggerSpec("skills_spellheaders_end", r"^\{/spellheaders\}$", GROUP_SLIST, False, True, None),
    TriggerSpec(
        "skills_recov_start",
        r"^\{recoveries\s((?P<type>.*)\s)?noprompt\}$",
        GROUP_SLIST,
        False,
        True,
        None,
    ),
    TriggerSpec("skills_recoveries_end", r"^\{/recoveries\}$", GROUP_SLIST, False, True, None),
    TriggerSpec(
        "skills_spell_line",
        r"^(?P<sn>\d+),(?P<name>.+),(?P<target>\d+),(?P<duration>\d+),(?P<pct>\d+),"
        r"(?P<rcvy>-?\d+),(?P<type>\d+)$",
        GROUP_SPELLS,
        False,
        True,
        {"sn": int, "target": int, "duration": int, "pct": int, "rcvy": int, "type": int},
    ),
    TriggerSpec(
        "skills_recov_line",
        r"^(?P<sn>\d+),(?P<name>.+),(?P<duration>\d+)$",
        GROUP_RECOVERIES,
        False,
        True,
        {"sn": int, "duration": int},
    ),
)


def find_by_name(name: str, names: Iterable[str]) -> str | None:
    """Return the one name that equals, starts with or contains ``name``, else None.

    An exact match wins, then the names that start with it, then the names that contain it; the
    first step with any hit decides, and it must have exactly one.
    """
    candidates = list(names)
    if name in candidates:
        return name
    for hits in (
        [n for n in candidates if n.startswith(name)],
        [n for n in candidates if name in n],
    ):
        if hits:
            return hits[0] if len(hits) == 1 else None
    return None


def code_name(table: Mapping[int, str], code: int) -> str:
    """Return the name of a code, or the code as text when the table does not know it."""
    return table.get(code, str(code))


def fail_payload(sn: int, target: int, reason: int, recovery: int) -> dict[str, Any]:
    """Return the payload of a skill-fail event, with the codes named."""
    return {
        "sn": sn,
        "reason": code_name(FAILREASON, reason),
        "target": code_name(FAILTARG, target),
        "recovery": recovery,
    }


def _expiry(duration: int, now: float) -> float:
    """Return the time an affect ends, or 0 when there is none."""
    return now + duration if duration > 0 else 0


class SkillTable:
    """The skills and recoveries by sn, with lookups by sn or name and the up-to-date flag."""

    def __init__(self) -> None:
        self.skills: dict[int, dict[str, Any]] = {}
        self.recoveries: dict[int, dict[str, Any]] = {}
        self.uptodate = False

    def count(self) -> int:
        """Return the number of skills."""
        return len(self.skills)

    def reset(self) -> None:
        """Forget everything."""
        self.skills = {}
        self.recoveries = {}
        self.uptodate = False

    def reset_affected(self) -> None:
        """Zero every duration, before an affected slist sets the current ones."""
        for skill in self.skills.values():
            skill["duration"] = 0
        for recovery in self.recoveries.values():
            recovery["duration"] = 0

    def add_skill(self, fields: Mapping[str, Any], now: float) -> None:
        """Add or replace a skill from the fields of a slist line."""
        sn = int(fields["sn"])
        self.skills[sn] = {
            "sn": sn,
            "name": fields["name"],
            "target": code_name(TARGET, fields["target"]),
            "duration": _expiry(fields["duration"], now),
            "percent": fields["pct"],
            "recovery": fields["rcvy"],
            "type": code_name(STYPE, fields["type"]),
            "spellup": False,
        }

    def add_recovery(self, fields: Mapping[str, Any], now: float) -> None:
        """Add or replace a recovery from the fields of a slist line."""
        sn = int(fields["sn"])
        self.recoveries[sn] = {
            "sn": sn,
            "name": fields["name"],
            "duration": _expiry(fields["duration"], now),
        }

    def set_duration(self, sn: int, seconds: int, now: float) -> bool:
        """Set when the affect of a skill ends; False for an unknown sn."""
        if sn not in self.skills:
            return False
        self.skills[sn]["duration"] = _expiry(seconds, now)
        return True

    def set_recovery_duration(self, sn: int, seconds: int, now: float) -> bool:
        """Set when a recovery ends; False for an unknown sn."""
        if sn not in self.recoveries:
            return False
        self.recoveries[sn]["duration"] = _expiry(seconds, now)
        return True

    def set_percent(self, sn: int, percent: int) -> bool:
        """Set the percent learned; False for an unknown sn."""
        if sn not in self.skills:
            return False
        self.skills[sn]["percent"] = percent
        return True

    def flag_spellup(self, sn: int) -> bool:
        """Flag a spell as a spellup; False for an unknown sn."""
        if sn not in self.skills:
            return False
        self.skills[sn]["spellup"] = True
        return True

    @staticmethod
    def _find(table: Mapping[int, dict[str, Any]], key: int | str) -> dict[str, Any] | None:
        """Return the entry of an sn, a digit string or a name, or None."""
        if isinstance(key, int) or str(key).isdigit():
            return table.get(int(key))
        by_name = {str(entry["name"]): sn for sn, entry in table.items()}
        found = find_by_name(str(key), by_name)
        return table[by_name[found]] if found is not None else None

    def get_recovery(self, key: int | str) -> dict[str, Any] | None:
        """Return a copy of a recovery by sn or name, or None."""
        found = self._find(self.recoveries, key)
        return copy.deepcopy(found) if found is not None else None

    def get_skill(self, key: int | str) -> dict[str, Any] | None:
        """Return a copy of a skill by sn or name, with its recovery resolved, or None."""
        found = self._find(self.skills, key)
        if found is None:
            return None
        skill = copy.deepcopy(found)
        skill["recovery"] = self.get_recovery(found["recovery"]) if found["recovery"] >= 0 else None
        return skill

    def spellups(self) -> list[dict[str, Any]]:
        """Return copies of the spellups."""
        return [copy.deepcopy(s) for s in self.skills.values() if s["spellup"]]

    def is_affected(self, key: int | str) -> bool:
        """Return True when the skill has an affect running."""
        skill = self._find(self.skills, key)
        return skill is not None and skill["duration"] > 0

    def is_blocked_by_recovery(self, key: int | str) -> bool:
        """Return True when a recovery that blocks the skill is running."""
        skill = self.get_skill(key)
        return bool(skill and skill["recovery"] and skill["recovery"]["duration"] > 0)

    def is_practiced(self, key: int | str) -> bool:
        """Return True when more than 10 percent is learned."""
        skill = self._find(self.skills, key)
        return skill is not None and skill["percent"] > 10

    def is_spellup(self, key: int | str) -> bool:
        """Return True for a spellup."""
        skill = self._find(self.skills, key)
        return skill is not None and bool(skill["spellup"])

    def can_use(self, key: int | str) -> bool:
        """Return True when the skill is practiced, not affected and not blocked."""
        return (
            self.is_practiced(key)
            and not self.is_affected(key)
            and not self.is_blocked_by_recovery(key)
        )

    def is_bad(self, key: int | str) -> bool:
        """Return True for an attack or special skill that is not a spellup."""
        skill = self._find(self.skills, key)
        return (
            skill is not None and skill["target"] in ("attack", "special") and not skill["spellup"]
        )
