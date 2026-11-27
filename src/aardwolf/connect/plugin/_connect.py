"""Aardwolf connect plugin: GMCP setup and first-active detection."""

from typing import Any

from bastproxy.libs.api import AddAPI
from bastproxy.libs.logger import get_logger
from bastproxy.libs.records import NetworkData, SendDataDirectlyToMud
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook

PRESS_RETURN_TRIGGER = "press_return"
PRESS_RETURN_REGEX = r"^\s*\[ Press Return to continue \]"
GMCP_MODULES = ["Char 1", "Room 1", "Comm 1", "Group 1", "Core 1"]
CHAR_PATHS = (
    "char.base.redos",
    "char.vitals.hp",
    "char.stats.str",
    "char.maxstats.maxhp",
    "char.worth.gold",
)
ROOM_PATH = "room.info.num"
QUEST_PATH = "comm.quest.action"
STATE_PATH = "char.status.state"
ACTIVE_STATES = (3, "3")

EVENT_GMCP = "ev_libs.net.mud_gmcp"
EVENT_GMCP_CHAR = "ev_libs.net.mud_gmcp_char"
EVENT_GMCP_ROOM = "ev_libs.net.mud_gmcp_room.info"
EVENT_GMCP_QUEST = "ev_libs.net.mud_gmcp_comm.quest"
EVENTS_GMCP_VITALS = tuple(
    f"ev_libs.net.mud_gmcp_char.{package}" for package in ("vitals", "maxstats", "status", "base")
)
VITALS_PROVIDER = "vitals"
VITALS_FIELDS: dict[str, str] = {
    "hp": "char.vitals.hp",
    "maxhp": "char.maxstats.maxhp",
    "mana": "char.vitals.mana",
    "maxmana": "char.maxstats.maxmana",
    "moves": "char.vitals.moves",
    "maxmoves": "char.maxstats.maxmoves",
    "level": "char.status.level",
    "tier": "char.base.tier",
    "remorts": "char.base.remorts",
    "tnl": "char.status.tnl",
    "align": "char.status.align",
    "state": "char.status.state",
    "pos": "char.status.pos",
    "enemy": "char.status.enemy",
    "enemypct": "char.status.enemypct",
}
EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"
EVENT_CLIENT_LOGGED_IN = "ev_plugins.core.clients_client_logged_in"


