"""Pure helpers for the afk plugin: the names, the title patterns and the tell handling."""

import time
from collections.abc import Iterable, Mapping
from typing import Any, NamedTuple

# the events afk listens to; copied, because a plugin never imports another
EVENT_CLIENT_DISCONNECTED = "ev_plugins.core.clients_client_disconnected"
EVENT_CLIENT_LOGGED_IN = "ev_plugins.core.clients_client_logged_in"
EVENT_GMCP_COMM = "ev_libs.net.mud_gmcp_comm.channel"
EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"

GMCP_MODULES = ["Comm 1"]

TYPE_TITLE = "afk_title"
TITLE_CMD = "title"
TITLE_REGEX = r"^title .+$"
# the title command with no arguments, which reads the current title
TYPE_TITLE_READ = "afk_title_read"
TITLE_READ_REGEX = r"^title$"
CLEAR_ARG = "clear"
TIMEOUT_EVENT = "cmd_{}_timeout"
GROUP_REPLY = "reply"
WATCH_NAME = "afk_title"

# The title command as a client types it, with the abbreviations the old plugin accepted. The
# abbreviations are not confirmed against Aardwolf.
WATCH_TITLE_REGEX = r"^(?:tit|titl|title) (?P<title>.*)$"

# The lines the MUD answers the title command with, confirmed on a real Aardwolf character. They
# open the hide window of a queued title and are the reply triggers.
TITLE_SET_REGEX = r"^Title now set to: (?P<title>.*)$"
TITLE_IS_REGEX = r"^Your title is: ?(?P<title>.*)$"
TITLE_CLEARED_REGEX = r"^Your title is cleared\.$"
# the lines that open the hide window of a queued set or clear
TITLE_REPLY_REGEX = f"{TITLE_SET_REGEX}|{TITLE_CLEARED_REGEX}"

# the most lines hidden after the opening line; mudcmds counts the opening line too
HIDE_MAX = 5

DEFAULT_AFK_TITLE = "is AFK."
TELL_CHANNEL = "tell"
TIME_FORMAT = "%a %b %d %Y %H:%M:%S"
# the name of the setting that defaults to TIME_FORMAT
SETTING_TIME_FORMAT = "timeformat"
QUEUE_KEY = "queue"


class TriggerSpec(NamedTuple):
    """A trigger the plugin adds: its name, regex and the group it is in."""

    name: str
    regex: str
    group: str


# the group is off until a title is pending
TRIGGERS: tuple[TriggerSpec, ...] = (
    TriggerSpec("afk_title_set", TITLE_SET_REGEX, GROUP_REPLY),
    TriggerSpec("afk_title_is", TITLE_IS_REGEX, GROUP_REPLY),
    TriggerSpec("afk_title_cleared", TITLE_CLEARED_REGEX, GROUP_REPLY),
)


def count_active(states: Iterable[tuple[bool, bool]]) -> int:
    """Return how many clients can play.

    Each state is (logged in, view only). A client that has not logged in, or that only views,
    does not count.
    """
    return sum(1 for logged_in, view_only in states if logged_in and not view_only)


def tell_entry(data: object, now: float) -> dict[str, Any] | None:
    """Return the entry to keep for a GMCP comm.channel message, or None when it is no tell.

    The entry holds the time as an epoch float, the sender and the message.
    """
    if not isinstance(data, Mapping) or data.get("chan") != TELL_CHANNEL:
        return None
    return {
        "timestamp": float(now),
        "player": str(data.get("player") or ""),
        "msg": str(data.get("msg") or ""),
    }


def title_to_send(is_afk: bool, afk_title: str, last_title: str) -> str | None:
    """Return the title to send, or None when it is empty."""
    title = afk_title if is_afk else last_title
    return title or None


def restore_args(last_title: str) -> str:
    """Return the arguments of the title command that ends AFK.

    An empty last title is restored with ``clear``: a bare ``title`` would only show the title.
    """
    return last_title or CLEAR_ARG


def read_title(captured: str | None, afk_title: str) -> str:
    """Return the title to remember from the MUD's answer to a bare ``title``.

    An empty answer means no title. A title equal to the afk title is not remembered, so ending
    AFK clears it instead of setting the afk title back.
    """
    title = (captured or "").strip()
    return "" if title == afk_title else title


def remember_title(typed: str | None, afk_title: str) -> str | None:
    """Return the typed title to keep as the last title, or None.

    A title the player typed that equals the afk title is not kept: it is the afk title set by hand.
    """
    if not typed or typed == afk_title:
        return None
    return typed


def _row(entry: object, time_format: str = TIME_FORMAT) -> str | None:
    """Return the display row of a stored tell, or None when the entry is bad."""
    if not isinstance(entry, Mapping):
        return None
    stamp = entry.get("timestamp")
    if isinstance(stamp, bool) or not isinstance(stamp, int | float):
        return None
    when = time.strftime(time_format, time.localtime(stamp))
    player = str(entry.get("player") or "")
    msg = str(entry.get("msg") or "")
    return f"{when:>25} - {player}: {msg}" if player else f"{when:>25} - {msg}"


def format_tells(entries: Iterable[object], time_format: str = TIME_FORMAT) -> list[str]:
    """Return the lines that show the kept tells, timed in ``time_format``.

    A bad entry is skipped.
    """
    rows = [row for row in (_row(entry, time_format) for entry in entries) if row is not None]
    if not rows:
        return ["The queue is empty"]
    return ["Tells received while afk", *rows]


def queue_notice(count: int) -> list[str]:
    """Return the lines that tell the client how many tells wait, none when there are none."""
    if count <= 0:
        return []
    noun = "tell" if count == 1 else "tells"
    return ["@BAFK Queue", f"@BYou have {count} {noun} in the queue"]
