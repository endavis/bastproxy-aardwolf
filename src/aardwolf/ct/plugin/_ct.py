"""Aardwolf ct plugin: show a table of the damage done after each mob kill."""

from typing import Any

from bastproxy.libs.records import NetworkData, NetworkDataLine, SendDataDirectlyToClient
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.events import RegisterToEvent

from aardwolf._libs.validate import int_validator

from ..libs import (
    EMPTYLINE_ID,
    EVENT_MOBK_KILL,
    LINE_LENGTH,
    SETTING_LINE_LENGTH,
    SETTINGS,
    TableHelpers,
    format_kill,
)


class CtPlugin(BasePlugin):
    """Queue the damage table of each kill and show the tables at the next empty line."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Start with no tables queued."""
        self._tables: list[str] = []
        # True while _show is registered on the empty line trigger
        self._waiting = False

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the color settings and the line length setting."""
        for name, (default, help_text) in SETTINGS.items():
            self.api("plugins.core.settings:setting.add")(
                self.plugin_id, name, default, "color", help_text
            )
        self.api("plugins.core.settings:setting.add")(
            self.plugin_id,
            SETTING_LINE_LENGTH,
            LINE_LENGTH,
            int,
            "the width of the damage table",
            validator=int_validator(1, 500),
        )

    def _setting(self, name: str) -> str:
        """Return a setting of the plugin."""
        return str(self.api("plugins.core.settings:setting.get")(self.plugin_id, name))

    def _helpers(self) -> TableHelpers:
        """Return the bastproxy helpers the table uses."""
        center = self.api("plugins.core.utils:string.center.colored")
        duration = self.api("plugins.core.utils:timedelta.to.string")
        return TableHelpers(
            center=lambda text, filler, length: str(center(text, filler, length)),
            duration=lambda start, end, num, unit: str(
                duration(start, end, colorn=num, colors=unit)
            ),
            escape=self.api("plugins.core.colors:colorcode.escape"),
        )

    def _client(self, text: str) -> None:
        """Send a text to the clients, without the preamble."""
        data = NetworkData(
            [NetworkDataLine(text, preamble=False)], owner_id=f"{self.plugin_id}:table"
        )
        SendDataDirectlyToClient(data)()

    @RegisterToEvent(event_name=EVENT_MOBK_KILL)
    def _eventcb_kill(self) -> None:
        """A kill: queue its table and show it at the next empty line."""
        record = self.api("plugins.core.events:event.current.record.get")()
        kill: dict[str, Any] = dict(record) if record else {}
        if "damage" not in kill:
            return
        self._tables.append(
            format_kill(
                kill,
                self._setting("statcolor"),
                self._setting("infocolor"),
                self._helpers(),
                int(self._setting(SETTING_LINE_LENGTH)),
            )
        )
        if not self._waiting:
            registered = self.api("plugins.core.triggers:trigger.register")(
                EMPTYLINE_ID, self._show
            )
            self._waiting = bool(registered)

    def _show(self) -> None:
        """An empty line: send the queued tables in order and stop waiting."""
        if self._waiting:
            self.api("plugins.core.triggers:trigger.unregister")(EMPTYLINE_ID, self._show)
            self._waiting = False
        tables, self._tables = self._tables, []
        for table in tables:
            self._client(table)
