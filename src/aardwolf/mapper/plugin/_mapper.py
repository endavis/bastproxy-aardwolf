"""Aardwolf mapper plugin: feed the core mapper with rooms, areas, flags and walking rules."""

import asyncio
import logging
import sqlite3
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from bastproxy.libs.logger import log_to
from bastproxy.libs.records import NetworkData, NetworkDataLine, SendDataDirectlyToClient
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.commands import AddArgument, AddCommand, AddParser, CommandResult
from bastproxy.plugins.core.events import RegisterToEvent

from ..libs import (
    EVENT_DISCONNECT,
    EVENT_GMCP_AREA,
    EVENT_GMCP_ROOM,
    EVENT_MOVE_ROOM,
    EVENT_ROOM_MISMATCH,
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
    detail_matches,
    exit_update,
    mismatch_lines,
    read_mush_db,
    requirement_allowed,
    resolve_import_path,
    room_from_gmcp,
    room_uid,
    search_lines,
    steps_to_commands,
    stored_room_with_flags,
    to_int,
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
        """Turn walk steps into commands."""
        return steps_to_commands(steps)

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
