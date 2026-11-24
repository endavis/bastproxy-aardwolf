"""Aardwolf mapper plugin: feed the core mapper with rooms, areas, flags and walking rules."""

import asyncio
import logging
import sqlite3
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from bastproxy.libs.logger import log_to
from bastproxy.libs.records import (
    NetworkData,
    NetworkDataLine,
    SendDataDirectlyToClient,
    SendDataDirectlyToMud,
)
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.commands import AddArgument, AddCommand, AddParser, CommandResult
from bastproxy.plugins.core.events import RegisterToEvent

from ..libs import (
    ANYWHERE,
    CEXIT_MAX_TIMEOUT,
    CEXIT_MIN_TIMEOUT,
    CEXIT_TIMEOUT,
    EVENT_DISCONNECT,
    EVENT_GMCP_AREA,
    EVENT_GMCP_ROOM,
    EVENT_MOVE_ROOM,
    EVENT_ROOM_MISMATCH,
    EVENT_WALK_FAILED,
    FLAG_NOPORTAL,
    FLAG_NORECALL,
    GMCP_LEVEL,
    GMCP_ROOM,
    GMCP_TIER,
    IMPORT_PROGRESS,
    IMPORT_SLICE,
    MAPPER,
    NOPORTAL_REGEX,
    NORECALL_REGEX,
    SEARCHES,
    MushDbError,
    MushMap,
    area_from_gmcp,
    command_chunks,
    detail_matches,
    exit_update,
    is_cexit,
    is_recall_command,
    mismatch_lines,
    movement_chunks,
    parse_command,
    portal_sort_key,
    read_mush_db,
    requirement_allowed,
    requirement_from_level,
    requirement_level,
    resolve_import_path,
    resolve_portal,
    room_from_gmcp,
    room_uid,
    search_lines,
    stored_room_with_flags,
    table_lines,
    to_int,
    total_wait,
)


