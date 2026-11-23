"""A real core mudcmds hide window for the plugin tests to drive.

The cp, skills and whois tests fake the command queue but not the hiding: their lines go through
the hide window of the real core ``MUDCmdsPlugin``, so the tests assert what a client would see.
The helper calls private methods of the core plugin (``_arm_hide``, ``_finish_hide``,
``_eventcb_hide_line``, ``_eventcb_hide_disconnect`` and ``_close_hide``), so a core bump that
renames one fails these tests loudly.
"""

from collections.abc import Callable
from typing import Any

CORE_ID = "plugins.core.mudcmds"


class CoreHide:
    """Wrap a real core mudcmds plugin, driving only its hide window."""

    def __init__(self, get_record: Callable[[], dict[str, Any]]) -> None:
        """Build the core plugin; get_record returns the record of the line being fed."""
        # imported here because the import needs BASTPROXY_HOME to be set
        from bastproxy.plugins.core.mudcmds.plugin._mudcmds import MUDCmdsPlugin, QueuedCommand

        self._queued_command = QueuedCommand
        self._get_record = get_record
        self.events_added: list[str] = []
        self.current: Any = None
        core: Any = MUDCmdsPlugin.__new__(MUDCmdsPlugin)
        core.plugin_id = CORE_ID
        core.api = self._api
        core.queue = []
        core.cmds = {}
        core.current_command = None
        core.timing_uid = None
        core._phook_init_plugin()
        # on a live link after login with promptfix loaded, a prompt has been seen
        core._prompts_seen = True
        self.core = core

    def _api(self, name: str) -> Callable[..., Any]:
        """Route the few APIs the hide code calls."""
        if name == "plugins.core.events:event.current.record.get":
            return self._get_record
        if name == "libs.api:caller.owner.get":
            return lambda **_: CORE_ID
        if name == "plugins.core.events:event.add":
            return lambda event, *_, **__: self.events_added.append(event)
        return lambda *_, **__: None

    @property
    def prompts_seen(self) -> bool:
        """Whether a prompt has been seen on the link."""
        return bool(self.core._prompts_seen)

    @prompts_seen.setter
    def prompts_seen(self, value: bool) -> None:
        self.core._prompts_seen = value

    def is_open(self) -> bool:
        """Whether a hide window is open; a method so mypy does not narrow it across asserts."""
        return self.core._hide_open is not None

    def is_armed(self) -> bool:
        """Whether a hide window is armed and waiting for its first line."""
        return self.core._hide_armed is not None

    def add_type(self, cmdtype: str, cmd: str, regex: str, **kwargs: object) -> None:
        """Register a command type with core, as the plugin's type.add does."""
        self.core._api_type_add(cmdtype, cmd, regex, **kwargs)

    def sent(self, cmdtype: str, cmd: str) -> None:
        """The queue sent a command of a type: arm its hide window."""
        self.current = self._queued_command(cmd=cmd, ctype=cmdtype, plugin=CORE_ID)
        self.core._arm_hide(self.current)

    def finished(self, cmdtype: str) -> None:
        """The plugin finished the current command, when it is of this type."""
        if self.current is not None and self.current.ctype == cmdtype:
            self.core._finish_hide(self.current)
            self.current = None

    def line(self) -> None:
        """A line reached the before-all-lines trigger."""
        self.core._eventcb_hide_line()

    def disconnect(self) -> None:
        """The MUD link closed."""
        self.core._eventcb_hide_disconnect()
        self.current = None

    def timed_out(self, cmdtype: str) -> None:
        """The command timed out: core closes its window and forgets the command."""
        self.core._close_hide(cmdtype)
        if self.current is not None and self.current.ctype == cmdtype:
            self.current = None
