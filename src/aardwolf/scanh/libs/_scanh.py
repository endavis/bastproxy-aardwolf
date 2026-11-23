"""Constants and pure helpers of the scan highlight plugin. No bastproxy imports."""

from collections.abc import Mapping, Sequence
from typing import NamedTuple

PLUGIN_ID = "plugins.aardwolf.scanh"
GROUP_SCAN = "scan"

TRIGGER_START = "scanh_start"
TRIGGER_END = "scanh_end"
TRIGGER_LINE = "scanh_line"
SCAN_START_REGEX = r"^\{scan\}$"
SCAN_END_REGEX = r"^\{/scan\}$"
SCAN_LINE_REGEX = r"^ "

# declared here, not imported from the cp, gq and quest plugins: plugins do not import plugins
EVENT_CP_MOBSLEFT = "ev_plugins.aardwolf.cp_mobsleft"
EVENT_CP_COMP = "ev_plugins.aardwolf.cp_comp"
EVENT_CP_FAILED = "ev_plugins.aardwolf.cp_failed"
EVENT_GQ_MOBSLEFT = "ev_plugins.aardwolf.gq_mobsleft"
EVENT_GQ_DONE = "ev_plugins.aardwolf.gq_done"
EVENT_GQ_WON = "ev_plugins.aardwolf.gq_won"
EVENT_GQ_COMPLETED = "ev_plugins.aardwolf.gq_completed"
EVENT_GQ_CANCELLED = "ev_plugins.aardwolf.gq_cancelled"
EVENT_QUEST_START = "ev_plugins.aardwolf.quest_start"
EVENT_QUEST_KILLED = "ev_plugins.aardwolf.quest_killed"
EVENT_QUEST_COMP = "ev_plugins.aardwolf.quest_comp"
EVENT_QUEST_FAILED = "ev_plugins.aardwolf.quest_failed"
EVENT_QUEST_RESET = "ev_plugins.aardwolf.quest_reset"
EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"

CP_MOBS_API = "plugins.aardwolf.cp:mobs.left.get"


class Source(NamedTuple):
    """A source of scan targets: its key, its tag and the names of its colour settings."""

    key: str
    tag: str
    textsetting: str
    backsetting: str


# the order is the order of the tags and of the colours
SOURCES: tuple[Source, ...] = (
    Source("cp", "CP", "cptextcolor", "cpbackcolor"),
    Source("gq", "GQ", "gqtextcolor", "gqbackcolor"),
    Source("quest", "Quest", "questtextcolor", "questbackcolor"),
)

# (name, default, help)
SETTINGS: tuple[tuple[str, str, str], ...] = (
    ("cpbackcolor", "@z14", "the background color for cp mobs"),
    ("gqbackcolor", "@z9", "the background color for gq mobs"),
    ("questbackcolor", "@z13", "the background color for quest mobs"),
    ("cptextcolor", "@x0", "the text color for cp mobs"),
    ("gqtextcolor", "@x0", "the text color for gq mobs"),
    ("questtextcolor", "@x0", "the text color for quest mobs"),
)


def mob_names(mobs: object) -> list[str]:
    """Return the lower-cased names of mob dicts, from nocolorname or name; skip the empty."""
    names: list[str] = []
    if not isinstance(mobs, Sequence) or isinstance(mobs, str):
        return names
    for mob in mobs:
        if not isinstance(mob, dict):
            continue
        name = str(mob.get("nocolorname") or mob.get("name") or "").lower().strip()
        if name:
            names.append(name)
    return names


def name_ends_line(line: str, name: str) -> bool:
    """Return True when the line ends with the name, at the start or after a non-letter."""
    text = line.lower().strip()
    wanted = name.lower().strip()
    if not wanted or not text.endswith(wanted):
        return False
    start = len(text) - len(wanted)
    return start == 0 or not text[start - 1].isalpha()


def matching_sources(line: str, targets: Mapping[str, Sequence[str]]) -> list[Source]:
    """Return the sources with a target the line ends with, in the order of SOURCES."""
    return [
        source
        for source in SOURCES
        if any(name_ends_line(line, name) for name in targets.get(source.key, ()))
    ]


def highlight(escaped_line: str, sources: Sequence[Source], textcolor: str, backcolor: str) -> str:
    """Return the line in the colours, followed by the tag of each source."""
    tags = " ".join(f"({source.tag})" for source in sources)
    return f"{textcolor}{backcolor}{escaped_line} - {tags}@x"
