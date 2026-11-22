"""Aardwolf quest plugin: turn the GMCP quest messages into events."""

import copy
import logging
import time
from typing import Any

from bastproxy.libs.logger import log_to
from bastproxy.libs.persistentdict import PersistentDict
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.events import RegisterToEvent

from aardwolf.libs import aardu

from ..libs import ACTION_EVENTS, EVENT_GMCP_QUEST, EVENTS, start_state


class QuestPlugin(BasePlugin):
    """Keep the current quest and raise an event for each GMCP quest action."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Load the saved quest state."""
        self.quest = PersistentDict(
            self.plugin_id, self.plugin_info.data_directory / "quest.txt", "c"
        )

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the events."""
        add_event = self.api("plugins.core.events:event.add")
        for event_name, info in EVENTS.items():
            add_event(
                event_name,
                self.plugin_id,
                description=info["description"],
                arg_descriptions=info["arg_descriptions"],
            )

    @staticmethod
    def _now() -> float:
        """Return the current time."""
        return time.time()

    def _level(self) -> int:
        """Return the total level of the character."""
        return aardu.actual_level_from_gmcp(self.api("libs.net.protocols:gmcp.value.get"))

    @RegisterToEvent(event_name=EVENT_GMCP_QUEST)
    def _eventcb_quest(self) -> None:
        """Handle a GMCP quest message: update the state and raise the event."""
        record = self.api("plugins.core.events:event.current.record.get")()
        data = record["data"]
        log_to(self.plugin_id, logging.DEBUG, "quest: %s", data)
        if not isinstance(data, dict):
            return
        action = data.get("action")
        event_name = ACTION_EVENTS.get(action) if isinstance(action, str) else None
        if event_name is None:
            return
        payload: dict[str, Any]
        if action == "start":
            self.quest.clear()
            self.quest.update(start_state(data, self._now(), self._level()))
            payload = copy.deepcopy(dict(self.quest))
        elif action == "killed":
            self.quest["killedtime"] = self._now()
            payload = copy.deepcopy(dict(self.quest))
        elif action == "comp":
            self.quest["finishtime"] = self._now()
            self.quest.update(data)
            payload = copy.deepcopy(dict(self.quest))
        elif action in ("fail", "timeout"):
            self.quest["finishtime"] = self._now()
            self.quest["failed"] = 1
            payload = copy.deepcopy(dict(self.quest))
        elif action == "status":
            payload = copy.deepcopy(data)
        else:
            payload = {}
        self.api("plugins.core.events:event.raise")(event_name, event_args=payload)
        self.quest.sync()

    @RegisterPluginHook("save")
    def _phook_save(self) -> None:
        """Save the quest state."""
        self.quest.sync()
