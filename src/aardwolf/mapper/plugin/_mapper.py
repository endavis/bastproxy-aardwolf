"""Aardwolf mapper plugin: feed the core mapper with rooms, areas, flags and walking rules."""

import asyncio
import logging
import sqlite3
import time
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
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

from aardwolf._libs.validate import int_validator

from ..libs import (
    ANYWHERE,
    API_EQ,
    API_EQ_ITEM_EQUIP,
    API_EQ_ITEM_GET,
    API_EQ_ITEM_PUT,
    API_EQ_WORN_GET,
    CEXIT_COLUMNS,
    CEXIT_MAX_TIMEOUT,
    CEXIT_MIN_TIMEOUT,
    CEXIT_TEXT_COLUMNS,
    CEXIT_TIMEOUT,
    EVENT_DISCONNECT,
    EVENT_GMCP_AREA,
    EVENT_GMCP_ROOM,
    EVENT_MOVE_ROOM,
    EVENT_ROOM_MISMATCH,
    EVENT_WALK_FAILED,
    EXIT_TEXT_COLUMNS,
    FLAG_NOPORTAL,
    FLAG_NORECALL,
    GMCP_LEVEL,
    GMCP_ROOM,
    GMCP_TIER,
    HELD_WEARLOC,
    IMPORT_BATCH,
    IMPORT_SLICE,
    MAPPER,
    NOPORTAL_REGEX,
    NORECALL_REGEX,
    PLACE_COLUMNS,
    PLACE_KINDS,
    PLACE_TEXT_COLUMNS,
    PORTAL_COLUMNS,
    PORTAL_ITYPE,
    PORTAL_TEXT_COLUMNS,
    PORTAL_WEARLOC,
    SEARCHES,
    SETTING_CEXIT_TIMEOUT,
    WEB_ROUTE_ADD,
    WEB_ROUTE_REMOVE,
    MushDbError,
    MushMap,
    PortalStep,
    WebRequest,
    area_arg,
    area_from_gmcp,
    area_link,
    command_chunks,
    detail_matches,
    is_cexit,
    is_recall_command,
    mismatch_lines,
    movement_plan,
    parse_command,
    portal_marker,
    portal_requirement,
    portal_serial,
    portal_sort_key,
    read_mush_db,
    requirement_allowed,
    requirement_from_level,
    requirement_level,
    resolve_import_path,
    resolve_portal,
    room_from_gmcp,
    room_link,
    room_uid,
    serial_arg,
    table_data,
    table_view,
    to_int,
    total_wait,
)


class _BatchRefusedError(Exception):
    """The core mapper refused a batch (None result), so nothing of it was written."""


def _chunks(items: list[Any], rows: Callable[[Any], int]) -> Iterator[list[Any]]:
    """Yield slices of items whose rows, counted as the core mapper does, fit IMPORT_BATCH."""
    chunk: list[Any] = []
    used = 0
    for item in items:
        cost = rows(item)
        if chunk and used + cost > IMPORT_BATCH:
            yield chunk
            chunk, used = [], 0
        chunk.append(item)
        used += cost
    if chunk:
        yield chunk


