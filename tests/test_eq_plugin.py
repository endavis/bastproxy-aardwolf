"""Tests for the Aardwolf eq plugin, with a stubbed API that drives its triggers."""

import copy
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from event_keys import assert_raised_described
from mudcmds_support import CoreHide

import aardwolf
from aardwolf.eq.libs import (
    EVENT_INVENTORY_ADDED,
    EVENT_INVENTORY_REMOVED,
    EVENT_PUT,
    EVENT_REMOVED,
    EVENT_TAKEN,
    EVENT_WORN,
    EVENTS,
    HIDE_MAX_LINES,
)

if TYPE_CHECKING:
    from bastproxy.libs.records import NetworkData

    from aardwolf.eq.plugin._eq import EqPlugin

PLUGIN_ID = "plugins.aardwolf.eq"
GROUP = f"{PLUGIN_ID}.data"
PROMPT = "[201/201hp 176/176mn 630/630mv 13qt 773tnl] >"
SWORD = "1001,KG,a test sword,25,5,0,24,-1"
CLOAK = "1002,,a test cloak,10,7,0,7,-1"
POTION = "2001,,a test potion,5,8,0,-1,-1"
BAG = "2002,K,a test bag,1,11,0,-1,-1"
GEM = "3001,,a test gem,1,6,0,-1,-1"
KEY = "4001,,a test key,1,13,0,-1,-1"
RING = "5001,,a test ring,1,6,0,-1,-1"
EQDATA = ["{eqdata}", SWORD, CLOAK, "{/eqdata}"]
INVDATA = ["{invdata}", POTION, BAG, "{/invdata}"]
BAGDATA = ["{invdata 2002}", GEM, "{/invdata}"]
KEYDATA = ["{keyring}", KEY, "{/keyring}"]
VAULTDATA = ["{vault}", RING, "{/vault}"]
COUNTS = "{vaultcounts}1,1,50{/vaultcounts}"
NO_VAULT = "You do not have a vault. See 'help vault' for how to acquire one."


