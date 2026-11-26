"""Tests for the Aardwolf mapper plugin, with a stubbed API."""

import asyncio
from collections.abc import Callable, Coroutine, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import MagicMock

import pytest
from mapper_support import FakeEq

import aardwolf
from aardwolf.mapper.libs import (
    CEXIT_COLUMNS,
    CEXIT_MAX_TIMEOUT,
    CEXIT_MIN_TIMEOUT,
    CEXIT_TIMEOUT,
    NOPORTAL_REGEX,
    NORECALL_REGEX,
    PLACE_COLUMNS,
    PORTAL_COLUMNS,
    portal_marker,
)

if TYPE_CHECKING:
    from bastproxy.plugins.core.commands import CommandResult

    from aardwolf.mapper.plugin._mapper import MapperPlugin

PLUGIN_ID = "plugins.aardwolf.mapper"
MAPPER = "plugins.client.mapper"
WEB = "plugins.core.web"
ROOM_A: dict[str, Any] = {
    "num": 1234,
    "name": "@RA Room@w",
    "zone": "aylor",
    "terrain": "city",
    "details": "bank",
    "exits": {"n": 1235, "s": -1},
    "coord": {"id": 0, "x": 30, "y": 19, "cont": 0},
}
ROOM_B: dict[str, Any] = {**ROOM_A, "num": 1235, "exits": {"s": 1234}}
ROOM_C: dict[str, Any] = {**ROOM_A, "num": 1236, "zone": "other"}


class FakeApi:
    """A stand-in for the bastproxy API that records what the plugin calls."""

    def __init__(self) -> None:
        self.gmcp: dict[str, Any] = {}
        self.record: dict[str, Any] = {}
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self.rooms: dict[str, dict[str, Any]] = {}
        self.areas: dict[str, dict[str, Any]] = {}
        self.trigger_adds: list[tuple[str, str]] = []
        self.trigger_regs: dict[str, Callable[..., Any]] = {}
        self.callbacks: dict[str, Callable[..., Any]] = {}
        self.current: str | None = None
        self.args: dict[str, Any] = {}
        self.tasks: list[Coroutine[Any, Any, None]] = []
        self.mud: list[list[str]] = []
        self.web = True
        self.eq = FakeEq()
        self.routes: dict[str, tuple[Callable[..., Any], str, list[dict[str, str]]]] = {}
        self.route_result: str | None = "/aardwolf/mapper"
        self.removed: list[str] = []
        self.settings: dict[str, Any] = {}
        self.validators: dict[str, Callable[..., Any]] = {}

    def _route_add(
        self,
        owner: str,
        subpath: str,
        handler: Callable[..., Any],
        title: str,
        columns: list[dict[str, str]],
    ) -> str | None:
        self.routes[subpath] = (handler, title, columns)
        return self.route_result

    def called(self, name: str) -> list[tuple[Any, ...]]:
        """Return the arguments of each call of an API."""
        return [args for api, args, _ in self.calls if api == name]

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""

        def record(*args: object, **kwargs: object) -> object:
            self.calls.append((name, args, kwargs))
            return table[name](*args, **kwargs)

        table: dict[str, Callable[..., Any]] = {
            f"{MAPPER}:room.add": lambda room: True,
            f"{MAPPER}:room.get": lambda uid: self.rooms.get(uid),
            f"{MAPPER}:room.current.set": self._set_current,
            f"{MAPPER}:room.current.get": lambda: self.current,
            f"{MAPPER}:exit.add": lambda *args: True,
            f"{MAPPER}:exit.remove": lambda *args: True,
            "libs.asynch:task.add": lambda coro, name: self.tasks.append(coro),
            "plugins.core.commands:command.current.args.get": lambda: self.args,
            "plugins.core.settings:setting.add": self._setting_add,
            "plugins.core.settings:setting.get": lambda pid, name: self.settings[name],
            f"{MAPPER}:area.add": lambda **kwargs: True,
            f"{MAPPER}:area.get": lambda uid: self.areas.get(uid),
            f"{MAPPER}:requirement.register": self._register("requirement"),
            f"{MAPPER}:requirement.unregister": lambda owner: None,
            f"{MAPPER}:movement.register": self._register("movement"),
            f"{MAPPER}:movement.unregister": lambda owner: None,
            "libs.api:api.exists": lambda name: (
                (self.web and name.startswith(WEB)) or (self.eq.present and name in self.eq.table())
            ),
            **self.eq.table(),
            f"{WEB}:web.route.add": self._route_add,
            f"{WEB}:web.route.remove": lambda owner: self.removed.append(owner),
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "libs.net.protocols:gmcp.value.get": self.gmcp.get,
            "libs.net.protocols:gmcp.send": lambda message: None,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
            "plugins.core.colors:colorcode.escape": lambda text: text,
            "plugins.core.colors:colorcode.strip": lambda text: text.replace("@R", "").replace(
                "@w", ""
            ),
        }
        return record if name in table else table[name]

    def _setting_add(self, pid: str, name: str, default: object, *a: object, **kw: object) -> None:
        self.settings.setdefault(name, default)
        if "validator" in kw:
            self.validators[name] = cast("Callable[..., Any]", kw["validator"])

    def _set_current(self, uid: str) -> None:
        self.current = uid

    def _register(self, kind: str) -> Callable[[str, Callable[..., Any]], None]:
        def register(owner: str, callback: Callable[..., Any]) -> None:
            assert owner == PLUGIN_ID
            self.callbacks[kind] = callback

        return register

    def _trigger_add(self, name: str, regex: str, **kwargs: object) -> SimpleNamespace:
        self.trigger_adds.append((name, regex))
        return SimpleNamespace(success=True, trigger=SimpleNamespace(trigger_id=name))

    def _trigger_register(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        self.trigger_regs[trigger_id] = func
        return True


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: "MapperPlugin", fake: FakeApi, sent: list[list[str]]) -> None:
        self.plugin = plugin
        self.fake = fake
        self.sent = sent

    def move(self, room: dict[str, Any]) -> None:
        """The character moves to a room."""
        self.fake.record = {"to": room}
        self.plugin._eventcb_move_room()

    def room_info(self, room: dict[str, Any]) -> None:
        """The MUD sends a Room.Info message."""
        self.fake.record = {"data": room}
        self.plugin._eventcb_room_info()

    def run_tasks(self) -> None:
        """Run the queued tasks in order."""
        while self.fake.tasks:
            asyncio.run(self.fake.tasks.pop(0))

    def area_info(self, data: object) -> None:
        """The MUD sends a Room.Area message."""
        self.fake.record = {"data": data}
        self.plugin._eventcb_room_area()


