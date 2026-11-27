"""Aardwolf quest plugin: turn the GMCP quest messages into events."""

import copy
import logging
import time
from typing import Any

from bastproxy.libs.logger import log_to
from bastproxy.libs.persistentdict import PersistentDict
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.events import RegisterToEvent

from aardwolf._libs import aardu
from aardwolf._libs.eventu import own_event, own_events

from ..libs import (
    ACTION_EVENTS,
    EVENT_GMCP_QUEST,
    EVENTS,
    PROVIDER_CURRENT,
    WEB_PROVIDER_ADD,
    WEB_PROVIDER_CHANGED,
    quest_current,
    start_state,
)


class QuestPlugin(BasePlugin):
    """Keep the current quest and raise an event for each GMCP quest action."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Load the saved quest state."""
        self.quest = PersistentDict(
            self.plugin_id, self.plugin_info.data_directory / "quest.txt", "c"
        )
        # the web providers the web plugin accepted
        self._web_providers: set[str] = set()

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the events."""
        add_event = self.api("plugins.core.events:event.add")
        for event_name, info in own_events(self.plugin_id, EVENTS).items():
            add_event(
                event_name,
                self.plugin_id,
                description=info["description"],
                arg_descriptions=info["arg_descriptions"],
            )
        self._add_web_providers()

    def _add_web_providers(self) -> None:
        """Offer the current quest as a web data provider."""
        self._web_providers = set()
        if self.api(WEB_PROVIDER_ADD)(self.plugin_id, PROVIDER_CURRENT, self._provider_current):
            self._web_providers.add(PROVIDER_CURRENT)

    def _provider_current(self) -> dict[str, Any]:
        """The current quest: target, area, room, end, time left and outcome."""
        return quest_current(self.quest, self._now())

    def _provider_changed(self, name: str) -> None:
        """Tell the web plugin a provider changed, when it was accepted."""
        if name in self._web_providers:
            self.api(WEB_PROVIDER_CHANGED)(self.plugin_id, name)

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
        suffix = ACTION_EVENTS.get(action) if isinstance(action, str) else None
        if suffix is None:
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
        self.api("plugins.core.events:event.raise")(
            own_event(self.plugin_id, suffix), event_args=payload
        )
        self.quest.sync()
        self._provider_changed(PROVIDER_CURRENT)

    @RegisterPluginHook("save")
    def _phook_save(self) -> None:
        """Save the quest state."""
        self.quest.sync()
