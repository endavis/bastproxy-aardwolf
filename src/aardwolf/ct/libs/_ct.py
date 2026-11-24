"""Constants and table helpers of the ct plugin. No bastproxy imports."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

# the event of the mobk plugin; ct keeps its own copy of the name
EVENT_MOBK_KILL = "ev_plugins.aardwolf.mobk_kill"
EMPTYLINE_ID = "t_plugins.core.triggers_emptyline"

LINE_LENGTH = 72
LABEL_WIDTH = 20

# name: (default, help)
SETTINGS: dict[str, tuple[str, str]] = {
    "statcolor": ("@W", "the stat color"),
    "infocolor": ("@x033", "the info color"),
}

_ROW = (
    "{stat}{label} {info}: {stat}{hits:^10} {damage:^10} ({percent:4.0%}) "
    "{misses:^10} {average:^10}"
)


@dataclass(frozen=True)
class TableHelpers:
    """The bastproxy helpers the table uses.

    Attributes:
        center: Centers a text with a filler, ``plugins.core.utils:string.center.colored``;
            called with the text, the filler and the length.
        duration: The time between two times as text, ``plugins.core.utils:timedelta.to.string``;
            called with the start, the end, the color of the numbers and the color of the units.
        escape: Escapes the color codes of a text, ``plugins.core.colors:colorcode.escape``.
    """

    center: Callable[[str, str, int], str]
    duration: Callable[[Any, Any, str, str], str]
    escape: Callable[[str], str]


def pad_label(label: str, escape: Callable[[str], str]) -> str:
    """Escape a label and pad it to 20 columns.

    The padding is counted on the raw label: an escaped ``@`` shows as one column.
    """
    return escape(label) + " " * max(0, LABEL_WIDTH - len(label))


def damage_label(damage_type: str, entry: Mapping[str, Any]) -> str:
    """Return the label of a damage type; a backstab started in combat says so."""
    if damage_type == "backstab" and "incombat" in entry:
        return f"{damage_type} (in)"
    return damage_type


def average(damage: int, hits: int) -> int:
    """Return the whole damage per hit; 0 without hits."""
    return damage // hits if hits else 0


def percent(damage: int, total: int) -> float:
    """Return the share of the total damage, 0 to 1; 0 when there is no damage."""
    return damage / total if total else 0.0


def title_text(kill: Mapping[str, Any], stat: str, info: str, helpers: TableHelpers) -> str:
    """Return the text of the title line: the mob, the fight time and the experience."""
    timestr = ""
    if kill.get("finishtime") and kill.get("starttime"):
        timestr = helpers.duration(kill["starttime"], kill["finishtime"], stat, info)
    xp = f"{stat}{kill['totalxp']}{info}xp"
    return f"{stat}{helpers.escape(str(kill['name']))}{info} : {timestr}{info} - {xp}"


def _row(
    stat: str,
    info: str,
    label: str,
    hits: object,
    damage: object,
    pct: float,
    misses: object,
    ave: object,
) -> str:
    """Return a row of the table."""
    return _ROW.format(
        stat=stat,
        info=info,
        label=label,
        hits=hits,
        damage=damage,
        percent=pct,
        misses=misses,
        average=ave,
    )


def format_kill(kill: Mapping[str, Any], stat: str, info: str, helpers: TableHelpers) -> str:
    """Return the damage table of a kill, as lines joined with newlines."""
    damage: Mapping[str, Mapping[str, Any]] = kill["damage"]
    total = sum(entry["damage"] for entry in damage.values())
    divider = info + "-" * LINE_LENGTH
    lines = [
        divider,
        info + helpers.center(title_text(kill, stat, info, helpers), "-", LINE_LENGTH),
        divider,
        _row(
            info,
            info,
            pad_label("Dam Type", helpers.escape),
            "Hits",
            "Damage",
            0,
            "Misses",
            "Average",
        ),
        divider,
    ]
    total_hits = 0
    total_misses = 0
    for damage_type in sorted(damage):
        entry = damage[damage_type]
        total_hits += entry["hits"]
        total_misses += entry["misses"]
        label = pad_label(damage_label(damage_type, entry), helpers.escape)
        lines.append(
            _row(
                stat,
                info,
                label,
                entry["hits"],
                entry["damage"],
                percent(entry["damage"], total),
                entry["misses"],
                average(entry["damage"], entry["hits"]),
            )
        )
    lines.append(divider)
    lines.append(
        _row(
            stat,
            info,
            pad_label("Total", helpers.escape),
            total_hits,
            total,
            1,
            total_misses,
            average(total, total_hits or 1),
        )
    )
    lines.append(divider)
    return "\n".join(lines)
