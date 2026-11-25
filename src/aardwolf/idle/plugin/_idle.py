"""Aardwolf idle plugin: send a look when the character's eyes glaze over."""

from bastproxy.libs.logger import get_logger
from bastproxy.libs.records import NetworkData, SendDataDirectlyToMud
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook

from ..libs import (
    ANTI_IDLE_CMD,
    GLAZE_REGEX,
    SETTING_COMMAND,
    SETTING_REGEX,
    TRIGGER_GLAZE,
    regex_error,
)


class IdlePlugin(BasePlugin):
    """Send a command when Aardwolf warns that the character is idle."""

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the settings and the glaze trigger, and watch the regex setting."""
        add = self.api("plugins.core.settings:setting.add")
        add(
            self.plugin_id,
            SETTING_COMMAND,
            ANTI_IDLE_CMD,
            str,
            "the command sent when the character idles",
            nocolor=True,
        )
        add(
            self.plugin_id,
            SETTING_REGEX,
            GLAZE_REGEX,
            str,
            "the regex of the idle warning line",
            nocolor=True,
            validator=regex_error,
        )
        self.api("plugins.core.events:event.register")(
            f"ev_{self.plugin_id}_var_{SETTING_REGEX}_modified", self._eventcb_regex_modified
        )
        result = self.api("plugins.core.triggers:trigger.add")(
            TRIGGER_GLAZE, self._setting(SETTING_REGEX)
        )
        if not result.success:
            get_logger(self.plugin_id).error("could not add the %s trigger", TRIGGER_GLAZE)
            return
        self.api("plugins.core.triggers:trigger.register")(
            result.trigger.trigger_id, self._trigger_glaze
        )

    def _setting(self, name: str) -> str:
        """Return the value of a setting of this plugin."""
        return str(self.api("plugins.core.settings:setting.get")(self.plugin_id, name))

    def _eventcb_regex_modified(self) -> None:
        """Point the glaze trigger at the new regex."""
        regex = self._setting(SETTING_REGEX)
        if not self.api("plugins.core.triggers:trigger.update")(TRIGGER_GLAZE, {"regex": regex}):
            get_logger(self.plugin_id).error(
                "could not update the %s trigger to %r", TRIGGER_GLAZE, regex
            )

    def _trigger_glaze(self) -> None:
        """Send the anti idle command so the mud does not disconnect the character."""
        self._send_to_mud(self._setting(SETTING_COMMAND))

    def _send_to_mud(self, line: str) -> None:
        """Send a line straight to the mud."""
        SendDataDirectlyToMud(NetworkData([line], owner_id=f"{self.plugin_id}:_send_to_mud"))()