@dataclass
class _TakenPortal:
    """A portal item taken for a use: where it came from and what the portal and held slots held."""

    serial: int
    container: str | None
    previous: dict[str, int | None]


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
        self._pending_portal: tuple[int, int, int] | None = None
        self._portal_token = 0
        self._taken: _TakenPortal | None = None

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the setting and triggers, register the callbacks and seed the room.

        Last, it adds the mapper commands under the core mapper (#189).
        """
        self.api("plugins.core.settings:setting.add")(
            self.plugin_id,
            SETTING_CEXIT_TIMEOUT,
            CEXIT_TIMEOUT,
            int,
            "seconds a cexit waits for the new room when no timeout is given",
            validator=int_validator(CEXIT_MIN_TIMEOUT, CEXIT_MAX_TIMEOUT),
        )
        self._add_trigger("noportal", NOPORTAL_REGEX, self._trigger_noportal)
        self._add_trigger("norecall", NORECALL_REGEX, self._trigger_norecall)
        self._mapper_api("requirement.register")(self.plugin_id, self._requirement)
        self._mapper_api("movement.register")(self.plugin_id, self._movement)
        info = self._gmcp(GMCP_ROOM)
        if room_uid(info) is not None:
            self._process_room(info)
        self._add_routes()
        self._add_client_commands()

    def _add_client_commands(self) -> None:
        """Add each command of this plugin under the core mapper as well.

        They keep their own names too. The core logs a refusal to this plugin's log.
        """
        add = self.api("plugins.core.commands:command.add.for.plugin")
        for name in sorted(vars(MapperPlugin)):
            if name.startswith("_command_"):
                add(MAPPER, getattr(self, name))

    def _setting(self, name: str) -> object:
        """Return the value of a setting of this plugin."""
        return self.api("plugins.core.settings:setting.get")(self.plugin_id, name)

    @RegisterPluginHook("uninitialize")
    def _phook_uninitialize(self) -> None:
        """Take the callbacks back from the mapper and stop a running import."""
        self._unload_token += 1
        self._cancel_walk()
        self._mapper_api("requirement.unregister")(self.plugin_id)
        self._mapper_api("movement.unregister")(self.plugin_id)
        if self.api("libs.api:api.exists")(WEB_ROUTE_REMOVE):
            self.api(WEB_ROUTE_REMOVE)(self.plugin_id)

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
        self._finish_portal(uid)
        self._restore_portal()
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
        """Store the area the MUD sent.

        No ``request room`` follows, unlike the old plugin: ``_check_area`` asks for an area
        only from ``_process_room``, after the room is stored and current, and a reply for
        the same room would be ignored (same number in ``move_payload``, ``_current`` set in
        ``_eventcb_room_info``, early return in ``_process_room``).
        """
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
        """The walk stopped or failed: drop the commands still waiting, put the portal back."""
        self._send_token += 1
        self._restore_portal()

    @RegisterToEvent(event_name=EVENT_ROOM_MISMATCH)
    def _eventcb_room_mismatch(self) -> None:
        """Tell the client that a room contradicts the map."""
        record = self._record()
        differences = record.get("differences")
        if isinstance(differences, dict):
            self._client(mismatch_lines(str(record.get("uid")), differences, self._escape))

    # room flags

    def _trigger_noportal(self) -> None:
        """The room does not allow portals; a portal being recorded is dropped."""
        self._set_flag(FLAG_NOPORTAL)
        pending = self._pending_portal
        if pending is not None:
            self._pending_portal = None
            self._portal_token += 1
            self._client([f"Mapper: the portal {pending[0]} was refused; it was not stored"])
            self._restore_portal()

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
        serial = (
            portal_serial(exit_dict.get("dir")) if exit_dict.get("fromuid") in ANYWHERE else None
        )
        if serial is not None and self._eq_item(serial) is None:
            self._debug("exit %s blocked: eq does not have item %s", exit_dict, serial)
            return False
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
        plan = movement_plan(steps)
        self._send_token += 1
        while plan:
            head = plan[0]
            if not isinstance(head, PortalStep):
                break
            plan.pop(0)
            if not self._walk_portal(head):
                return []
        if not plan:
            return []
        first = plan[0]
        self._send_rest(plan[1:], self._send_token)
        return first[1] if isinstance(first, tuple) else []

    def _walk_portal(self, step: PortalStep) -> bool:
        """Use a portal item of a walk; report and return False when it cannot be used."""
        failure = self._use_portal(step.serial)
        if failure is not None:
            self._client([f"Mapper: {failure}; the walk stops"])
            return False
        return True

    def _cancel_walk(self) -> None:
        """Drop the commands waiting to be sent, and any custom exit or portal being recorded."""
        self._send_token += 1
        self._cexit_token += 1
        self._pending_cexit = None
        self._portal_token += 1
        self._pending_portal = None
        self._taken = None

    def _mud(self, commands: list[str]) -> None:
        """Send commands to the MUD."""
        SendDataDirectlyToMud(NetworkData(commands, owner_id=f"{self.plugin_id}:walk"))()

    def _send_rest(
        self, chunks: Sequence[tuple[float, list[str]] | PortalStep], token: int
    ) -> None:
        """Queue the chunks that follow a wait."""
        if chunks:
            self.api("libs.asynch:task.add")(
                self._send_later(chunks, token), f"{self.plugin_id}:walk"
            )

    async def _send_later(
        self, chunks: Sequence[tuple[float, list[str]] | PortalStep], token: int
    ) -> None:
        """Send each chunk after its delay, unless a newer walk or a cancel came first."""
        for chunk in chunks:
            if token != self._send_token:
                return
            if isinstance(chunk, PortalStep):
                if not self._walk_portal(chunk):
                    return
                continue
            delay, commands = chunk
            if delay:
                self._client([f"Mapper: waiting {delay:g} seconds"])
                await asyncio.sleep(delay)
                if token != self._send_token:
                    return
            if commands:
                self._mud(commands)

    # portal items

    def _eq_ready(self) -> bool:
        """Return True when every eq API a portal item needs exists."""
        exists = self.api("libs.api:api.exists")
        return all(bool(exists(name)) for name in API_EQ)

    def _eq_item(self, serial: int) -> dict[str, Any] | None:
        """Return the eq item with this serial, or None when eq or the item is missing."""
        if not self._eq_ready():
            return None
        item: dict[str, Any] | None = self.api(API_EQ_ITEM_GET)(serial)
        return item

    def _item_name(self, serial: int) -> str:
        """Return the escaped name of a portal item, or its serial when eq does not know it."""
        item = self._eq_item(serial)
        name = str(item.get("name") or "") if item else ""
        return self._escape(name) if name else str(serial)

    def _worn_serial(self, location: str) -> int | None:
        """Return the serial of the item eq lists in a wear location, or None."""
        worn: dict[str, Any] | None = self.api(API_EQ_WORN_GET)(location)
        return to_int(worn.get("serial")) if worn else None

    def _use_portal(self, serial: int) -> str | None:
        """Take a portal item, wear it and send enter; return why it cannot, else None.

        A plain wear puts the portal in the portal slot when the character has bought it and
        holds it otherwise. The items of both slots are noted so `_restore_portal` can wear
        back the one the portal displaced.
        """
        self._restore_portal()
        if not self._eq_ready():
            return "the eq plugin is not loaded"
        item = self._eq_item(serial)
        if item is None:
            return f"eq does not know item {serial}"
        previous = {loc: self._worn_serial(loc) for loc in (PORTAL_WEARLOC, HELD_WEARLOC)}
        if serial in previous.values() or item.get("container") == "Worn":
            self._mud(["enter"])
            return None
        self.api(API_EQ_ITEM_EQUIP)(serial)
        container = item.get("container")
        self._taken = _TakenPortal(serial, str(container) if container else None, previous)
        self._mud(["enter"])
        return None

    def _displaced_slots(self, taken: _TakenPortal) -> list[str]:
        """Return the wear locations whose previous item the portal replaced.

        The slot eq lists the portal in is the one. When eq has not yet seen where the portal
        went, every slot whose item changed since it was noted is returned.
        """
        for loc in taken.previous:
            if self._worn_serial(loc) == taken.serial:
                return [loc]
        return [loc for loc, was in taken.previous.items() if self._worn_serial(loc) != was]

    def _restore_portal(self) -> None:
        """Put the taken portal back where it came from and wear what it displaced."""
        taken = self._taken
        if taken is None:
            return
        self._taken = None
        if not self._eq_ready():
            return
        slots = self._displaced_slots(taken)
        if taken.container:
            self.api(API_EQ_ITEM_PUT)(taken.serial, taken.container)
        if not slots:
            log_to(
                self.plugin_id,
                logging.WARNING,
                "portal %s was put back but eq has not seen which slot it took; nothing re-worn",
                taken.serial,
            )
            return
        for loc in slots:
            was = taken.previous[loc]
            if was:
                self.api(API_EQ_ITEM_EQUIP)(was, loc)

    def _finish_portal(self, uid: str) -> None:
        """Store the portal being recorded when the new room arrives."""
        pending = self._pending_portal
        if pending is None:
            return
        serial, level, _ = pending
        self._pending_portal = None
        self._portal_token += 1
        self._put_portal(
            ANYWHERE[0],
            {
                "fromuid": ANYWHERE[0],
                "dir": portal_marker(serial),
                "touid": uid,
                "cost": 1,
                "requirement": None,
            },
            requirement=portal_requirement(serial, level),
        )
        self._client([f"Mapper: portal {self._item_name(serial)} ({serial}) -> {uid}"])

    async def _portal_timeout(self, token: int, seconds: float) -> None:
        """Stop recording a portal when no new room arrives in time."""
        await asyncio.sleep(seconds)
        pending = self._pending_portal
        if token != self._portal_token or pending is None:
            return
        self._pending_portal = None
        self._client([f"Mapper: no new room after using portal {pending[0]}; it was not stored"])
        self._restore_portal()

    def _requirement_for(self, direction: str, level: object) -> dict[str, Any] | None:
        """Return the requirement of an exit with this direction and level; an item portal
        keeps its serial in it."""
        serial = portal_serial(direction)
        if serial is None:
            return requirement_from_level(level)
        return portal_requirement(serial, to_int(level))

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
        """Write the read map through map.batch.add in chunks; captured data wins."""
        phase = "areas"
        done = 0
        total = len(data.areas)
        counts = {"areas": 0, "rooms": 0, "flagged": 0, "notes": 0, "exits": 0, "updated": 0}
        first = True

        async def write(batch: dict[str, Any], size: int) -> bool:
            """Write one chunk, report progress, yield between calls; False to stop."""
            nonlocal first, done
            if not first:
                await asyncio.sleep(0)
            first = False
            if token != self._unload_token:
                return False
            result = self._mapper_api("map.batch.add")(overwrite=False, **batch)
            if result is None:
                raise _BatchRefusedError
            counts["areas"] += result["areas"]
            counts["rooms"] += result["new_rooms"]
            counts["flagged"] += result["rooms"] - result["new_rooms"]
            counts["exits"] += result["new_exits"]
            counts["updated"] += result["exits"] - result["new_exits"]
            counts["notes"] += result["notes"]
            done += size
            self._client([f"Mapper import: {phase} {done}/{total}"])
            return token == self._unload_token

        try:
            self._client([f"Mapper import: {phase} 0/{total}"])
            for chunk in _chunks(data.areas, lambda _: 1):
                if not await write({"areas": chunk}, len(chunk)):
                    return
            phase, done, total = "rooms", 0, len(data.rooms)
            self._client([f"Mapper import: {phase} 0/{total}"])
            for chunk in _chunks(data.rooms, lambda r: 2 if data.notes.get(r["uid"]) else 1):
                notes = {r["uid"]: data.notes[r["uid"]] for r in chunk if data.notes.get(r["uid"])}
                if not await write({"rooms": chunk, "notes": notes}, len(chunk)):
                    return
            phase, done = "exits", 0
            exits = [
                {"fromuid": f, "dir": d, "touid": touid, "cost": 1, "requirement": req}
                for f, items in data.exits.items()
                for d, touid, req in items
            ]
            total = len(exits)
            self._client([f"Mapper import: {phase} 0/{total}"])
            for chunk in _chunks(exits, lambda _: 1):
                if not await write({"exits": chunk}, len(chunk)):
                    return
        except (sqlite3.Error, _BatchRefusedError) as exc:
            log_to(self.plugin_id, logging.ERROR, "import failed in %s", phase, exc_info=True)
            reason = (
                "the mapper refused a batch" if isinstance(exc, _BatchRefusedError) else str(exc)
            )
            self._client([f"Mapper import stopped in {phase} at {done}/{total}: {reason}"])
            return
        self._client(
            [
                f"Mapper import done: {counts['areas']} areas, {counts['rooms']} rooms "
                f"(flags added to {counts['flagged']} stored), {counts['exits']} exits "
                f"({counts['updated']} updated), {counts['notes']} notes; "
                f"skipped {data.skipped_rooms} rooms and {data.skipped_exits} exits"
            ]
        )

    # searches

    def _search_area(self, where: str) -> tuple[str, str | None]:
        """Return the area id a search names (`here` is the current room's area) and, when it
        cannot be told, a failure line."""
        if where != "here":
            return where, None
        current = self._mapper_api("room.current.get")()
        room = self._mapper_api("room.get")(current) if current else None
        area = room.get("area") if room else None
        if not area:
            return where, "Mapper: the current room is not known"
        return str(area), None

    def _search_rows(self, kind: str, where: str) -> list[tuple[str, str, str, str]] | None:
        """Return the (uid, name, area, found) rows of a search in an area id, in room uid
        order; None when the area has no mapped rooms."""
        rooms = sorted(
            self._mapper_api("room.list")(area=where),
            key=lambda r: (to_int(r["uid"]), str(r["uid"])),
        )
        if not rooms:
            return None
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
        return rows

    def _text_table(
        self, title: str, columns: list[dict[str, str]], rows: Iterable[Sequence[str]]
    ) -> list[str]:
        """Return a table of text lines formatted by the core ``table.format``."""
        return list(
            self.api("plugins.core.utils:table.format")(title, table_data(columns, rows), columns)
        )

    def _search(self, kind: str) -> CommandResult:
        """List the rooms of an area that match a search, in room uid order."""
        where, failure = self._search_area(str(self._args().get("area") or "here").strip().lower())
        if failure:
            return CommandResult(False, [failure])
        rows = self._search_rows(kind, where)
        if rows is None:
            return CommandResult(False, [f"Mapper: area {where} has no mapped rooms"])
        if not rows:
            return CommandResult(True, [f"No {kind} found in {where}"])
        title = f"Mapper {kind} in {where}: {len(rows)} rooms"
        return CommandResult(True, self._text_table(title, PLACE_TEXT_COLUMNS, rows))

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
    @AddArgument(
        "-T",
        "--timeout",
        help="seconds to wait for the new room, default the cexittimeout setting",
        type=int,
        default=0,
    )
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
        timeout = to_int(args.get("timeout")) or int(str(self._setting(SETTING_CEXIT_TIMEOUT)))
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

    def _exit_rows(
        self, rooms: list[dict[str, Any]], exits_of: Callable[[str], list[dict[str, Any]]]
    ) -> list[tuple[str, ...]]:
        """Return the (uid, name, area, command, to, level) rows of the exits that `exits_of`
        picks in each room, rooms in numeric uid order."""
        rows: list[tuple[str, ...]] = []
        for found in sorted(rooms, key=lambda r: (to_int(r["uid"]), str(r["uid"]))):
            for item in exits_of(found["uid"]):
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
        return rows

    def _cexit_rows(self, rooms: list[dict[str, Any]]) -> list[tuple[str, ...]]:
        """Return the custom exit rows of rooms."""
        return self._exit_rows(rooms, self._cexits_of)

    def _lock_rows(self, rooms: list[dict[str, Any]]) -> list[tuple[str, ...]]:
        """Return the rows of the exits of rooms that need a level above 0."""

        def locked(uid: str) -> list[dict[str, Any]]:
            return [
                e
                for e in self._mapper_api("exit.list")(uid)
                if requirement_level(e["requirement"]) > 0
            ]

        return self._exit_rows(rooms, locked)

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
        rows = self._cexit_rows(rooms)
        if not rows:
            return CommandResult(True, [f"No custom exits found in {where}"])
        title = f"Mapper custom exits in {where}: {len(rows)}"
        return CommandResult(True, self._text_table(title, CEXIT_TEXT_COLUMNS, rows))

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
                True, self._text_table(f"Mapper exits of {uid}", EXIT_TEXT_COLUMNS, rows)
            )
        found = next((e for e in exits if e["dir"] == text), None)
        if found is None:
            return CommandResult(False, [f"Mapper: room {uid} has no exit {text}"])
        level = args.get("level")
        if level is None:
            shown = requirement_level(found["requirement"])
            return CommandResult(True, [f"Mapper: exit {text} of {uid} needs level {shown}"])
        self._mapper_api("exit.add")(
            uid, text, found["touid"], found["cost"], self._requirement_for(text, level)
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
        text = str(ref).strip()
        serial = serial_arg(text)
        portal = resolve_portal(self._portals(), portal_marker(serial) if serial else text)
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
    @AddArgument(
        "command",
        help="the command that takes the portal, or the serial of a portal item to use and record",
        nargs="+",
    )
    @AddArgument(
        "-l",
        "--level",
        help="the level needed; an item portal defaults to the item's level, 0 for none",
        type=int,
        default=None,
    )
    @AddArgument("-t", "--touid", help="the room it leads to; the current room", default=None)
    @AddArgument("-r", "--recall", help="store it as a recall", action="store_true")
    def _command_portal(self) -> CommandResult:
        """Add a portal; recall, home and hom are stored as recalls. A serial uses the item."""
        args = self._args()
        text = " ".join(str(word) for word in args.get("command") or []).strip()
        serial = serial_arg(text)
        if serial is not None:
            return self._portal_item(serial, args)
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

    def _portal_item(self, serial: int, args: dict[str, Any]) -> CommandResult:
        """Record a portal item: use it and store the room it leads to, or with -t store it."""
        if args.get("recall"):
            return CommandResult(False, ["Mapper: a portal item cannot be a recall"])
        if not self._eq_ready():
            return CommandResult(False, ["Mapper: the eq plugin is not loaded"])
        item = self._eq_item(serial)
        if item is None:
            return CommandResult(False, [f"Mapper: eq does not know item {serial}"])
        if to_int(item.get("itype")) != PORTAL_ITYPE:
            return CommandResult(False, [f"Mapper: item {serial} is not a portal"])
        level = args.get("level")
        level = to_int(item.get("level")) if level is None else to_int(level)
        name = self._item_name(serial)
        exit_dict = {"fromuid": ANYWHERE[0], "dir": portal_marker(serial)}
        if not self._requirement(portal_requirement(serial, level), exit_dict):
            return CommandResult(False, [f"Mapper: {name} ({serial}) needs level {level}"])
        touid = args.get("touid")
        if touid:
            if self._known_room(str(touid)) is None:
                return CommandResult(False, ["Mapper: the room is not known"])
            self._put_portal(
                ANYWHERE[0],
                {
                    "fromuid": ANYWHERE[0],
                    "dir": portal_marker(serial),
                    "touid": str(touid),
                    "cost": 1,
                    "requirement": None,
                },
                requirement=portal_requirement(serial, level),
            )
            return CommandResult(True, [f"Mapper: portal {name} ({serial}) -> {touid}"])
        if self._pending_cexit is not None or self._pending_portal is not None:
            return CommandResult(
                False, ["Mapper: a custom exit or portal is already being recorded"]
            )
        failure = self._use_portal(serial)
        if failure is not None:
            return CommandResult(False, [f"Mapper: {failure}"])
        self._portal_token += 1
        self._pending_portal = (serial, level, self._portal_token)
        timeout = int(str(self._setting(SETTING_CEXIT_TIMEOUT)))
        self.api("libs.asynch:task.add")(
            self._portal_timeout(self._portal_token, timeout), f"{self.plugin_id}:portal"
        )
        return CommandResult(True, [f"Mapper: recording portal {name} ({serial}) by entering it"])

    @staticmethod
    def _kind_name(kind: str) -> str:
        """Return the name of a portal kind."""
        return "recall" if kind == ANYWHERE[1] else "portal"

    @AddCommand()
    @AddParser(description="list the portals and recalls")
    @AddArgument("filter", help="part of an area id", nargs="?", default="")
    def _command_portals(self) -> CommandResult:
        """List the portals and recalls, numbered, in area order."""
        rows = self._portal_rows(str(self._args().get("filter") or ""))
        if not rows:
            return CommandResult(True, ["No portals found"])
        title = f"Mapper portals: {len(rows)}"
        return CommandResult(True, self._text_table(title, PORTAL_TEXT_COLUMNS, rows))

    def _portal_rows(self, wanted: str) -> list[tuple[str, ...]]:
        """Return the (#, kind, area, name, to, command, level) rows of the portals whose room
        area contains `wanted`; the numbers count all portals."""
        wanted = wanted.strip().lower()
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
                    self._portal_label(str(portal["dir"])),
                    str(requirement_level(portal["requirement"])),
                )
            )
        return rows

    def _portal_label(self, direction: str) -> str:
        """Return what the command column shows: the command, or the name of a portal item."""
        serial = portal_serial(direction)
        if serial is None:
            return self._escape(direction)
        item = self._eq_item(serial)
        if item is None:
            return f"item {serial} (not carried)"
        return f"{self._item_name(serial)} ({serial})"

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
        serial = serial_arg(text)
        if serial is None and parse_command(text) is None:
            return CommandResult(
                False, ["Mapper: the command is empty or a wait(N) is not 0 < N <= 40"]
            )
        new = portal_marker(serial) if serial is not None else text
        level = requirement_level(portal["requirement"])
        self._put_portal(
            portal["fromuid"], portal, dir=new, requirement=self._requirement_for(new, level)
        )
        return CommandResult(True, [f"Mapper: portal {portal['dir']} is now {new}"])

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
        self._put_portal(
            portal["fromuid"],
            portal,
            requirement=self._requirement_for(str(portal["dir"]), level),
        )
        return CommandResult(True, [f"Mapper: portal {portal['dir']} needs level {max(level, 0)}"])

    @AddCommand()
    @AddParser(description="switch a portal between a portal and a recall")
    @AddArgument("ref", help="the portal number as #N, or its command in quotes")
    def _command_portalrecall(self) -> CommandResult:
        """Make a portal a recall, or a recall a portal."""
        portal, failure = self._portal_arg(self._args().get("ref"))
        if portal is None:
            return failure or CommandResult(False, ["Mapper: no such portal"])
        if portal_serial(portal["dir"]) is not None:
            return CommandResult(False, ["Mapper: a portal item cannot be a recall"])
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

    # web pages

    def _add_routes(self) -> None:
        """Add the three table pages to the web server; nothing when the web plugin is absent."""
        if not self.api("libs.api:api.exists")(WEB_ROUTE_ADD):
            return
        routes: tuple[
            tuple[str, Callable[[WebRequest], dict[str, Any]], str, list[dict[str, str]]], ...
        ] = (
            ("portals", self._web_portals, "Mapper portals", PORTAL_COLUMNS),
            ("cexits", self._web_cexits, "Mapper custom exits", CEXIT_COLUMNS),
            (
                "places",
                self._web_places,
                "Mapper shops, trainers, questors and notes",
                PLACE_COLUMNS,
            ),
        )
        for subpath, handler, title, columns in routes:
            path = self.api(WEB_ROUTE_ADD)(self.plugin_id, subpath, handler, title, columns)
            if path is None:
                log_to(
                    self.plugin_id, logging.WARNING, "the web server refused the %s page", subpath
                )

    @staticmethod
    def _error(status: int, message: str) -> dict[str, Any]:
        """Return the error response of a page."""
        return {"kind": "error", "status": status, "message": message}

    def _table(
        self,
        request: WebRequest,
        title: str,
        rows: list[list[Any]],
        columns: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Return the table response: the page of rows the request asks for."""
        query = request.table
        if query is None:
            return self._error(400, "this page needs a table request")
        page, total = table_view(
            rows,
            columns,
            sort=query.sort,
            descending=query.descending,
            filters=query.filters,
            offset=query.offset,
            count=query.count,
        )
        return {"kind": "table", "title": title, "rows": page, "total": total}

    def _area_cell(self, area: str) -> str | dict[str, str]:
        """Return the cell of an area id: a link to its page, or empty text."""
        return area_link(area, self._escape(area)) if area else ""

    def _web_portals(self, request: WebRequest) -> dict[str, Any]:
        """Serve the portals and recalls, the rows of the portals command."""
        rows: list[list[Any]] = []
        for number, kind, area, name, touid, command, level in self._portal_rows(""):
            rows.append(
                [
                    to_int(number.removeprefix("#")),
                    kind,
                    self._area_cell(area),
                    room_link(touid, name) if area else name,
                    touid,
                    command,
                    to_int(level),
                ]
            )
        return self._table(request, "Mapper portals", rows, PORTAL_COLUMNS)

    def _area_rooms(
        self, request: WebRequest
    ) -> tuple[str, list[dict[str, Any]], dict[str, Any] | None]:
        """Return the area the `area` query names with its rooms, or an error response."""
        area = area_arg(request.query.get("area", ""))
        if area is None:
            return "", [], self._error(400, "the area is too long")
        where, failure = self._search_area(area)
        if failure:
            return where, [], self._error(404, failure)
        rooms: list[dict[str, Any]] = self._mapper_api("room.list")(area=where)
        if not rooms:
            return where, [], self._error(404, f"area {where} has no mapped rooms")
        return where, rooms, None

    def _web_cexits(self, request: WebRequest) -> dict[str, Any]:
        """Serve the custom exits of one area, or its locked exits with `show=locks`."""
        show = request.query.get("show", "").strip().lower()
        if show not in ("", "cexits", "locks"):
            return self._error(400, "show is cexits or locks")
        where, rooms, failure = self._area_rooms(request)
        if failure:
            return failure
        found = self._lock_rows(rooms) if show == "locks" else self._cexit_rows(rooms)
        rows: list[list[Any]] = [
            [
                uid,
                room_link(uid, name),
                self._area_cell(area),
                command,
                touid,
                to_int(level),
            ]
            for uid, name, area, command, touid, level in found
        ]
        label = "Locked exits" if show == "locks" else "Custom exits"
        return self._table(request, f"{label} in {where}", rows, CEXIT_COLUMNS)

    def _web_places(self, request: WebRequest) -> dict[str, Any]:
        """Serve the shops, trainers, questors or noted rooms of one area."""
        kind = request.query.get("kind", "").strip().lower() or PLACE_KINDS[0]
        if kind not in PLACE_KINDS:
            return self._error(400, f"kind is one of {', '.join(PLACE_KINDS)}")
        where, _, failure = self._area_rooms(request)
        if failure:
            return failure
        found = self._search_rows(kind, where) or []
        rows: list[list[Any]] = [
            [uid, room_link(uid, name), self._area_cell(area), match]
            for uid, name, area, match in found
        ]
        return self._table(request, f"Mapper {kind} in {where}", rows, PLACE_COLUMNS)
