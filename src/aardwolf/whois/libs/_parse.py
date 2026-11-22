"""Regexes and pure helpers that turn whois output and GMCP values into the whois state."""

from collections.abc import Callable, Mapping
from typing import Any

from aardwolf.libs.aardu import CLASSABBREV, actual_level

WHOIS_COMMAND_REGEX = r"^(whoi|whois)$"
HEADER_REGEX = r"^\[.*\]\s+.*\s*\((?P<sex>\w+)\s+\w+\)$"
CLASSES_REGEX = r"^\[Multiclass Player: (?P<classes>.*) \]$"
STAT1_REGEX = r"^(?P<name1>[\w\s]*)\s*:\s*\[\s*(?P<val1>[\w\d\s]*)\s*\]\s*$"
STAT2_REGEX = (
    r"^(?P<name1>[\w\s]*)\s*:\s*\[\s*(?P<val1>[\w\d\s]*)\s*\]"
    r"\s*(?P<name2>[\w\s]*)\s*:\s*\[\s*(?P<val2>[\w\d\s]*)\s*\]\s*$"
)
STAT3_REGEX = (
    r"^(?P<name1>[\w\s]*)\s*:\s*\[\s*(?P<val1>[\w\d\s]*)\s*\]"
    r"\s*(?P<name2>[\w\s]*)\s*:\s*\[\s*(?P<val2>[\w\d\s]*)\s*\]"
    r"\s*(?P<name3>[\w\s]*)\s*:\s*\[\s*(?P<val3>[\w\d\s]*)\s*\]\s*$"
)
POWERUP_REGEX = (
    r"^(?P<name1>[\w\s]*)\s*:\s*\[\s*(?P<val1>[\w\d\s]*)\s*\]"
    r"\s*([\w\s]*)\s*:\s*\[\s*(?P<pval1>[\w\d\s]*)\s*\]\s*\[\s*"
    r"(?P<pval2>[\w\d\s]*)\s*\]\s*$"
)
END_REGEX = r"^-{74,74}$"


def _int(value: object, default: int = 0) -> int:
    """Return a value as an int, or the default when it is missing or not numeric."""
    if isinstance(value, bool) or not isinstance(value, int | float | str | bytes):
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _lower(value: object) -> str:
    """Return a value as lower-case text, or an empty string when it is missing."""
    return "" if value is None else str(value).lower()


def stat_values(matches: Mapping[str, str | None]) -> dict[str, str]:
    """Return the stats of a whois stat line, keyed by the lower-case label without spaces."""
    stats: dict[str, str] = {}
    for i in range(1, 4):
        name = matches.get(f"name{i}")
        value = matches.get(f"val{i}")
        if name is None or value is None:
            continue
        key = name.lower().strip().replace(" ", "")
        if key:
            stats[key] = value.strip()
    for key, group in (("powerupsall", "pval1"), ("powerupsmort", "pval2")):
        value = matches.get(group)
        if value is not None:
            stats[key] = value.strip()
    return stats


def _class_abbreviation(name: object) -> str:
    """Return the abbreviation of a class name; an unknown name passes through."""
    lowered = _lower(name).strip()
    return CLASSABBREV.get(lowered, lowered)


def multiclass_classes(text: str) -> list[dict[str, object]]:
    """Return the classes of the multiclass line, one per remort, as abbreviations."""
    return [
        {"remort": index + 1, "class": _class_abbreviation(name)}
        for index, name in enumerate(text.split("/"))
    ]


def single_class(name: object) -> list[dict[str, object]]:
    """Return the class list of a character with one class; empty when the class is unknown."""
    abbreviation = _class_abbreviation(name)
    if not abbreviation:
        return []
    return [{"remort": 1, "class": abbreviation}]


def header_values(gmcp_get: Callable[[str], object], sex: str) -> dict[str, Any]:
    """Return the state the whois header sets, read from GMCP; missing values do not raise."""
    name = gmcp_get("char.base.name")
    return {
        "name": "" if name is None else str(name),
        "level": _int(gmcp_get("char.status.level")),
        "tiers": _int(gmcp_get("char.base.tier")),
        "redos": _int(gmcp_get("char.base.redos")),
        "race": _lower(gmcp_get("char.base.race")),
        "sex": sex.lower(),
        "subclass": _lower(gmcp_get("char.base.subclass")),
        "powerupsall": 0,
        "powerupsmort": 0,
        "remorts": _int(gmcp_get("char.base.remorts"), 1),
    }


def total_levels(state: Mapping[str, Any]) -> int:
    """Return the total level of the whois state."""
    return actual_level(
        _int(state.get("level")),
        _int(state.get("remorts"), 1),
        _int(state.get("tiers")),
        _int(state.get("redos")),
    )
