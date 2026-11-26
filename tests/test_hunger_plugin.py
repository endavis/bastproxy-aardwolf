"""Tests for the Aardwolf hunger plugin, with a stubbed API that drives its triggers."""

import ast
import re
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

import aardwolf
from aardwolf.hunger.libs import (
    API_WALK_START,
    EVENT_DISCONNECT,
    EVENT_EQ_INVENTORY_ADDED,
    EVENT_EQ_PUT,
    EVENT_EQ_TAKEN,
    EVENT_MOVE_ROOM,
    EVENT_WALK_DONE,
    EVENT_WALK_FAILED,
    EVENT_WALK_STARTED,
    PENDING_TIMEOUT,
    REPLY_TRIGGERS,
    STAGE_TRIGGERS,
    TIMER_FETCH,
    TIMER_REPLY,
)

if TYPE_CHECKING:
    from bastproxy.libs.records import NetworkData
    from bastproxy.plugins.core.commands import CommandResult

    from aardwolf.hunger.plugin import _hunger

PLUGIN_ID = "plugins.aardwolf.hunger"
CARAFE = 111
BAG = 900
FILLROOM = "1234"
HUNGRY = "## You start to feel hungry."
VERY_THIRSTY = "## You are very thirsty; your healing is reduced."
DEHYDRATED = "## You are dehydrated; your healing is greatly reduced."
EMPTY = "Sacramental Carafe is empty."
FILLED = "You fill Sacramental Carafe with orange juice."
DRANK = "You drink some orange juice from Sacramental Carafe."
GULPED = "You gulp down some orange juice from Sacramental Carafe."
FULL = "You are now full."
NOSOURCE = "There is no liquid source here."


class FakeApi:
    """A stand-in for the bastproxy API."""

    def __init__(self) -> None:
        self.settings: dict[str, Any] = {}
        self.validators: dict[str, Callable[..., Any]] = {}
        self.triggers: dict[str, dict[str, Any]] = {}
        self.callbacks: dict[str, Callable[[], None]] = {}
        self.timers: dict[str, tuple[Callable[[], None], float, bool]] = {}
        self.gmcp: dict[str, Any] = {"room.info.num": 55}
        self.record: dict[str, Any] = {}
        self.args: dict[str, Any] = {}
        # the calls that matter, in order
        self.calls: list[tuple[str, Any]] = []
        self.items: dict[int, dict[str, Any]] = {
            CARAFE: {"serial": CARAFE, "container": str(BAG), "name": "Sacramental Carafe"}
        }
        self.mapper_loaded = True
        self.mapped = {FILLROOM}
        self.walk_state = "idle"
        self.walk_ok = True

    def _setting_add(
        self, pid: str, name: str, default: object, *rest: object, **kwargs: object
    ) -> None:
        self.settings.setdefault(name, default)
        validator = kwargs.get("validator")
        if callable(validator):
            self.validators[name] = validator

    def _setting_set(self, pid: str, name: str, value: object) -> bool:
        validator = self.validators.get(name)
        if validator is not None and validator(value) is not None:
            return False
        self.settings[name] = value
        return True

    def _trigger_add(self, name: str, regex: str, **kwargs: object) -> SimpleNamespace:
        self.triggers[name] = {
            "regex": regex,
            "enabled": kwargs.get("enabled", True),
            "group": kwargs.get("group"),
        }
        return SimpleNamespace(success=True, trigger=SimpleNamespace(trigger_id=name))

    def _group_toggle(self, group: str, flag: bool) -> bool:
        self.calls.append(("group", flag))
        for trigger in self.triggers.values():
            if trigger["group"] == group:
                trigger["enabled"] = flag
        return True

    def _timer_add(self, name: str, func: Callable[[], None], seconds: float, **kw: object) -> None:
        assert name not in self.timers
        self.timers[name] = (func, seconds, bool(kw.get("onetime")))

    def _item_find(self, name: str) -> list[dict[str, Any]]:
        return [dict(i) for i in self.items.values() if name in str(i.get("name"))]

    def _item_get(self, serial: int) -> dict[str, Any] | None:
        item = self.items.get(int(serial))
        return dict(item) if item else None

    def _walk_start(self, room: str) -> bool:
        self.calls.append(("walk.start", room))
        return self.walk_ok

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.settings:setting.add": self._setting_add,
            "plugins.core.settings:setting.get": lambda pid, key: self.settings[key],
            "plugins.core.settings:setting.set": self._setting_set,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self.callbacks.__setitem__,
            "plugins.core.triggers:group.toggle.enable": self._group_toggle,
            "plugins.core.timers:timer.add": self._timer_add,
            "plugins.core.timers:timer.exists": lambda n: n in self.timers,
            "plugins.core.timers:timer.remove": self.timers.pop,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.commands:command.current.args.get": lambda: self.args,
            "libs.net.protocols:gmcp.value.get": lambda path: self.gmcp.get(path),
            "libs.api:api.exists": lambda n: self.mapper_loaded or "mapper" not in n,
            "plugins.aardwolf.eq:item.get": self._item_get,
            "plugins.aardwolf.eq:item.find.by.name": self._item_find,
            "plugins.aardwolf.eq:item.fetch": lambda s: self.calls.append(("fetch", s)),
            "plugins.aardwolf.eq:item.put": lambda s: self.calls.append(("put", s)),
            "plugins.client.mapper:walk.start": self._walk_start,
            "plugins.client.mapper:walk.get": lambda: {"state": self.walk_state},
            "plugins.client.mapper:room.get": lambda uid: (
                {"uid": uid} if uid in self.mapped else None
            ),
        }
        return table[name]