def build(fake: FakeApi, sent: list[list[str]]) -> "MapperPlugin":
    """Build and load a plugin."""
    from aardwolf.mapper.plugin import _mapper

    plugin = _mapper.MapperPlugin.__new__(_mapper.MapperPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    plugin._client = sent.append  # type: ignore[method-assign,assignment]
    plugin._mud = fake.mud.append  # type: ignore[method-assign,assignment]
    plugin._phook_init_plugin()
    plugin._phook_initialize()
    return plugin


def make(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, gmcp: dict[str, Any]) -> Env:
    """Build an Env with a GMCP cache."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    fake = FakeApi()
    fake.gmcp.update(gmcp)
    sent: list[list[str]] = []
    return Env(build(fake, sent), fake, sent)


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """A loaded plugin with an empty GMCP cache."""
    made = make(monkeypatch, tmp_path, {})
    yield made
    for task in made.fake.tasks:
        task.close()


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader finds the plugin and its dependencies include the mapper and move."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.mapper" in {p["plugin_id"] for p in result.plugins}
    from aardwolf.mapper import PLUGIN_DEPENDENCIES

    assert "plugins.client.mapper" in PLUGIN_DEPENDENCIES
    assert "plugins.aardwolf.move" in PLUGIN_DEPENDENCIES


def test_after_load_registers(env: Env) -> None:
    """The triggers and both callbacks are set up."""
    assert env.fake.trigger_adds == [("noportal", NOPORTAL_REGEX), ("norecall", NORECALL_REGEX)]
    assert set(env.fake.trigger_regs) == {"noportal", "norecall"}
    assert set(env.fake.callbacks) == {"requirement", "movement"}


def test_seed_from_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A room in the GMCP cache at load is stored and made current."""
    env = make(monkeypatch, tmp_path, {"room.info": ROOM_A})
    room = env.fake.called(f"{MAPPER}:room.add")[0][0]
    assert room["uid"] == "1234"
    assert room["name"] == "A Room"
    assert env.fake.called(f"{MAPPER}:room.current.set") == [("1234",)]


def test_empty_cache_does_nothing(env: Env) -> None:
    """With no cached room nothing is stored."""
    assert not env.fake.called(f"{MAPPER}:room.add")
    assert not env.fake.called(f"{MAPPER}:room.current.set")


def test_first_room_info_then_ignored(env: Env) -> None:
    """The first room.info is taken; later ones are left to move_room."""
    env.room_info(ROOM_A)
    assert env.fake.called(f"{MAPPER}:room.current.set") == [("1234",)]
    env.room_info(ROOM_B)
    env.room_info(ROOM_A)
    assert len(env.fake.called(f"{MAPPER}:room.add")) == 1


def test_move_room(env: Env) -> None:
    """A move stores the room with its exits and makes it current, once."""
    env.move(ROOM_A)
    room = env.fake.called(f"{MAPPER}:room.add")[0][0]
    assert room["exits"] == {"n": "1235", "s": "-1"}
    assert env.fake.called(f"{MAPPER}:room.current.set") == [("1234",)]
    env.move(ROOM_A)
    assert len(env.fake.called(f"{MAPPER}:room.add")) == 1
    env.move(ROOM_B)
    assert env.fake.called(f"{MAPPER}:room.current.set")[-1] == ("1235",)


def test_stored_flags_survive(env: Env) -> None:
    """The flags of the stored room are sent again so room.add does not wipe them."""
    env.fake.rooms["1234"] = {"uid": "1234", "flags": ["noportal"]}
    env.move(ROOM_A)
    assert env.fake.called(f"{MAPPER}:room.add")[0][0]["flags"] == ["noportal"]


def test_nomap_room(env: Env) -> None:
    """A room with num -1 leads to no calls."""
    env.move({**ROOM_A, "num": -1})
    assert not env.fake.called(f"{MAPPER}:room.add")
    assert not env.fake.called(f"{MAPPER}:room.current.set")
    assert not env.fake.called("libs.net.protocols:gmcp.send")


def test_area_requested_once(env: Env) -> None:
    """An unknown area is requested once; a known one never."""
    env.move(ROOM_A)
    env.move({**ROOM_B, "zone": "aylor"})
    assert env.fake.called("libs.net.protocols:gmcp.send") == [("request area",)]
    env.fake.areas["other"] = {"uid": "other"}
    env.move(ROOM_C)
    assert len(env.fake.called("libs.net.protocols:gmcp.send")) == 1


def test_area_reply(env: Env) -> None:
    """A room.area reply is stored and clears the pending zone."""
    env.move(ROOM_A)
    env.area_info({"id": "aylor", "name": "Aylor", "col": "@W", "flags": "virtual"})
    call = next(kw for api, _, kw in env.fake.calls if api == f"{MAPPER}:area.add")
    assert call == {
        "uid": "aylor",
        "name": "Aylor",
        "flags": ["virtual"],
        "details": {"col": "@W"},
    }
    assert "aylor" not in env.plugin._requested_areas
    env.area_info({"name": "no id"})
    assert len([1 for api, _, _ in env.fake.calls if api == f"{MAPPER}:area.add"]) == 1


def test_disconnect_resets(env: Env) -> None:
    """After a disconnect the room and the area are handled again."""
    env.room_info(ROOM_A)
    env.plugin._eventcb_disconnect()
    env.room_info(ROOM_A)
    assert len(env.fake.called(f"{MAPPER}:room.add")) == 2
    assert len(env.fake.called("libs.net.protocols:gmcp.send")) == 2


@pytest.mark.parametrize(("trigger", "flag"), [("noportal", "noportal"), ("norecall", "norecall")])
def test_flag_triggers(env: Env, trigger: str, flag: str) -> None:
    """A flag trigger marks the current room, without exits, once."""
    env.fake.trigger_regs[trigger]()
    assert not env.fake.called(f"{MAPPER}:room.add")
    env.move(ROOM_A)
    env.fake.rooms["1234"] = {"uid": "1234", "name": "A Room", "area": "aylor", "flags": []}
    before = len(env.fake.called(f"{MAPPER}:room.add"))
    env.fake.trigger_regs[trigger]()
    added = env.fake.called(f"{MAPPER}:room.add")
    assert len(added) == before + 1
    assert flag in added[-1][0]["flags"]
    assert "exits" not in added[-1][0]
    assert env.sent == [[f"Mapper: room 1234 marked {flag}"]]
    env.fake.rooms["1234"]["flags"] = [flag]
    env.fake.trigger_regs[trigger]()
    assert len(env.fake.called(f"{MAPPER}:room.add")) == before + 1


def test_flag_trigger_unstored_room(env: Env) -> None:
    """A room the mapper does not have is left alone."""
    env.move(ROOM_A)
    env.fake.rooms.clear()
    before = len(env.fake.called(f"{MAPPER}:room.add"))
    env.fake.trigger_regs["noportal"]()
    assert len(env.fake.called(f"{MAPPER}:room.add")) == before


def test_requirement_callback(env: Env) -> None:
    """The requirement callback reads the level and tier from GMCP."""
    callback = env.fake.callbacks["requirement"]
    env.fake.gmcp.update({"char.status.level": 50, "char.base.tier": 0})
    exit_dict = {"fromuid": "1", "dir": "n"}
    assert not callback({"level": 100}, exit_dict)
    assert callback({"level": 50}, exit_dict)
    assert not callback({"tier": 1}, exit_dict)
    env.fake.gmcp["char.base.tier"] = 1
    assert callback({"tier": 1}, exit_dict)


def test_movement_callback(env: Env) -> None:
    """The movement callback builds speedwalks."""
    steps = [{"fromuid": "1", "dir": d} for d in ("n", "n", "n", "e", "e")]
    assert env.fake.callbacks["movement"](steps) == ["run 3n2e"]


def test_room_mismatch_event(env: Env) -> None:
    """A mismatch event tells the client the uid, the area change and the purge hint."""
    env.fake.record = {"uid": "1234", "differences": {"area": ("old", "new")}}
    env.plugin._eventcb_room_mismatch()
    text = "\n".join(env.sent[0])
    assert "1234" in text
    assert "old -> new" in text
    assert "purge -a old" in text


def test_room_mismatch_name_only(env: Env) -> None:
    """A name-only mismatch is shown, and its text goes through colorcode.escape."""
    env.fake.record = {"uid": "1234", "differences": {"name": ("Old", "New")}}
    env.plugin._eventcb_room_mismatch()
    assert "  name: Old -> New" in env.sent[0]
    assert env.fake.called("plugins.core.colors:colorcode.escape")


def test_area_reply_sends_no_room_request(env: Env) -> None:
    """The area reply stores the area; no room is requested again (#157)."""
    env.move(ROOM_A)
    env.area_info({"id": "aylor", "name": "Aylor"})
    assert env.fake.called("libs.net.protocols:gmcp.send") == [("request area",)]
    assert env.fake.called(f"{MAPPER}:area.add")


def test_area_reply_without_room_sends_nothing(env: Env) -> None:
    """An area reply before any room is stored and requests nothing."""
    env.area_info({"id": "aylor", "name": "Aylor"})
    assert not env.fake.called("libs.net.protocols:gmcp.send")
    assert env.fake.called(f"{MAPPER}:area.add")


def test_uninitialize(env: Env) -> None:
    """Both callbacks are taken back."""
    env.plugin._phook_uninitialize()
    assert env.fake.called(f"{MAPPER}:requirement.unregister") == [(PLUGIN_ID,)]
    assert env.fake.called(f"{MAPPER}:movement.unregister") == [(PLUGIN_ID,)]


CEXIT = "open north;wait(2);north"


@pytest.fixture
def delays(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Make asyncio.sleep return at once and record the delays."""
    seen: list[float] = []

    async def fake_sleep(delay: float, result: object = None) -> None:
        seen.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    return seen


def start_cexit(env: Env, **args: object) -> "CommandResult":
    """Stand in room A, and run the cexit command."""
    env.move(ROOM_A)
    env.fake.rooms["1234"] = {"uid": "1234", "name": "A Room", "area": "aylor", "flags": []}
    env.fake.args = {
        "command": [CEXIT],
        "level": 50,
        "timeout": 0,
        "touid": None,
        "fromuid": None,
        **args,
    }
    result: CommandResult = env.plugin._command_cexit()
    return result


def test_cexit_records_on_arrival(env: Env, delays: list[float]) -> None:
    """The first part is sent at once, the rest after the wait; the new room stores the exit."""
    result = start_cexit(env)
    assert result.success
    assert env.fake.mud == [["open north"]]
    assert len(env.fake.tasks) == 2
    env.move(ROOM_B)
    assert env.fake.called(f"{MAPPER}:exit.add") == [("1234", CEXIT, "1235", 1, {"level": 50})]
    assert env.sent[-1] == ["Mapper: custom exit 1234 (open north;wait(2);north) -> 1235"]
    env.run_tasks()
    assert env.fake.mud == [["open north"], ["north"]]
    assert delays == [2.0, 7.0]
    assert env.plugin._pending_cexit is None
    assert not any("no new room" in line for chunk in env.sent for line in chunk)


def test_cexit_timeout(env: Env, delays: list[float]) -> None:
    """With no new room the timeout (default 5 plus the waits) clears the record and reports."""
    start_cexit(env)
    env.run_tasks()
    assert delays == [2.0, 7.0]
    assert env.plugin._pending_cexit is None
    assert "no new room" in env.sent[-1][0]
    assert not env.fake.called(f"{MAPPER}:exit.add")


def test_cexit_timeout_setting_is_the_default_wait(env: Env, delays: list[float]) -> None:
    """The cexittimeout setting replaces the 5 second default; an explicit -T wins."""
    assert env.fake.settings["cexittimeout"] == CEXIT_TIMEOUT
    env.fake.settings["cexittimeout"] = 9
    start_cexit(env)
    env.run_tasks()
    assert delays == [2.0, 11.0]
    env.plugin._pending_cexit = None
    delays.clear()
    start_cexit(env, timeout=3)
    env.run_tasks()
    assert delays == [2.0, 5.0]


def test_cexit_timeout_setting_is_validated(env: Env) -> None:
    """The setting stays inside the minimum and maximum of the command."""
    check = env.fake.validators["cexittimeout"]
    assert check(CEXIT_MIN_TIMEOUT) is None
    assert check(CEXIT_MAX_TIMEOUT) is None
    assert check(CEXIT_MIN_TIMEOUT - 1) is not None
    assert check(CEXIT_MAX_TIMEOUT + 1) is not None
    assert check("5") is not None


def test_cexit_same_room_is_ignored(env: Env) -> None:
    """Arriving in the room it left does not record the exit."""
    start_cexit(env)
    env.plugin._finish_cexit("1234")
    assert env.plugin._pending_cexit is not None


def test_cexit_refusals(env: Env) -> None:
    """Unknown room, a second recording, a bad wait and a bad timeout send nothing."""
    env.fake.args = {"command": ["go"], "level": 0, "timeout": 0, "touid": None, "fromuid": None}
    assert not env.plugin._command_cexit().success
    assert start_cexit(env).success
    assert not env.plugin._command_cexit().success
    env.plugin._pending_cexit = None
    env.fake.mud.clear()
    for bad in ({"command": ["go;wait(41)"]}, {"command": [" "]}, {"timeout": 1}, {"timeout": 41}):
        env.fake.args = {**env.fake.args, **bad}
        assert not env.plugin._command_cexit().success
    assert env.fake.mud == []
    assert env.plugin._pending_cexit is None


def test_cexit_direct(env: Env) -> None:
    """With -t the exit is stored at once and nothing is sent."""
    env.fake.rooms["1"] = {"uid": "1"}
    env.fake.rooms["2"] = {"uid": "2"}
    env.fake.args = {"command": ["go"], "level": 0, "timeout": 0, "touid": "2", "fromuid": "1"}
    assert env.plugin._command_cexit().success
    assert env.fake.called(f"{MAPPER}:exit.add") == [("1", "go", "2", 1, None)]
    assert env.fake.mud == []
    for args in ({"fromuid": "9"}, {"touid": "9"}, {"touid": "1"}):
        env.fake.args = {**env.fake.args, **args}
        assert not env.plugin._command_cexit().success
    assert len(env.fake.called(f"{MAPPER}:exit.add")) == 1


def walk(env: Env) -> list[str]:
    """Run the movement callback on a walk with a waited cexit in the middle."""
    steps = [
        {"fromuid": "1", "dir": "n"},
        {"fromuid": "1", "dir": "open door;wait(2);e"},
        {"fromuid": "1", "dir": "s"},
    ]
    first: list[str] = env.fake.callbacks["movement"](steps)
    return first


def test_movement_waits(env: Env, delays: list[float]) -> None:
    """The callback returns the first chunk; the rest is sent after the delay."""
    assert walk(env) == ["n", "open door"]
    env.run_tasks()
    assert env.fake.mud == [["e", "s"]]
    assert delays == [2.0]
    assert env.sent == [["Mapper: waiting 2 seconds"]]


@pytest.mark.parametrize("cancel", ["move", "failed", "disconnect", "uninitialize"])
def test_movement_waits_cancelled(env: Env, delays: list[float], cancel: str) -> None:
    """A new move, a failed walk, a disconnect or an unload stop the waiting commands."""
    walk(env)
    if cancel == "move":
        assert env.fake.callbacks["movement"]([{"fromuid": "1", "dir": "n"}]) == ["n"]
    elif cancel == "failed":
        env.plugin._eventcb_walk_failed()
    elif cancel == "disconnect":
        env.plugin._eventcb_disconnect()
    else:
        env.plugin._phook_uninitialize()
    env.run_tasks()
    assert env.fake.mud == []


def test_disconnect_drops_pending_cexit(env: Env, delays: list[float]) -> None:
    """A disconnect forgets the custom exit being recorded."""
    start_cexit(env)
    env.plugin._eventcb_disconnect()
    assert env.plugin._pending_cexit is None
    env.run_tasks()
    assert not any("no new room" in line for chunk in env.sent for line in chunk)


def test_web_routes_are_added(env: Env) -> None:
    """Loading adds the three table pages with their column specs."""
    routes = env.fake.routes
    assert set(routes) == {"portals", "cexits", "places"}
    assert routes["portals"][2] == PORTAL_COLUMNS
    assert routes["cexits"][2] == CEXIT_COLUMNS
    assert routes["places"][2] == PLACE_COLUMNS
    assert routes["portals"][0] == env.plugin._web_portals
    assert len(env.fake.called("plugins.core.web:web.route.add")) == 3
    assert all(call[0] == PLUGIN_ID for call in env.fake.called("plugins.core.web:web.route.add"))


def test_no_routes_without_the_web_plugin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """With no web.route.add API nothing is added, and unloading removes nothing."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    fake = FakeApi()
    fake.web = False
    plugin = build(fake, [])
    assert fake.routes == {}
    plugin._phook_uninitialize()
    assert fake.removed == []


def test_a_refused_route_does_not_raise(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The web plugin returns None for a refused route; loading goes on."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    fake = FakeApi()
    fake.route_result = None
    build(fake, [])
    assert len(fake.routes) == 3


def test_unload_removes_the_routes(env: Env) -> None:
    """Unloading takes the plugin's routes down."""
    env.plugin._phook_uninitialize()
    assert env.fake.removed == [PLUGIN_ID]


def test_web_dependency() -> None:
    """The plugin depends on the core web plugin."""
    import aardwolf.mapper as package

    assert "plugins.core.web" in package.PLUGIN_DEPENDENCIES


# portal items

PORTAL_ARGS: dict[str, Any] = {"command": ["7"], "level": None, "touid": None, "recall": False}
ENTER = ["enter"]


def stock_eq(env: Env, *, previous: bool = True) -> None:
    """Item 7 is a portal in bag 1000; the portal slot holds item 3 when `previous`."""
    env.fake.eq.add(7, "a swirling portal", level=50, container="1000")
    env.fake.eq.add(3, "a ring", itype=7, container="Worn")
    env.fake.eq.lands = "portal"  # eq sees the portal land in the portal slot
    if previous:
        env.fake.eq.worn["portal"] = 3


def start_portal(env: Env, **args: object) -> "CommandResult":
    """Stand in room A with the portal in a bag, and run the portal command on it."""
    env.move(ROOM_A)
    env.fake.rooms["1234"] = {"uid": "1234", "name": "A Room", "area": "aylor", "flags": []}
    env.fake.args = {**PORTAL_ARGS, **args}
    result: CommandResult = env.plugin._command_portal()
    return result


def exits_added(env: Env) -> list[tuple[Any, ...]]:
    """Return the arguments of each exit.add call."""
    return env.fake.called(f"{MAPPER}:exit.add")


def test_portal_item_records_on_arrival(env: Env) -> None:
    """The portal is held in place of the ring, entered, stored on arrival and put back."""
    stock_eq(env)
    result = start_portal(env)
    assert result.success
    assert env.fake.mud == [ENTER]
    assert env.fake.eq.calls == [("equip", 7)]
    assert env.plugin._portal_token == 1
    env.move(ROOM_B)
    assert exits_added(env) == [("*", portal_marker(7), "1235", 1, {"serial": 7, "level": 50})]
    assert env.sent[-1] == ["Mapper: portal a swirling portal (7) -> 1235"]
    assert env.fake.eq.calls[1:] == [("put", 7, "1000"), ("equip", 3, "portal")]
    assert env.plugin._pending_portal is None
    assert env.plugin._taken is None


def test_portal_item_level_override(env: Env) -> None:
    """-l replaces the item's level; -l 0 stores no level."""
    stock_eq(env)
    start_portal(env, level=20)
    env.move(ROOM_B)
    assert exits_added(env)[0][4] == {"serial": 7, "level": 20}
    env.plugin._pending_portal = None
    env.plugin._current = None
    start_portal(env, level=0)
    env.move(ROOM_B)
    assert exits_added(env)[1][4] == {"serial": 7}


def test_portal_item_already_in_the_slot(env: Env) -> None:
    """A portal already held is entered and nothing is moved or restored."""
    stock_eq(env, previous=False)
    env.fake.eq.items[7]["container"] = "Worn"
    env.fake.eq.worn["portal"] = 7
    assert start_portal(env).success
    assert env.fake.mud == [ENTER]
    assert env.fake.eq.calls == []
    env.move(ROOM_B)
    assert len(exits_added(env)) == 1
    assert env.fake.eq.calls == []


def test_portal_item_from_inventory_with_an_empty_slot(env: Env) -> None:
    """With nothing in the slot only the portal is held, then put back to the inventory."""
    stock_eq(env, previous=False)
    env.fake.eq.items[7]["container"] = "Inventory"
    start_portal(env)
    assert env.fake.eq.calls == [("equip", 7)]
    env.move(ROOM_B)
    assert env.fake.eq.calls[1:] == [("put", 7, "Inventory")]


@pytest.mark.parametrize(("lands", "other"), [("portal", "hold"), ("hold", "portal")])
@pytest.mark.parametrize("walk", [False, True])
def test_portal_item_wear_lands_in_the_bought_or_held_slot(
    env: Env, lands: str, other: str, walk: bool
) -> None:
    """A plain wear is sent; the item the portal displaced is worn back at that slot only."""
    stock_eq(env, previous=False)
    env.fake.eq.add(3, "a ring", itype=7, container="Worn")
    env.fake.eq.add(4, "a lamp", itype=7, container="Worn")
    env.fake.eq.worn[lands] = 3
    env.fake.eq.worn[other] = 4
    env.fake.eq.lands = lands
    if walk:
        assert env.plugin._use_portal(7) is None
        env.plugin._restore_portal()
    else:
        start_portal(env)
        env.plugin._pending_portal = None
        env.plugin._portal_token += 1
        env.plugin._restore_portal()
    assert env.fake.eq.calls == [("equip", 7), ("put", 7, "1000"), ("equip", 3, lands)]


@pytest.mark.parametrize("walk", [False, True])
def test_portal_item_unseen_move_restores_the_changed_slot(env: Env, walk: bool) -> None:
    """When eq has not seen the portal move, the slot whose item changed is restored."""
    stock_eq(env, previous=False)
    env.fake.eq.add(3, "a ring", itype=7, container="Worn")
    env.fake.eq.worn["hold"] = 3
    env.fake.eq.lands = None
    if walk:
        assert env.plugin._use_portal(7) is None
    else:
        start_portal(env)
    env.fake.eq.worn["hold"] = 5  # eq now lists a different item there
    env.fake.eq.add(5, "a stick", itype=7, container="Worn")
    env.plugin._restore_portal()
    assert env.fake.eq.calls == [("equip", 7), ("put", 7, "1000"), ("equip", 3, "hold")]


def test_portal_item_nothing_decided_puts_the_portal_back(env: Env) -> None:
    """With no slot seen to change the portal is put back and nothing is worn."""
    stock_eq(env)
    env.fake.eq.lands = None
    assert env.plugin._use_portal(7) is None
    env.plugin._restore_portal()
    assert env.fake.eq.calls == [("equip", 7), ("put", 7, "1000")]


def test_portal_item_already_held_is_entered_without_restore(env: Env) -> None:
    """An item eq lists in the held slot is entered and nothing is moved or restored."""
    stock_eq(env, previous=False)
    env.fake.eq.items[7]["container"] = "Worn"
    env.fake.eq.worn["hold"] = 7
    assert start_portal(env).success
    assert env.plugin._taken is None
    env.plugin._restore_portal()
    assert env.fake.eq.calls == []


def test_portal_item_above_level_is_refused(env: Env) -> None:
    """A portal above the tier-adjusted level is refused at once; nothing is sent or stored."""
    stock_eq(env)
    env.fake.gmcp.update({"char.status.level": 29, "char.base.tier": 2})  # counts as 49
    result = start_portal(env)
    assert not result.success
    assert result.message == ["Mapper: a swirling portal (7) needs level 50"]
    assert env.fake.mud == []
    assert env.fake.eq.calls == []
    assert env.plugin._pending_portal is None
    assert not exits_added(env)
    start_portal(env, touid="1234")
    assert not exits_added(env)


def test_portal_item_at_level_records(env: Env) -> None:
    """A portal at the tier-adjusted level records as before."""
    stock_eq(env)
    env.fake.gmcp.update({"char.status.level": 30, "char.base.tier": 2})
    assert start_portal(env).success
    env.move(ROOM_B)
    assert exits_added(env) == [("*", portal_marker(7), "1235", 1, {"serial": 7, "level": 50})]


def test_portal_item_level_override_is_checked(env: Env) -> None:
    """-l replaces the item's level for the check as well as the stored requirement."""
    stock_eq(env)
    env.fake.gmcp.update({"char.status.level": 10, "char.base.tier": 0})
    assert not start_portal(env).success
    assert start_portal(env, level=5).success
    env.plugin._pending_portal = None
    assert start_portal(env, level=0).success
    env.fake.mud.clear()
    result = start_portal(env, level=60)
    assert result.message == ["Mapper: a swirling portal (7) needs level 60"]
    assert env.fake.mud == []


def test_portal_item_refusals_send_nothing(env: Env) -> None:
    """An unknown item, a non portal, a recall, a second recording and no eq store nothing."""
    stock_eq(env)
    assert not start_portal(env, command=["99"]).success
    assert not start_portal(env, command=["3"]).success
    assert not start_portal(env, recall=True).success
    env.fake.eq.present = False
    assert not start_portal(env).success
    env.fake.eq.present = True
    env.plugin._pending_cexit = ("1234", "go", None, 1)
    assert not start_portal(env).success
    env.plugin._pending_cexit = None
    assert start_portal(env).success
    env.fake.mud.clear()
    env.fake.eq.calls.clear()
    assert not start_portal(env).success
    assert env.fake.mud == []
    assert env.fake.eq.calls == []
    assert not exits_added(env)


def test_portal_item_timeout(env: Env, delays: list[float]) -> None:
    """With no new room the exit is not stored and the portal is put back."""
    stock_eq(env)
    start_portal(env)
    env.run_tasks()
    assert delays == [CEXIT_TIMEOUT]
    assert "no new room" in env.sent[-1][0]
    assert not exits_added(env)
    assert env.fake.eq.calls[1:] == [("put", 7, "1000"), ("equip", 3, "portal")]
    assert env.plugin._pending_portal is None


def test_portal_item_refused_by_the_room(env: Env, delays: list[float]) -> None:
    """The noportal line drops the recording and puts the portal back."""
    stock_eq(env)
    start_portal(env)
    env.fake.rooms["1234"] = {"uid": "1234", "name": "A Room", "area": "aylor", "flags": []}
    env.fake.trigger_regs["noportal"]()
    assert "refused" in env.sent[-1][0]
    assert env.fake.eq.calls[1:] == [("put", 7, "1000"), ("equip", 3, "portal")]
    env.run_tasks()
    assert not exits_added(env)
    assert not any("no new room" in line for chunk in env.sent for line in chunk)


def test_portal_item_direct(env: Env) -> None:
    """With -t the exit is stored at once, nothing is used, and the room must be known."""
    stock_eq(env)
    env.fake.rooms["5"] = {"uid": "5"}
    assert start_portal(env, touid="5").success
    assert exits_added(env) == [("*", portal_marker(7), "5", 1, {"serial": 7, "level": 50})]
    assert env.fake.mud == []
    assert env.fake.eq.calls == []
    assert not start_portal(env, touid="9").success
    assert len(exits_added(env)) == 1


def test_portal_text_command_is_unchanged(env: Env) -> None:
    """A text command is stored as it is, with no eq call."""
    stock_eq(env)
    env.move(ROOM_A)
    env.fake.rooms["1234"] = {"uid": "1234", "name": "A Room", "area": "aylor", "flags": []}
    env.fake.args = {**PORTAL_ARGS, "command": ["hold", "7;enter"], "level": 30}
    assert env.plugin._command_portal().success
    assert exits_added(env) == [("*", "hold 7;enter", "1234", 1, {"level": 30})]
    assert env.fake.mud == []
    assert env.fake.eq.calls == []


def test_disconnect_and_unload_drop_the_pending_portal(env: Env) -> None:
    """A disconnect or an unload forget the portal being recorded and the one taken."""
    stock_eq(env)
    start_portal(env)
    env.plugin._eventcb_disconnect()
    assert env.plugin._pending_portal is None
    assert env.plugin._taken is None
    start_portal(env)
    env.plugin._phook_uninitialize()
    assert env.plugin._pending_portal is None
    assert env.plugin._taken is None


def item_walk(env: Env, *steps: dict[str, str]) -> list[str]:
    """Run the movement callback on steps."""
    result: list[str] = env.fake.callbacks["movement"](list(steps))
    return result


PORTAL_STEP = {"fromuid": "*", "dir": portal_marker(7)}


def test_walk_uses_the_portal_first(env: Env) -> None:
    """The portal is taken and entered before the returned commands; the move puts it back."""
    stock_eq(env)
    assert item_walk(env, PORTAL_STEP, {"fromuid": "1235", "dir": "e"}) == ["e"]
    assert env.fake.mud == [ENTER]
    assert env.fake.eq.calls == [("equip", 7)]
    env.move(ROOM_B)
    assert env.fake.eq.calls[1:] == [("put", 7, "1000"), ("equip", 3, "portal")]


def test_walk_failed_puts_the_portal_back(env: Env) -> None:
    """A walk that stops after the portal still restores."""
    stock_eq(env)
    item_walk(env, PORTAL_STEP)
    env.plugin._eventcb_walk_failed()
    assert env.fake.eq.calls[1:] == [("put", 7, "1000"), ("equip", 3, "portal")]
    env.plugin._eventcb_walk_failed()
    assert len(env.fake.eq.calls) == 3


def test_walk_mid_path_portal(env: Env) -> None:
    """A portal after other steps is used when its turn comes, then the rest is sent."""
    stock_eq(env)
    steps = [{"fromuid": "1", "dir": "n"}, PORTAL_STEP, {"fromuid": "2", "dir": "e"}]
    assert item_walk(env, *steps) == ["n"]
    assert env.fake.mud == []
    env.run_tasks()
    assert env.fake.mud == [ENTER, ["e"]]
    assert env.fake.eq.calls == [("equip", 7)]


def test_walk_mid_path_portal_is_cancelled(env: Env) -> None:
    """A cancelled walk does not use the waiting portal."""
    stock_eq(env)
    item_walk(env, {"fromuid": "1", "dir": "n"}, PORTAL_STEP)
    env.plugin._eventcb_walk_failed()
    env.run_tasks()
    assert env.fake.mud == []
    assert env.fake.eq.calls == []


def test_walk_unknown_item_returns_nothing(env: Env) -> None:
    """An item eq does not have is reported and nothing is sent."""
    assert item_walk(env, PORTAL_STEP, {"fromuid": "2", "dir": "e"}) == []
    assert env.fake.mud == []
    assert "does not know item 7" in env.sent[-1][0]
    env.run_tasks()
    assert env.fake.mud == []


def test_disconnect_drops_the_taken_portal(env: Env) -> None:
    """A disconnect forgets the taken portal, so the next move restores nothing."""
    stock_eq(env)
    item_walk(env, PORTAL_STEP)
    env.plugin._eventcb_disconnect()
    env.move(ROOM_B)
    assert len(env.fake.eq.calls) == 1


def test_requirement_blocks_a_missing_item(env: Env) -> None:
    """An item portal is blocked when eq lacks the item or is absent; the level still applies."""
    callback = env.fake.callbacks["requirement"]
    env.fake.gmcp.update({"char.status.level": 50, "char.base.tier": 0})
    step = {"fromuid": "*", "dir": portal_marker(7)}
    assert not callback({"serial": 7}, step)
    stock_eq(env)
    assert callback({"serial": 7}, step)
    assert callback({"serial": 7, "level": 50}, step)
    assert not callback({"serial": 7, "level": 51}, step)
    env.fake.eq.present = False
    assert not callback({"serial": 7}, step)
    # a text portal does not need eq
    assert callback({"level": 50}, {"fromuid": "*", "dir": "hold 7;enter"})
