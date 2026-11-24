"""Aardwolf idle plugin: send a look when the character's eyes glaze over."""

from bastproxy.libs.logger import get_logger
from bastproxy.libs.records import NetworkData, SendDataDirectlyToMud
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook

from ..libs import ANTI_IDLE_CMD, GLAZE_REGEX, TRIGGER_GLAZE


class IdlePlugin(BasePlugin):
    """Send a look when Aardwolf warns that the character is idle."""

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the glaze trigger and register its callback."""
        result = self.api("plugins.core.triggers:trigger.add")(TRIGGER_GLAZE, GLAZE_REGEX)
        if not result.success:
            get_logger(self.plugin_id).error("could not add the %s trigger", TRIGGER_GLAZE)
            return
        self.api("plugins.core.triggers:trigger.register")(
            result.trigger.trigger_id, self._trigger_glaze
        )

    def _trigger_glaze(self) -> None:
        """Send a look so the mud does not disconnect the character."""
        self._send_to_mud(ANTI_IDLE_CMD)

    def _send_to_mud(self, line: str) -> None:
        """Send a line straight to the mud."""
        SendDataDirectlyToMud(NetworkData([line], owner_id=f"{self.plugin_id}:_send_to_mud"))()
