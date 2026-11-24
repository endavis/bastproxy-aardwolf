"""Aardwolf aarch plugin: show which Aarchaeology items are still needed to complete the set."""

from typing import Any

from bastproxy.plugins._baseplugin import BasePlugin
from bastproxy.plugins.core.commands import AddArgument, AddCommand, AddParser, CommandResult

from ..libs import AARCH_TAG, API_EQ_FIND_BY_NAME, count_items, need_lines


class AarchPlugin(BasePlugin):
    """Count the Aarchaeology items in eq's cache and list the pieces still needed."""

    def _args(self) -> dict[str, Any]:
        """Return the arguments of the running command."""
        args = self.api("plugins.core.commands:command.current.args.get")()
        return dict(args) if args else {}

    @AddCommand()
    @AddParser(description="show the aarch pieces that are still needed")
    @AddArgument("filter", help="a word in the name of a piece to look for", nargs="*", default=[])
    def _command_need(self) -> CommandResult:
        """List the pieces of the set that are not held, optionally by a word in the name."""
        if not self.api("libs.api:api.exists")(API_EQ_FIND_BY_NAME):
            return CommandResult(True, ["The eq plugin is not loaded, so no items are known"])
        found = self.api(API_EQ_FIND_BY_NAME)(AARCH_TAG)
        names = [entry.get("name") for entry in found if isinstance(entry, dict)]
        text = " ".join(str(word) for word in self._args().get("filter") or [])
        return CommandResult(True, need_lines(count_items(names), text))
