"""Constants, the output reader and the flag learner of the aflags plugin. No bastproxy imports."""

import re
from typing import Any

# the skills plugin's events and the disconnect event, listened to by name
SKILLS_PREFIX = "ev_plugins.aardwolf.skills_"
EVENT_AFFON = f"{SKILLS_PREFIX}affon"
EVENT_AFFOFF = f"{SKILLS_PREFIX}affoff"
EVENT_AFFECTED_UPDATE = f"{SKILLS_PREFIX}affected_update"
EVENT_UPTODATE = f"{SKILLS_PREFIX}uptodate"
EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"

# the event this plugin raises
EVENT_DIFF = "ev_plugins.aardwolf.aflags_diff"

EVENTS: dict[str, dict[str, Any]] = {
    EVENT_DIFF: {
        "description": ["raised when a read of the affect flags found a flag added or removed"],
        "arg_descriptions": {
            "added": "the flags that are new, sorted, as a list",
            "removed": "the flags that are gone, sorted, as a list",
            "sn": "the sn of the affect that changed, or None when it is not one",
        },
    },
}

# the built-in trigger that sees every line; cp reads the end of its output the same way
ALL_LINES_ID = "t_plugins.core.triggers_all"

TYPE_AFLAGS = "aflags"
CMD = "aflags"
CMD_REGEX = r"^aflags$"
TIMEOUT_EVENT = "cmd_{}_timeout"

# the line that starts the output; the flags follow the colon, comma separated
HEADER_REGEX = r"^Affect Flags: (?P<flags>.*)$"
_HEADER = re.compile(HEADER_REGEX)

# the most lines hidden after the header; mudcmds counts the header too, and the blank line
# and the prompt after the flags are hidden as well, so the type gets HIDE_MAX_LINES + 2
HIDE_MAX_LINES = 50


def split_flags(text: str) -> list[str]:
    """Return the flags in a comma separated text, lowercased and stripped, without blanks."""
    flags = (part.strip().lower() for part in text.split(","))
    return [flag for flag in flags if flag]


class AflagsReader:
    """Read the output of ``aflags``, one line at a time.

    Lines before the header are ignored, a prompt of the previous command among them. The header
    starts the read, each non-blank line after it adds flags, an Aardwolf ``{`` tag line is
    skipped, and a blank line or a prompt ends it.
    """

    def __init__(self) -> None:
        """Start with no read."""
        self.flags: set[str] = set()
        self.started = False
        self.finished = False

    def start(self) -> None:
        """Forget the last read."""
        self.flags = set()
        self.started = False
        self.finished = False

    def feed(self, text: str, is_prompt: bool = False) -> bool:
        """Take a line; return True when it ended the read."""
        if self.finished:
            return False
        if not self.started:
            match = _HEADER.match(text)
            if match and not is_prompt:
                self.started = True
                self.flags.update(split_flags(match.group("flags")))
            return False
        if is_prompt or not text.strip():
            self.finished = True
            return True
        if not text.lstrip().startswith("{"):
            self.flags.update(split_flags(text))
        return False


def flag_diff(before: set[str], after: set[str]) -> tuple[list[str], list[str]]:
    """Return the flags added and the flags removed, each sorted."""
    return sorted(after - before), sorted(before - after)


class FlagLearner:
    """Learn which flags an affect sets, from the reads that follow its change.

    ``change`` notes an sn, ``start`` moves the noted sns into the read that begins, and
    ``learn`` stores the flags that read found when exactly one sn changed.
    """

    def __init__(self) -> None:
        """Start with nothing learned."""
        self.table: dict[int, list[str]] = {}
        self._pending: set[int] = set()
        self._reading: set[int] = set()

    def change(self, sn: int) -> None:
        """An affect changed: it belongs to the next read."""
        self._pending.add(sn)

    def start(self) -> None:
        """A read begins: the changes noted so far belong to it."""
        self._reading = self._pending
        self._pending = set()

    def learn(self, added: list[str] | set[str], removed: list[str] | set[str]) -> int | None:
        """A read ended: store the flags under the sn, and return it, when it is clear."""
        reading = self._reading
        self._reading = set()
        diff = sorted(set(added) | set(removed))
        if len(reading) != 1 or not diff:
            return None
        (sn,) = reading
        self.table[sn] = diff
        return sn

    def reset(self) -> None:
        """Drop the changes noted; what was learned stays."""
        self._pending = set()
        self._reading = set()
