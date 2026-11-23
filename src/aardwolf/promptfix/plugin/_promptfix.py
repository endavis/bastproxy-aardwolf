"""Aardwolf prompt fixer plugin: make the prompt and battle prompt end in %c."""

import logging
from typing import Any

from bastproxy.libs.logger import get_logger, log_to
from bastproxy.libs.records import (
    NetworkData,
    NetworkDataLine,
    SendDataDirectlyToClient,
    SendDataDirectlyToMud,
)
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.events import RegisterToEvent

from ..libs import (
    EVENT_AUTOFIX_MODIFIED,
    EVENT_DISCONNECT,
    EVENT_PROMPTS,
    GMCP_REQUEST,
    PROMPT_KINDS,
    PROMPT_SET_REGEX,
    PROMPT_SET_TRIGGER,
    SETTING_AUTOFIX,
    PromptStatus,
    fix_prompt,
    fixed_message,
    too_long_message,
)

_INIT = "__init__"


class PromptFixPlugin(BasePlugin):
    """Make the prompt and battle prompt end in %c, so the next line never sticks to them."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Initialize the state."""
        self._requesting = False

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the setting and the trigger for a prompt change."""
        self.api("plugins.core.settings:setting.add")(
            self.plugin_id,
            SETTING_AUTOFIX,
            True,
            bool,
            "change a prompt that does not end in %c so that it does",
        )
        result = self.api("plugins.core.triggers:trigger.add")(PROMPT_SET_TRIGGER, PROMPT_SET_REGEX)
        if result.success:
            self.api("plugins.core.triggers:trigger.register")(
                result.trigger.trigger_id, self._trigger_prompt_set
            )
        else:
            get_logger(self.plugin_id).error("could not add the %s trigger", PROMPT_SET_TRIGGER)

    @RegisterPluginHook("character_active")
    def _phook_character_active(self) -> None:
        """The character is first active: read the prompts."""
        self._request_prompts()

    def _enabled(self) -> bool:
        """Return True when the fixer is turned on."""
        return bool(self.api("plugins.core.settings:setting.get")(self.plugin_id, SETTING_AUTOFIX))

    def _request_prompts(self) -> None:
        """Ask the mud for the prompts, unless the fixer is off or a request is waiting."""
        if not self._enabled() or self._requesting:
            return
        if self.api("libs.net.protocols:gmcp.send")(GMCP_REQUEST):
            self._requesting = True

    def _trigger_prompt_set(self) -> None:
        """The mud says a prompt was set: read the prompts again."""
        self._request_prompts()

    @RegisterToEvent(event_name=EVENT_PROMPTS)
    def _eventcb_prompts(self) -> None:
        """Fix the prompts that do not end in %c."""
        self._requesting = False
        if not self._enabled():
            return
        record = self.api("plugins.core.events:event.current.record.get")() or {}
        data = record.get("data")
        if not isinstance(data, dict):
            return
        for key, command, label in PROMPT_KINDS:
            prompt = data.get(key)
            if not isinstance(prompt, str):
                continue
            self._fix_one(command, label, prompt)

    def _fix_one(self, command: str, label: str, prompt: str) -> None:
        """Fix one prompt and tell the client; the prompt text itself is never shown."""
        fix = fix_prompt(prompt)
        if fix.status == PromptStatus.FIXED:
            self._send_to_mud(f"{command} {fix.prompt}")
            self._send_to_client(fixed_message(label))
        elif fix.status == PromptStatus.TOO_LONG:
            log_to(self.plugin_id, logging.WARNING, "the %s is too long to fix", label)
            self._send_to_client(too_long_message(label))

    @RegisterToEvent(event_name=EVENT_DISCONNECT)
    def _eventcb_disconnect(self) -> None:
        """Forget a waiting request when the mud disconnects."""
        self._requesting = False

    @RegisterToEvent(event_name=EVENT_AUTOFIX_MODIFIED)
    def _eventcb_autofix_modified(self) -> None:
        """The fixer was turned on while the character is active: read the prompts."""
        record: dict[str, Any] = self.api("plugins.core.events:event.current.record.get")() or {}
        if record.get("oldvalue") == _INIT or not record.get("newvalue"):
            return
        if (
            self.api("plugins.core.proxy:mud.is.connected")()
            and self.api("libs.api:character.is.active")()
        ):
            self._request_prompts()

    def _send_to_mud(self, line: str) -> None:
        """Send a line straight to the mud."""
        SendDataDirectlyToMud(NetworkData([line], owner_id=f"{self.plugin_id}:_send_to_mud"))()

    def _send_to_client(self, message: str) -> None:
        """Send a message straight to the clients."""
        SendDataDirectlyToClient(
            NetworkData([NetworkDataLine(message)], owner_id=f"{self.plugin_id}:_send_to_client")
        )()
