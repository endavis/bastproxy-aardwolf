"""Tests for the Aardwolf itemid plugin, with a stubbed API that drives its triggers."""

import ast
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
from aardwolf.itemid.libs import (
    API_EQ_IDENTIFY_ADD,
    API_EQ_ITEM_FETCH,
    API_EQ_ITEM_GET,
    API_EQ_ITEM_PUT,
    API_EQDB_ITEM_GET,
    API_EQDB_ITEM_SAVE,
    API_SKILL_GET,
    EVENT_IDENTIFIED,
    EVENTS,
    TYPE_IDENTIFY,
    TYPE_INVDETAILS,
)

if TYPE_CHECKING:
    from bastproxy.libs.records import NetworkData

    from aardwolf.itemid.plugin import _itemid

PLUGIN_ID = "plugins.aardwolf.itemid"
GROUP_INV = f"{PLUGIN_ID}.invdetails"
GROUP_ID = f"{PLUGIN_ID}.identify"
PROMPT = "<100/100hp 50/50mn 90/90mv> "
BORDER = "+-----------------------------------------------------------------+"
DETAILS = [
    "{invdetails}",
    "{invheader}1001|50|5|12000|7|wielded|glow, hum|Nobody|Example|-1|0|0|0|123",
    "{statmod}Strength|2",
    "{weapon}dagger|17|Slice|Pierce|sharp",
    "{container}100|20|3|2|30|5|50",
    "{/invdetails}",
]
IDENTIFY = [
    BORDER,
    "| Keywords   : gleaming test blade                                |",
    "| Name       : a gleaming test blade                              |",
    "| Id         : 1001                                               |",
    BORDER,
    "| Material   : steel                                              |",
    BORDER,
    "|   A synthetic note.                                             |",
    BORDER,
]


def eq_item(serial: int, container: str, wearslot: int = -1) -> dict[str, Any]:
    """An item as eq has it."""
    return {
        "serial": serial,
        "cname": f"@Wan item {serial}@w",
        "name": f"an item {serial}",
        "container": container,
        "origcontainer": None,
        "hasbeenided": False,
        "wearslot": wearslot,
    }


