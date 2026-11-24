"""Aardwolf mapper plugin: feed the core mapper with rooms, areas, flags and walking rules."""

import logging
from collections.abc import Callable
from typing import Any

from bastproxy.libs.logger import log_to
from bastproxy.libs.records import NetworkData, NetworkDataLine, SendDataDirectlyToClient
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
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
    MAPPER,
    NOPORTAL_REGEX,
    NORECALL_REGEX,
    area_from_gmcp,
    mismatch_lines,
    requirement_allowed,
    room_from_gmcp,
    room_uid,
    steps_to_commands,
    to_int,
)


class MapperPlugin(BasePlugin):
    """Give the core mapper the rooms, areas and walking rules of Aardwolf."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Start with no known room."""
        self._current: str | None = None
        self._requested_areas: set[str] = set()

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
        """Take the callbacks back from the mapper."""
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
