"""The a102 plugin: counted toggles for Aardwolf telnet option 102 and its data events."""

import logging

from bastproxy.libs.api import AddAPI
from bastproxy.libs.logger import log_to
from bastproxy.libs.records import NetworkData, SendDataDirectlyToMud
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.events import RegisterToEvent

from ..libs import (
    A102_OPTION,
    OFF,
    ON,
    OPTION_NAMES,
    apply_toggle,
    off_payloads,
    option_number,
    parse_pair,
    parse_toggle,
    state_payloads,
    tag_command,
    tag_name,
)

MUD_DATA_ARGS = {
    "option": "the option number",
    "flag": "the flag the MUD sent with it",
}


class A102Plugin(BasePlugin):
    """Toggle Aardwolf option 102 features and publish the MUD's two-byte reports."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Initialize the instance."""
        self.option_counts: dict[int, int] = {}
        self.enabled = False
        self.option_events: set[int] = set()
        self.tag_counts: dict[str, int] = {}
        self.tags_sent: set[str] = set()
        self.attributes_to_save_on_reload = ["option_counts", "tag_counts", "tags_sent"]

    @property
    def data_event(self) -> str:
        """The event raised for every two-byte message from the MUD."""
        return f"ev_{self.plugin_id}_mud_data"

    def option_event(self, number: int) -> str:
        """The event raised for the messages of one option number."""
        return f"ev_{self.plugin_id}_mud_option_{number}"

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Own option 102 and add the data event."""
        self.api("libs.net.protocols:telopt.register")(A102_OPTION)
        self.api("plugins.core.events:event.add")(
            self.data_event,
            self.plugin_id,
            description=["raised for every two-byte option 102 message from the MUD"],
            arg_descriptions=MUD_DATA_ARGS,
        )
        # after a reload the link may already be up, and no enabled event follows
        info = self.api("libs.net.protocols:telopt.get")(A102_OPTION)
        if info and info.get("mud_enabled"):
            self._eventcb_mud_enabled()

    # Runs before the base uninitialize hook (priority 100), which unregisters option 102
    # and would make telopt.send refuse the sends.
    @RegisterPluginHook("uninitialize", priority=10)
    def _phook_turn_options_off(self) -> None:
        """On a real unload, turn off every counted option; a reload keeps them on."""
        if self.is_reloading_f or not self.enabled:
            return
        for payload in off_payloads(self.option_counts):
            self.api("libs.net.protocols:telopt.send")(A102_OPTION, payload)

    @RegisterPluginHook("uninitialize", priority=10)
    def _phook_turn_tags_off(self) -> None:
        """On a real unload, turn off the tags this connection turned on; a reload keeps them."""
        if self.is_reloading_f:
            return
        if self._character_active():
            for key in sorted(self.tags_sent):
                self._send_to_mud(tag_command(key, False))
        self.tags_sent.clear()

    def _send_to_mud(self, line: str) -> None:
        """Send a line straight to the mud."""
        SendDataDirectlyToMud(NetworkData([line], owner_id=f"{self.plugin_id}:_send_to_mud"))()

    def _character_active(self) -> bool:
        """Return True when the character is active, so the MUD takes commands."""
        return bool(self.api("libs.api:character.is.active")())

    def _toggle_number(self, number: int, enable: bool) -> bool:
        """Count a toggle and tell the MUD when its state changed and it can hear it."""
        flag = apply_toggle(self.option_counts, number, enable)
        if flag is not None and self.enabled:
            self.api("libs.net.protocols:telopt.send")(A102_OPTION, bytes([number, flag]))
        return True

    @AddAPI(
        "option.toggle",
        description="turn an option 102 feature on or off; requests are counted",
    )
    def _api_option_toggle(self, name: str, enable: bool) -> bool:
        """Count one on or off request for an option.

        @Yname@w     = the option name, for example SPELLUPTAGS
        @Yenable@w   = True to turn it on, False to turn it off

        The MUD hears about the first on and the last off. Returns False for an unknown name.
        """
        number = option_number(name)
        if number is None:
            log_to(self.plugin_id, logging.WARNING, "unknown option 102 option name %r", name)
            return False
        return self._toggle_number(number, bool(enable))

    @AddAPI(
        "tag.toggle",
        description="turn a MUD tags command tag on or off; requests are counted",
    )
    def _api_tag_toggle(self, name: str, enable: bool) -> bool:
        """Count one on or off request for a tag of the MUD's ``tags`` command.

        @Yname@w     = the tag name, for example SCAN
        @Yenable@w   = True to turn it on, False to turn it off

        The MUD hears the first on and the last off, and only while the character is active.
        Returns False for an invalid name.
        """
        key = tag_name(name)
        if key is None:
            log_to(self.plugin_id, logging.WARNING, "invalid tag name %r", name)
            return False
        flag = apply_toggle(self.tag_counts, key, bool(enable))
        if flag == ON and key not in self.tags_sent and self._character_active():
            self._send_to_mud(tag_command(key, True))
            self.tags_sent.add(key)
        elif flag == OFF and key in self.tags_sent:
            if self._character_active():
                self._send_to_mud(tag_command(key, False))
            self.tags_sent.discard(key)
        return True

    @RegisterPluginHook("character_active")
    def _phook_character_active(self) -> None:
        """The character is active: turn on the counted tags not yet sent on this connection."""
        for key in sorted(self.tag_counts):
            if self.tag_counts[key] > 0 and key not in self.tags_sent:
                self._send_to_mud(tag_command(key, True))
                self.tags_sent.add(key)

    @RegisterToEvent(event_name="ev_libs.net.mud_muddisconnect")
    def _eventcb_mud_disconnected(self) -> None:
        """The MUD link dropped: the next connection needs its tags sent again."""
        self.tags_sent.clear()

    @AddAPI("payload.send", description="send a raw option 102 payload to the MUD")
    def _api_payload_send(self, payload: bytes) -> bool:
        """Send ``payload`` as an option 102 subnegotiation; False when it was not sent."""
        return bool(self.api("libs.net.protocols:telopt.send")(A102_OPTION, payload))

    @RegisterToEvent(event_name="ev_libs.net.mud_telopt_102_enabled")
    def _eventcb_mud_enabled(self) -> None:
        """Option 102 came up on the MUD link: send the state of every counted option."""
        self.enabled = True
        for payload in state_payloads(self.option_counts):
            self.api("libs.net.protocols:telopt.send")(A102_OPTION, payload)

    @RegisterToEvent(event_name="ev_libs.net.mud_telopt_102_disabled")
    def _eventcb_mud_disabled(self) -> None:
        """Option 102 went down on the MUD link."""
        self.enabled = False

    @RegisterToEvent(event_name="ev_libs.net.client_telopt_102")
    def _eventcb_client_data(self) -> None:
        """A client sent an option 102 toggle: count it like a plugin's."""
        record = self.api("plugins.core.events:event.current.record.get")()
        if record.get("view_only"):
            log_to(self.plugin_id, logging.DEBUG, "ignoring a view only client's option 102 data")
            return
        toggle = parse_toggle(record["data"])
        if toggle is None:
            log_to(
                self.plugin_id,
                logging.DEBUG,
                "ignoring malformed client option 102 data %r",
                record["data"],
            )
            return
        self._toggle_number(*toggle)

    @RegisterToEvent(event_name="ev_libs.net.mud_telopt_102")
    def _eventcb_mud_data(self) -> None:
        """The MUD sent option 102 data: raise the events for a two-byte message."""
        record = self.api("plugins.core.events:event.current.record.get")()
        pair = parse_pair(record["data"])
        if pair is None:
            log_to(self.plugin_id, logging.DEBUG, "ignoring option 102 data %r", record["data"])
            return
        number, flag = pair
        args = {"option": number, "flag": flag}
        raise_event = self.api("plugins.core.events:event.raise")
        raise_event(self.data_event, dict(args))
        if number not in self.option_events:
            self.api("plugins.core.events:event.add")(
                self.option_event(number),
                self.plugin_id,
                description=[
                    f"raised for option 102 messages about option {number}"
                    f" ({OPTION_NAMES.get(number, 'unknown')})"
                ],
                arg_descriptions=MUD_DATA_ARGS,
            )
            self.option_events.add(number)
        raise_event(self.option_event(number), dict(args))