class FakeApi:
    """A stand-in for the bastproxy API that records the calls and drives the triggers."""

    def __init__(self) -> None:
        self.events_added: list[str] = []
        self.registered: dict[str, Callable[..., Any]] = {}
        self.types: dict[str, dict[str, Any]] = {}
        self.started: list[str] = []
        self.finished: list[str] = []
        self.queued: list[tuple[str, str]] = []
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
        self.eq: dict[int, dict[str, Any]] = {}
        self.fetched: list[int] = []
        self.put: list[tuple[int, str]] = []
        self.put_result: str | bool | None = True
        self.added: list[tuple[int, dict[str, Any]]] = []
        self.add_result = True
        self.saved: list[dict[str, Any]] = []
        self.db: dict[int, dict[str, Any]] = {}
        self.skills: dict[int, dict[str, Any]] = {}

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.events:event.add": lambda ev, by, **kw: self.events_added.append(ev),
            "plugins.core.events:event.raise": self._event_raise,
            "plugins.core.events:event.register": self.registered.__setitem__,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.mudcmds:type.add": self._type_add,
            "plugins.core.mudcmds:command.queue": lambda t, a="": self.queued.append((t, a)),
            "plugins.core.mudcmds:command.start": self.started.append,
            "plugins.core.mudcmds:command.finish": self._command_finish,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
            "plugins.core.triggers:group.toggle.enable": self._group_toggle,
            "plugins.core.colors:colorcode.strip": lambda text: re.sub(
                r"@x\d{1,3}|@[A-Za-z]", "", text
            ),
            "plugins.core.commands:command.current.args.get": lambda: self.args,
            "libs.api:api.exists": lambda api_name: api_name in self.existing,
            API_EQ_ITEM_GET: lambda serial: copy.deepcopy(self.eq.get(serial)),
            API_EQ_ITEM_FETCH: self._fetch,
            API_EQ_ITEM_PUT: self._put,
            API_EQ_IDENTIFY_ADD: self._add,
            API_EQDB_ITEM_GET: lambda serial: copy.deepcopy(self.db.get(serial)),
            API_EQDB_ITEM_SAVE: self._save,
            API_SKILL_GET: lambda sn: self.skills.get(sn),
        }
        return table[name]

    def _event_raise(self, name: str, event_args: dict[str, Any] | None = None) -> None:
        self.raised.append((name, event_args or {}))

    def _save(self, item: dict[str, Any]) -> bool:
        self.saved.append(item)
        return True

    def _fetch(self, serial: int) -> bool:
        self.fetched.append(serial)
        if serial in self.eq:
            # invmon moves the item to the inventory
            self.eq[serial]["container"] = "Inventory"
        return serial in self.eq

    def _put(self, serial: int, container: str) -> str | None:
        self.put.append((serial, container))
        if self.put_result is True:
            return container
        return self.put_result or None

    def _add(self, serial: int, attributes: dict[str, Any]) -> bool:
        self.added.append((serial, attributes))
        return self.add_result

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

    def feed(self, lines: list[str], prompt: bool = False) -> None:
        """Run each line through the hide window and the enabled triggers."""
        for index, text in enumerate(lines):
            line = SimpleNamespace(
                noansi=text,
                colorcoded=text,
                is_prompt=prompt and index == len(lines) - 1,
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
    """The plugin under test with its fake API and what it sent to the client."""

    def __init__(self, plugin: "_itemid.ItemIdPlugin", fake: FakeApi, client: list[str]) -> None:
        self.plugin = plugin
        self.fake = fake
        self.client = client

    def queued_read(self, cmdtype: str) -> None:
        """mudcmds sends a queued command: run its beforef, then arm its hide window."""
        spec = self.fake.types[cmdtype]
        spec["beforef"]()
        self.fake.core.sent(cmdtype, spec["cmd"])

    def read_both(self, details: list[str] = DETAILS, identify: list[str] = IDENTIFY) -> None:
        """Run both queued commands with their replies and prompts."""
        self.queued_read(TYPE_INVDETAILS)
        self.fake.feed(details)
        self.fake.feed([PROMPT], prompt=True)
        self.queued_read(TYPE_IDENTIFY)
        self.fake.feed(identify)
        self.fake.feed([PROMPT], prompt=True)

    def clear(self) -> None:
        """Forget what was recorded."""
        self.fake.raised.clear()
        self.fake.queued.clear()
        self.client.clear()


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build an ItemIdPlugin with a fake API and load it."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from aardwolf.itemid.plugin import _itemid

    client: list[str] = []

    class FakeClient:
        def __init__(self, message: "NetworkData") -> None:
            self.message = message

        def __call__(self) -> None:
            client.extend(str(item.line) for item in self.message)

    monkeypatch.setattr(_itemid, "SendDataDirectlyToClient", FakeClient)
    fake = FakeApi()
    fake.eq[1001] = eq_item(1001, "Inventory")
    fake.eq[2001] = eq_item(2001, "3002")
    fake.eq[2002] = eq_item(2002, "Worn", wearslot=24)
    plugin = _itemid.ItemIdPlugin.__new__(_itemid.ItemIdPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    plugin._phook_initialize()
    yield Env(plugin, fake, client)


# loading


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.itemid" in {p["plugin_id"] for p in result.plugins}


def test_dependencies_name_eq_and_leave_out_the_optional_plugins() -> None:
    from aardwolf import itemid

    assert "plugins.aardwolf.eq" in itemid.PLUGIN_DEPENDENCIES
    assert not any(dep.endswith(("eqdb", "skills")) for dep in itemid.PLUGIN_DEPENDENCIES)


def test_plugin_imports_no_other_plugin() -> None:
    """A plugin reaches another through its API: only aardwolf._libs and its own package."""
    root = Path(aardwolf.__file__).resolve().parent / "itemid"
    for path in root.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                if node.module.startswith("aardwolf."):
                    assert node.module.startswith(("aardwolf._libs", "aardwolf.itemid")), path
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("aardwolf.") or alias.name.startswith(
                        ("aardwolf._libs", "aardwolf.itemid")
                    ), path


def test_after_load(env: Env) -> None:
    fake = env.fake
    assert set(fake.events_added) == set(EVENTS)
    assert set(fake.types) == {TYPE_INVDETAILS, TYPE_IDENTIFY}
    invdetails = fake.types[TYPE_INVDETAILS]
    assert (invdetails["cmd"], invdetails["regex"]) == ("invdetails", r"^invdetails \d+$")
    assert invdetails["hide_output"] is True
    assert invdetails["hide_start"] == r"^\{invdetails\}$"
    identify = fake.types[TYPE_IDENTIFY]
    assert (identify["cmd"], identify["regex"]) == ("identify", r"^identify \d+$")
    assert identify["hide_output"] is True
    assert re.match(identify["hide_start"], BORDER)
    assert all("hide_end" not in spec for spec in fake.types.values())
    assert set(fake.triggers) == set(fake.callbacks)
    assert len(fake.triggers) == 4
    assert fake.enabled() == set()
    assert {t["group"] for t in fake.triggers.values()} == {GROUP_INV, GROUP_ID}
    assert set(fake.registered) == {
        f"cmd_{TYPE_INVDETAILS}_timeout",
        f"cmd_{TYPE_IDENTIFY}_timeout",
    }


# an inventory item


def test_identify_an_inventory_item_queues_both_commands_and_sends_no_fetch(env: Env) -> None:
    assert env.plugin._api_item_identify(1001) is None
    assert env.fake.queued == [(TYPE_INVDETAILS, "1001"), (TYPE_IDENTIFY, "1001")]
    assert env.fake.fetched == []


def test_the_queued_flow_hides_everything_and_hands_the_item_to_eq(env: Env) -> None:
    fake = env.fake
    env.plugin._api_item_identify(1001)
    env.read_both()
    assert fake.hidden == [*DETAILS, PROMPT, *IDENTIFY, PROMPT]
    assert fake.shown == []
    assert fake.started == [TYPE_INVDETAILS, TYPE_IDENTIFY]
    assert fake.finished == [TYPE_INVDETAILS, TYPE_IDENTIFY]
    assert fake.enabled() == set()
    assert len(fake.added) == 1
    serial, attributes = fake.added[0]
    assert serial == 1001
    assert attributes["keywords"] == ["gleaming", "test", "blade"]
    assert attributes["flags"] == ["glow", "hum"]
    assert attributes["material"] == "steel"
    assert attributes["notes"] == {"ntext": "A synthetic note."}
    assert attributes["statmod"] == {"Strength": 2}
    assert attributes["container"]["capacity"] == 100
    assert attributes["cname"] == "@Wan item 1001@w"
    assert attributes["name"] == "an item 1001"
    assert fake.saved == []
    assert fake.put == []
    assert [name for name, _ in fake.raised] == [EVENT_IDENTIFIED]
    assert_raised_described(fake.raised, EVENTS)
    payload = fake.raised[0][1]
    assert payload["serial"] == 1001
    assert payload["item"]["material"] == "steel"
    assert env.plugin._pending == []


def test_the_groups_are_on_between_the_start_and_the_end(env: Env) -> None:
    fake = env.fake
    env.queued_read(TYPE_INVDETAILS)
    assert fake.enabled() == {t for t, v in fake.triggers.items() if v["group"] == GROUP_INV}
    env.queued_read(TYPE_IDENTIFY)
    assert fake.enabled() >= {"itemid_identify_line"}


def test_a_typed_invdetails_and_identify_are_shown_and_not_parsed(env: Env) -> None:
    fake = env.fake
    fake.feed(DETAILS)
    fake.feed(IDENTIFY)
    fake.feed([PROMPT], prompt=True)
    assert fake.shown == [*DETAILS, *IDENTIFY, PROMPT]
    assert fake.hidden == []
    assert fake.added == []
    assert fake.raised == []
    assert fake.started == []


# caching


def test_a_cached_item_returns_a_copy_and_queues_nothing(env: Env) -> None:
    env.plugin._api_item_identify(1001)
    env.read_both()
    env.clear()
    cached = env.plugin._api_item_identify(1001)
    assert cached is not None
    assert cached["material"] == "steel"
    cached["material"] = "changed"
    again = env.plugin._api_item_identify("1001")
    assert again is not None
    assert again["material"] == "steel"
    assert env.fake.queued == []


def test_force_queues_again_and_a_pending_serial_is_not_queued_twice(env: Env) -> None:
    env.plugin._api_item_identify(1001)
    env.read_both()
    env.clear()
    assert env.plugin._api_item_identify(1001, force=True) is None
    assert len(env.fake.queued) == 2
    assert env.plugin._api_item_identify(1001, force=True) is None
    assert len(env.fake.queued) == 2
    assert env.plugin._api_item_identify("x") is None
    assert len(env.fake.queued) == 2


# fetch and put back


def test_a_bag_item_is_fetched_and_the_event_waits_for_the_put(env: Env) -> None:
    fake = env.fake
    env.plugin._api_item_identify(2001)
    assert fake.fetched == [2001]
    env.read_both(
        [line.replace("1001|50", "2001|50") for line in DETAILS],
        IDENTIFY,
    )
    assert fake.put == [(2001, "3002")]
    assert [name for name, _ in fake.raised] == []
    assert len(fake.added) == 1
    fake.record = {"serial": 2001, "container": "9999"}
    env.plugin._eventcb_eq_put()
    assert fake.raised == []
    fake.record = {"serial": 1001, "container": "3002"}
    env.plugin._eventcb_eq_put()
    assert fake.raised == []
    fake.record = {"serial": 2001, "container": "3002"}
    env.plugin._eventcb_eq_put()
    assert [name for name, _ in fake.raised] == [EVENT_IDENTIFIED]
    assert fake.raised[0][1]["serial"] == 2001
    assert env.plugin._waits == {}


def test_a_worn_item_is_released_by_the_worn_event(env: Env) -> None:
    fake = env.fake
    env.plugin._api_item_identify(2002)
    assert fake.fetched == [2002]
    env.read_both([line.replace("1001|50", "2002|50") for line in DETAILS])
    assert fake.put == [(2002, "Worn")]
    assert fake.raised == []
    fake.record = {"item": {"serial": 1001}, "location": 24}
    env.plugin._eventcb_eq_worn()
    assert fake.raised == []
    fake.record = {"item": {"serial": 2002}, "location": 24}
    env.plugin._eventcb_eq_worn()
    assert [name for name, _ in fake.raised] == [EVENT_IDENTIFIED]


def test_a_put_that_returns_none_raises_at_once(env: Env) -> None:
    env.fake.put_result = None
    env.plugin._api_item_identify(2001)
    env.read_both([line.replace("1001|50", "2001|50") for line in DETAILS])
    assert [name for name, _ in env.fake.raised] == [EVENT_IDENTIFIED]
    assert env.plugin._waits == {}


def test_an_item_already_back_raises_at_once(env: Env) -> None:
    env.plugin._api_item_identify(2001)
    env.fake.eq[2001]["container"] = "3002"
    env.read_both([line.replace("1001|50", "2001|50") for line in DETAILS])
    assert [name for name, _ in env.fake.raised] == [EVENT_IDENTIFIED]


def test_the_inventory_removed_event_releases_a_wait(env: Env) -> None:
    env.plugin._api_item_identify(2001)
    env.read_both([line.replace("1001|50", "2001|50") for line in DETAILS])
    assert env.fake.raised == []
    env.fake.record = {"item": {"serial": 2001}}
    env.plugin._eventcb_eq_inventory_removed()
    assert [name for name, _ in env.fake.raised] == [EVENT_IDENTIFIED]


def test_disconnect_clears_everything(env: Env) -> None:
    fake = env.fake
    env.plugin._api_item_identify(1001)
    env.read_both()
    env.plugin._api_item_identify(2001)
    env.queued_read(TYPE_INVDETAILS)
    env.plugin._eventcb_disconnect()
    plugin = env.plugin
    assert (plugin._cache, plugin._pending, plugin._fetched, plugin._waits) == ({}, [], {}, {})
    assert plugin._show == set()
    assert fake.enabled() == set()
    assert plugin._api_item_identify(1001) is None
    assert len(fake.queued) == 6


# mismatches and failures


def test_an_invheader_for_another_serial_is_dropped(env: Env) -> None:
    fake = env.fake
    env.plugin._api_item_identify(1001)
    env.read_both([line.replace("1001|50", "7777|50") for line in DETAILS])
    assert fake.added == []
    assert [name for name, _ in fake.raised] == []
    assert env.plugin._cache == {}
    assert env.plugin._pending == []


def test_an_identify_with_no_invdetails_result_is_not_merged_and_the_item_is_put_back(
    env: Env,
) -> None:
    fake = env.fake
    env.plugin._api_item_identify(2001)
    env.queued_read(TYPE_INVDETAILS)
    fake.feed(["{invdetails}", "{/invdetails}"])
    fake.feed([PROMPT], prompt=True)
    env.queued_read(TYPE_IDENTIFY)
    fake.feed(IDENTIFY)
    fake.feed([PROMPT], prompt=True)
    assert fake.added == []
    assert fake.put == [(2001, "3002")]
    assert env.plugin._cache == {}
    # the stale item of the invdetails before does not come back (no currentitem)
    assert env.plugin._details_result is None


def test_an_invdetails_without_an_invheader_does_not_reuse_the_item_before(env: Env) -> None:
    fake = env.fake
    env.plugin._api_item_identify(1001)
    env.read_both()
    assert len(fake.added) == 1
    env.plugin._api_item_identify(2001)
    env.queued_read(TYPE_INVDETAILS)
    fake.feed(["{invdetails}", "{statmod}Strength|9", "{/invdetails}"])
    fake.feed([PROMPT], prompt=True)
    env.queued_read(TYPE_IDENTIFY)
    fake.feed(IDENTIFY)
    fake.feed([PROMPT], prompt=True)
    assert len(fake.added) == 1
    assert 2001 not in env.plugin._cache


def test_the_invdetails_timeout_resets_the_reader_and_the_group(env: Env) -> None:
    fake = env.fake
    env.plugin._api_item_identify(1001)
    env.queued_read(TYPE_INVDETAILS)
    fake.feed(["{invdetails}", "{statmod}Strength|9"])
    fake.core.timed_out(TYPE_INVDETAILS)
    env.plugin._eventcb_invdetails_timeout()
    assert fake.enabled() == set()
    assert env.plugin._details.result() == {}
    # the identify is still queued for the same serial, and it finishes with nothing to merge
    assert env.plugin._pending == [1001]
    env.queued_read(TYPE_IDENTIFY)
    fake.feed(IDENTIFY)
    fake.feed([PROMPT], prompt=True)
    assert fake.added == []
    assert env.plugin._pending == []


def test_the_identify_timeout_drops_the_entry_and_puts_the_item_back(env: Env) -> None:
    fake = env.fake
    env.plugin._api_item_identify(2001)
    env.queued_read(TYPE_INVDETAILS)
    fake.feed(DETAILS[:2] + DETAILS[-1:])
    env.queued_read(TYPE_IDENTIFY)
    fake.feed(IDENTIFY[:3])
    fake.core.timed_out(TYPE_IDENTIFY)
    env.plugin._eventcb_identify_timeout()
    assert fake.enabled() == set()
    assert env.plugin._pending == []
    assert env.plugin._identify.result() == {}
    assert fake.put == [(2001, "3002")]
    assert fake.added == []
    assert fake.raised == []


# saving


def test_eq_returning_false_saves_through_eqdb_when_it_exists(env: Env) -> None:
    fake = env.fake
    fake.add_result = False
    fake.existing.add(API_EQDB_ITEM_SAVE)
    env.plugin._api_item_identify(1001)
    env.read_both()
    assert len(fake.saved) == 1
    assert fake.saved[0]["material"] == "steel"
    assert "tempmod" not in fake.saved[0]


def test_eq_returning_false_without_eqdb_saves_nothing(env: Env) -> None:
    env.fake.add_result = False
    env.plugin._api_item_identify(1001)
    env.read_both()
    assert env.fake.saved == []
    assert [name for name, _ in env.fake.raised] == [EVENT_IDENTIFIED]


def test_tempmods_are_kept_in_the_cache_and_not_given_to_eq(env: Env) -> None:
    env.plugin._api_item_identify(1001)
    env.read_both([*DETAILS[:-1], "{tempmod}7,0,0,Strength,30", DETAILS[-1]])
    assert "tempmod" not in env.fake.added[0][1]
    assert env.plugin._cache[1001]["tempmod"][0]["sn"] == 7


# the id command and item.show


def test_id_without_a_serial_and_with_a_bad_one(env: Env) -> None:
    env.fake.args = {"serial": "", "force": False, "database": False}
    assert env.plugin._command_id().message == ["Please supply a serial #"]
    env.fake.args = {"serial": "abc", "force": False, "database": False}
    assert env.plugin._command_id().message == ["abc is not a serial number"]


def test_id_of_an_unknown_item_says_so(env: Env) -> None:
    env.fake.args = {"serial": "404", "force": False, "database": False}
    assert env.plugin._command_id().message == ["Could not find 404"]
    assert env.fake.queued == []


def test_id_of_a_cached_item_sends_the_box(env: Env) -> None:
    env.plugin._api_item_identify(1001)
    env.read_both()
    env.clear()
    env.fake.args = {"serial": "1001", "force": False, "database": False}
    assert env.plugin._command_id().message == []
    assert env.fake.queued == []
    assert env.client[0] == env.client[-1]
    text = "\n".join(re.sub(r"@.", "", line) for line in env.client)
    assert "Keywords   : gleaming test blade" in text
    assert "Location   : Inventory" in text
    assert "Weapon Type: dagger" in text


def test_id_of_an_uncached_item_identifies_and_then_shows(env: Env) -> None:
    env.fake.args = {"serial": "1001", "force": False, "database": False}
    assert env.plugin._command_id().message == []
    assert len(env.fake.queued) == 2
    assert env.client == []
    env.read_both()
    assert [name for name, _ in env.fake.raised] == [EVENT_IDENTIFIED]
    assert any("Keywords" in line for line in env.client)
    assert env.plugin._show == set()


def test_id_force_identifies_a_cached_item_again(env: Env) -> None:
    env.plugin._api_item_identify(1001)
    env.read_both()
    env.clear()
    env.fake.args = {"serial": "1001", "force": True, "database": False}
    env.plugin._command_id()
    assert len(env.fake.queued) == 2
    assert env.client == []


def test_id_that_cannot_identify_says_so(env: Env) -> None:
    env.fake.args = {"serial": "1001", "force": False, "database": False}
    env.plugin._command_id()
    env.plugin._eventcb_invdetails_timeout()
    env.queued_read(TYPE_IDENTIFY)
    env.fake.core.timed_out(TYPE_IDENTIFY)
    env.plugin._eventcb_identify_timeout()
    assert env.client == ["Could not identify 1001"]


def test_id_database_reads_eqdb_even_when_eq_does_not_know_the_item(env: Env) -> None:
    fake = env.fake
    fake.existing.add(API_EQDB_ITEM_GET)
    fake.db[8888] = {"serial": 8888, "keywords": ["old", "thing"], "flags": [], "level": 3}
    fake.args = {"serial": "8888", "force": False, "database": True}
    assert env.plugin._command_id().message == []
    assert fake.queued == []
    assert any("Keywords   : old thing" in re.sub(r"@.", "", line) for line in env.client)


def test_id_database_with_eqdb_missing_or_without_the_item_says_so(env: Env) -> None:
    fake = env.fake
    fake.args = {"serial": "8888", "force": False, "database": True}
    assert "eqdb plugin is not loaded" in str(env.plugin._command_id().message)
    fake.existing.add(API_EQDB_ITEM_GET)
    assert env.plugin._command_id().message == ["8888 is not in the database"]
    assert env.client == []


def test_item_show_sends_messages_to_the_client(env: Env) -> None:
    env.plugin._api_item_show(404)
    env.plugin._api_item_show("x")
    assert env.client == ["Could not find 404", "x is not a serial number"]


def test_item_format_uses_the_location_given_or_eqs(env: Env) -> None:
    item = {"serial": 2002, "keywords": ["a"]}

    def strip(lines: list[str]) -> str:
        return "\n".join(re.sub(r"@.", "", line) for line in lines)

    assert "Location   : Worn - wielded" in strip(env.plugin._api_item_format(item))
    assert "Location   : Keyring" in strip(env.plugin._api_item_format(item, "Keyring"))


def test_skill_names_come_from_the_skills_plugin_when_it_exists(env: Env) -> None:
    item = {"serial": 1, "skillmod": {5: 2, 6: 1}}
    env.fake.existing.add(API_SKILL_GET)
    env.fake.skills[5] = {"name": "test skill"}
    text = "\n".join(re.sub(r"@.", "", line) for line in env.plugin._api_item_format(item, "x"))
    assert "Modifies Test skill by +2" in text
    assert "Modifies sn 6 by +1" in text
    env.fake.existing.clear()
    text = "\n".join(re.sub(r"@.", "", line) for line in env.plugin._api_item_format(item, "x"))
    assert "Modifies sn 5 by +2" in text


def test_a_tagged_line_before_the_block_is_not_read(
    env: Env, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A fetch's {invmon} line can arrive after beforef turns the group on: it is not parsed."""
    from aardwolf.itemid.plugin import _itemid

    logged: list[tuple[Any, ...]] = []
    monkeypatch.setattr(_itemid, "log_to", lambda *args, **kwargs: logged.append(args))
    env.plugin._api_item_identify(1001)
    env.queued_read(TYPE_INVDETAILS)
    env.fake.feed(["{invmon}5,3001,2002,-1"])
    env.fake.feed(DETAILS)
    env.fake.feed([PROMPT], prompt=True)
    env.queued_read(TYPE_IDENTIFY)
    env.fake.feed(IDENTIFY)
    env.fake.feed([PROMPT], prompt=True)
    assert logged == []
    assert env.fake.added[0][1]["statmod"] == {"Strength": 2}


def test_the_box_names_the_bag_an_item_is_in(env: Env) -> None:
    def text() -> str:
        return "\n".join(re.sub(r"@.", "", line) for line in env.plugin._box({"serial": 2001}))

    assert "Location   : 3002 " in text()
    bag = eq_item(3002, "Inventory")
    bag["name"] = "Vladia's Shopping Bag"
    env.fake.eq[3002] = bag
    assert "Location   : Vladia's Shopping Bag (3002)" in text()
    assert "Location   : Inventory" in "\n".join(
        re.sub(r"@.", "", line) for line in env.plugin._box({"serial": 1001})
    )
