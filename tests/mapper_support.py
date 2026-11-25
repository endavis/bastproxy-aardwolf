"""A stateful fake of the core mapper APIs and the plugin built on it, shared by the tests."""

import asyncio
import copy
import sqlite3
from collections.abc import Callable, Coroutine, Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from bastproxy.plugins.core.commands import CommandResult

    from aardwolf.mapper.plugin._mapper import MapperPlugin

PLUGIN_ID = "plugins.aardwolf.mapper"
MAPPER = "plugins.client.mapper"


class FakeMapper:
    """A stateful stand-in for the core mapper APIs and the few other APIs the commands use."""

    def __init__(self) -> None:
        self.areas: dict[str, dict[str, Any]] = {}
        self.rooms: dict[str, dict[str, Any]] = {}
        self.exits: dict[tuple[str, str], dict[str, Any]] = {}
        self.notes: dict[str, str] = {}
        self.current: str | None = None
        self.args: dict[str, Any] = {}
        self.tasks: list[Coroutine[Any, Any, None]] = []
        self.calls: list[str] = []
        self.fail_exit_add = False
        self.batches: list[dict[str, Any]] = []
        self.batch_limit = 1000
        self.on_batch: Callable[[], None] | None = None
        self.batch_error: Exception | None = None
        self.gmcp: dict[str, Any] = {}

    def state(self) -> dict[str, Any]:
        """Return a deep copy of everything stored."""
        return copy.deepcopy(
            {"areas": self.areas, "rooms": self.rooms, "exits": self.exits, "notes": self.notes}
        )

    def count(self, *names: str) -> int:
        """Return how many calls the given APIs got."""
        return sum(1 for call in self.calls if call in names)

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake of an API."""
        short = name.removeprefix(f"{MAPPER}:")
        table: dict[str, Callable[..., Any]] = {
            "area.get": lambda uid: self.areas.get(uid),
            "area.add": self.area_add,
            "room.get": self.room_get,
            "room.add": self.room_add,
            "room.list": self.room_list,
            "room.current.get": lambda: self.current,
            "room.note.get": lambda uid: self.notes.get(uid),
            "room.note.set": self.note_set,
            "exit.add": self.exit_add,
            "map.batch.add": self.batch_add,
            "exit.list": self.exit_list,
            "exit.remove": self.exit_remove,
            "libs.asynch:task.add": lambda coro, task_name: self.tasks.append(coro),
            "plugins.core.commands:command.current.args.get": lambda: self.args,
            "plugins.core.colors:colorcode.escape": lambda text: text,
            "libs.net.protocols:gmcp.value.get": self.gmcp.get,
        }
        func = table[short if name.startswith(MAPPER) else name]

        def record(*args: object, **kwargs: object) -> object:
            self.calls.append(short)
            return func(*args, **kwargs)

        return record

    def batch_add(
        self,
        areas: list[dict[str, Any]] | None = None,
        rooms: list[dict[str, Any]] | None = None,
        exits: list[dict[str, Any]] | None = None,
        notes: dict[str, str] | None = None,
        overwrite: bool = True,
    ) -> dict[str, int] | None:
        """Behave like the core map.batch.add: row cap, fill mode and counts."""
        areas, rooms, exits, notes = areas or [], rooms or [], exits or [], notes or {}
        rows = len(areas) + len(rooms) + len(exits) + len(notes)
        self.batches.append({"rows": rows, "overwrite": overwrite, "kinds": self._kinds(locals())})
        if rows > self.batch_limit:
            return None
        if self.batch_error is not None:
            raise self.batch_error
        if self.on_batch is not None:
            self.on_batch()
        counts = dict.fromkeys(
            ("areas", "rooms", "new_rooms", "exits", "new_exits", "notes", "skipped"), 0
        )
        for area in areas:
            if overwrite or area["uid"] not in self.areas:
                self.areas[area["uid"]] = {**area}
                counts["areas"] += 1
        for room in rooms:
            stored = self.rooms.get(room["uid"])
            body = {k: v for k, v in room.items() if k != "exits"}
            if stored is None:
                self.rooms[room["uid"]] = body
                counts["rooms"] += 1
                counts["new_rooms"] += 1
            elif overwrite:
                self.rooms[room["uid"]] = body
                counts["rooms"] += 1
            else:
                missing = [f for f in room["flags"] if f not in stored["flags"]]
                if missing:
                    stored["flags"] = [*stored["flags"], *missing]
                    counts["rooms"] += 1
        for item in exits:
            key = (item["fromuid"], item["dir"])
            old = self.exits.get(key)
            if old is None:
                self.exits[key] = {**item}
                counts["exits"] += 1
                counts["new_exits"] += 1
            elif overwrite:
                touid = old["touid"] if item["touid"] == "-1" else item["touid"]
                self.exits[key] = {**item, "touid": touid}
                counts["exits"] += 1
            else:
                new = dict(old)
                if old["touid"] == "-1":
                    new["touid"] = item["touid"]
                if old["requirement"] is None:
                    new["requirement"] = item["requirement"]
                if new != old:
                    self.exits[key] = new
                    counts["exits"] += 1
        for uid, text in notes.items():
            if uid in self.rooms and (overwrite or not self.notes.get(uid)):
                self.notes[uid] = text
                counts["notes"] += 1
        return counts

    @staticmethod
    def _kinds(args: dict[str, Any]) -> set[str]:
        """Return which of areas, rooms, exits and notes a batch call carried."""
        return {k for k in ("areas", "rooms", "exits", "notes") if args.get(k)}

    def area_add(
        self, uid: str, name: str = "", flags: Iterable[str] = (), details: object = None
    ) -> bool:
        """Store an area."""
        self.areas[uid] = {"uid": uid, "name": name, "flags": list(flags), "details": details}
        return True

    def room_add(self, room: dict[str, Any]) -> bool:
        """Store a room; exits in the payload are not part of these tests."""
        assert "exits" not in room
        self.rooms[room["uid"]] = {k: v for k, v in room.items() if k != "exits"}
        return True

    def room_get(self, uid: str) -> dict[str, Any] | None:
        """Return a room with its exits and note."""
        room = self.rooms.get(uid)
        if room is None:
            return None
        return {**room, "exits": self.exit_list(uid), "note": self.notes.get(uid)}

    def room_list(
        self,
        name: str | None = None,
        area: str | None = None,
        flag: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """List the rooms of an area in uid text order, like the store."""
        rooms = [r for r in self.rooms.values() if area is None or r["area"] == area]
        return sorted(copy.deepcopy(rooms), key=lambda r: str(r["uid"]))

    def note_set(self, uid: str, text: str) -> bool:
        """Store a note for an existing room."""
        if uid not in self.rooms:
            return False
        self.notes[uid] = text
        return True

    def exit_add(
        self, fromuid: str, dir: str, touid: str = "-1", cost: int = 1, requirement: object = None
    ) -> bool:
        """Store an exit; an unexplored touid never overwrites a known one."""
        if self.fail_exit_add:
            raise sqlite3.OperationalError("disk is full")
        old = self.exits.get((fromuid, dir))
        if old is not None and touid == "-1":
            touid = old["touid"]
        self.exits[(fromuid, dir)] = {
            "fromuid": fromuid,
            "dir": dir,
            "touid": touid,
            "cost": cost,
            "requirement": requirement,
        }
        return True

    def exit_remove(self, fromuid: str, dir: str) -> bool:
        """Remove an exit; True when it existed."""
        return self.exits.pop((fromuid, dir), None) is not None

    def exit_list(self, fromuid: str) -> list[dict[str, Any]]:
        """List the exits of a room."""
        return [copy.deepcopy(e) for (f, _), e in self.exits.items() if f == fromuid]


class Env:
    """The plugin under test with its fake."""

    def __init__(self, plugin: "MapperPlugin", fake: FakeMapper, sent: list[list[str]]) -> None:
        self.plugin = plugin
        self.fake = fake
        self.sent = sent

    def lines(self) -> list[str]:
        """Return everything sent to the client, flattened."""
        return [line for chunk in self.sent for line in chunk]

    def run_import(self, path: Path) -> "CommandResult":
        """Run the importmush command and then the task it queued."""
        self.fake.args = {"path": str(path)}
        result: CommandResult = self.plugin._command_importmush()
        if result.success:
            assert len(self.fake.tasks) == 1
            asyncio.run(self.fake.tasks.pop())
        return result

    def run(self, name: str, /, **args: object) -> "CommandResult":
        """Run a command with these arguments and, when it queued tasks, run them too."""
        self.fake.args = args
        result: CommandResult = getattr(self.plugin, f"_command_{name}")()
        while self.fake.tasks:
            asyncio.run(self.fake.tasks.pop(0))
        return result

    def search(self, command: str, area: str = "here") -> "CommandResult":
        """Run a search command."""
        self.fake.args = {"area": area}
        result: CommandResult = getattr(self.plugin, f"_command_{command}")()
        return result


def build_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Env:
    """Return a plugin with a stateful fake mapper."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from aardwolf.mapper.plugin import _mapper

    fake = FakeMapper()
    sent: list[list[str]] = []
    plugin = _mapper.MapperPlugin.__new__(_mapper.MapperPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    plugin._client = sent.append  # type: ignore[method-assign,assignment]
    plugin._phook_init_plugin()
    return Env(plugin, fake, sent)


def room(uid: str, area: str, name: str = "A Room") -> dict[str, Any]:
    """Return a stored room."""
    return {"uid": uid, "name": name, "area": area, "flags": [], "details": None}