class Env:
    """The plugin under test with its fake API and what it sent."""

    def __init__(self, plugin: "_hunger.HungerPlugin", fake: FakeApi, clock: list[float]) -> None:
        self.plugin = plugin
        self.fake = fake
        self.clock = clock
        self.mud: list[str] = []
        self.owners: list[str] = []
        self.notices: list[str] = []

    def feed(self, text: str) -> None:
        """Run a line through the enabled triggers, as the trigger plugin would."""
        for name, trigger in self.fake.triggers.items():
            match = re.match(trigger["regex"], text)
            if trigger["enabled"] and match:
                self.fake.record = {"matches": match.groupdict()}
                self.fake.callbacks[name]()

    def event(self, handler: Callable[[], None], **record: object) -> None:
        """Deliver an event record to a handler."""
        self.fake.record = dict(record)
        handler()

    def taken(self, serial: int = CARAFE) -> None:
        """Deliver eq_taken."""
        self.event(self.plugin._eventcb_taken, serial=serial)

    def command(self, handler: Callable[[], "CommandResult"], **args: object) -> "CommandResult":
        """Run a command with arguments."""
        self.fake.args = args
        return handler()

    def fire_timer(self, name: str) -> None:
        """Fire and remove a one shot timer."""
        func, _, _ = self.fake.timers.pop(name)
        func()

    def reply_on(self) -> bool:
        """Return True when the reply triggers are on."""
        return all(self.fake.triggers[spec.name]["enabled"] for spec in REPLY_TRIGGERS)

    def sent_to_mud(self) -> list[str]:
        """What went to the mud."""
        return list(self.mud)


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Env:
    """A loaded plugin with drinking on and the carafe set as the container."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from aardwolf.hunger.plugin import _hunger

    clock = [1000.0]
    monkeypatch.setattr(_hunger, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    fake = FakeApi()
    plugin = _hunger.HungerPlugin.__new__(_hunger.HungerPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    built = Env(plugin, fake, clock)

    class FakeSend:
        def __init__(self, message: "NetworkData") -> None:
            self.message = message

        def __call__(self) -> None:
            for item in self.message:
                built.mud.append(str(item.line))
                fake.calls.append(("send", str(item.line)))
            built.owners.append(str(self.message.owner_id))

    monkeypatch.setattr(_hunger, "SendDataDirectlyToMud", FakeSend)
    plugin._phook_init_plugin()
    plugin._phook_initialize()
    plugin._client = built.notices.extend  # type: ignore[method-assign,assignment]
    fake.settings.update({"drink": True, "container": "Carafe"})
    return built


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.hunger" in {p["plugin_id"] for p in result.plugins}


def test_imports_no_other_plugin() -> None:
    """The plugin never imports another plugin."""
    root = Path(aardwolf.__file__).resolve().parent / "hunger"
    for path in root.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names = [node.module]
            for name in names:
                assert not name.startswith("aardwolf.") or name.startswith(
                    ("aardwolf.hunger", "aardwolf._libs")
                )
                assert not name.startswith("bastproxy.plugins.") or name.startswith(
                    (
                        "bastproxy.plugins._baseplugin",
                        "bastproxy.plugins.core.commands",
                        "bastproxy.plugins.core.events",
                    )
                )


def test_after_load(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """after_load adds every setting with its default, the triggers, and the reply group off."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from aardwolf.hunger.plugin import _hunger

    fake = FakeApi()
    plugin = _hunger.HungerPlugin.__new__(_hunger.HungerPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    plugin._phook_initialize()
    assert fake.settings == {
        "drink": False,
        "container": "",
        "cooldown": 60,
        "fillroom": "",
        "fillobject": "",
    }
    assert set(fake.validators) == {"cooldown"}
    assert {s.name for s in STAGE_TRIGGERS} | {s.name for s in REPLY_TRIGGERS} == set(
        fake.callbacks
    )
    for spec in STAGE_TRIGGERS:
        assert fake.triggers[spec.name]["enabled"] is True
    for spec in REPLY_TRIGGERS:
        assert fake.triggers[spec.name]["enabled"] is False
        assert fake.triggers[spec.name]["group"] == f"{PLUGIN_ID}.hunger_reply"
    assert fake.validators["cooldown"](0) is not None
    assert fake.validators["cooldown"](60) is None


def test_off_by_default(env: Env) -> None:
    """With drinking off a stage line fetches and sends nothing."""
    env.fake.settings["drink"] = False
    env.feed(HUNGRY)
    assert env.fake.calls == []
    assert env.mud == []


def test_container_in_a_bag(env: Env) -> None:
    """A stage line fetches, eq_taken sends the drink, and the put follows."""
    env.feed(VERY_THIRSTY)
    assert env.fake.calls == [("fetch", CARAFE)]
    assert env.mud == []
    assert TIMER_FETCH in env.fake.timers
    assert not env.reply_on()
    env.taken()
    assert env.fake.calls[1:] == [("send", f"gulp {CARAFE}"), ("put", CARAFE), ("group", True)]
    assert TIMER_FETCH not in env.fake.timers
    assert TIMER_REPLY in env.fake.timers
    assert env.reply_on()
    assert env.owners == [f"{PLUGIN_ID}:send"]


def test_container_in_inventory(env: Env) -> None:
    """In the inventory the drink goes out at once, with no fetch and no put."""
    env.fake.items[CARAFE]["container"] = "Inventory"
    env.feed(HUNGRY)
    assert env.mud == [f"gulp {CARAFE}"]
    assert [c for c in env.fake.calls if c[0] in ("fetch", "put")] == []
    assert env.reply_on()


def test_container_without_a_known_place_drinks_at_once(env: Env) -> None:
    """An item eq knows no container for is drunk from at once, with no put back."""
    env.fake.items[CARAFE]["container"] = None
    env.fake.settings["container"] = str(CARAFE)
    env.feed(HUNGRY)
    assert env.mud == [f"gulp {CARAFE}"]
    assert [c for c in env.fake.calls if c[0] in ("fetch", "put")] == []


def test_serial_setting(env: Env) -> None:
    """A setting of all digits is a serial, looked up with item.get."""
    env.fake.settings["container"] = str(CARAFE)
    env.feed(HUNGRY)
    assert env.fake.calls == [("fetch", CARAFE)]


def test_taken_for_another_serial_does_nothing(env: Env) -> None:
    env.feed(HUNGRY)
    env.taken(serial=5)
    assert env.mud == []
    assert env.plugin._pending is not None


def test_fetch_timeout(env: Env) -> None:
    """The pending action is dropped after the timeout, and a late eq_taken sends nothing."""
    env.feed(HUNGRY)
    assert env.fake.timers[TIMER_FETCH][1] == PENDING_TIMEOUT
    env.fire_timer(TIMER_FETCH)
    assert env.notices
    assert not env.plugin._busy()
    env.taken()
    assert env.mud == []
    assert not env.reply_on()


def test_reply_timeout_turns_the_reply_triggers_off(env: Env) -> None:
    env.fake.items[CARAFE]["container"] = "Inventory"
    env.feed(HUNGRY)
    assert env.reply_on()
    env.fire_timer(TIMER_REPLY)
    assert not env.reply_on()
    assert not env.plugin._busy()


def test_cooldown(env: Env) -> None:
    """Three lines inside the cooldown make one attempt; one after it attempts again."""
    env.fake.items[CARAFE]["container"] = "Inventory"
    env.feed(HUNGRY)
    env.feed(VERY_THIRSTY)
    env.feed(DEHYDRATED)
    assert env.mud == [f"gulp {CARAFE}"]
    env.feed(DRANK)
    env.clock[0] += 59
    env.feed(HUNGRY)
    assert len(env.mud) == 1
    env.clock[0] += 1
    env.feed(HUNGRY)
    assert len(env.mud) == 2


def test_cooldown_setting_is_read(env: Env) -> None:
    env.fake.items[CARAFE]["container"] = "Inventory"
    env.fake.settings["cooldown"] = 5
    env.feed(HUNGRY)
    env.feed(DRANK)
    env.clock[0] += 5
    env.feed(HUNGRY)
    assert len(env.mud) == 2


def test_line_while_pending_sends_nothing(env: Env) -> None:
    env.feed(HUNGRY)
    env.clock[0] += 1000
    env.feed(HUNGRY)
    assert env.fake.calls == [("fetch", CARAFE)]


def test_missing_container_gives_one_message(env: Env) -> None:
    """A missing container gives one message and no command, even after the cooldown."""
    env.fake.items.clear()
    env.feed(HUNGRY)
    assert len(env.notices) == 1
    assert env.fake.calls == []
    env.clock[0] += 1000
    env.feed(HUNGRY)
    env.feed(DEHYDRATED)
    assert len(env.notices) == 1
    assert env.fake.calls == []


def test_unset_container_is_missing(env: Env) -> None:
    env.fake.settings["container"] = ""
    env.feed(HUNGRY)
    assert len(env.notices) == 1
    assert env.mud == []


def test_setting_change_clears_the_block(env: Env) -> None:
    env.fake.items.clear()
    env.feed(HUNGRY)
    env.fake.items[CARAFE] = {"serial": CARAFE, "container": "Inventory", "name": "Carafe"}
    env.clock[0] += 1000
    env.feed(HUNGRY)
    assert env.mud == []
    env.fake.settings["container"] = "Carafe"
    env.plugin._eventcb_container_modified()
    env.feed(HUNGRY)
    assert env.mud == [f"gulp {CARAFE}"]


@pytest.mark.parametrize("handler", ["_eventcb_inventory_added", "_eventcb_put", "_eventcb_taken"])
def test_eq_event_for_the_item_clears_the_block(env: Env, handler: str) -> None:
    env.fake.items.clear()
    env.feed(HUNGRY)
    env.fake.items[CARAFE] = {"serial": CARAFE, "container": "Inventory", "name": "Carafe"}
    env.event(getattr(env.plugin, handler), serial=CARAFE)
    env.clock[0] += 1000
    env.feed(HUNGRY)
    assert env.mud == [f"gulp {CARAFE}"]


def test_eq_event_without_the_item_keeps_the_block(env: Env) -> None:
    env.fake.items.clear()
    env.feed(HUNGRY)
    env.event(env.plugin._eventcb_inventory_added, serial=7)
    env.clock[0] += 1000
    env.feed(HUNGRY)
    assert len(env.notices) == 1
    assert env.fake.calls == []


def test_empty_container(env: Env) -> None:
    """The empty reply blocks drinking, sets the flag and gives one message."""
    env.fake.items[CARAFE]["container"] = "Inventory"
    env.feed(HUNGRY)
    env.feed(EMPTY)
    assert env.plugin._empty is True
    assert len(env.notices) == 1
    assert "Sacramental Carafe is empty" in env.notices[0]
    assert not env.reply_on()
    env.clock[0] += 1000
    env.feed(HUNGRY)
    assert env.mud == [f"gulp {CARAFE}"]
    assert len(env.notices) == 1


def test_empty_stays_blocked_after_the_put_back(env: Env) -> None:
    """The put back raises eq events; they must not undo an empty container."""
    env.feed(HUNGRY)
    env.taken()
    env.feed(EMPTY)
    env.event(env.plugin._eventcb_put, serial=CARAFE)
    env.clock[0] += 1000
    env.feed(HUNGRY)
    assert env.mud == [f"gulp {CARAFE}"]


def test_empty_line_with_reply_triggers_off_does_nothing(env: Env) -> None:
    env.feed(EMPTY)
    assert env.plugin._empty is False
    assert env.notices == []


def test_drank_turns_the_reply_triggers_off(env: Env) -> None:
    env.fake.items[CARAFE]["container"] = "Inventory"
    env.feed(HUNGRY)
    env.feed(DRANK)
    assert not env.reply_on()
    assert TIMER_REPLY not in env.fake.timers
    assert not env.plugin._busy()


def test_gulp_reply_then_full_ends_the_wait_once(env: Env) -> None:
    """A gulp answers with one line and then "You are now full."; the wait ends once."""
    env.fake.items[CARAFE]["container"] = "Inventory"
    env.feed(HUNGRY)
    assert env.reply_on()
    env.feed(GULPED)
    assert not env.reply_on()
    assert TIMER_REPLY not in env.fake.timers
    assert not env.plugin._busy()
    env.feed(FULL)
    assert not env.reply_on()
    assert env.plugin._empty is False
    assert env.notices == []
    assert env.mud == [f"gulp {CARAFE}"]


def test_empty_after_a_gulp_blocks(env: Env) -> None:
    """The empty line still blocks drinking when the command was a gulp."""
    env.fake.items[CARAFE]["container"] = "Inventory"
    env.feed(HUNGRY)
    assert env.mud == [f"gulp {CARAFE}"]
    env.feed(EMPTY)
    assert env.plugin._empty is True
    env.clock[0] += 1000
    env.feed(HUNGRY)
    assert env.mud == [f"gulp {CARAFE}"]


def test_fillsource(env: Env) -> None:
    env.fake.gmcp["room.info.num"] = 1234
    result = env.command(env.plugin._command_fillsource, object="fountain", show=False)
    assert result.success is True
    assert env.fake.settings["fillroom"] == FILLROOM
    assert env.fake.settings["fillobject"] == "fountain"
    result = env.command(env.plugin._command_fillsource, object="", show=False)
    assert env.fake.settings["fillobject"] == ""


@pytest.mark.parametrize("num", [None, -1, 0])
def test_fillsource_refuses_an_unknown_room(env: Env, num: int | None) -> None:
    env.fake.gmcp["room.info.num"] = num
    result = env.command(env.plugin._command_fillsource, object="", show=False)
    assert result.success is False
    assert env.fake.settings["fillroom"] == ""


def test_fillsource_show(env: Env) -> None:
    env.fake.settings.update({"fillroom": FILLROOM, "fillobject": "fountain"})
    result = env.command(env.plugin._command_fillsource, object="", show=True)
    assert result.message == [f"Fill room: {FILLROOM}", "Fill object: fountain"]
    assert env.fake.settings["fillobject"] == "fountain"


def fill_setup(env: Env, here: int | str = 1234, obj: str = "") -> None:
    env.fake.settings.update({"fillroom": FILLROOM, "fillobject": obj})
    env.fake.gmcp["room.info.num"] = here


@pytest.mark.parametrize(
    ("obj", "command"), [("", f"fill {CARAFE}"), ("fountain", f"fill {CARAFE} fountain")]
)
def test_fill_in_the_room(env: Env, obj: str, command: str) -> None:
    fill_setup(env, obj=obj)
    result = env.command(env.plugin._command_fill)
    assert result.success is True
    assert env.fake.calls == [("fetch", CARAFE)]
    env.taken()
    assert env.mud == [command]
    assert ("put", CARAFE) in env.fake.calls
    assert env.reply_on()
    assert ("walk.start", FILLROOM) not in env.fake.calls


def test_filled_reply_clears_empty_and_block(env: Env) -> None:
    env.fake.items[CARAFE]["container"] = "Inventory"
    env.feed(HUNGRY)
    env.feed(EMPTY)
    fill_setup(env)
    env.command(env.plugin._command_fill)
    env.feed(FILLED)
    assert env.plugin._empty is False
    assert env.plugin._blocked is None
    assert not env.reply_on()
    env.clock[0] += 1000
    env.feed(HUNGRY)
    assert env.mud[-1] == f"gulp {CARAFE}"


def test_no_source_keeps_empty_and_tells_the_client(env: Env) -> None:
    env.fake.items[CARAFE]["container"] = "Inventory"
    env.feed(HUNGRY)
    env.feed(EMPTY)
    env.notices.clear()
    fill_setup(env)
    env.command(env.plugin._command_fill)
    env.feed(NOSOURCE)
    assert env.plugin._empty is True
    assert any("no liquid source" in n for n in env.notices)
    assert not env.reply_on()


def test_fill_elsewhere_walks_then_fills_once(env: Env) -> None:
    fill_setup(env, here=55)
    result = env.command(env.plugin._command_fill)
    assert result.success is True
    assert env.fake.calls == [("walk.start", FILLROOM)]
    assert env.mud == []
    env.event(env.plugin._eventcb_walk_started, target=FILLROOM)
    assert env.plugin._fill_walk == FILLROOM
    env.event(env.plugin._eventcb_walk_done, target="999")
    assert env.fake.calls == [("walk.start", FILLROOM)]
    env.event(env.plugin._eventcb_walk_done, target=FILLROOM)
    assert env.fake.calls[1:] == [("fetch", CARAFE)]
    env.taken()
    assert env.mud == [f"fill {CARAFE}"]
    env.event(env.plugin._eventcb_walk_done, target=FILLROOM)
    assert env.mud == [f"fill {CARAFE}"]


@pytest.mark.parametrize("reason", ["no path", "stopped"])
def test_walk_failed_is_reported(env: Env, reason: str) -> None:
    fill_setup(env, here=55)
    env.command(env.plugin._command_fill)
    env.event(env.plugin._eventcb_walk_failed, target=FILLROOM, reason=reason, uid="55")
    assert any(reason in n for n in env.notices)
    assert env.plugin._fill_walk is None
    env.event(env.plugin._eventcb_walk_done, target=FILLROOM)
    assert env.mud == []
    assert env.fake.calls == [("walk.start", FILLROOM)]


def test_walk_failed_for_another_target_is_ignored(env: Env) -> None:
    fill_setup(env, here=55)
    env.command(env.plugin._command_fill)
    env.event(env.plugin._eventcb_walk_failed, target="999", reason="stopped", uid="55")
    assert env.notices == []
    assert env.plugin._fill_walk == FILLROOM


def test_walk_started_elsewhere_clears_the_pending_fill(env: Env) -> None:
    fill_setup(env, here=55)
    env.command(env.plugin._command_fill)
    env.event(env.plugin._eventcb_walk_started, target="999")
    assert env.plugin._fill_walk is None
    env.event(env.plugin._eventcb_walk_done, target=FILLROOM)
    assert env.mud == []


def test_fill_failures_report_and_send_nothing(env: Env) -> None:
    fill_setup(env, here=55)
    env.fake.walk_ok = False
    result = env.command(env.plugin._command_fill)
    assert result.success is False
    assert env.plugin._fill_walk is None
    env.fake.walk_ok = True
    env.fake.mapper_loaded = False
    result = env.command(env.plugin._command_fill)
    assert "mapper is not loaded" in result.message[0]
    env.fake.mapper_loaded = True
    env.fake.mapped = set()
    result = env.command(env.plugin._command_fill)
    assert "not mapped" in result.message[0]
    env.fake.mapped = {FILLROOM}
    env.fake.walk_state = "walking"
    result = env.command(env.plugin._command_fill)
    assert "already under way" in result.message[0]
    assert env.fake.calls == [("walk.start", FILLROOM)]
    assert env.mud == []


def test_fill_failures_without_settings(env: Env) -> None:
    result = env.command(env.plugin._command_fill)
    assert result.success is False
    assert "fill room" in result.message[0]
    env.fake.settings["fillroom"] = FILLROOM
    env.fake.settings["container"] = ""
    result = env.command(env.plugin._command_fill)
    assert "container" in result.message[0]
    assert env.fake.calls == []


def test_fill_with_a_missing_container_in_the_room(env: Env) -> None:
    fill_setup(env)
    env.fake.items.clear()
    result = env.command(env.plugin._command_fill)
    assert result.success is False
    assert env.mud == []


def move_into(env: Env, room: int) -> None:
    env.event(env.plugin._eventcb_move_room, to={"num": room}, **{"from": {"num": 55}})


def test_room_entry_fills_when_empty(env: Env) -> None:
    fill_setup(env)
    env.plugin._empty = True
    move_into(env, 1234)
    assert env.fake.calls == [("fetch", CARAFE)]
    env.taken()
    assert env.mud == [f"fill {CARAFE}"]


def test_room_entry_without_empty_or_in_another_room_does_nothing(env: Env) -> None:
    fill_setup(env)
    move_into(env, 1234)
    env.plugin._empty = True
    move_into(env, 77)
    assert env.fake.calls == []


@pytest.mark.parametrize("move_first", [True, False])
def test_arrival_fills_once_in_either_order(env: Env, move_first: bool) -> None:
    fill_setup(env, here=55)
    env.plugin._empty = True
    env.command(env.plugin._command_fill)
    env.fake.gmcp["room.info.num"] = 1234
    if move_first:
        move_into(env, 1234)
        env.event(env.plugin._eventcb_walk_done, target=FILLROOM)
    else:
        env.event(env.plugin._eventcb_walk_done, target=FILLROOM)
        move_into(env, 1234)
    env.taken()
    assert env.mud == [f"fill {CARAFE}"]
    assert [c for c in env.fake.calls if c[0] == "fetch"] == [("fetch", CARAFE)]


def test_no_source_after_an_automatic_fill_names_the_stored_room(env: Env) -> None:
    fill_setup(env)
    env.plugin._empty = True
    move_into(env, 1234)
    env.taken()
    env.feed(NOSOURCE)
    assert any("stored fill room" in n for n in env.notices)


def test_never_travels_by_itself(env: Env) -> None:
    """No trigger, timer or event handler starts a walk."""
    fill_setup(env, here=55)
    env.plugin._empty = True
    lines = [
        HUNGRY,
        VERY_THIRSTY,
        DEHYDRATED,
        DRANK,
        EMPTY,
        FILLED,
        NOSOURCE,
    ]
    for line in lines:
        env.feed(line)
        env.clock[0] += 1000
    for name in list(env.fake.timers):
        env.fire_timer(name)
    plugin = env.plugin
    env.taken()
    env.event(plugin._eventcb_put, serial=CARAFE)
    env.event(plugin._eventcb_inventory_added, serial=CARAFE)
    env.event(plugin._eventcb_container_modified)
    env.event(plugin._eventcb_walk_started, target=FILLROOM)
    env.event(plugin._eventcb_walk_done, target=FILLROOM)
    env.event(plugin._eventcb_walk_failed, target=FILLROOM, reason="stopped")
    env.event(plugin._eventcb_disconnect)
    plugin._empty = True
    move_into(env, 1234)
    move_into(env, 77)
    assert ("walk.start", FILLROOM) not in env.fake.calls
    assert not [c for c in env.fake.calls if c[0] == "walk.start"]


def test_walk_start_is_only_called_from_the_fill_command_chain() -> None:
    """The walk.start constant is used in one method, which only the fill command calls."""
    path = Path(aardwolf.__file__).resolve().parent / "hunger" / "plugin" / "_hunger.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    users: set[str] = set()
    callers: set[str] = set()
    for func in ast.walk(tree):
        if not isinstance(func, ast.FunctionDef):
            continue
        for node in ast.walk(func):
            if isinstance(node, ast.Name) and node.id == "API_WALK_START":
                users.add(func.name)
            if isinstance(node, ast.Attribute) and node.attr == "_start_fill_walk":
                callers.add(func.name)
    assert users == {"_start_fill_walk"}
    assert callers == {"_command_fill"}
    libs = Path(aardwolf.__file__).resolve().parent / "hunger" / "libs" / "_hunger.py"
    assert API_WALK_START in libs.read_text(encoding="utf-8")


def test_disconnect_clears_everything(env: Env) -> None:
    fill_setup(env, here=55)
    env.command(env.plugin._command_fill)
    env.fake.items[CARAFE]["container"] = "Inventory"
    env.feed(HUNGRY)
    assert env.plugin._busy()
    env.event(env.plugin._eventcb_disconnect)
    assert not env.plugin._busy()
    assert env.plugin._fill_walk is None
    assert env.plugin._last is None
    assert env.fake.timers == {}
    assert not env.reply_on()
    env.event(env.plugin._eventcb_walk_done, target=FILLROOM)
    assert len(env.mud) == 1


def test_status(env: Env) -> None:
    result = env.command(env.plugin._command_status)
    assert result.success is True
    assert result.message[0] == "Drinking: on"
    assert f"serial {CARAFE}" in result.message[1]


def test_uninitialize_removes_timers(env: Env) -> None:
    env.feed(HUNGRY)
    env.plugin._phook_uninitialize()
    assert env.fake.timers == {}


def test_event_names() -> None:
    """The names listened to are the ones the other plugins raise."""
    assert EVENT_EQ_TAKEN.endswith("eq_taken")
    assert EVENT_EQ_PUT.endswith("eq_put")
    assert EVENT_EQ_INVENTORY_ADDED.endswith("eq_inventory_added")
    assert EVENT_MOVE_ROOM.endswith("move_room")
    assert EVENT_DISCONNECT.endswith("muddisconnect")
    assert EVENT_WALK_STARTED.endswith("walk_started")
    assert EVENT_WALK_DONE.endswith("walk_done")
    assert EVENT_WALK_FAILED.endswith("walk_failed")