class ConnectPlugin(BasePlugin):
    """Set up Aardwolf GMCP and detect when the character is first active."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Initialize the state flags."""
        self._vitals_offered: set[str] = set()
        self._reset_state()

    def _reset_state(self) -> None:
        """Clear the per-connection state."""
        self._first_active = False
        self._gmcp_ready = False
        self._sent_char = False
        self._sent_room = False
        self._sent_quest = False

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add GMCP modules, the Press Return trigger and the event callbacks."""
        self.api("libs.net.protocols:gmcp.modules.add")(GMCP_MODULES)

        result = self.api("plugins.core.triggers:trigger.add")(
            PRESS_RETURN_TRIGGER, PRESS_RETURN_REGEX
        )
        if result.success:
            self.api("plugins.core.triggers:trigger.register")(
                result.trigger.trigger_id, self._trigger_press_return
            )
        else:
            get_logger(self.plugin_id).error("could not add the %s trigger", PRESS_RETURN_TRIGGER)

        register = self.api("plugins.core.events:event.register")
        register(EVENT_GMCP, self._eventcb_gmcp_setup)
        register(EVENT_GMCP_CHAR, self._eventcb_check)
        register(EVENT_GMCP_ROOM, self._eventcb_check)
        register(EVENT_GMCP_QUEST, self._eventcb_check)
        register(EVENT_DISCONNECT, self._eventcb_mud_disconnected)
        register(EVENT_CLIENT_LOGGED_IN, self._eventcb_client_logged_in)
        for event in EVENTS_GMCP_VITALS:
            register(event, self._eventcb_vitals_changed)

        # loaded mid-session: the mud is already connected and the character logged in
        if self._mud_connected() and self._state_is_active():
            self._gmcp_setup()
            self._request_all()
            self._check_first_active()

    @RegisterPluginHook("after_load", priority=60)
    def _phook_add_web_providers(self) -> None:
        """Offer the character vitals as a web data provider; a refusal is logged."""
        self._vitals_offered = set()
        add = self.api("plugins.core.web:web.provider.add")
        if add(self.plugin_id, VITALS_PROVIDER, self._provider_vitals):
            self._vitals_offered.add(VITALS_PROVIDER)

    def _provider_vitals(self) -> dict[str, Any]:
        """Return the vitals from the cached GMCP data; a missing value is None."""
        return {name: self._gmcp_value(path) for name, path in VITALS_FIELDS.items()}

    def _provider_changed(self, name: str) -> None:
        """Tell the web listeners a provider changed, when it was offered."""
        if name in self._vitals_offered:
            self.api("plugins.core.web:web.provider.changed.raise")(self.plugin_id, name)

    def _eventcb_vitals_changed(self) -> None:
        """Raise a vitals change after a vitals, maxstats, status or base message."""
        self._provider_changed(VITALS_PROVIDER)

    def _mud_connected(self) -> bool:
        """Return True when the proxy is connected to the mud."""
        return bool(self.api("plugins.core.proxy:mud.is.connected")())

    def _gmcp_value(self, path: str) -> object:
        """Return the cached GMCP value at a dotted path, or None."""
        return self.api("libs.net.protocols:gmcp.value.get")(path)

    def _gmcp_send(self, package: str) -> bool:
        """Send a GMCP message to the mud; False when it was not sent."""
        return bool(self.api("libs.net.protocols:gmcp.send")(package))

    def _state_is_active(self) -> bool:
        """Return True when the character state is active (3)."""
        return self._gmcp_value(STATE_PATH) in ACTIVE_STATES

    def _send_to_mud(self, line: str) -> None:
        """Send a line straight to the mud."""
        SendDataDirectlyToMud(NetworkData([line], owner_id=f"{self.plugin_id}:_send_to_mud"))()

    def _gmcp_setup(self) -> None:
        """Turn on raw colors and group updates once GMCP works."""
        if not self._gmcp_ready and self._gmcp_send("rawcolor on"):
            self._gmcp_send("group on")
            self._gmcp_ready = True

    def _request_all(self) -> None:
        """Ask the mud for the room, quest and character data."""
        self._gmcp_send("request room")
        self._gmcp_send("request quest")
        self._gmcp_send("request char")

    def _eventcb_gmcp_setup(self) -> None:
        """Set up GMCP on the first GMCP message from the mud."""
        self._gmcp_setup()

    def _eventcb_client_logged_in(self) -> None:
        """Request the data again for a client that logged in."""
        if self._mud_connected() and self._gmcp_ready:
            self._request_all()

    def _eventcb_check(self) -> None:
        """Check for first active after a GMCP update."""
        self._check_first_active()

    def _check_data(self, paths: tuple[str, ...], request: str, flag: str) -> bool:
        """Return True when all paths have values, else request the data once."""
        if all(self._gmcp_value(path) is not None for path in paths):
            return True
        if not getattr(self, flag) and self._gmcp_send(request):
            setattr(self, flag, True)
        return False

    def _check_char(self) -> bool:
        """Return True when the character data is present."""
        return self._check_data(CHAR_PATHS, "request char", "_sent_char")

    def _check_room(self) -> bool:
        """Return True when the room data is present."""
        return self._check_data((ROOM_PATH,), "request room", "_sent_room")

    def _check_quest(self) -> bool:
        """Return True when the quest data is present."""
        return self._check_data((QUEST_PATH,), "request quest", "_sent_quest")

    def _check_first_active(self) -> None:
        """Mark the character first active when all its data is in."""
        if self._first_active or not self._mud_connected():
            return
        checks = [self._check_char(), self._check_room(), self._check_quest()]
        if all(checks) and self._state_is_active():
            self._set_first_active()

    def _set_first_active(self) -> None:
        """Record first active, look around and raise the active event."""
        self._first_active = True
        self._send_to_mud("look")
        self._send_to_mud("map")
        self._sent_char = self._sent_room = self._sent_quest = False
        if not self.api("libs.api:character.is.active")():
            self.api("libs.api:character.active.set")(True)
        get_logger(self.plugin_id).info("character is first active")

    def _trigger_press_return(self) -> None:
        """Press return at a pager prompt until the character is first active."""
        if not self._first_active:
            self._send_to_mud("")

    def _eventcb_mud_disconnected(self) -> None:
        """Forget the connection state when the mud disconnects."""
        self._reset_state()
        self._provider_changed(VITALS_PROVIDER)

    @AddAPI("character.is.first.active", description="True once the character was first active")
    def _api_character_is_first_active(self) -> bool:
        """Return True once the character has been first active."""
        return self._first_active
