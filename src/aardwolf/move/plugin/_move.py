"""Aardwolf move plugin: raise an event when the character changes room."""

import copy
import logging
from typing import Any

from bastproxy.libs.logger import log_to
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.events import RegisterToEvent

from ..libs import (
    EVENT_DISCONNECT,
    EVENT_GMCP_ROOM,
    EVENT_MOVE_ROOM,
    EVENTS,
    GMCP_ROOM,
    move_payload,
    room_num,
)


class MovePlugin(BasePlugin):
    """Remember the last room and raise an event when the room changes."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Start with no known room."""
        self._last: dict[str, Any] | None = None

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the event and seed the last room from the GMCP cache."""
        add_event = self.api("plugins.core.events:event.add")
        for event_name, info in EVENTS.items():
            add_event(
                event_name,
                self.plugin_id,
                description=info["description"],
                arg_descriptions=info["arg_descriptions"],
            )
        room = self.api("libs.net.protocols:gmcp.value.get")(GMCP_ROOM)
        if room_num(room) is not None:
            self._last = copy.deepcopy(dict(room))

    @RegisterToEvent(event_name=EVENT_GMCP_ROOM)
    def _eventcb_room_info(self) -> None:
        """Raise move_room when the room num changed."""
        record: dict[str, Any] = self.api("plugins.core.events:event.current.record.get")() or {}
        data = record.get("data")
        if not isinstance(data, dict) or room_num(data) is None:
            return
        payload = move_payload(self._last, data)
        if payload is not None:
            log_to(self.plugin_id, logging.DEBUG, "raising move_room: %s", payload)
            self.api("plugins.core.events:event.raise")(EVENT_MOVE_ROOM, event_args=payload)
        self._last = copy.deepcopy(data)

    @RegisterToEvent(event_name=EVENT_DISCONNECT)
    def _eventcb_disconnect(self) -> None:
        """Forget the last room when the mud disconnects."""
        self._last = None
