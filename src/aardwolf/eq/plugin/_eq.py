"""Aardwolf eq plugin: track the items the character wears, carries, keeps and stores."""

import copy
import functools
import logging
from collections.abc import Callable, Mapping
from typing import Any

from bastproxy.libs.api import AddAPI
from bastproxy.libs.logger import get_logger, log_to
from bastproxy.libs.records import NetworkData, SendDataDirectlyToMud
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.commands import AddArgument, AddCommand, AddParser, CommandResult
from bastproxy.plugins.core.events import RegisterToEvent

from aardwolf._libs.eventu import own_event, own_events
from aardwolf._libs.itemu import WEARLOCS

from ..libs import (
    API_A102_TOGGLE,
    API_EQDB_SAVE,
    EVENT_DISCONNECT,
    EVENTS,
    FIXED_TYPES,
    GROUP_DATA,
    HIDE_MAX_LINES,
    INVENTORY,
    INVMON_OPTION,
    KEYRING,
    PLACE_KEYS,
    TRIGGERS,
    VAULT,
    VAULT_NOT_READ,
    WORN,
    DisplayOptions,
    EqState,
    InvmonOutcome,
    TriggerSpec,
    TypeSpec,
    container_lines,
    container_type,
    get_command,
    inventory_extra_lines,
    parse_item_line,
    put_command,
    quote_arg,
    tag_container,
    to_serial,
    type_for,
    vault_count_lines,
    worn_lines,
)

_CALLBACKS = {
    "eq_invmon": "_trigger_invmon",
    "eq_invitem": "_trigger_invitem",
    "eq_data_start": "_trigger_data_start",
    "eq_data_end": "_trigger_data_end",
    "eq_vaultcounts": "_trigger_vaultcounts",
    "eq_no_vault": "_trigger_no_vault",
    "eq_dead": "_trigger_dead",
    "eq_data_line": "_trigger_data_line",
}
_END_TAGS = {"invdata": "invdata", "eqdata": "eqdata", "keyring": "keyring", "vault": "vault"}
NOT_CACHED = "That item is not in the cache"


