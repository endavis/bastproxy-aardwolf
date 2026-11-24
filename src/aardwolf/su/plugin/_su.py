"""Aardwolf su plugin: recast the spellups of the character on itself when they wear off."""

import logging
from typing import Any

from bastproxy.libs.logger import log_to
from bastproxy.libs.persistentdict import PersistentDict
from bastproxy.libs.records import NetworkData, NetworkDataLine, SendDataDirectlyToClient
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.commands import AddArgument, AddCommand, AddParser, CommandResult
from bastproxy.plugins.core.events import RegisterToEvent

from ..libs import (
    ACTION_BLOCK,
    ACTION_CLEAR,
    ACTION_DISABLE,
    ACTION_NOCASTROOM,
    ACTION_NOMANA,
    ACTION_NOMOVES,
    ACTION_RESEND,
    ACTION_STOP,
    API_SKILL_CAN_USE,
    API_SKILL_GET,
    API_SKILL_IS_AFFECTED,
    API_SKILL_IS_BLOCKED,
    API_SKILL_IS_PRACTICED,
    API_SKILL_IS_SPELLUP,
    API_SKILL_SEND,
    API_SPELLUPS_GET,
    API_UP_TO_DATE,
    DISABLE_REASONS,
    EVENT_AFFECTED_UPDATE,
    EVENT_AFFOFF,
    EVENT_AFFON,
    EVENT_DISCONNECT,
    EVENT_ENABLED_MODIFIED,
    EVENT_FAIL,
    EVENT_GAIN,
    EVENT_GMCP_STATUS,
    EVENT_GMCP_VITALS,
    EVENT_MOVE_ROOM,
    EVENT_RECOFF,
    EVENT_UPTODATE,
    GMCP_MANA,
    GMCP_MOVES,
    GMCP_ROOM_NUM,
    GMCP_STATE,
    GROUP,
    SETTING_INIT,
    SPELLUP_FILE,
    TIMER_NAME,
    WAIT_TIMEOUT,
    SpellupList,
    cast_blockers,
    check_lines,
    fail_action,
    is_active_state,
    list_header,
    list_row,
    next_spell,
    parse_spell_arg,
    room_key,
    to_int,
)

NOCAST_ROOMS = "nocastrooms"


