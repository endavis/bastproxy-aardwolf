"""Aardwolf aflags plugin: keep the character's affect flags from the ``aflags`` command."""

import copy
import logging
from typing import Any

from bastproxy.libs.api import AddAPI
from bastproxy.libs.logger import log_to
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.commands import AddArgument, AddCommand, AddParser, CommandResult
from bastproxy.plugins.core.events import RegisterToEvent

from aardwolf._libs.eventu import own_event, own_events

from ..libs import (
    ALL_LINES_ID,
    CMD,
    CMD_REGEX,
    EVENT_AFFECTED_UPDATE,
    EVENT_AFFOFF,
    EVENT_AFFON,
    EVENT_DISCONNECT,
    EVENT_UPTODATE,
    EVENTS,
    HEADER_REGEX,
    HIDE_MAX_LINES,
    SUFFIX_DIFF,
    TIMEOUT_EVENT,
    TYPE_AFLAGS,
    AflagsReader,
    FlagLearner,
    flag_diff,
)


class AflagsPlugin(BasePlugin):
    """Keep the set of affect flags, refresh it when an affect changes, and raise the change."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Create the empty state."""
        self._flags: set[str] = set()
        self._reader = AflagsReader()
        self._learner = FlagLearner()
        # True from the start of a queued aflags until the read ends, times out or the link drops
        self._reading = False
        self._listening = False
        # a refresh asked for during a read; mudcmds would drop it, so it is queued after the read
        self._again = False

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the event, the command type and the timeout handler."""
        for event_name, info in own_events(self.plugin_id, EVENTS).items():
            self.api("plugins.core.events:event.add")(
                event_name,
                self.plugin_id,
                description=info["description"],
                arg_descriptions=info["arg_descriptions"],
            )
        self.api("plugins.core.mudcmds:type.add")(
            TYPE_AFLAGS,
            CMD,
            CMD_REGEX,
            # beforef runs only for a queued command, so a typed aflags is shown and not parsed
            beforef=self._command_started,
            hide_output=True,
            hide_start=HEADER_REGEX,
            hide_max=HIDE_MAX_LINES + 2,
        )
        self.api("plugins.core.events:event.register")(
            TIMEOUT_EVENT.format(TYPE_AFLAGS), self._eventcb_timeout
        )

    @RegisterPluginHook("character_active")
    def _phook_character_active(self) -> None:
        """The character is active: read the flags."""
        self._refresh()

    # the aflags command

    def _refresh(self) -> None:
        """Queue a read of the flags, or ask for one more after the read that is running."""
        if self._reading:
            self._again = True
            return
        self.api("plugins.core.mudcmds:command.queue")(TYPE_AFLAGS)

    def _command_started(self) -> None:
        """The queue is sending aflags: start its timing and look at every line."""
        self._reader.start()
        self._learner.start()
        self._reading = True
        self._again = False
        self._listen(True)
        self.api("plugins.core.mudcmds:command.start")(TYPE_AFLAGS)

    def _listen(self, flag: bool) -> None:
        """Start or stop looking at every line."""
        if flag and not self._listening:
            self._listening = bool(
                self.api("plugins.core.triggers:trigger.register")(ALL_LINES_ID, self._line)
            )
        elif not flag and self._listening:
            self.api("plugins.core.triggers:trigger.unregister")(ALL_LINES_ID, self._line)
            self._listening = False

    def _line(self) -> None:
        """Feed a line to the reader; the end of the output ends the read."""
        record = self.api("plugins.core.events:event.current.record.get")() or {}
        line = record.get("line")
        text = str(getattr(line, "noansi", line)) if line is not None else ""
        if self._reader.feed(text, bool(getattr(line, "is_prompt", False))):
            self._end_read()

    def _end_read(self) -> None:
        """The output is complete: replace the flags, raise what changed and finish the command."""
        self._listen(False)
        self._reading = False
        after = set(self._reader.flags)
        added, removed = flag_diff(self._flags, after)
        sn = self._learner.learn(added, removed)
        self._flags = after
        if sn is not None:
            log_to([self.plugin_id], logging.DEBUG, "sn %d sets the flags %s", sn, added or removed)
        if added or removed:
            self._raise(SUFFIX_DIFF, {"added": added, "removed": removed, "sn": sn})
        self.api("plugins.core.mudcmds:command.finish")(TYPE_AFLAGS)
        if self._again:
            self._again = False
            self._refresh()

    def _abort_read(self) -> None:
        """Drop a read that did not finish; the flags stay as they were."""
        self._listen(False)
        self._reading = False
        self._again = False
        self._reader.start()
        self._learner.learn([], [])

    def _raise(self, suffix: str, payload: dict[str, Any]) -> None:
        """Raise one of this plugin's events with a payload that is a copy."""
        self.api("plugins.core.events:event.raise")(
            own_event(self.plugin_id, suffix), event_args=copy.deepcopy(payload)
        )

    def _record(self) -> dict[str, Any]:
        """Return the record of the current event."""
        return dict(self.api("plugins.core.events:event.current.record.get")() or {})

    # events

    def _note_change(self) -> None:
        """An affect changed: note its sn and read the flags."""
        sn = self._record().get("sn")
        if isinstance(sn, int) and not isinstance(sn, bool):
            self._learner.change(sn)
        self._refresh()

    @RegisterToEvent(event_name=EVENT_AFFON)
    def _eventcb_affon(self) -> None:
        """An affect started."""
        self._note_change()

    @RegisterToEvent(event_name=EVENT_AFFOFF)
    def _eventcb_affoff(self) -> None:
        """An affect ended."""
        self._note_change()

    @RegisterToEvent(event_name=EVENT_AFFECTED_UPDATE)
    def _eventcb_affected_update(self) -> None:
        """The skills plugin read the affects."""
        self._refresh()

    @RegisterToEvent(event_name=EVENT_UPTODATE)
    def _eventcb_uptodate(self) -> None:
        """The skills plugin finished reading the skills."""
        self._refresh()

    @RegisterToEvent(event_name=EVENT_DISCONNECT)
    def _eventcb_disconnect(self) -> None:
        """Forget the flags, and drop a read in progress."""
        self._abort_read()
        self._learner.reset()
        self._flags = set()

    def _eventcb_timeout(self) -> None:
        """No end to the output: the queue is freed by the timeout, so stop reading."""
        log_to([self.plugin_id], logging.DEBUG, "aflags timed out, the flags are kept")
        self._abort_read()

    # api

    @AddAPI("flag.check", description="return True when the character has the affect flag")
    def _api_flag_check(self, flag: str) -> bool:
        """Return True when the flag is set; the case of the flag does not matter."""
        flag = str(flag).strip().lower()
        return bool(flag) and flag in self._flags

    # commands

    @AddCommand()
    @AddParser(description="refresh the affect flags")
    def _command_refresh(self) -> CommandResult:
        """Read the flags again."""
        self._refresh()
        return CommandResult(True, ["Refreshing Affect Flags"])

    @AddCommand()
    @AddParser(description="check to see if affected by a flag")
    @AddArgument("flag", help="the flag to check", nargs="?", default="")
    def _command_check(self) -> CommandResult:
        """Say whether a flag is active."""
        args = self.api("plugins.core.commands:command.current.args.get")() or {}
        flag = str(args.get("flag", ""))
        if not flag:
            return CommandResult(True, ["Please specify a flag"])
        state = "active" if self._api_flag_check(flag) else "inactive"
        return CommandResult(True, [f"Affect {flag} is {state}"])

    @AddCommand()
    @AddParser(description="list the affect flags")
    def _command_list(self) -> CommandResult:
        """List the flags that are active."""
        if not self._flags:
            return CommandResult(True, ["There are no affects active"])
        lines = [f"The following {len(self._flags)} affects are active"]
        lines.extend(f"  {flag}" for flag in sorted(self._flags))
        return CommandResult(True, lines)
