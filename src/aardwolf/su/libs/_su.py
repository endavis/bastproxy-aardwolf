"""Constants, the spellup list and the casting rules of the su plugin. No bastproxy imports."""

from collections.abc import Callable, Collection, Iterable, MutableMapping
from typing import Any

# the skills plugin's events, the move plugin's event and the disconnect event, listened to by name
EVENT_AFFON = "ev_plugins.aardwolf.skills_affon"
EVENT_AFFOFF = "ev_plugins.aardwolf.skills_affoff"
EVENT_RECOFF = "ev_plugins.aardwolf.skills_recoff"
EVENT_GAIN = "ev_plugins.aardwolf.skills_gain"
EVENT_FAIL = "ev_plugins.aardwolf.skills_fail"
EVENT_AFFECTED_UPDATE = "ev_plugins.aardwolf.skills_affected_update"
EVENT_UPTODATE = "ev_plugins.aardwolf.skills_uptodate"
EVENT_MOVE_ROOM = "ev_plugins.aardwolf.move_room"
EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"
EVENT_GMCP_VITALS = "ev_libs.net.mud_gmcp_char.vitals"
EVENT_GMCP_STATUS = "ev_libs.net.mud_gmcp_char.status"
SETTING_INIT = "__init__"

# the APIs of the skills plugin, used by name
API_SKILL_GET = "plugins.aardwolf.skills:skill.get"
API_SKILL_SEND = "plugins.aardwolf.skills:skill.send"
API_SKILL_CAN_USE = "plugins.aardwolf.skills:skill.can.use"
API_SKILL_IS_AFFECTED = "plugins.aardwolf.skills:skill.is.affected"
API_SKILL_IS_BLOCKED = "plugins.aardwolf.skills:skill.is.blocked.by.recovery"
API_SKILL_IS_PRACTICED = "plugins.aardwolf.skills:skill.is.practiced"
API_SKILL_IS_SPELLUP = "plugins.aardwolf.skills:skill.is.spellup"
API_SPELLUPS_GET = "plugins.aardwolf.skills:spellups.get"
API_UP_TO_DATE = "plugins.aardwolf.skills:is.up.to.date"

GMCP_STATE = "char.status.state"
GMCP_MANA = "char.vitals.mana"
GMCP_MOVES = "char.vitals.moves"
GMCP_ROOM_NUM = "room.info.num"
ACTIVE_STATE = 3

SPELLUP_FILE = "spellups.txt"
ORDER_KEY = "sorder"
SELF_KEY = "self"
# keys of the old plugin's file that are never used
DROPPED_KEYS = ("oorder", "other")
TIMER_NAME = "su_waiting"
WAIT_TIMEOUT = 15
GROUP = "Spellups on Self"
# a spell with this percent or less is not practiced
PRACTICED_ABOVE = 10
# the names of the settings that default to the two constants above
SETTING_PRACTICED_ABOVE = "practicedabove"
SETTING_WAIT_TIMEOUT = "waittimeout"

# what a failed cast asks the plugin to do
ACTION_IGNORE = "ignore"
ACTION_NOMANA = "nomana"
ACTION_NOMOVES = "nomoves"
ACTION_NOCASTROOM = "nocastroom"
ACTION_STOP = "stop"
ACTION_RESEND = "resend"
ACTION_DISABLE = "disable"
ACTION_BLOCK = "block"
ACTION_CLEAR = "clear"

# the failures that disable the spell, with why
DISABLE_REASONS: dict[str, str] = {
    "alreadyaff": "you are already affected",
    "disabled": "it is disabled mudside",
    "wrongtarget": "it can not be cast on yourself",
}
_ANY_SN_ACTIONS: dict[str, str] = {
    "nomana": ACTION_NOMANA,
    "nomoves": ACTION_NOMOVES,
    "nocastroom": ACTION_NOCASTROOM,
    "fighting": ACTION_STOP,
    "notactive": ACTION_STOP,
}

_ROW = "%-3s - %-30s : %2s %2s %2s %2s  %-2s  %-2s"
_CHECK = "%-25s : %-10s - %s"


