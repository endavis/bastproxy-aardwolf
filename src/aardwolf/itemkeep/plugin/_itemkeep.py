"""Aardwolf itemkeep plugin: keep items of chosen types when they reach the inventory."""

from typing import Any

from bastproxy.libs.logger import get_logger
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.events import RegisterToEvent

from ..libs import (
    EVENT_DISCONNECT,
    EVENT_EQ_INVENTORY_ADDED,
    EVENT_EQ_REMOVED,
    EVENT_EQ_TAKEN,
    GROUP_REPLY,
    HIDE_MAX,
    KEEP_CMD,
    KEEP_HIDE_START,
    KEEP_REGEX,
    SETTINGS,
    TIMEOUT_EVENT,
    TRIGGERS,
    TYPE_KEEP,
    TriggerSpec,
    should_keep,
)


class ItemKeepPlugin(BasePlugin):
    """Queue a keep for an item of an enabled type that reaches the inventory."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Create the empty state."""
        # the serials a keep was sent for; eq never updates shortflags, so a cached item can
        # come back without its K and a second keep might unkeep it. Cleared on disconnect.
        self._kept: set[int] = set()
        self._groups_ready = False

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the settings, the command type, the reply triggers and the timeout handler."""
        add = self.api("plugins.core.settings:setting.add")
        for name, help_text in SETTINGS.items():
            add(self.plugin_id, name, False, bool, help_text)
        self._add_type()
        for trigger in TRIGGERS:
            self._add_trigger(trigger)
        self.api("plugins.core.events:event.register")(
            TIMEOUT_EVENT.format(TYPE_KEEP), self._eventcb_keep_timeout
        )

    # setup helpers

    def _add_type(self) -> None:
        """Add the keep command type, which hides its output when it is queued."""
        self.api("plugins.core.mudcmds:type.add")(
            TYPE_KEEP,
            KEEP_CMD,
            KEEP_REGEX,
            # beforef runs only for a queued command, so a typed keep is shown and not parsed
            beforef=self._command_started,
            hide_output=True,
            hide_start=KEEP_HIDE_START,
            hide_max=HIDE_MAX,
        )

    def _add_trigger(self, spec: TriggerSpec) -> None:
        """Add a trigger, off, in its group, and register its callback."""
        result = self.api("plugins.core.triggers:trigger.add")(
            spec.name, spec.regex, enabled=False, group=self._group(spec.group)
        )
        if not result.success:
            get_logger(self.plugin_id).error("could not add the %s trigger", spec.name)
            return
        self.api("plugins.core.triggers:trigger.register")(
            result.trigger.trigger_id, self._trigger_reply
        )
        self._groups_ready = True

    def _group(self, suffix: str) -> str:
        """Return the trigger group name; group names are global, so it carries the plugin id."""
        return f"{self.plugin_id}.{suffix}"

    def _toggle(self, flag: bool) -> None:
        """Turn the reply trigger group on or off, when the triggers exist."""
        if self._groups_ready:
            self.api("plugins.core.triggers:group.toggle.enable")(self._group(GROUP_REPLY), flag)

    def _record(self) -> dict[str, Any]:
        """Return the record of the current event."""
        return dict(self.api("plugins.core.events:event.current.record.get")() or {})

    # the keep command

    def _command_started(self) -> None:
        """The queue is sending a keep: start its timing and read its reply."""
        self.api("plugins.core.mudcmds:command.start")(TYPE_KEEP)
        self._toggle(True)

    def _trigger_reply(self) -> None:
        """A reply line: the keep is answered, so finish the command."""
        self._toggle(False)
        self.api("plugins.core.mudcmds:command.finish")(TYPE_KEEP)

    def _eventcb_keep_timeout(self) -> None:
        """No reply matched: the queue is freed by the timeout, so stop reading."""
        get_logger(self.plugin_id).debug("no reply to a keep matched, timed out")
        self._toggle(False)

    # items reaching the inventory

    def _check(self, item: object) -> None:
        """Queue a keep for the item when its type is on and it is not kept."""
        if not isinstance(item, dict):
            return
        get = self.api("plugins.core.settings:setting.get")
        serial = should_keep(item, lambda name: bool(get(self.plugin_id, name)))
        if serial is None:
            get_logger(self.plugin_id).debug("no keep for item %r", item.get("serial"))
            return
        if serial in self._kept:
            return
        self._kept.add(serial)
        self.api("plugins.core.mudcmds:command.queue")(TYPE_KEEP, str(serial))

    @RegisterToEvent(event_name=EVENT_EQ_INVENTORY_ADDED)
    def _eventcb_inventory_added(self) -> None:
        """An item was added to the inventory."""
        self._check(self._record().get("item"))

    @RegisterToEvent(event_name=EVENT_EQ_TAKEN)
    def _eventcb_taken(self) -> None:
        """An item was taken from a bag, the vault or the keyring."""
        self._check(self._record().get("item"))

    @RegisterToEvent(event_name=EVENT_EQ_REMOVED)
    def _eventcb_removed(self) -> None:
        """A worn item was taken off."""
        self._check(self._record().get("item"))

    @RegisterToEvent(event_name=EVENT_DISCONNECT)
    def _eventcb_disconnect(self) -> None:
        """Forget what was kept and stop reading a reply."""
        self._kept.clear()
        self._toggle(False)