class FakeApi:
    """A stand-in for the bastproxy API that records the calls and drives the triggers."""

    def __init__(self) -> None:
        self.gmcp: dict[str, Any] = {}
        self.events_added: list[str] = []
        self.types: dict[str, dict[str, Any]] = {}
        self.removed_types: list[str] = []
        self.started: list[str] = []
        self.finished: list[str] = []
        self.queued: list[str] = []
        self.raised: list[tuple[str, dict[str, Any]]] = []
        self.triggers: dict[str, dict[str, Any]] = {}
        self.callbacks: dict[str, Callable[..., Any]] = {}
        self.group_toggles: list[tuple[str, bool]] = []
        self.core = CoreHide(lambda: self.record)
        self.shown: list[str] = []
        self.hidden: list[str] = []
        self.record: dict[str, Any] = {}
        self.args: dict[str, Any] = {}
        self.existing: set[str] = set()
        self.saved: list[dict[str, Any]] = []

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.events:event.add": lambda ev, by, **kw: self.events_added.append(ev),
            "plugins.core.events:event.raise": self._event_raise,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.mudcmds:type.add": self._type_add,
            "plugins.core.mudcmds:type.remove": self.removed_types.append,
            "plugins.core.mudcmds:command.queue": self.queued.append,
            "plugins.core.mudcmds:command.start": self.started.append,
            "plugins.core.mudcmds:command.finish": self._command_finish,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
            "plugins.core.triggers:group.toggle.enable": self._group_toggle,
            "plugins.core.colors:colorcode.strip": lambda text: re.sub(
                r"@x\d{1,3}|@[A-Za-z]", "", text
            ),
            "plugins.core.commands:command.current.args.get": lambda: self.args,
            "libs.net.protocols:gmcp.value.get": self.gmcp.get,
            "libs.api:api.exists": lambda api_name: api_name in self.existing,
            "plugins.aardwolf.eqdb:item.save": self._item_save,
        }
        return table[name]

    def _event_raise(self, name: str, event_args: dict[str, Any] | None = None) -> None:
        self.raised.append((name, event_args or {}))

    def _item_save(self, item: dict[str, Any]) -> bool:
        self.saved.append(item)
        return True

    def _type_add(self, cmdtype: str, cmd: str, regex: str, **kwargs: object) -> None:
        self.types[cmdtype] = {"cmd": cmd, "regex": regex, **kwargs}
        self.core.add_type(cmdtype, cmd, regex, **kwargs)

    def _command_finish(self, cmdtype: str) -> None:
        self.finished.append(cmdtype)
        self.core.finished(cmdtype)

    def _trigger_add(self, name: str, regex: str, **kwargs: object) -> SimpleNamespace:
        self.triggers[name] = {
            "regex": regex,
            "enabled": kwargs.get("enabled", True),
            "group": kwargs.get("group"),
        }
        return SimpleNamespace(success=True, trigger=SimpleNamespace(trigger_id=name))

    def _trigger_register(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        self.callbacks[trigger_id] = func
        return True

    def _group_toggle(self, group: str, flag: bool) -> bool:
        assert any(t["group"] == group for t in self.triggers.values()), f"unknown group {group}"
        self.group_toggles.append((group, flag))
        for trigger in self.triggers.values():
            if trigger["group"] == group:
                trigger["enabled"] = flag
        return True

    def feed(
        self,
        lines: list[str],
        prompt: bool = False,
        colored: dict[str, str] | None = None,
    ) -> None:
        """Run each line through the triggers, as the triggers plugin does."""
        for index, text in enumerate(lines):
            marked = prompt and index == len(lines) - 1
            line = SimpleNamespace(
                noansi=text,
                colorcoded=(colored or {}).get(text, text),
                is_prompt=marked,
                send=True,
                internal=False,
            )
            self.record = {"matches": {}, "line": line}
            self.core.line()
            for name, trigger in list(self.triggers.items()):
                if not trigger["enabled"]:
                    continue
                match = re.match(trigger["regex"], text)
                if match and name in self.callbacks:
                    self.record = {"matches": match.groupdict(), "line": line}
                    self.callbacks[name]()
            (self.shown if line.send else self.hidden).append(text)

    def enabled(self) -> set[str]:
        """The names of the enabled triggers."""
        return {name for name, trigger in self.triggers.items() if trigger["enabled"]}


class Env:
    """The plugin under test with its fake API and the commands it sent."""

    def __init__(self, plugin: "EqPlugin", fake: FakeApi, sent: list[str]) -> None:
        self.plugin = plugin
        self.fake = fake
        self.sent = sent

    def queued_read(self, cmdtype: str) -> None:
        """mudcmds sends a queued data command: run its beforef, then arm its hide window."""
        spec = self.fake.types[cmdtype]
        spec["beforef"]()
        self.fake.core.sent(cmdtype, spec["cmd"])

    def fill(self) -> None:
        """Read worn, inventory, bag, keyring and vault, typed, so everything is shown."""
        for block in (EQDATA, INVDATA, BAGDATA, KEYDATA, VAULTDATA):
            self.fake.feed(block)
        self.fake.feed([COUNTS])
        self.fake.raised.clear()
        self.fake.queued.clear()
        self.sent.clear()

    def invmon(self, action: int, serial: int, container: int = -1, location: int = -1) -> None:
        """Feed one invmon line."""
        self.fake.feed([f"{{invmon}}{action},{serial},{container},{location}"])

    def disconnect(self) -> None:
        """The MUD link closes."""
        self.plugin._eventcb_disconnect()
        self.fake.core.disconnect()


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build an EqPlugin with a fake API and load it."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from aardwolf.eq.plugin import _eq

    sent: list[str] = []

    class FakeSend:
        def __init__(self, message: "NetworkData") -> None:
            self.message = message

        def __call__(self) -> None:
            sent.extend(str(item.line) for item in self.message)

    monkeypatch.setattr(_eq, "SendDataDirectlyToMud", FakeSend)
    fake = FakeApi()
    plugin = _eq.EqPlugin.__new__(_eq.EqPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    plugin._phook_initialize()
    yield Env(plugin, fake, sent)


# loading


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.eq" in {p["plugin_id"] for p in result.plugins}


def test_dependencies_leave_out_other_plugins() -> None:
    """The plugin depends on core and connect, and not on eqdb or another feature plugin."""
    from aardwolf import eq

    assert "plugins.aardwolf.connect" in eq.PLUGIN_DEPENDENCIES
    assert not any(dep.endswith("eqdb") for dep in eq.PLUGIN_DEPENDENCIES)


def test_after_load(env: Env) -> None:
    """after_load adds the events, the four types and the triggers; only the line trigger is off."""
    fake = env.fake
    assert set(fake.events_added) == set(EVENTS)
    assert set(fake.types) == {"eq_worn", "eq_inventory", "eq_keyring", "eq_vault"}
    worn = fake.types["eq_worn"]
    assert (worn["cmd"], worn["regex"]) == ("eqdata", r"^eqdata$")
    assert worn["hide_output"] is True
    assert worn["hide_start"] == r"^\{eqdata\}$"
    # no hide_end on any type: the window closes at the prompt after finish
    assert all("hide_end" not in spec for spec in fake.types.values())
    assert worn["hide_max"] == HIDE_MAX_LINES + 2
    vault = fake.types["eq_vault"]
    assert vault["cmd"] == "vault data"
    assert re.match(vault["hide_start"], "{vault}")
    assert re.match(vault["hide_start"], NO_VAULT)
    assert fake.types["eq_keyring"]["cmd"] == "keyring data"
    assert fake.types["eq_inventory"]["regex"] == r"^invdata$"
    assert set(fake.triggers) == {
        "eq_invmon",
        "eq_invitem",
        "eq_data_start",
        "eq_data_end",
        "eq_vaultcounts",
        "eq_no_vault",
        "eq_data_line",
    }
    assert fake.enabled() == set(fake.triggers) - {"eq_data_line"}
    assert fake.triggers["eq_data_line"]["group"] == GROUP
    assert set(fake.callbacks) == set(fake.triggers)


def test_character_active_queues_worn_inventory_keyring(env: Env) -> None:
    """Outside a bank the vault is left out."""
    env.plugin._phook_character_active()
    assert env.fake.queued == ["eq_worn", "eq_inventory", "eq_keyring"]


def test_character_active_in_a_bank_queues_the_vault(env: Env) -> None:
    env.fake.gmcp["room.info.details"] = "bank,safe"
    env.plugin._phook_character_active()
    assert env.fake.queued == ["eq_worn", "eq_inventory", "eq_keyring", "eq_vault"]


def test_character_active_without_gmcp_does_not_raise(env: Env) -> None:
    """A missing room is not a bank."""
    env.fake.gmcp.clear()
    env.plugin._phook_character_active()
    assert "eq_vault" not in env.fake.queued
    env.fake.gmcp["room.info.details"] = None
    env.plugin._phook_character_active()
    assert "eq_vault" not in env.fake.queued


# the data commands


def test_queued_eqdata_fills_the_state_and_is_hidden(env: Env) -> None:
    fake = env.fake
    env.queued_read("eq_worn")
    fake.feed(EQDATA)
    fake.feed([PROMPT], prompt=True)
    assert env.plugin.state.worn[24] == 1001
    assert env.plugin.state.worn[7] == 1002
    assert fake.started == ["eq_worn"]
    assert fake.finished == ["eq_worn"]
    # the prompt after the end tag is hidden too, then the window is closed
    assert fake.hidden == [*EQDATA, PROMPT]
    assert fake.shown == []
    fake.feed(["Someone tells you 'hello'"])
    assert fake.shown == ["Someone tells you 'hello'"]
    assert not fake.enabled() & {"eq_data_line"}


def test_data_line_trigger_is_on_only_inside_a_block(env: Env) -> None:
    fake = env.fake
    fake.feed([SWORD])
    assert env.plugin.state.items == {}
    fake.feed(["{eqdata}"])
    assert "eq_data_line" in fake.enabled()
    fake.feed([SWORD, "{/eqdata}"])
    assert "eq_data_line" not in fake.enabled()
    assert fake.group_toggles == [(GROUP, True), (GROUP, False)]


def test_typed_eqdata_is_parsed_and_shown(env: Env) -> None:
    fake = env.fake
    fake.feed(EQDATA)
    fake.feed([PROMPT], prompt=True)
    assert env.plugin.state.worn[24] == 1001
    assert fake.shown == [*EQDATA, PROMPT]
    assert fake.hidden == []
    # only a queued command starts timing, so a typed one never trips mudcmds' start check
    assert fake.started == []


def test_queued_invdata_adds_the_bag_type_and_queues_it(env: Env) -> None:
    fake = env.fake
    env.queued_read("eq_inventory")
    fake.feed(INVDATA)
    assert env.plugin.state.serials("Inventory") == [2001, 2002]
    assert fake.types["eq_container_2002"]["cmd"] == "invdata 2002"
    assert fake.types["eq_container_2002"]["regex"] == r"^invdata 2002$"
    assert fake.types["eq_container_2002"]["hide_start"] == r"^\{invdata 2002\}$"
    assert fake.queued == ["eq_container_2002"]


def test_bag_block_fills_the_bag_and_is_hidden(env: Env) -> None:
    fake = env.fake
    fake.feed(INVDATA)
    fake.core.disconnect()
    env.queued_read("eq_container_2002")
    fake.shown.clear()
    fake.feed(BAGDATA)
    fake.feed([PROMPT], prompt=True)
    assert env.plugin.state.serials("2002") == [3001]
    assert fake.finished[-1] == "eq_container_2002"
    assert fake.hidden[-len(BAGDATA) :] == BAGDATA
    assert fake.shown == [PROMPT]


def test_second_inventory_read_does_not_add_the_bag_type_again(env: Env) -> None:
    fake = env.fake
    fake.feed(INVDATA)
    fake.feed(INVDATA)
    assert list(fake.types).count("eq_container_2002") == 1
    assert fake.queued == ["eq_container_2002"]


def test_a_typed_block_for_an_unknown_bag_gets_a_type_for_later(env: Env) -> None:
    env.fake.feed(["{invdata 777}", GEM, "{/invdata}"])
    assert env.plugin.state.serials("777") == [3001]
    assert "eq_container_777" in env.fake.types
    # no start for a type that did not exist; mudcmds ignores a finish that is not current
    assert env.fake.started == []


def test_queued_vault_hides_through_the_next_prompt_and_stores_int_counts(env: Env) -> None:
    fake = env.fake
    env.queued_read("eq_vault")
    fake.feed(VAULTDATA)
    fake.feed([COUNTS])
    fake.feed([PROMPT], prompt=True)
    fake.feed(["a later line"])
    assert fake.hidden == [*VAULTDATA, COUNTS, PROMPT]
    assert fake.shown == ["a later line"]
    assert env.plugin.state.serials("Vault") == [5001]
    assert env.plugin.state.vault_counts == {"items": 1, "total": 1, "max": 50}


def test_queued_vault_with_no_vault_finishes_and_is_hidden(env: Env) -> None:
    """Aardwolf's no-vault answer ends the queued read at once, and it and its prompt are hidden."""
    fake = env.fake
    env.fill()
    fake.finished.clear()
    fake.shown.clear()
    env.queued_read("eq_vault")
    fake.feed([NO_VAULT, ""])
    fake.feed([PROMPT], prompt=True)
    fake.feed(["a later line"])
    assert fake.finished == ["eq_vault"]
    assert fake.hidden == [NO_VAULT, "", PROMPT]
    assert fake.shown == ["a later line"]
    assert env.plugin.state.serials("Vault") == []
    assert env.plugin.state.vault_counts is None


def test_typed_vault_data_with_no_vault_is_shown(env: Env) -> None:
    fake = env.fake
    fake.feed([NO_VAULT, ""])
    fake.feed([PROMPT], prompt=True)
    assert fake.shown == [NO_VAULT, "", PROMPT]
    assert env.plugin.state.serials("Vault") == []


def test_queued_keyring_is_hidden(env: Env) -> None:
    env.queued_read("eq_keyring")
    env.fake.feed(KEYDATA)
    env.fake.feed([PROMPT], prompt=True)
    assert env.plugin.state.serials("Keyring") == [4001]
    assert env.fake.hidden == [*KEYDATA, PROMPT]
    assert env.fake.shown == []


def test_mismatched_end_tag_does_not_commit(env: Env) -> None:
    fake = env.fake
    fake.feed(["{eqdata}", SWORD, "{/keyring}"])
    assert env.plugin.state.worn[24] is None
    fake.feed(["{/eqdata}"])
    assert env.plugin.state.worn[24] == 1001


def test_a_bad_line_inside_a_block_is_skipped(env: Env) -> None:
    env.fake.feed(["{eqdata}", "12,not,an,item", SWORD, "{/eqdata}"])
    assert env.plugin.state.serials("Worn") == [1001]


def test_a_block_end_without_a_start_is_ignored(env: Env) -> None:
    env.fake.feed(["{/eqdata}"])
    assert env.fake.finished == []


# invmon


def test_invmon_wear_raises_a_deep_copied_item(env: Env) -> None:
    env.fill()
    env.invmon(2, 2001, location=5)
    name, payload = env.fake.raised[0]
    assert name == EVENT_WORN
    assert payload["location"] == 5
    assert payload["item"]["serial"] == 2001
    payload["item"]["name"] = "changed"
    assert env.plugin.state.items[2001]["name"] == "a test potion"
    assert env.plugin.state.worn[5] == 2001
    assert_raised_described(env.fake.raised, EVENTS)


def test_invmon_remove_raises_removed(env: Env) -> None:
    env.fill()
    env.invmon(1, 1001, location=24)
    assert [n for n, _ in env.fake.raised] == [EVENT_REMOVED]
    assert env.plugin.state.serials("Inventory")[0] == 1001


def test_invmon_put_in_a_bag_raises_put_with_serial_and_container(env: Env) -> None:
    env.fill()
    env.invmon(6, 2001, container=2002)
    name, payload = env.fake.raised[0]
    assert name == EVENT_PUT
    assert payload["serial"] == 2001
    assert payload["container"] == "2002"
    assert env.plugin.state.serials("2002")[0] == 2001
    assert_raised_described(env.fake.raised, EVENTS)


def test_invmon_all_actions_raise_only_described_keys(env: Env) -> None:
    env.fill()
    for action, serial, container in (
        (5, 3001, 2002),
        (11, 2001, -1),
        (12, 4001, -1),
        (9, 2001, -1),
        (10, 5001, -1),
        (4, 1001, -1),
        (3, 3001, -1),
    ):
        env.invmon(action, serial, container)
    names = {name for name, _ in env.fake.raised}
    assert {EVENT_TAKEN, EVENT_PUT, EVENT_INVENTORY_REMOVED} <= names
    assert_raised_described(env.fake.raised, EVENTS)


def test_invmon_added_unknown_item_refreshes_the_inventory(env: Env) -> None:
    env.fill()
    env.invmon(4, 9999)
    assert env.fake.raised == [
        (EVENT_PUT, {"serial": 9999, "container": "Inventory", "item": None})
    ]
    assert env.fake.queued == ["eq_inventory"]


def test_invitem_then_invmon_added_raises_inventory_added(env: Env) -> None:
    env.fill()
    env.fake.feed(["{invitem}6001,,a new thing,3,6,0,-1,-1"])
    assert env.plugin.state.items[6001]["name"] == "a new thing"
    env.invmon(4, 6001)
    assert [n for n, _ in env.fake.raised] == [EVENT_INVENTORY_ADDED, EVENT_PUT]


def test_invmon_removed_bag_removes_its_type(env: Env) -> None:
    env.fill()
    env.invmon(3, 2002)
    assert env.fake.removed_types == ["eq_container_2002"]
    assert env.plugin.state.container_copy(2002) is None


def test_invmon_bad_data_matches_nothing(env: Env) -> None:
    env.fill()
    env.fake.feed(["{invmon}x,1,2,3", "{invmon}1,2,3"])
    assert env.fake.raised == []
    assert env.fake.queued == []


def test_invmon_callback_with_bad_data_logs_and_returns(env: Env) -> None:
    env.fill()
    env.fake.record = {"matches": {"action": "x", "serial": "1", "container": "2"}}
    env.plugin._trigger_invmon()
    assert env.fake.raised == []


def test_invmon_unknown_bag_put_queues_the_new_bag_and_inventory(env: Env) -> None:
    env.fill()
    env.invmon(6, 2001, container=777)
    assert "eq_container_777" in env.fake.types
    assert env.fake.queued == ["eq_container_777", "eq_inventory"]


def test_invmon_vault_refresh_only_in_a_bank(env: Env) -> None:
    env.fill()
    env.invmon(10, 9999)
    assert env.fake.queued == ["eq_inventory"]
    env.fake.queued.clear()
    env.fake.gmcp["room.info.details"] = "bank"
    env.invmon(10, 9999)
    assert env.fake.queued == ["eq_vault", "eq_inventory"]


# invitem


def test_invitem_adds_and_updates_with_cname_from_colorcoded(env: Env) -> None:
    fake = env.fake
    colored = {
        "{invitem}7001,K,a red thing,3,6,0,-1,-1": "{invitem}7001,K,@Ra red thing@w,3,6,0,-1,-1"
    }
    fake.feed(["{invitem}7001,K,a red thing,3,6,0,-1,-1"], colored=colored)
    item = env.plugin.state.items[7001]
    assert item["cname"] == "@Ra red thing@w"
    assert item["name"] == "a red thing"
    fake.feed(["{invitem}7001,K,a red thing,4,6,0,-1,-1"])
    assert env.plugin.state.items[7001]["level"] == 4
    fake.feed(["{invitem}garbage"])
    assert len(env.plugin.state.items) == 1


# disconnect


def test_disconnect_clears_state_group_and_bag_types(env: Env) -> None:
    env.fill()
    assert env.plugin.state.items
    env.disconnect()
    assert env.plugin.state.items == {}
    assert env.fake.removed_types == ["eq_container_2002"]
    env.fake.feed(["{eqdata}"])
    env.disconnect()
    assert "eq_data_line" not in env.fake.enabled()
    env.fake.feed([SWORD])
    env.fake.feed(["{/eqdata}"])
    assert env.plugin.state.items == {}


# APIs


def test_read_apis_return_copies_and_accept_text(env: Env) -> None:
    env.fill()
    plugin = env.plugin
    item = plugin._api_item_get("1001")
    assert item is not None
    item["name"] = "changed"
    assert plugin._api_item_get(1001)["name"] == "a test sword"
    assert plugin._api_item_get("nope") is None
    assert plugin._api_item_get(404) is None
    assert [i["serial"] for i in plugin._api_item_find_by_name("test sw")] == [1001]
    assert plugin._api_container_get("2002") == plugin._api_container_get(2002)
    assert plugin._api_container_get(2002)["items"] == [3001]
    assert plugin._api_container_get("none") is None


def test_eq_worn_get_serves_mobk(env: Env) -> None:
    """mobk calls eq.worn.get(24) and reads the serial; it never raises."""
    from aardwolf.mobk.libs import EQ_WORN_API

    assert f"{PLUGIN_ID}:eq.worn.get" == EQ_WORN_API
    env.fill()
    worn = env.plugin._api_eq_worn_get(24)
    assert worn is not None
    assert worn["serial"] == 1001
    assert env.plugin._api_eq_worn_get(25) is None
    assert env.plugin._api_eq_worn_get("wielded")["serial"] == 1001
    assert env.plugin._api_eq_worn_get("24")["serial"] == 1001
    assert env.plugin._api_eq_worn_get("nowhere") is None


def test_item_fetch_sends_the_right_command(env: Env) -> None:
    env.fill()
    plugin = env.plugin
    assert plugin._api_item_fetch(3001)
    assert plugin._api_item_fetch(4001)
    assert plugin._api_item_fetch(5001)
    assert plugin._api_item_fetch(1001)
    assert plugin._api_item_fetch("2001")
    assert env.sent == ["get 3001 2002", "keyring get 4001", "vault get 5001", "remove 1001"]
    assert plugin.state.items[3001]["origcontainer"] == "2002"
    assert plugin.state.items[2001]["origcontainer"] is None


def test_item_fetch_rejects_unknown_and_non_numeric(env: Env) -> None:
    env.fill()
    assert not env.plugin._api_item_fetch(404)
    assert not env.plugin._api_item_fetch("sword")
    assert not env.plugin._api_item_fetch(None)
    assert env.sent == []


def test_item_fetch_of_an_invitem_only_item_sends_nothing(env: Env) -> None:
    env.fake.feed(["{invitem}6001,,a new thing,3,6,0,-1,-1"])
    assert env.plugin._api_item_fetch(6001)
    assert env.sent == []


def test_item_put_without_a_container_uses_origcontainer(env: Env) -> None:
    env.fill()
    plugin = env.plugin
    assert plugin._api_item_put(2001) is None
    assert plugin._api_item_fetch(3001)
    env.invmon(5, 3001, container=2002)
    env.sent.clear()
    assert plugin._api_item_put(3001) == "2002"
    assert env.sent == ["put 3001 2002"]
    env.invmon(6, 3001, container=2002)
    assert plugin.state.items[3001]["origcontainer"] is None
    assert plugin._api_item_put(3001) is None


def test_item_put_fetches_from_another_container_first(env: Env) -> None:
    env.fill()
    assert env.plugin._api_item_put(3001, "Keyring") == "Keyring"
    assert env.sent == ["get 3001 2002", "keyring put 3001"]


def test_item_put_to_worn_uses_the_last_location_name(env: Env) -> None:
    env.fill()
    plugin = env.plugin
    assert plugin._api_item_fetch(1001)
    env.invmon(1, 1001, location=24)
    env.sent.clear()
    assert plugin._api_item_put(1001) == "Worn"
    assert env.sent == ["wear 1001 wielded"]


def test_item_put_to_worn_with_a_location(env: Env) -> None:
    env.fill()
    assert env.plugin._api_item_put(2001, "Worn", "hold") == "Worn"
    assert env.plugin._api_item_put(2001, "Worn", 4) == "Worn"
    assert env.plugin._api_item_put(2001, "Worn") == "Worn"
    assert env.sent == ["wear 2001 hold", "wear 2001 rear", "wear 2001"]


def test_item_put_to_inventory_sends_only_the_fetch(env: Env) -> None:
    env.fill()
    assert env.plugin._api_item_put(3001, "Inventory") == "Inventory"
    assert env.sent == ["get 3001 2002"]


def test_item_put_to_where_it_is_or_to_nothing_sends_nothing(env: Env) -> None:
    env.fill()
    assert env.plugin._api_item_put(2001, "Inventory") == "Inventory"
    assert env.plugin._api_item_put(2001, "nowhere") is None
    assert env.plugin._api_item_put(404, "Keyring") is None
    assert env.plugin._api_item_put("x", "Keyring") is None
    assert env.sent == []


def test_item_equip_and_lastworn(env: Env) -> None:
    env.fill()
    plugin = env.plugin
    assert plugin._api_item_equip(2001, "hold")
    assert plugin._api_item_equip(2001)
    assert not plugin._api_item_equip(404)
    assert plugin._api_item_fetch(1001)
    env.invmon(1, 1001, location=24)
    env.sent.clear()
    assert plugin._api_item_equip(1001, "lastworn")
    assert env.sent == ["wear 1001 wielded"]


def test_item_unequip(env: Env) -> None:
    env.fill()
    assert env.plugin._api_item_unequip(1001)
    assert env.sent == ["remove 1001"]
    assert not env.plugin._api_item_unequip(2001)
    assert not env.plugin._api_item_unequip("x")
    assert not env.plugin._api_item_unequip(404)
    assert env.sent == ["remove 1001"]


def test_identify_add_merges_and_saves_only_when_eqdb_exists(env: Env) -> None:
    env.fill()
    plugin = env.plugin
    assert plugin._api_item_identify_add(1001, {"material": "test", "serial": 5})
    item = plugin.state.items[1001]
    assert item["material"] == "test"
    assert item["serial"] == 1001
    assert item["hasbeenided"] is True
    assert env.fake.saved == []
    env.fake.existing.add("plugins.aardwolf.eqdb:item.save")
    assert plugin._api_item_identify_add("1001", {"score": 12})
    assert len(env.fake.saved) == 1
    assert env.fake.saved[0]["score"] == 12
    env.fake.saved[0]["name"] = "changed"
    assert plugin.state.items[1001]["name"] == "a test sword"
    assert not plugin._api_item_identify_add(404, {"score": 1})
    assert len(env.fake.saved) == 1


# commands


def test_refresh_queues_the_types(env: Env) -> None:
    env.fill()
    result = env.plugin._command_refresh()
    assert result.message == ["Refreshing EQ"]
    assert env.fake.queued == ["eq_worn", "eq_inventory", "eq_keyring", "eq_container_2002"]


def test_icache(env: Env) -> None:
    env.fill()
    env.fake.args = {"item": "1001"}
    lines = env.plugin._command_icache().message
    assert lines[0] == "Item 1001"
    assert "name: a test sword" in lines
    assert lines[1:] == sorted(lines[1:])
    env.fake.args = {"item": "404"}
    assert env.plugin._command_icache().message == ["That item is not in the cache"]
    env.fake.args = {"item": "sword"}
    assert env.plugin._command_icache().message == ["sword is not a serial number"]


def test_get_with_a_known_serial_fetches(env: Env) -> None:
    env.fill()
    env.fake.args = {"item": "3001", "otherargs": []}
    result = env.plugin._command_get()
    assert result.message == []
    assert env.sent == ["get 3001 2002"]


def test_get_with_unknown_words_sends_them_quoted(env: Env) -> None:
    env.fill()
    env.fake.args = {"item": "two words", "otherargs": ["bag"]}
    env.plugin._command_get()
    assert env.sent == ["get 'two words' bag"]
    env.sent.clear()
    env.fake.args = {"item": "9999", "otherargs": []}
    env.plugin._command_get()
    assert env.sent == ["get 9999"]


def test_put_with_a_known_item_and_bag(env: Env) -> None:
    env.fill()
    env.fake.args = {"item": "2001", "otherargs": ["2002"]}
    assert env.plugin._command_put().message == []
    assert env.sent == ["put 2001 2002"]


def test_put_without_a_destination_goes_back_or_says_why(env: Env) -> None:
    env.fill()
    env.fake.args = {"item": "2001", "otherargs": []}
    assert "no container" in env.plugin._command_put().message[0]
    assert env.sent == []
    assert env.plugin._api_item_fetch(3001)
    env.invmon(5, 3001, container=2002)
    env.sent.clear()
    env.fake.args = {"item": "3001", "otherargs": []}
    env.plugin._command_put()
    assert env.sent == ["put 3001 2002"]


def test_put_fallback_sends_the_item_once(env: Env) -> None:
    env.fill()
    env.fake.args = {"item": "backpack", "otherargs": ["big bag"]}
    env.plugin._command_put()
    assert env.sent == ["put backpack 'big bag'"]
    env.sent.clear()
    env.fake.args = {"item": "2001", "otherargs": ["unknownbag"]}
    env.plugin._command_put()
    assert env.sent == ["put 2001 unknownbag"]


def test_state_is_not_shared_between_events_payloads(env: Env) -> None:
    env.fill()
    env.invmon(2, 2001, location=5)
    before = copy.deepcopy(env.plugin.state.items[2001])
    env.fake.raised[0][1]["item"]["level"] = 99
    assert env.plugin.state.items[2001] == before