class SuPlugin(BasePlugin):
    """Cast the spellups on self, one at a time, whenever one is missing and a cast can work."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Load the saved spellups and create the empty state."""
        self.spellups = PersistentDict(
            self.plugin_id, self.plugin_info.data_directory / SPELLUP_FILE, "c"
        )
        self.ups = SpellupList(self.spellups)
        self.spellups.sync()
        # the spell cast and not answered yet; None when no cast is waiting
        self._waiting: int | None = None
        self._nocast = False
        self._nomana = False
        self._nomoves = False
        self._lastmana = -1
        self._lastmoves = -1
        # the spells a recovery blocks, until a recovery ends or the connection drops
        self._blocked: set[int] = set()

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the settings and set the nocast state from the room the character is in."""
        add = self.api("plugins.core.settings:setting.add")
        add(self.plugin_id, "enabled", True, bool, "auto spellup is enabled")
        add(
            self.plugin_id,
            NOCAST_ROOMS,
            {},
            dict,
            "the rooms where casting is not allowed",
            readonly=True,
        )
        self._nocast = self._room_is_nocast(self._gmcp_room())

    @RegisterPluginHook("character_active")
    def _phook_character_active(self) -> None:
        """The character is active: cast what is missing."""
        self._nextspell()

    @RegisterPluginHook("save")
    def _phook_save(self) -> None:
        """Save the spellups."""
        self.spellups.sync()

    @RegisterPluginHook("uninitialize", priority=10)
    def _phook_uninitialize(self) -> None:
        """Remove the waiting timer."""
        self._remove_timer()

    # helpers

    def _record(self) -> dict[str, Any]:
        """Return the record of the current event."""
        return dict(self.api("plugins.core.events:event.current.record.get")() or {})

    def _args(self) -> dict[str, Any]:
        """Return the arguments of the running command."""
        args = self.api("plugins.core.commands:command.current.args.get")()
        return dict(args) if args else {}

    def _setting(self, name: str) -> object:
        """Return a setting of the plugin."""
        return self.api("plugins.core.settings:setting.get")(self.plugin_id, name)

    def _gmcp(self, path: str) -> object:
        """Return a GMCP value."""
        return self.api("libs.net.protocols:gmcp.value.get")(path)

    def _gmcp_room(self) -> str | None:
        """Return the key of the room the character is in, or None when it is not known."""
        return room_key({"num": self._gmcp(GMCP_ROOM_NUM)})

    def _client(self, lines: list[str]) -> None:
        """Send lines to the clients."""
        data = NetworkData(
            [NetworkDataLine(line, preamble=False) for line in lines],
            owner_id=f"{self.plugin_id}:notice",
        )
        SendDataDirectlyToClient(data)()

    def _debug(self, message: str, *args: object) -> None:
        """Write a debug line to the plugin log."""
        log_to(self.plugin_id, logging.DEBUG, message, *args)

    def _nocast_rooms(self) -> dict[str, bool]:
        """Return the nocast rooms."""
        rooms = self._setting(NOCAST_ROOMS)
        return dict(rooms) if isinstance(rooms, dict) else {}

    def _room_is_nocast(self, room: str | None) -> bool:
        """Return True when the room is a known nocast room."""
        return room is not None and room in self._nocast_rooms()

    @staticmethod
    def _key(arg: str) -> int | str:
        """Return a spell argument as the sn when it is a number, else the name."""
        number = to_int(arg)
        return arg if number is None else number

    def _skill(self, arg: str) -> dict[str, Any] | None:
        """Return the skill an argument names, or None."""
        skill = self.api(API_SKILL_GET)(self._key(arg))
        return skill if isinstance(skill, dict) else None

    # waiting

    def _remove_timer(self) -> None:
        """Remove the waiting timer when there is one (timer.remove logs an error otherwise)."""
        if self.api("plugins.core.timers:timer.exists")(TIMER_NAME):
            self.api("plugins.core.timers:timer.remove")(TIMER_NAME)

    def _clear_waiting(self) -> None:
        """Stop waiting for a cast."""
        self._waiting = None
        self._remove_timer()

    def _start_waiting(self, sn: int) -> None:
        """Wait for the answer to a cast, for at most WAIT_TIMEOUT seconds."""
        self._waiting = sn
        self._remove_timer()
        self.api("plugins.core.timers:timer.add")(
            TIMER_NAME, self._timer_waiting, WAIT_TIMEOUT, onetime=True
        )

    def _timer_waiting(self) -> None:
        """The cast got no answer in time: stop waiting, without casting again at once."""
        self._debug("no answer to the cast of %s in %d seconds", self._waiting, WAIT_TIMEOUT)
        self._waiting = None

    # casting

    def _blockers(self) -> list[str]:
        """Return the reasons nothing is cast now."""
        state = self._gmcp(GMCP_STATE)
        return cast_blockers(
            enabled=bool(self._setting("enabled")),
            connected=bool(self.api("plugins.core.proxy:mud.is.connected")()),
            active=bool(self.api("libs.api:character.is.active")()),
            state=state,
            up_to_date=bool(self.api(API_UP_TO_DATE)()),
            waiting=self._waiting,
            nocast=self._nocast,
            nomana=self._nomana,
            nomoves=self._nomoves,
        )

    def _nextspell(self) -> None:
        """Cast the next spell that can be cast, when casting is allowed."""
        blockers = self._blockers()
        if blockers:
            self._debug("not casting: %s", ", ".join(blockers))
            return
        can_use = self.api(API_SKILL_CAN_USE)
        skip: set[int] = set(self._blocked)
        while True:
            sn = next_spell(self.ups.order(), self.ups.is_enabled, can_use, skip)
            if sn is None:
                return
            if self.api(API_SKILL_SEND)(sn):
                self._start_waiting(sn)
                return
            skip.add(sn)

    def _disable(self, sn: int, why: str) -> None:
        """Disable a spell, save, and tell the client."""
        self.ups.set_enabled(sn, False)
        self.spellups.sync()
        skill = self._skill(str(sn)) or {}
        name = skill.get("name", sn)
        self._client([f"@BSpellup - disabled {name} because {why}"])

    # events

    @RegisterToEvent(event_name=EVENT_AFFON)
    def _eventcb_affon(self) -> None:
        """An affect started: when it is the cast waited on, stop waiting."""
        if self._record().get("sn") == self._waiting:
            self._clear_waiting()
        self._nextspell()

    @RegisterToEvent(event_name=EVENT_AFFOFF)
    def _eventcb_affoff(self) -> None:
        """An affect ended: cast it again."""
        self._nextspell()

    @RegisterToEvent(event_name=EVENT_AFFECTED_UPDATE)
    def _eventcb_affected_update(self) -> None:
        """The durations of the affects were read."""
        self._nextspell()

    @RegisterToEvent(event_name=EVENT_UPTODATE)
    def _eventcb_uptodate(self) -> None:
        """The skills are known."""
        self._nextspell()

    @RegisterToEvent(event_name=EVENT_RECOFF)
    def _eventcb_recoff(self) -> None:
        """A recovery ended: the spells it blocked can be cast again."""
        self._blocked.clear()
        self._nextspell()

    @RegisterToEvent(event_name=EVENT_GAIN)
    def _eventcb_gain(self) -> None:
        """A skill was practiced: cast it when it is a spellup."""
        sn = to_int(self._record().get("sn"))
        if sn is not None and self.ups.contains(sn):
            self._nextspell()

    @RegisterToEvent(event_name=EVENT_FAIL)
    def _eventcb_fail(self) -> None:
        """A cast failed: do what the reason asks."""
        record = self._record()
        sn = to_int(record.get("sn"))
        reason = record.get("reason")
        action = fail_action(reason, sn, self._waiting)
        if action == ACTION_NOMANA:
            self._clear_waiting()
            self._nomana = True
            self._lastmana = to_int(self._gmcp(GMCP_MANA)) or -1
        elif action == ACTION_NOMOVES:
            self._clear_waiting()
            self._nomoves = True
            self._lastmoves = to_int(self._gmcp(GMCP_MOVES)) or -1
        elif action == ACTION_NOCASTROOM:
            self._clear_waiting()
            self._nocast = True
            room = self._gmcp_room()
            if room is not None:
                rooms = {**self._nocast_rooms(), room: True}
                self.api("plugins.core.settings:setting.set")(self.plugin_id, NOCAST_ROOMS, rooms)
        elif action in (ACTION_STOP, ACTION_CLEAR):
            self._clear_waiting()
        elif sn is None:
            return
        elif action == ACTION_RESEND:
            self.api(API_SKILL_SEND)(sn)
            self._start_waiting(sn)
        elif action == ACTION_DISABLE:
            self._clear_waiting()
            self._disable(sn, DISABLE_REASONS[str(reason)])
            self._nextspell()
        elif action == ACTION_BLOCK:
            self._clear_waiting()
            self._blocked.add(sn)
            self._nextspell()

    @RegisterToEvent(event_name=EVENT_DISCONNECT)
    def _eventcb_disconnect(self) -> None:
        """The connection dropped: forget what a connection knew."""
        self._clear_waiting()
        self._nocast = False
        self._nomana = False
        self._nomoves = False
        self._lastmana = -1
        self._lastmoves = -1
        self._blocked.clear()

    @RegisterToEvent(event_name=EVENT_GMCP_VITALS)
    def _eventcb_vitals(self) -> None:
        """Mana or moves came back: cast again."""
        resume = False
        if self._nomana:
            mana = to_int(self._gmcp(GMCP_MANA))
            if mana is not None and mana > self._lastmana:
                self._lastmana = -1
                self._nomana = False
                resume = True
        if self._nomoves:
            moves = to_int(self._gmcp(GMCP_MOVES))
            if moves is not None and moves > self._lastmoves:
                self._lastmoves = -1
                self._nomoves = False
                resume = True
        if resume:
            self._nextspell()

    @RegisterToEvent(event_name=EVENT_GMCP_STATUS)
    def _eventcb_status(self) -> None:
        """The character state changed: cast when it is active."""
        if is_active_state(self._gmcp(GMCP_STATE)):
            self._nextspell()

    @RegisterToEvent(event_name=EVENT_MOVE_ROOM)
    def _eventcb_move_room(self) -> None:
        """The character moved: a nocast room stops casting, any other lets it go on."""
        room = room_key(self._record().get("to"))
        if self._room_is_nocast(room):
            self._nocast = True
            return
        was = self._nocast
        self._nocast = False
        if was:
            self._nextspell()

    @RegisterToEvent(event_name=EVENT_ENABLED_MODIFIED)
    def _eventcb_enabled_modified(self) -> None:
        """Casting was turned on: cast what is missing."""
        record = self._record()
        if record.get("newvalue") and record.get("oldvalue") != SETTING_INIT:
            self._nextspell()

    # commands

    def _add_spell(self, arg: str, place: int, override: bool) -> str:
        """Add a spell to the list and return the line to show."""
        skill = self._skill(arg)
        if not skill:
            return f"{arg:<20}: does not exist"
        sn = int(skill["sn"])
        if not override and not self.api(API_SKILL_IS_SPELLUP)(sn):
            return f"{skill['name']:<20}: not a spellup"
        index = self.ups.add(sn, place)
        if index is None:
            return f"{skill['name']:<30}: already activated"
        return f"{skill['name']:<20}:  place {index}"

    @AddCommand(group=GROUP)
    @AddParser(description="add a spellup to the self list")
    @AddArgument(
        "spell",
        help="the spells to add (name or name:place), use 'all' to add all practiced spellups",
        default=[],
        nargs="*",
    )
    @AddArgument(
        "-o",
        "--override",
        help="add even if the spell is not flagged as a spellup by the mud",
        action="store_true",
    )
    def _command_add(self) -> CommandResult:
        """Add spells to the list."""
        args = self._args()
        spells: list[str] = args.get("spell") or []
        if not spells:
            return CommandResult(False, ["Please supply a spell"])
        lines: list[str] = []
        if spells[0].lower() == "all":
            for spell in self.api(API_SPELLUPS_GET)():
                if self.api(API_SKILL_IS_PRACTICED)(spell["sn"]):
                    lines.append(self._add_spell(str(spell["sn"]), -1, False))
        else:
            for arg in spells:
                parsed = parse_spell_arg(arg)
                if parsed is None:
                    lines.append(f"{arg}: please use name or name:place, place being a number")
                    continue
                lines.append(self._add_spell(parsed[0], parsed[1], bool(args.get("override"))))
        self.spellups.sync()
        self._nextspell()
        return CommandResult(True, lines)

    @AddCommand(group=GROUP)
    @AddParser(description="list spellups for self")
    @AddArgument(
        "match",
        help="list only spellups that have this argument in them",
        default="",
        nargs="?",
    )
    def _command_list(self) -> CommandResult:
        """List the spellups."""
        match = str(self._args().get("match") or "").lower()
        order = self.ups.order()
        if not order:
            return CommandResult(True, ["There are no spellups"])
        lines = list_header()
        for index, sn in enumerate(order):
            skill = self.api(API_SKILL_GET)(sn)
            if not skill:
                lines.append(f"{index:<3}: please check the skills plugin")
            elif not match or match in str(skill["name"]).lower():
                lines.append(
                    list_row(
                        index,
                        str(skill["name"]),
                        affected=bool(self.api(API_SKILL_IS_AFFECTED)(sn)),
                        pending=self._waiting == sn,
                        blocked=bool(self.api(API_SKILL_IS_BLOCKED)(sn)),
                        disabled=not self.ups.is_enabled(sn),
                        percent=int(skill["percent"]),
                    )
                )
        return CommandResult(True, lines)

    @AddCommand(group=GROUP)
    @AddParser(description="remove a spellup from the self list")
    @AddArgument(
        "spell",
        help="the spells to remove, use 'all' to remove all spellups",
        default=[],
        nargs="*",
    )
    def _command_rem(self) -> CommandResult:
        """Remove spells from the list."""
        spells: list[str] = self._args().get("spell") or []
        if not spells:
            return CommandResult(True, ["Please supply a spell/skill to remove"])
        lines: list[str] = []
        if spells[0].lower() == "all":
            self.ups.clear()
            self._clear_waiting()
            lines.append("All spellups to be cast on self cleared")
        else:
            for arg in spells:
                skill = self._skill(arg)
                if not skill:
                    lines.append(f"{arg} does not exist")
                    continue
                sn = int(skill["sn"])
                if self.ups.remove(sn):
                    if self._waiting == sn:
                        self._clear_waiting()
                    lines.append(f"Removed {skill['name']} from spellups to self")
                else:
                    lines.append(f"{skill['name']} is not in the spellups to self")
        self.spellups.sync()
        return CommandResult(True, lines)

    def _enable(self, flag: bool) -> CommandResult:
        """Enable or disable the spells of the running command."""
        word = "enable" if flag else "disable"
        spells: list[str] = self._args().get("spell") or []
        if not spells:
            return CommandResult(True, [f"Please supply a spell/skill to {word}"])
        lines: list[str] = []
        if spells[0].lower() == "all":
            self.ups.set_all(flag)
            lines.append(f"All spellups {word}d")
        else:
            for arg in spells:
                skill = self._skill(arg)
                if not skill:
                    lines.append(f"{arg}: could not find spell")
                elif self.ups.set_enabled(int(skill["sn"]), flag):
                    lines.append(f"{skill['name']}: {word}d")
                else:
                    lines.append(f"{skill['name']}: not in self spellup list")
        self.spellups.sync()
        if flag:
            self._nextspell()
        return CommandResult(True, lines)

    @AddCommand(group=GROUP)
    @AddParser(description="enable spellups on self")
    @AddArgument(
        "spell",
        help="the spells to enable, use 'all' to enable all spellups",
        default=[],
        nargs="*",
    )
    def _command_en(self) -> CommandResult:
        """Enable spells in the list."""
        return self._enable(True)

    @AddCommand(group=GROUP)
    @AddParser(description="disable spells on self")
    @AddArgument(
        "spell",
        help="the spells to disable, use 'all' to disable all spellups",
        default=[],
        nargs="*",
    )
    def _command_dis(self) -> CommandResult:
        """Disable spells in the list."""
        return self._enable(False)

    @AddCommand(group=GROUP)
    @AddParser(description="check the data needed for casting")
    def _command_check(self) -> CommandResult:
        """Show every condition for casting and whether it holds."""
        return CommandResult(
            True,
            check_lines(
                enabled=bool(self._setting("enabled")),
                connected=bool(self.api("plugins.core.proxy:mud.is.connected")()),
                active=bool(self.api("libs.api:character.is.active")()),
                waiting=self._waiting,
                nocast=self._nocast,
                nomoves=self._nomoves,
                nomana=self._nomana,
                up_to_date=bool(self.api(API_UP_TO_DATE)()),
                state=self._gmcp(GMCP_STATE),
            ),
        )