class MapperPlugin(BasePlugin):
    """Give the core mapper the rooms, areas and walking rules of Aardwolf."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Start with no known room."""
        self._current: str | None = None
        self._requested_areas: set[str] = set()
        self._importing = False
        self._unload_token = 0
        self._pending_cexit: tuple[str, str, dict[str, Any] | None, int] | None = None
        self._send_token = 0
        self._cexit_token = 0

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the triggers, register the callbacks and seed the room from the GMCP cache."""
        self._add_trigger("noportal", NOPORTAL_REGEX, self._trigger_noportal)
        self._add_trigger("norecall", NORECALL_REGEX, self._trigger_norecall)
        self._mapper_api("requirement.register")(self.plugin_id, self._requirement)
        self._mapper_api("movement.register")(self.plugin_id, self._movement)
        info = self._gmcp(GMCP_ROOM)
        if room_uid(info) is not None:
            self._process_room(info)

    @RegisterPluginHook("uninitialize")
    def _phook_uninitialize(self) -> None:
        """Take the callbacks back from the mapper and stop a running import."""
        self._unload_token += 1
        self._cancel_walk()
        self._mapper_api("requirement.unregister")(self.plugin_id)
        self._mapper_api("movement.unregister")(self.plugin_id)

    # helpers

    def _mapper_api(self, name: str) -> Callable[..., Any]:
        """Return an API of the core mapper."""
        result: Callable[..., Any] = self.api(f"{MAPPER}:{name}")
        return result

    def _gmcp(self, path: str) -> object:
        """Return a GMCP value."""
        return self.api("libs.net.protocols:gmcp.value.get")(path)

    def _record(self) -> dict[str, Any]:
        """Return the record of the current event."""
        return dict(self.api("plugins.core.events:event.current.record.get")() or {})

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

    def _add_trigger(self, name: str, regex: str, func: Callable[[], None]) -> None:
        """Add a trigger and register its callback."""
        result = self.api("plugins.core.triggers:trigger.add")(name, regex)
        if not result.success:
            log_to(self.plugin_id, logging.ERROR, "could not add the %s trigger", name)
            return
        self.api("plugins.core.triggers:trigger.register")(result.trigger.trigger_id, func)

    # rooms and areas

    def _process_room(self, info: object) -> None:
        """Store a room, make it the current one and ask for its area; each room once."""
        uid = room_uid(info)
        if uid is None or not isinstance(info, dict) or uid == self._current:
            return
        self._store_room(uid, info)
        self._finish_cexit(uid)
        self._mapper_api("room.current.set")(uid)
        self._current = uid
        self._check_area(info.get("zone"))

    def _store_room(self, uid: str, info: dict[str, Any]) -> None:
        """Add the room to the mapper, keeping the flags it already has."""
        stored = self._mapper_api("room.get")(uid)
        flags = list(stored.get("flags") or []) if stored else []
        name = self.api("plugins.core.colors:colorcode.strip")(str(info.get("name", "")))
        self._mapper_api("room.add")(room_from_gmcp(info, name, flags))

    def _check_area(self, zone: object) -> None:
        """Ask the MUD for an area the mapper does not know, once per connection."""
        if not isinstance(zone, str) or not zone or zone in self._requested_areas:
            return
        if self._mapper_api("area.get")(zone) is not None:
            return
        self._requested_areas.add(zone)
        self.api("libs.net.protocols:gmcp.send")("request area")

    @RegisterToEvent(event_name=EVENT_MOVE_ROOM)
    def _eventcb_move_room(self) -> None:
        """The character moved: store the new room and make it the current one."""
        self._process_room(self._record().get("to"))

    @RegisterToEvent(event_name=EVENT_GMCP_ROOM)
    def _eventcb_room_info(self) -> None:
        """Take the first room after a load or a reconnect; move_room handles the rest."""
        if self._current is None:
            self._process_room(self._record().get("data"))

    @RegisterToEvent(event_name=EVENT_GMCP_AREA)
    def _eventcb_room_area(self) -> None:
        """Store the area the MUD sent."""
        kwargs = area_from_gmcp(self._record().get("data"))
        if kwargs is None:
            return
        self._mapper_api("area.add")(**kwargs)
        self._requested_areas.discard(kwargs["uid"])

    @RegisterToEvent(event_name=EVENT_DISCONNECT)
    def _eventcb_disconnect(self) -> None:
        """Forget the room and the pending areas when the mud disconnects."""
        self._current = None
        self._requested_areas.clear()
        self._cancel_walk()

    @RegisterToEvent(event_name=EVENT_WALK_FAILED)
    def _eventcb_walk_failed(self) -> None:
        """The walk stopped or failed: drop the commands still waiting to be sent."""
        self._send_token += 1

    @RegisterToEvent(event_name=EVENT_ROOM_MISMATCH)
    def _eventcb_room_mismatch(self) -> None:
        """Tell the client that a room contradicts the map."""
        record = self._record()
        differences = record.get("differences")
        if isinstance(differences, dict):
            self._client(mismatch_lines(str(record.get("uid")), differences))

    # room flags

    def _trigger_noportal(self) -> None:
        """The room does not allow portals."""
        self._set_flag(FLAG_NOPORTAL)

    def _trigger_norecall(self) -> None:
        """The room does not allow recall."""
        self._set_flag(FLAG_NORECALL)

    def _set_flag(self, flag: str) -> None:
        """Add a flag to the current room, without touching its exits."""
        uid = self._current
        if uid is None:
            return
        room = self._mapper_api("room.get")(uid)
        if not room:
            return
        flags = list(room.get("flags") or [])
        if flag in flags:
            return
        self._mapper_api("room.add")(
            {
                "uid": uid,
                "name": room.get("name"),
                "area": room.get("area"),
                "terrain": room.get("terrain"),
                "x": room.get("x"),
                "y": room.get("y"),
                "z": room.get("z"),
                "details": room.get("details"),
                "flags": [*flags, flag],
            }
        )
        self._client([f"Mapper: room {uid} marked {flag}"])

    # walking

    def _requirement(self, requirement: object, exit_dict: dict[str, Any]) -> bool:
        """Say whether the character may use an exit, from its level and tier."""
        level = self._gmcp(GMCP_LEVEL)
        tier = self._gmcp(GMCP_TIER)
        allowed = requirement_allowed(
            requirement,
            exit_dict,
            to_int(level) if level is not None else None,
            to_int(tier) if tier is not None else None,
        )
        if not allowed:
            self._debug("exit %s blocked by %s", exit_dict, requirement)
        return allowed

    def _movement(self, steps: list[dict[str, Any]]) -> list[str]:
        """Turn walk steps into commands; the commands after a wait are sent later."""
        chunks = movement_chunks(steps)
        self._send_token += 1
        if not chunks:
            return []
        self._send_rest(chunks[1:], self._send_token)
        return chunks[0][1]

    def _cancel_walk(self) -> None:
        """Drop the commands waiting to be sent and any custom exit being recorded."""
        self._send_token += 1
        self._cexit_token += 1
        self._pending_cexit = None

    def _mud(self, commands: list[str]) -> None:
        """Send commands to the MUD."""
        SendDataDirectlyToMud(NetworkData(commands, owner_id=f"{self.plugin_id}:walk"))()

    def _send_rest(self, chunks: list[tuple[float, list[str]]], token: int) -> None:
        """Queue the chunks that follow a wait."""
        if chunks:
            self.api("libs.asynch:task.add")(
                self._send_later(chunks, token), f"{self.plugin_id}:walk"
            )

    async def _send_later(self, chunks: list[tuple[float, list[str]]], token: int) -> None:
        """Send each chunk after its delay, unless a newer walk or a cancel came first."""
        for delay, commands in chunks:
            if token != self._send_token:
                return
            if delay:
                self._client([f"Mapper: waiting {delay:g} seconds"])
                await asyncio.sleep(delay)
                if token != self._send_token:
                    return
            if commands:
                self._mud(commands)

    # commands

    def _args(self) -> dict[str, Any]:
        """Return the arguments of the running command."""
        args = self.api("plugins.core.commands:command.current.args.get")()
        return dict(args) if args else {}

    def _escape(self, text: str) -> str:
        """Escape colour codes so a name or note shows as it is."""
        result: str = self.api("plugins.core.colors:colorcode.escape")(text)
        return result

    # importing a MUSHclient map

    @AddCommand()
    @AddParser(description="import a MUSHclient Aardwolf.db into the map")
    @AddArgument("path", help="the Aardwolf.db file; quote it when it has spaces")
    def _command_importmush(self) -> CommandResult:
        """Import the rooms, exits, areas and notes of a MUSHclient map database."""
        if self._importing:
            return CommandResult(False, ["Mapper import: an import is already running"])
        try:
            path = resolve_import_path(str(self._args().get("path", "")))
        except MushDbError as exc:
            return CommandResult(False, [f"Mapper import: {exc}"])
        self._importing = True
        try:
            self.api("libs.asynch:task.add")(
                self._import(path, self._unload_token), f"{self.plugin_id}:import"
            )
        except Exception:
            self._importing = False
            raise
        return CommandResult(True, [f"Mapper import: reading {path}"])

    async def _import(self, path: Path, token: int) -> None:
        """Read the database in a thread, then write it to the mapper on the loop."""
        try:
            try:
                data = await asyncio.to_thread(read_mush_db, path)
            except MushDbError as exc:
                self._client([f"Mapper import: {exc}"])
                return
            except Exception:
                log_to(self.plugin_id, logging.ERROR, "reading %s failed", path, exc_info=True)
                self._client(["Mapper import: reading the file failed, see the plugin log"])
                return
            if token != self._unload_token:
                return
            await self._write_import(data, token)
        finally:
            self._importing = False

    async def _write_import(self, data: MushMap, token: int) -> None:
        """Write the read map to the core mapper in time slices; captured data wins."""
        started = time.monotonic()
        phase = "areas"
        done = 0
        total = len(data.areas)
        counts = {"areas": 0, "rooms": 0, "flagged": 0, "notes": 0, "exits": 0, "updated": 0}

        async def step() -> bool:
            """Count an item, report progress, yield when the slice is used; False to stop."""
            nonlocal started, done
            done += 1
            if done % IMPORT_PROGRESS == 0:
                self._client([f"Mapper import: {phase} {done}/{total}"])
            if token != self._unload_token:
                return False
            if time.monotonic() - started >= IMPORT_SLICE:
                await asyncio.sleep(0)
                started = time.monotonic()
                return token == self._unload_token
            return True

        try:
            self._client([f"Mapper import: {phase} 0/{total}"])
            for area in data.areas:
                if self._mapper_api("area.get")(area["uid"]) is None:
                    self._mapper_api("area.add")(**area)
                    counts["areas"] += 1
                if not await step():
                    return
            phase, done, total = "rooms", 0, len(data.rooms)
            self._client([f"Mapper import: {phase} 0/{total}"])
            for room in data.rooms:
                self._import_room(room, data.notes.get(room["uid"]), counts)
                if not await step():
                    return
            phase, done = "exits", 0
            total = sum(len(items) for items in data.exits.values())
            self._client([f"Mapper import: {phase} 0/{total}"])
            for fromuid, items in data.exits.items():
                stored = {e["dir"]: e for e in self._mapper_api("exit.list")(fromuid)}
                for direction, touid, requirement in items:
                    update = exit_update(stored.get(direction), touid, requirement)
                    if update is not None:
                        counts["updated" if direction in stored else "exits"] += 1
                        self._mapper_api("exit.add")(fromuid, direction, *update)
                    if not await step():
                        return
        except sqlite3.Error as exc:
            log_to(self.plugin_id, logging.ERROR, "import failed in %s", phase, exc_info=True)
            self._client([f"Mapper import stopped in {phase} at {done}/{total}: {exc}"])
            return
        self._client(
            [
                f"Mapper import done: {counts['areas']} areas, {counts['rooms']} rooms "
                f"(flags added to {counts['flagged']} stored), {counts['exits']} exits "
                f"({counts['updated']} updated), {counts['notes']} notes; "
                f"skipped {data.skipped_rooms} rooms and {data.skipped_exits} exits"
            ]
        )

    def _import_room(self, room: dict[str, Any], note: str | None, counts: dict[str, int]) -> None:
        """Add a room the map does not have, or only add the flags a stored room lacks."""
        stored = self._mapper_api("room.get")(room["uid"])
        if stored is None:
            self._mapper_api("room.add")(room)
            counts["rooms"] += 1
        else:
            update = stored_room_with_flags(stored, room["flags"])
            if update is not None:
                self._mapper_api("room.add")(update)
                counts["flagged"] += 1
        if note and not self._mapper_api("room.note.get")(room["uid"]):
            self._mapper_api("room.note.set")(room["uid"], note)
            counts["notes"] += 1

    # searches

    def _search(self, kind: str) -> CommandResult:
        """List the rooms of an area that match a search, in room uid order."""
        where = str(self._args().get("area") or "here").strip().lower()
        if where == "here":
            current = self._mapper_api("room.current.get")()
            room = self._mapper_api("room.get")(current) if current else None
            area = room.get("area") if room else None
            if not area:
                return CommandResult(False, ["Mapper: the current room is not known"])
            where = str(area)
        rooms = sorted(
            self._mapper_api("room.list")(area=where),
            key=lambda r: (to_int(r["uid"]), str(r["uid"])),
        )
        if not rooms:
            return CommandResult(False, [f"Mapper: area {where} has no mapped rooms"])
        rows: list[tuple[str, str, str, str]] = []
        for found in rooms:
            if kind == "notes":
                text = self._mapper_api("room.note.get")(found["uid"])
                match = self._escape(str(text)) if text else ""
            else:
                match = ", ".join(detail_matches(found.get("details"), SEARCHES[kind]))
            if match:
                rows.append(
                    (str(found["uid"]), self._escape(str(found["name"])), str(found["area"]), match)
                )
        if not rows:
            return CommandResult(True, [f"No {kind} found in {where}"])
        title = f"Mapper {kind} in {where}: {len(rows)} rooms"
        return CommandResult(True, search_lines(title, rows))

    @AddCommand()
    @AddParser(description="list the shops and banks of an area")
    @AddArgument("area", help="here or an area id", nargs="?", default="here")
    def _command_shops(self) -> CommandResult:
        """List the shops and banks of the current area or a named one."""
        return self._search("shops")

    @AddCommand()
    @AddParser(description="list the trainers of an area")
    @AddArgument("area", help="here or an area id", nargs="?", default="here")
    def _command_train(self) -> CommandResult:
        """List the trainers of the current area or a named one."""
        return self._search("train")

    @AddCommand()
    @AddParser(description="list the questors of an area")
    @AddArgument("area", help="here or an area id", nargs="?", default="here")
    def _command_quest(self) -> CommandResult:
        """List the questors of the current area or a named one."""
        return self._search("quest")

    @AddCommand()
    @AddParser(description="list the rooms with a note in an area")
    @AddArgument("area", help="here or an area id", nargs="?", default="here")
    def _command_notes(self) -> CommandResult:
        """List the rooms with a note in the current area or a named one."""
        return self._search("notes")

    # custom exits

    def _known_room(self, uid: str | None) -> dict[str, Any] | None:
        """Return the stored room, or None for no uid or an unknown room."""
        if not uid:
            return None
        room: dict[str, Any] | None = self._mapper_api("room.get")(uid)
        return room

    def _cexits_of(self, uid: str) -> list[dict[str, Any]]:
        """Return the custom exits of a room."""
        return [e for e in self._mapper_api("exit.list")(uid) if is_cexit(e)]

    def _finish_cexit(self, uid: str) -> None:
        """Store the custom exit being recorded when the new room arrives."""
        pending = self._pending_cexit
        if pending is None or uid == pending[0]:
            return
        fromuid, command, requirement, _ = pending
        self._pending_cexit = None
        self._cexit_token += 1
        self._mapper_api("exit.add")(fromuid, command, uid, 1, requirement)
        self._client([f"Mapper: custom exit {fromuid} ({command}) -> {uid}"])

    async def _cexit_timeout(self, token: int, seconds: float) -> None:
        """Stop recording a custom exit when no new room arrives in time."""
        await asyncio.sleep(seconds)
        pending = self._pending_cexit
        if token != self._cexit_token or pending is None:
            return
        self._pending_cexit = None
        self._client([f"Mapper: no new room after {pending[1]}; the custom exit was not stored"])

    @AddCommand()
    @AddParser(description="record or add a custom exit from the current room")
    @AddArgument("command", help="the command; use ; and wait(N) between parts", nargs="+")
    @AddArgument("-l", "--level", help="the level needed", type=int, default=0)
    @AddArgument("-T", "--timeout", help="seconds to wait for the new room", type=int, default=0)
    @AddArgument("-t", "--touid", help="add the exit to this room without walking", default=None)
    @AddArgument("-f", "--fromuid", help="the room the exit leaves from", default=None)
    def _command_cexit(self) -> CommandResult:
        """Walk a custom exit and store it when a new room arrives, or add it with -t."""
        args = self._args()
        text = " ".join(str(word) for word in args.get("command") or []).strip()
        parts = parse_command(text)
        if parts is None:
            return CommandResult(
                False, ["Mapper: the command is empty or a wait(N) is not 0 < N <= 40"]
            )
        requirement = requirement_from_level(args.get("level"))
        touid = args.get("touid")
        if touid:
            fromuid = str(args.get("fromuid") or self._mapper_api("room.current.get")() or "")
            if self._known_room(fromuid) is None or self._known_room(str(touid)) is None:
                return CommandResult(False, ["Mapper: both rooms must be known"])
            if fromuid == str(touid):
                return CommandResult(False, ["Mapper: the exit must lead to another room"])
            self._mapper_api("exit.add")(fromuid, text, str(touid), 1, requirement)
            return CommandResult(True, [f"Mapper: custom exit {fromuid} ({text}) -> {touid}"])
        current = self._mapper_api("room.current.get")()
        if self._known_room(current) is None:
            return CommandResult(False, ["Mapper: the current room is not known"])
        if self._pending_cexit is not None:
            return CommandResult(False, ["Mapper: a custom exit is already being recorded"])
        timeout = to_int(args.get("timeout")) or CEXIT_TIMEOUT
        if not CEXIT_MIN_TIMEOUT <= timeout <= CEXIT_MAX_TIMEOUT:
            return CommandResult(
                False,
                [f"Mapper: the timeout must be {CEXIT_MIN_TIMEOUT} to {CEXIT_MAX_TIMEOUT} seconds"],
            )
        chunks = command_chunks(parts)
        self._cexit_token += 1
        self._send_token += 1
        self._pending_cexit = (str(current), text, requirement, self._cexit_token)
        if chunks[0][1]:
            self._mud(chunks[0][1])
        self._send_rest(chunks[1:], self._send_token)
        self.api("libs.asynch:task.add")(
            self._cexit_timeout(self._cexit_token, timeout + total_wait(parts)),
            f"{self.plugin_id}:cexit",
        )
        return CommandResult(True, [f"Mapper: recording custom exit ({text}) from {current}"])

    @AddCommand()
    @AddParser(description="list the custom exits of an area or the current room")
    @AddArgument("where", help="here, thisroom or an area id", nargs="?", default="here")
    def _command_cexits(self) -> CommandResult:
        """List the custom exits of the current area, the current room or a named area."""
        where = str(self._args().get("where") or "here").strip().lower()
        current = self._mapper_api("room.current.get")()
        room = self._known_room(current)
        if where in ("here", "thisroom"):
            if room is None:
                return CommandResult(False, ["Mapper: the current room is not known"])
            rooms = (
                [room]
                if where == "thisroom"
                else self._mapper_api("room.list")(area=room.get("area"))
            )
        else:
            rooms = self._mapper_api("room.list")(area=where)
        rooms = sorted(rooms, key=lambda r: (to_int(r["uid"]), str(r["uid"])))
        rows: list[tuple[str, ...]] = []
        for found in rooms:
            for item in self._cexits_of(found["uid"]):
                rows.append(
                    (
                        str(found["uid"]),
                        self._escape(str(found["name"])),
                        str(found["area"]),
                        self._escape(str(item["dir"])),
                        str(item["touid"]),
                        str(requirement_level(item["requirement"])),
                    )
                )
        if not rows:
            return CommandResult(True, [f"No custom exits found in {where}"])
        title = f"Mapper custom exits in {where}: {len(rows)}"
        header = ("uid", "name", "area", "command", "to", "level")
        return CommandResult(True, table_lines(title, header, rows))

    @AddCommand()
    @AddParser(description="delete a custom exit, or all of them, of the current room")
    @AddArgument("command", help="the exit to delete; none deletes every custom exit", nargs="*")
    def _command_cexitdel(self) -> CommandResult:
        """Delete one custom exit of the current room, or all of them."""
        current = self._mapper_api("room.current.get")()
        if self._known_room(current) is None:
            return CommandResult(False, ["Mapper: the current room is not known"])
        text = " ".join(str(word) for word in self._args().get("command") or []).strip()
        found = self._cexits_of(str(current))
        if text:
            found = [e for e in found if e["dir"] == text]
        if not found:
            return CommandResult(False, ["Mapper: no matching custom exit in this room"])
        for item in found:
            self._mapper_api("exit.remove")(str(current), item["dir"])
        return CommandResult(True, [f"Mapper: deleted {len(found)} custom exits from {current}"])

    @AddCommand()
    @AddParser(description="delete the custom exits of an area, or of all areas")
    @AddArgument("where", help="here, an area id or all", nargs="?", default="here")
    @AddArgument("-c", "--confirm", help="delete them; without it only count", action="store_true")
    def _command_cexitpurge(self) -> CommandResult:
        """Count, or with --confirm delete, the custom exits of an area or of every area."""
        args = self._args()
        where = str(args.get("where") or "here").strip().lower()
        if where == "here":
            room = self._known_room(self._mapper_api("room.current.get")())
            if room is None or not room.get("area"):
                return CommandResult(False, ["Mapper: the current room is not known"])
            where = str(room["area"])
        rooms = (
            self._mapper_api("room.list")()
            if where == "all"
            else self._mapper_api("room.list")(area=where)
        )
        targets = [(r["uid"], e["dir"]) for r in rooms for e in self._cexits_of(r["uid"])]
        if not targets:
            return CommandResult(True, [f"No custom exits found in {where}"])
        if not args.get("confirm"):
            return CommandResult(
                True, [f"Mapper: {len(targets)} custom exits in {where}; add --confirm to delete"]
            )
        self.api("libs.asynch:task.add")(
            self._purge_exits(targets, where, self._unload_token), f"{self.plugin_id}:purge"
        )
        return CommandResult(True, [f"Mapper: deleting {len(targets)} custom exits in {where}"])

    async def _purge_exits(self, targets: list[tuple[str, str]], where: str, token: int) -> None:
        """Remove exits in time slices so a large map does not stall the loop."""
        started = time.monotonic()
        for fromuid, direction in targets:
            self._mapper_api("exit.remove")(fromuid, direction)
            if time.monotonic() - started >= IMPORT_SLICE:
                await asyncio.sleep(0)
                started = time.monotonic()
            if token != self._unload_token:
                return
        self._client([f"Mapper: deleted {len(targets)} custom exits in {where}"])

    # exit locks

    @AddCommand()
    @AddParser(description="show or set the level needed to use an exit")
    @AddArgument("exit", help="the exit; none lists the room's exits", nargs="*")
    @AddArgument("-r", "--room", help="the room; the current room by default", default=None)
    @AddArgument("-l", "--level", help="the level to lock it at; 0 unlocks", type=int, default=None)
    def _command_lockexit(self) -> CommandResult:
        """List the exits of a room, or show or set the lock of one."""
        args = self._args()
        uid = str(args.get("room") or self._mapper_api("room.current.get")() or "")
        if self._known_room(uid) is None:
            return CommandResult(False, ["Mapper: the room is not known"])
        exits = self._mapper_api("exit.list")(uid)
        text = " ".join(str(word) for word in args.get("exit") or []).strip()
        if not text:
            rows = [
                (
                    self._escape(str(e["dir"])),
                    str(e["touid"]),
                    str(requirement_level(e["requirement"])),
                )
                for e in exits
            ]
            return CommandResult(
                True, table_lines(f"Mapper exits of {uid}", ("exit", "to", "level"), rows)
            )
        found = next((e for e in exits if e["dir"] == text), None)
        if found is None:
            return CommandResult(False, [f"Mapper: room {uid} has no exit {text}"])
        level = args.get("level")
        if level is None:
            shown = requirement_level(found["requirement"])
            return CommandResult(True, [f"Mapper: exit {text} of {uid} needs level {shown}"])
        self._mapper_api("exit.add")(
            uid, text, found["touid"], found["cost"], requirement_from_level(level)
        )
        return CommandResult(True, [f"Mapper: exit {text} of {uid} needs level {max(level, 0)}"])

    # portals

    def _portals(self) -> list[dict[str, Any]]:
        """Return the portal and recall exits sorted by area, room number and command."""
        found = [
            *self._mapper_api("exit.list")(ANYWHERE[0]),
            *self._mapper_api("exit.list")(ANYWHERE[1]),
        ]
        rooms = {e["touid"]: self._known_room(e["touid"]) for e in found}
        return sorted(found, key=lambda e: portal_sort_key(e, rooms[e["touid"]]))

    def _portal_arg(self, ref: object) -> tuple[dict[str, Any] | None, CommandResult | None]:
        """Return the portal a reference names, or a failure result."""
        portal = resolve_portal(self._portals(), str(ref))
        if portal is None:
            return None, CommandResult(False, [f"Mapper: no portal {ref}"])
        return dict(portal), None

    def _put_portal(self, kind: str, portal: dict[str, Any], **changes: object) -> None:
        """Store a portal under a kind with some fields changed, removing the old exit."""
        new = {**portal, **changes}
        self._mapper_api("exit.remove")(portal["fromuid"], portal["dir"])
        for other in ANYWHERE:
            if other != kind:
                self._mapper_api("exit.remove")(other, new["dir"])
        self._mapper_api("exit.add")(
            kind, new["dir"], new["touid"], new["cost"], new["requirement"]
        )

    @AddCommand()
    @AddParser(description="add a portal, or a recall, that leads to a room")
    @AddArgument("command", help="the command that takes the portal", nargs="+")
    @AddArgument("-l", "--level", help="the level needed", type=int, default=0)
    @AddArgument("-t", "--touid", help="the room it leads to; the current room", default=None)
    @AddArgument("-r", "--recall", help="store it as a recall", action="store_true")
    def _command_portal(self) -> CommandResult:
        """Add a portal; recall, home and hom are stored as recalls."""
        args = self._args()
        text = " ".join(str(word) for word in args.get("command") or []).strip()
        if parse_command(text) is None:
            return CommandResult(
                False, ["Mapper: the command is empty or a wait(N) is not 0 < N <= 40"]
            )
        touid = str(args.get("touid") or self._mapper_api("room.current.get")() or "")
        if self._known_room(touid) is None:
            return CommandResult(False, ["Mapper: the room is not known"])
        kind = ANYWHERE[1] if args.get("recall") or is_recall_command(text) else ANYWHERE[0]
        self._put_portal(
            kind,
            {"fromuid": kind, "dir": text, "touid": touid, "cost": 1, "requirement": None},
            requirement=requirement_from_level(args.get("level")),
        )
        return CommandResult(True, [f"Mapper: {self._kind_name(kind)} {text} -> {touid}"])

    @staticmethod
    def _kind_name(kind: str) -> str:
        """Return the name of a portal kind."""
        return "recall" if kind == ANYWHERE[1] else "portal"

    @AddCommand()
    @AddParser(description="list the portals and recalls")
    @AddArgument("filter", help="part of an area id", nargs="?", default="")
    def _command_portals(self) -> CommandResult:
        """List the portals and recalls, numbered, in area order."""
        wanted = str(self._args().get("filter") or "").strip().lower()
        rows: list[tuple[str, ...]] = []
        for number, portal in enumerate(self._portals(), start=1):
            room = self._known_room(portal["touid"])
            area = str(room.get("area") or "") if room else ""
            if wanted and wanted not in area.lower():
                continue
            rows.append(
                (
                    f"#{number}",
                    self._kind_name(portal["fromuid"]),
                    area,
                    self._escape(str(room.get("name") or "")) if room else "",
                    str(portal["touid"]),
                    self._escape(str(portal["dir"])),
                    str(requirement_level(portal["requirement"])),
                )
            )
        if not rows:
            return CommandResult(True, ["No portals found"])
        header = ("#", "kind", "area", "name", "to", "command", "level")
        return CommandResult(True, table_lines(f"Mapper portals: {len(rows)}", header, rows))

    @AddCommand()
    @AddParser(description="change the command of a portal")
    @AddArgument("ref", help="the portal number as #N, or its command in quotes")
    @AddArgument("command", help="the new command", nargs="+")
    def _command_portalchange(self) -> CommandResult:
        """Give a portal a new command, keeping its room, level and kind."""
        args = self._args()
        portal, failure = self._portal_arg(args.get("ref"))
        if portal is None:
            return failure or CommandResult(False, ["Mapper: no such portal"])
        text = " ".join(str(word) for word in args.get("command") or []).strip()
        if parse_command(text) is None:
            return CommandResult(
                False, ["Mapper: the command is empty or a wait(N) is not 0 < N <= 40"]
            )
        self._put_portal(portal["fromuid"], portal, dir=text)
        return CommandResult(True, [f"Mapper: portal {portal['dir']} is now {text}"])

    @AddCommand()
    @AddParser(description="set the level needed for a portal")
    @AddArgument("ref", help="the portal number as #N, or its command in quotes")
    @AddArgument("level", help="the level; 0 for none", type=int)
    def _command_portallevel(self) -> CommandResult:
        """Set the level of a portal."""
        args = self._args()
        portal, failure = self._portal_arg(args.get("ref"))
        if portal is None:
            return failure or CommandResult(False, ["Mapper: no such portal"])
        level = to_int(args.get("level"))
        self._put_portal(portal["fromuid"], portal, requirement=requirement_from_level(level))
        return CommandResult(True, [f"Mapper: portal {portal['dir']} needs level {max(level, 0)}"])

    @AddCommand()
    @AddParser(description="switch a portal between a portal and a recall")
    @AddArgument("ref", help="the portal number as #N, or its command in quotes")
    def _command_portalrecall(self) -> CommandResult:
        """Make a portal a recall, or a recall a portal."""
        portal, failure = self._portal_arg(self._args().get("ref"))
        if portal is None:
            return failure or CommandResult(False, ["Mapper: no such portal"])
        kind = ANYWHERE[0] if portal["fromuid"] == ANYWHERE[1] else ANYWHERE[1]
        self._put_portal(kind, portal, fromuid=kind)
        return CommandResult(True, [f"Mapper: {portal['dir']} is now a {self._kind_name(kind)}"])

    @AddCommand()
    @AddParser(description="delete a portal")
    @AddArgument("ref", help="the portal number as #N, or its command in quotes")
    def _command_portaldel(self) -> CommandResult:
        """Delete a portal or a recall."""
        portal, failure = self._portal_arg(self._args().get("ref"))
        if portal is None:
            return failure or CommandResult(False, ["Mapper: no such portal"])
        self._mapper_api("exit.remove")(portal["fromuid"], portal["dir"])
        return CommandResult(True, [f"Mapper: deleted portal {portal['dir']}"])

    @AddCommand()
    @AddParser(description="delete every portal and recall")
    @AddArgument("-c", "--confirm", help="delete them; without it only count", action="store_true")
    def _command_portalpurge(self) -> CommandResult:
        """Delete every portal and recall; the exits of rooms stay."""
        portals = self._portals()
        if not portals:
            return CommandResult(True, ["No portals found"])
        if not self._args().get("confirm"):
            return CommandResult(
                True, [f"Mapper: {len(portals)} portals; add --confirm to delete them"]
            )
        for portal in portals:
            self._mapper_api("exit.remove")(portal["fromuid"], portal["dir"])
        return CommandResult(True, [f"Mapper: deleted {len(portals)} portals"])
