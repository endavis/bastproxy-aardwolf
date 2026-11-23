"""Aardwolf repop plugin: send a message to a channel when an area repops."""

import time

from bastproxy.libs.logger import get_logger
from bastproxy.libs.records import NetworkData, SendDataDirectlyToMud
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.events import RegisterToEvent

from ..libs import (
    DEFAULT_CHANNEL,
    DEFAULT_FORMAT,
    EVENT_GMCP_REPOP,
    SETTING_CHANNEL,
    SETTING_FORMAT,
    format_message,
    repop_command,
    repop_zone,
)


class RepopPlugin(BasePlugin):
    """Send a message to a channel when an area repops."""

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the settings."""
        add = self.api("plugins.core.settings:setting.add")
        add(
            self.plugin_id,
            SETTING_CHANNEL,
            DEFAULT_CHANNEL,
            str,
            "the channel to send the repop message",
        )
        add(
            self.plugin_id,
            SETTING_FORMAT,
            DEFAULT_FORMAT,
            str,
            "the format of the message; ${zone} and ${time} are replaced",
            nocolor=True,
        )

    @RegisterToEvent(event_name=EVENT_GMCP_REPOP)
    def _eventcb_repop(self) -> None:
        """A zone repopped: send the message to the channel."""
        record = self.api("plugins.core.events:event.current.record.get")() or {}
        zone = repop_zone(record.get("data"))
        if zone is None:
            get_logger(self.plugin_id).debug("comm.repop without a zone, nothing sent")
            return
        get = self.api("plugins.core.settings:setting.get")
        message = format_message(
            str(get(self.plugin_id, SETTING_FORMAT)),
            zone,
            time.strftime("%X", time.localtime()),
        )
        line = repop_command(str(get(self.plugin_id, SETTING_CHANNEL)), message)
        if line is not None:
            self._send_to_mud(line)

    def _send_to_mud(self, line: str) -> None:
        """Send a line straight to the mud."""
        SendDataDirectlyToMud(NetworkData([line], owner_id=f"{self.plugin_id}:_send_to_mud"))()