class EqPlugin(BasePlugin):
    """Follow invmon and the data commands, and keep the items and where they are."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Create the empty state and the state of the data reader."""
        self.state = EqState()
        # the container being read, the tag that opened it, and the item lines seen so far
        self._reading: str | None = None
        self._reading_tag = ""
        self._buffer: list[dict[str, Any]] = []
        self._groups_ready = False
        # the bags that have a command type
        self._bag_types: set[str] = set()
        # True while this plugin asks option 102 for the invmon tags
        self._invmon_on = False

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the events, the command types and the triggers."""
        add_event = self.api("plugins.core.events:event.add")
        for event_name, info in own_events(self.plugin_id, EVENTS).items():
            add_event(
                event_name,
                self.plugin_id,
                description=info["description"],
                arg_descriptions=info["arg_descriptions"],
            )
        for spec in FIXED_TYPES:
            self._add_type(spec)
        for trigger in TRIGGERS:
            self._add_trigger(trigger)
        # nothing is tracked without the invmon tags, so ask for them
        self.api(API_A102_TOGGLE)(INVMON_OPTION, True)
        self._invmon_on = True

    @RegisterPluginHook("uninitialize", priority=10)
    def _phook_uninitialize(self) -> None:
        """Take back the invmon request, on reload and on unload, so the counts stay balanced."""
        if not self._invmon_on:
            return
        self._invmon_on = False
        self.api(API_A102_TOGGLE)(INVMON_OPTION, False)

    @RegisterPluginHook("character_active")
    def _phook_character_active(self) -> None:
        """The character is active: read what it wears and carries."""
        self._refresh_all()

    # setup helpers

    def _add_type(self, spec: TypeSpec) -> None:
        """Add a command type that hides its output when it is queued."""
        kwargs: dict[str, Any] = {
            # beforef runs only for a queued command, so a typed data command never starts one
            "beforef": functools.partial(self._command_started, spec.cmdtype),
            "hide_output": True,
            "hide_start": spec.hide_start,
            "hide_max": HIDE_MAX_LINES + 2,
        }
        self.api("plugins.core.mudcmds:type.add")(spec.cmdtype, spec.cmd, spec.regex, **kwargs)

    def _command_started(self, cmdtype: str) -> None:
        """The queue is sending one of our data commands: start its timing."""
        self.api("plugins.core.mudcmds:command.start")(cmdtype)

    def _add_trigger(self, spec: TriggerSpec) -> None:
        """Add a trigger and register its callback."""
        kwargs: dict[str, Any] = {"enabled": spec.enabled}
        if spec.group:
            kwargs["group"] = self._group(spec.group)
        if spec.omit:
            kwargs["omit"] = True
        if spec.argtypes:
            kwargs["argtypes"] = spec.argtypes
        result = self.api("plugins.core.triggers:trigger.add")(spec.name, spec.regex, **kwargs)
        if not result.success:
            get_logger(self.plugin_id).error("could not add the %s trigger", spec.name)
            return
        callback: Callable[[], None] = getattr(self, _CALLBACKS[spec.name])
        self.api("plugins.core.triggers:trigger.register")(result.trigger.trigger_id, callback)
        if spec.group:
            self._groups_ready = True

    def _group(self, suffix: str) -> str:
        """Return the trigger group name; group names are global, so it carries the plugin id."""
        return f"{self.plugin_id}.{suffix}"

    def _toggle_data(self, flag: bool) -> None:
        """Turn the data line trigger on or off, when it exists."""
        if self._groups_ready:
            self.api("plugins.core.triggers:group.toggle.enable")(self._group(GROUP_DATA), flag)

    def _record(self) -> dict[str, Any]:
        """Return the record of the current event."""
        return dict(self.api("plugins.core.events:event.current.record.get")() or {})

    def _matches(self) -> dict[str, Any]:
        """Return the groups the current trigger matched."""
        return dict(self._record().get("matches") or {})

    def _raise(self, suffix: str, payload: dict[str, Any]) -> None:
        """Raise one of this plugin's events with a payload that is a copy."""
        self.api("plugins.core.events:event.raise")(
            own_event(self.plugin_id, suffix), event_args=copy.deepcopy(payload)
        )

    def _args(self) -> dict[str, Any]:
        """Return the arguments of the running command."""
        args = self.api("plugins.core.commands:command.current.args.get")()
        return dict(args) if args else {}

    def _gmcp_value(self, path: str) -> object:
        """Return the cached GMCP value at a dotted path, or None."""
        return self.api("libs.net.protocols:gmcp.value.get")(path)

    def _in_bank(self) -> bool:
        """Return True when the room is a bank; a missing value is not a bank."""
        return "bank" in str(self._gmcp_value("room.info.details") or "")

    def _strip(self, text: str) -> str:
        """Remove the colour codes of the text."""
        return str(self.api("plugins.core.colors:colorcode.strip")(text))

    def _send(self, command: str) -> None:
        """Send a command to the MUD."""
        SendDataDirectlyToMud(NetworkData([command], owner_id=f"{self.plugin_id}:send"))()

    def _parse(self, noansi: str) -> dict[str, Any] | None:
        """Parse the current line, or the text given, as an item line."""
        line = self._record().get("line")
        return parse_item_line(noansi, getattr(line, "colorcoded", None), self._strip)

    # container types and reading

    def _add_bag_type(self, cid: str) -> None:
        """Add the command type of a bag, when it has none."""
        if cid not in self._bag_types:
            self._bag_types.add(cid)
            self._add_type(container_type(cid))

    def _remove_bag_type(self, cid: str) -> None:
        """Remove the command type of a bag."""
        if cid in self._bag_types:
            self._bag_types.discard(cid)
            self.api("plugins.core.mudcmds:type.remove")(type_for(cid).cmdtype)

    def _sync_types(self) -> None:
        """Give every bag a command type, and take back the type of a bag that is gone."""
        bags = set(self.state.bag_cids())
        for cid in sorted(self._bag_types - bags):
            self._remove_bag_type(cid)
        for cid in sorted(bags - self._bag_types):
            self._add_bag_type(cid)

    def _queue(self, cid: str) -> bool:
        """Queue the command that reads a container; return True when it was queued."""
        if cid == VAULT and not self._in_bank():
            return False
        if cid not in (WORN, INVENTORY, KEYRING, VAULT) and cid not in self._bag_types:
            return False
        self.api("plugins.core.mudcmds:command.queue")(type_for(cid).cmdtype)
        return True

    def _refresh_all(self) -> None:
        """Queue every container: worn, inventory, keyring, the vault in a bank, the bags."""
        for cid in (WORN, INVENTORY, KEYRING, VAULT, *self.state.bag_cids()):
            self._queue(cid)

    def _known_type(self, cid: str) -> bool:
        """Return True when a command type exists for the container."""
        return cid in (WORN, INVENTORY, KEYRING, VAULT) or cid in self._bag_types

    # triggers

    def _trigger_invmon(self) -> None:
        """An invmon line: move the item, raise what happened and read what is out of date."""
        matches = self._matches()
        try:
            action = int(matches["action"])
            serial = int(matches["serial"])
            container = int(matches["container"])
            location = int(matches["location"])
        except (KeyError, TypeError, ValueError):
            log_to([self.plugin_id], logging.ERROR, "the invmon line has bad data: %s", matches)
            return
        outcome = self.state.apply_invmon(action, serial, container, location)
        self._finish_invmon(action, outcome)

    def _finish_invmon(self, action: int, outcome: InvmonOutcome) -> None:
        """Add and remove the bag types, raise the events and queue the refreshes."""
        if not outcome.events and not outcome.refresh and action not in (3, 7):
            log_to([self.plugin_id], logging.DEBUG, "invmon action %d changed nothing", action)
        for cid in outcome.dropped_containers:
            self._remove_bag_type(cid)
        for cid in outcome.new_containers:
            self._add_bag_type(cid)
        for name, payload in outcome.events:
            self._raise(name, payload)
        for cid in outcome.refresh:
            self._queue(cid)

    def _trigger_invitem(self) -> None:
        """An invitem line: add the item to the cache, or update it."""
        data = str(self._matches().get("data", ""))
        parsed = self._parse(data)
        if parsed is None:
            log_to([self.plugin_id], logging.DEBUG, "invitem is not an item line: %s", data)
            return
        self.state.upsert(parsed)

    def _trigger_data_start(self) -> None:
        """The start tag of a block: begin reading the container it names."""
        matches = self._matches()
        tag = str(matches.get("tag", ""))
        cid = tag_container(tag, matches.get("cid"))
        if cid is None:
            log_to([self.plugin_id], logging.DEBUG, "unknown data block %s", matches)
            return
        if self._reading is not None:
            log_to([self.plugin_id], logging.DEBUG, "block %s cut off by a new one", self._reading)
        self._reading = cid
        self._reading_tag = _END_TAGS[tag]
        self._buffer = []
        self._toggle_data(True)

    def _trigger_data_line(self) -> None:
        """An item line inside a block: keep it until the block ends."""
        if self._reading is None:
            return
        data = str(self._matches().get("data", ""))
        parsed = self._parse(data)
        if parsed is None:
            log_to([self.plugin_id], logging.DEBUG, "not an item line: %s", data)
            return
        self._buffer.append(parsed)

    def _trigger_data_end(self) -> None:
        """The end tag of a block: commit the lines, stop reading and finish the command."""
        cid = self._reading
        if cid is None:
            return
        if self._matches().get("tag") != self._reading_tag:
            log_to([self.plugin_id], logging.DEBUG, "end tag does not match block %s", cid)
            return
        new_bags = self.state.commit(cid, self._buffer)
        self._stop_reading()
        self._sync_types()
        for bag in new_bags:
            self._queue(bag)
        if self._known_type(cid):
            self.api("plugins.core.mudcmds:command.finish")(type_for(cid).cmdtype)

    def _stop_reading(self) -> None:
        """Forget the block being read."""
        self._reading = None
        self._reading_tag = ""
        self._buffer = []
        self._toggle_data(False)

    def _trigger_no_vault(self) -> None:
        """The character has no vault: record an empty one and finish the vault read."""
        self.state.commit(VAULT, [])
        self.state.vault_counts = None
        self.api("plugins.core.mudcmds:command.finish")(type_for(VAULT).cmdtype)

    def _trigger_vaultcounts(self) -> None:
        """The counts that follow a vault block: the items, the total and the maximum."""
        matches = self._matches()
        try:
            self.state.vault_counts = {
                "items": int(matches["items"]),
                "total": int(matches["total"]),
                "max": int(matches["max"]),
            }
        except (KeyError, TypeError, ValueError):
            log_to([self.plugin_id], logging.DEBUG, "bad vaultcounts: %s", matches)

    def _trigger_dead(self) -> None:
        """The character died: forget what it carries, keep the vault, and read it all again."""
        dropped = self.state.reset_carried()
        log_to([self.plugin_id], logging.DEBUG, "the character died, bags dropped: %s", dropped)
        self._stop_reading()
        self._sync_types()
        self._refresh_all()

    # events

    @RegisterToEvent(event_name=EVENT_DISCONNECT)
    def _eventcb_disconnect(self) -> None:
        """Forget the items, abandon a block in progress and remove the bag types."""
        self.state.reset()
        self._stop_reading()
        for cid in sorted(self._bag_types):
            self._remove_bag_type(cid)

    # APIs

    @AddAPI("item.get", description="return a copy of an item by serial, or None")
    def _api_item_get(self, serial: int | str) -> dict[str, Any] | None:
        """Return a copy of an item, or None."""
        number = to_serial(serial)
        return self.state.item_copy(number) if number is not None else None

    @AddAPI("item.find.by.name", description="return copies of the items with text in the name")
    def _api_item_find_by_name(self, name: str) -> list[dict[str, Any]]:
        """Return copies of the items with ``name`` in their name; the match is case sensitive."""
        return self.state.find_by_name(name)

    @AddAPI("container.get", description="return a copy of a container, or None")
    def _api_container_get(self, cid: int | str) -> dict[str, Any] | None:
        """Return ``{cid, items}`` of a container; Worn adds ``slots`` and Vault ``counts``."""
        return self.state.container_copy(cid)

    @AddAPI("container.refresh", description="queue the read of one container")
    def _api_container_refresh(self, cid: int | str) -> bool:
        """Queue the read of Worn, Inventory, Keyring, Vault or a bag; False when it cannot be."""
        resolved = self._resolve_container(str(cid))
        if resolved is None:
            return False
        return self._queue(resolved)

    @AddAPI("eq.worn.get", description="return a copy of the item worn at a slot or location")
    def _api_eq_worn_get(self, location: int | str) -> dict[str, Any] | None:
        """Return a copy of the item worn at a slot number or location name, or None."""
        return self.state.worn_at(location)

    def _fetch_command(self, serial: int) -> str | None:
        """Return the command that takes an item out of the container it is in."""
        item = self.state.items[serial]
        cid = item["container"]
        return get_command(cid, serial) if cid else None

    @AddAPI(
        "item.fetch",
        description="take an item out of its container, noting where to put it back",
    )
    def _api_item_fetch(self, serial: int | str) -> bool:
        """Send the command that gets an item into the inventory; return True when it is known."""
        number = to_serial(serial)
        if number is None or number not in self.state.items:
            return False
        command = self._fetch_command(number)
        if command:
            self.state.set_origin(number)
            self._send(command)
        return True

    @AddAPI("item.put", description="put an item into a container, or back where it came from")
    def _api_item_put(
        self,
        serial: int | str,
        container: int | str | None = None,
        location: int | str | None = None,
    ) -> str | None:
        """Put an item into a container; return the container id, or None when nothing was done.

        Without ``container`` the item goes back to where it was fetched from. An item in
        another container is fetched first. ``location`` is the wear location for Worn, by
        name or number; without it the last location the item was worn at is used.
        """
        number = to_serial(serial)
        if number is None or number not in self.state.items:
            return None
        item = self.state.items[number]
        target = str(container) if container is not None else item["origcontainer"]
        if not target or not self.state.has_container(target):
            return None
        if item["container"] == target:
            return target
        if item["container"] not in (None, INVENTORY):
            command = self._fetch_command(number)
            if command:
                self._send(command)
        put = put_command(target, number, self._wear_name(number, location))
        if put:
            self._send(put)
        return target

    def _wear_name(self, serial: int, location: int | str | None) -> str | None:
        """Return the wear location name to wear an item at, or None."""
        if isinstance(location, str) and location:
            return location
        if isinstance(location, int) and not isinstance(location, bool):
            return WEARLOCS[location] if 0 <= location < len(WEARLOCS) else None
        slot = self.state.lastworn.get(serial)
        return WEARLOCS[slot] if slot is not None and 0 <= slot < len(WEARLOCS) else None

    @AddAPI("item.equip", description="wear an item, at a location or at the last one it was at")
    def _api_item_equip(self, serial: int | str, location: int | str | None = None) -> bool:
        """Wear an item; ``location`` ``lastworn`` or None uses where it was last worn."""
        if location == "lastworn":
            location = None
        return self._api_item_put(serial, WORN, location) is not None

    @AddAPI("item.unequip", description="take off a worn item")
    def _api_item_unequip(self, serial: int | str) -> bool:
        """Take an item off; return False when it is not worn."""
        number = to_serial(serial)
        item = self.state.items.get(number) if number is not None else None
        if item is None or item["container"] != WORN:
            return False
        return bool(self._api_item_fetch(serial))

    @AddAPI("item.identify.add", description="add the details of an identify to an item")
    def _api_item_identify_add(self, serial: int | str, attributes: Mapping[str, Any]) -> bool:
        """Merge identify details into an item and save it when eqdb is loaded."""
        number = to_serial(serial)
        item = self.state.items.get(number) if number is not None else None
        if item is None:
            return False
        skipped = PLACE_KEYS | {"serial"}
        item.update({key: value for key, value in attributes.items() if key not in skipped})
        item["hasbeenided"] = True
        if self.api("libs.api:api.exists")(API_EQDB_SAVE):
            # eqdb reads "container" as the container detail, not as the place
            saved = {key: value for key, value in item.items() if key not in PLACE_KEYS}
            saved |= {key: value for key, value in attributes.items() if key != "serial"}
            self.api(API_EQDB_SAVE)(copy.deepcopy(saved))
        return True

    # commands

    @AddCommand()
    @AddParser(description="read the worn items, the inventory, the keyring and the vault again")
    def _command_refresh(self) -> CommandResult:
        """Read everything again."""
        self._refresh_all()
        return CommandResult(True, ["Refreshing EQ"])

    @AddCommand()
    @AddParser(description="show what is in the cache for an item")
    @AddArgument("item", help="the serial of the item", nargs="?", default="")
    def _command_icache(self) -> CommandResult:
        """Show one line per field of a cached item, or the size of the cache."""
        text = str(self._args().get("item", ""))
        if not text:
            count = len(self.state.items)
            return CommandResult(True, [f"{count} items in the cache; give a serial to show one"])
        serial = to_serial(text)
        if serial is None:
            return CommandResult(True, [f"{text} is not a serial number"])
        item = self.state.items.get(serial)
        if item is None:
            return CommandResult(True, [NOT_CACHED])
        lines = [f"Item {serial}"]
        lines.extend(f"{key}: {item[key]}" for key in sorted(item) if key != "serial")
        return CommandResult(True, lines)

    @AddCommand(format=False, preamble=False)
    @AddParser(description="get an item, from wherever it is")
    @AddArgument("item", help="the serial of the item, or what to get", nargs="?", default="")
    @AddArgument("otherargs", help="the rest of the get command", nargs="*", default=[])
    def _command_get(self) -> CommandResult:
        """Get an item by serial, or send the words to the MUD as a get command."""
        args = self._args()
        serial = to_serial(args.get("item"))
        if serial is not None and self._api_item_fetch(serial):
            return CommandResult(True, [])
        parts = [quote_arg(str(word)) for word in [args.get("item"), *args["otherargs"]] if word]
        command = " ".join(["get", *parts])
        self._send(command)
        return CommandResult(True, [f"serial is not known, sending '{command}'"])

    @AddCommand(format=False, preamble=False)
    @AddParser(description="put an item in something")
    @AddArgument("item", help="the serial of the item, or what to put", nargs="?", default="")
    @AddArgument("otherargs", help="the rest of the put command", nargs="*", default=[])
    def _command_put(self) -> CommandResult:
        """Put an item in a bag, or send the words to the MUD as a put command."""
        args = self._args()
        others = [str(word) for word in args["otherargs"]]
        serial = to_serial(args.get("item"))
        if serial is not None and serial in self.state.items:
            if not others:
                if self._api_item_put(serial) is None:
                    return CommandResult(True, [f"Item {serial} has no container to go back to"])
                return CommandResult(True, [])
            bag = to_serial(others[0]) if len(others) == 1 else None
            if bag is not None and self.state.has_container(str(bag)):
                self._api_item_put(serial, str(bag))
                return CommandResult(True, [])
        parts = [quote_arg(str(word)) for word in [args.get("item"), *others] if word]
        command = " ".join(["put", *parts])
        self._send(command)
        return CommandResult(True, [f"sending '{command}'"])

    def _resolve_container(self, text: str) -> str | None:
        """Return the id of the container a name or serial points at, or None."""
        for name in (WORN, INVENTORY, KEYRING, VAULT):
            if text.lower() == name.lower():
                return name
        serial = to_serial(text)
        if serial is not None and self.state.has_container(str(serial)):
            return str(serial)
        return None

    @AddCommand(format=False, preamble=False)
    @AddParser(description="show the equipment worn")
    @AddArgument("-n", "--noflags", help="do not show the item flags", action="store_true")
    @AddArgument("-c", "--score", help="show the item score", action="store_true")
    @AddArgument("-s", "--serial", help="show the item serial", action="store_true")
    def _command_eq(self) -> CommandResult:
        """Show what the character wears."""
        args = self._args()
        opts = DisplayOptions(
            noflags=bool(args.get("noflags")),
            score=bool(args.get("score")),
            serial=bool(args.get("serial")),
        )
        return CommandResult(True, worn_lines(list(self.state.worn), self.state.items, opts))

    @AddCommand(format=False, preamble=False)
    @AddParser(description="show the inventory, or another container")
    @AddArgument(
        "container",
        help="the container: Inventory, Worn, Keyring, Vault or the serial of a bag",
        nargs="?",
        default=INVENTORY,
    )
    @AddArgument("-n", "--noflags", help="do not show the item flags", action="store_true")
    @AddArgument("-c", "--score", help="show the item score", action="store_true")
    @AddArgument("-s", "--serial", help="show the item serial", action="store_true")
    @AddArgument("-g", "--nogroup", help="do not group like items", action="store_true")
    def _command_inv(self) -> CommandResult:
        """Show the items in a container."""
        args = self._args()
        text = str(args.get("container", INVENTORY))
        opts = DisplayOptions(
            noflags=bool(args.get("noflags")),
            score=bool(args.get("score")),
            serial=bool(args.get("serial")),
            nogroup=bool(args.get("nogroup")),
        )
        cid = self._resolve_container(text)
        if cid is None:
            return CommandResult(True, [f"container {text} does not exist"])
        state = self.state
        if cid == WORN:
            return CommandResult(True, worn_lines(list(state.worn), state.items, opts))
        if cid == VAULT and not state.vault_read:
            return CommandResult(True, list(VAULT_NOT_READ))
        lines = container_lines(cid, state.serials(cid), state.items, opts)
        if cid == VAULT and state.vault_counts is not None:
            lines.extend(vault_count_lines(state.vault_counts))
        elif cid == INVENTORY:
            counts = state.vault_counts if state.vault_read else None
            lines.extend(inventory_extra_lines(len(state.serials(KEYRING)), counts))
        return CommandResult(True, lines)
