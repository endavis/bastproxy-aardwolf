"""Aardwolf config plugin: settings shared by the Aardwolf plugins."""

from typing import Any

from bastproxy.libs.api import AddAPI
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.commands import AddArgument, AddCommand, AddParser, CommandResult
from bastproxy.plugins.core.events import RegisterToEvent

from aardwolf._libs.eventu import own_event, own_events

from ..libs import (
    DEFAULT_QUESTMASTERS,
    EVENTS,
    QUESTMASTERS,
    SUFFIX_QUESTMASTERS_CHANGED,
    add_name,
    normalize_name,
    remove_name,
)

_INIT = "__init__"


class ConfigPlugin(BasePlugin):
    """Keep the questmaster list and tell the other plugins when it changes."""

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the events and the setting."""
        add_event = self.api("plugins.core.events:event.add")
        for event_name, info in own_events(self.plugin_id, EVENTS).items():
            add_event(
                event_name,
                self.plugin_id,
                description=info["description"],
                arg_descriptions=info["arg_descriptions"],
            )
        self.api("plugins.core.settings:setting.add")(
            self.plugin_id,
            QUESTMASTERS,
            list(DEFAULT_QUESTMASTERS),
            list,
            "the names of the questmasters",
            readonly=True,
        )

    def _questmasters(self) -> list[str]:
        """Return a new list of the questmaster names."""
        names = self.api("plugins.core.settings:setting.get")(self.plugin_id, QUESTMASTERS)
        return list(names or [])

    @AddAPI("questmasters.get", description="return a copy of the questmaster names")
    def _api_questmasters_get(self) -> list[str]:
        """Return a copy of the questmaster names."""
        return self._questmasters()

    @RegisterToEvent(event_name="ev_{plugin_id}_var_questmasters_modified")
    def _eventcb_questmasters_modified(self) -> None:
        """Pass the core setting event on as the questmasters changed event."""
        record = self.api("plugins.core.events:event.current.record.get")()
        if record["oldvalue"] == _INIT:
            return
        self.api("plugins.core.events:event.raise")(
            own_event(self.plugin_id, SUFFIX_QUESTMASTERS_CHANGED),
            event_args={"questmasters": list(record["newvalue"])},
        )

    def _args(self) -> dict[str, Any]:
        """Return the arguments of the running command."""
        args = self.api("plugins.core.commands:command.current.args.get")()
        return dict(args) if args else {}

    @AddCommand()
    @AddParser(description="add, remove or list the questmasters")
    @AddArgument(
        "action",
        help="add or remove a name; leave out to list the names",
        default="",
        nargs="?",
    )
    @AddArgument("name", help="the questmaster name, spaces allowed", nargs="*", default=[])
    def _command_questmaster(self) -> CommandResult:
        """Add, remove or list the questmasters."""
        args = self._args()
        action = args.get("action", "")
        names = self._questmasters()
        if not action:
            if not names:
                return CommandResult(True, ["There are no questmasters"])
            return CommandResult(True, ["Questmasters:", *names])
        if action not in ("add", "remove"):
            return CommandResult(False, [f"unknown action {action}: use add or remove"])
        name = normalize_name(args.get("name") or [])
        if not name:
            return CommandResult(False, ["give a questmaster name"])
        if action == "add":
            added = add_name(names, name)
            if added is None:
                return CommandResult(True, [f"{name} is already a questmaster"])
            self._save(added)
            return CommandResult(True, [f"{name} was added to the questmasters"])
        removed = remove_name(names, name)
        if removed is None:
            return CommandResult(
                True,
                [
                    f"{name} is not a questmaster "
                    "(exact name, case matters; list them with no action)"
                ],
            )
        self._save(removed)
        return CommandResult(True, [f"{name} was removed from the questmasters"])

    def _save(self, names: list[str]) -> None:
        """Write the list through the settings plugin, which saves it and raises the event."""
        self.api("plugins.core.settings:setting.set")(self.plugin_id, QUESTMASTERS, names)