def to_int(value: object) -> int | None:
    """Return an int for an int or a string of digits, else None (a bool is not a number)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def is_active_state(state: object) -> bool:
    """Return True when the GMCP character state is the active one (3, or the text "3")."""
    return to_int(state) == ACTIVE_STATE


def room_key(room: object) -> str | None:
    """Return the key of a room.info message in the nocast rooms, or None without a num."""
    if isinstance(room, dict):
        num = to_int(room.get("num"))
        return None if num is None else str(num)
    return None


def parse_spell_arg(arg: str) -> tuple[str, int] | None:
    """Split ``name`` or ``name:place`` into the name and the place (-1 for the end).

    Returns None when the name is empty or the place is not a number.
    """
    name, sep, place = arg.partition(":")
    if not name:
        return None
    if not sep:
        return name, -1
    number = to_int(place)
    return None if number is None else (name, number)


def next_spell(
    order: Iterable[int],
    is_enabled: Callable[[int], bool],
    can_use: Callable[[int], bool],
    skip: Collection[int] = (),
) -> int | None:
    """Return the first sn in order that is enabled, not skipped and usable, else None."""
    for sn in order:
        if sn not in skip and is_enabled(sn) and can_use(sn):
            return sn
    return None


def cast_blockers(
    *,
    enabled: bool,
    connected: bool,
    active: bool,
    state: object,
    up_to_date: bool,
    waiting: int | None,
    nocast: bool,
    nomana: bool,
    nomoves: bool,
) -> list[str]:
    """Return the reasons nothing is cast now; an empty list means a spell may be cast."""
    reasons: list[str] = []
    checks = (
        (not enabled, "not enabled"),
        (not connected, "not connected to the mud"),
        (not active, "character is not active"),
        (not is_active_state(state), "character state is not 3"),
        (not up_to_date, "skills are not up to date"),
        (waiting is not None, "waiting for a cast"),
        (nocast, "in a nocast room"),
        (nomana, "out of mana"),
        (nomoves, "out of moves"),
    )
    for blocked, reason in checks:
        if blocked:
            reasons.append(reason)
    return reasons


def fail_action(reason: object, sn: object, waiting: int | None) -> str:
    """Return what a failed cast asks for, from the reason and whether it is the cast waited on."""
    if isinstance(reason, str) and reason in _ANY_SN_ACTIONS:
        return _ANY_SN_ACTIONS[reason]
    if waiting is None or sn != waiting:
        return ACTION_IGNORE
    if reason == "lostconc":
        return ACTION_RESEND
    if isinstance(reason, str) and reason in DISABLE_REASONS:
        return ACTION_DISABLE
    if reason == "recblock":
        return ACTION_BLOCK
    return ACTION_CLEAR


def list_header() -> list[str]:
    """Return the two header lines of the list command."""
    return [_ROW % ("Num", "Name", "A", "P", "B", "D", "NP", "NL"), "@B" + "-" * 60]


def list_row(
    index: int,
    name: str,
    *,
    affected: bool,
    pending: bool,
    blocked: bool,
    disabled: bool,
    percent: int,
    practiced_above: int = PRACTICED_ABOVE,
) -> str:
    """Return a line of the list command.

    A spell at ``practiced_above`` percent or less is shown as not practiced.
    """
    return _ROW % (
        index,
        name,
        "A" if affected else "",
        "P" if pending else "",
        "B" if blocked else "",
        "D" if disabled else "",
        "NP" if 0 < percent <= practiced_above else "",
        "NL" if percent <= 0 else "",
    )


def check_lines(
    *,
    enabled: bool,
    connected: bool,
    active: bool,
    waiting: int | None,
    nocast: bool,
    nomoves: bool,
    nomana: bool,
    up_to_date: bool,
    state: object,
) -> list[str]:
    """Return the lines of the check command."""
    return [
        _CHECK % ("enabled", enabled, "should be True to cast spells"),
        _CHECK % ("connected", connected, "should be True to cast spells"),
        _CHECK % ("character active", active, "should be True to cast spells"),
        _CHECK
        % ("waiting", waiting, "the spell that was last cast, should be None to cast spells"),
        _CHECK % ("nocast", nocast, "the room is nocast, should be False to cast spells"),
        _CHECK % ("nomoves", nomoves, "ran out of moves, should be False to cast spells"),
        _CHECK % ("nomana", nomana, "ran out of mana, should be False to cast spells"),
        _CHECK % ("Skills are up to date", up_to_date, "should be True to cast spells"),
        _CHECK % ("Char state", state, "should be 3 to cast spells"),
    ]


class SpellupList:
    """The spellups on self over a mapping with the keys ``sorder`` and ``self``.

    ``sorder`` is the list of sn in cast order; ``self`` maps a sn to ``{"enabled": bool}``.
    The mapping is a PersistentDict in the plugin, so a changed list is saved with a sync.
    """

    def __init__(self, data: MutableMapping[str, Any]) -> None:
        """Wrap the mapping and normalize it."""
        self.data = data
        self.normalize()

    def normalize(self) -> bool:
        """Repair the mapping; return True when something changed.

        Drops the unused keys of the old plugin, turns digit strings into ints, removes
        duplicates and orphan entries, and enables a spell with no entry.
        """
        changed = False
        for key in DROPPED_KEYS:
            if key in self.data:
                del self.data[key]
                changed = True
        raw_order = self.data.get(ORDER_KEY)
        raw_self = self.data.get(SELF_KEY)
        order: list[int] = []
        for value in raw_order if isinstance(raw_order, list) else []:
            sn = to_int(value)
            if sn is not None and sn not in order:
                order.append(sn)
        entries: dict[int, dict[str, bool]] = {}
        old_entries = raw_self if isinstance(raw_self, dict) else {}
        by_sn: dict[int, Any] = {}
        for key, value in old_entries.items():
            sn = to_int(key)
            if sn is not None:
                by_sn[sn] = value
        for sn in order:
            entry = by_sn.get(sn)
            enabled = entry.get("enabled", True) if isinstance(entry, dict) else True
            entries[sn] = {"enabled": bool(enabled)}
        if raw_order != order or raw_self != entries:
            self.data[ORDER_KEY] = order
            self.data[SELF_KEY] = entries
            changed = True
        return changed

    def order(self) -> list[int]:
        """Return a copy of the cast order."""
        return list(self.data[ORDER_KEY])

    def contains(self, sn: int) -> bool:
        """Return True when the sn is in the list."""
        return sn in self.data[SELF_KEY]

    def is_enabled(self, sn: int) -> bool:
        """Return True when the sn is in the list and enabled."""
        entry = self.data[SELF_KEY].get(sn)
        return bool(entry and entry["enabled"])

    def add(self, sn: int, place: int = -1) -> int | None:
        """Add an enabled sn at the place (-1 for the end); return its index, None if present."""
        if self.contains(sn):
            return None
        self.data[SELF_KEY][sn] = {"enabled": True}
        if place > -1:
            self.data[ORDER_KEY].insert(place, sn)
        else:
            self.data[ORDER_KEY].append(sn)
        return int(self.data[ORDER_KEY].index(sn))

    def remove(self, sn: int) -> bool:
        """Remove the sn; return True when it was in the list."""
        if not self.contains(sn):
            return False
        self.data[ORDER_KEY].remove(sn)
        del self.data[SELF_KEY][sn]
        return True

    def clear(self) -> None:
        """Remove every spellup."""
        self.data[ORDER_KEY] = []
        self.data[SELF_KEY] = {}

    def set_enabled(self, sn: int, enabled: bool) -> bool:
        """Enable or disable the sn; return True when it is in the list."""
        if not self.contains(sn):
            return False
        self.data[SELF_KEY][sn]["enabled"] = enabled
        return True

    def set_all(self, enabled: bool) -> None:
        """Enable or disable every spellup."""
        for entry in self.data[SELF_KEY].values():
            entry["enabled"] = enabled
