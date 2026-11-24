"""Tests for the mapper plugin commands: the MUSHclient import and the searches."""

import argparse
import asyncio
import copy
import hashlib
import sqlite3
from collections.abc import Callable, Coroutine, Iterable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from mush_db import build_mush_db

from aardwolf.mapper.libs import room_from_gmcp

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


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """A plugin with a stateful fake mapper."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from aardwolf.mapper.plugin import _mapper

    fake = FakeMapper()
    sent: list[list[str]] = []
    plugin = _mapper.MapperPlugin.__new__(_mapper.MapperPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    plugin._client = sent.append  # type: ignore[method-assign,assignment]
    plugin._phook_init_plugin()
    yield Env(plugin, fake, sent)


@pytest.fixture
def db(tmp_path: Path) -> Path:
    """A made-up MUSH database."""
    return build_mush_db(tmp_path / "Aardwolf.db")


def test_import_end_to_end(env: Env, db: Path) -> None:
    """Areas, rooms, exits with requirements, portals, recall and notes are created."""
    result = env.run_import(db)
    assert result.success
    fake = env.fake
    assert set(fake.areas) == {"testarea", "otherarea"}
    assert fake.areas["testarea"]["flags"] == ["flagone", "flagtwo"]
    assert set(fake.rooms) == {"100", "101", "102", "103", "200"}
    assert fake.rooms["100"]["details"] == {"details": "bank,shop", "coord_id": None, "cont": None}
    assert fake.rooms["101"]["flags"] == ["norecall"]
    assert fake.exits[("101", "n")]["requirement"] == {"level": 50}
    assert fake.exits[("101", "n")]["touid"] == "102"
    assert fake.exits[("100", "e")]["touid"] == "-1"
    assert fake.exits[("*", "enter test")]["touid"] == "100"
    assert fake.exits[("*", "enter far")]["requirement"] == {"level": 100}
    assert fake.exits[("**", "recall")]["touid"] == "100"
    assert all(e["cost"] == 1 for e in fake.exits.values())
    assert len(fake.exits) == 8
    assert fake.notes == {"100": "bookmark note", "102": "bookmark wins"}
    lines = env.lines()
    assert "Mapper import: areas 0/2" in lines
    assert "Mapper import: rooms 0/5" in lines
    assert "Mapper import: exits 0/8" in lines
    assert lines[-1] == (
        "Mapper import done: 2 areas, 5 rooms (flags added to 0 stored), "
        "8 exits (0 updated), 2 notes; skipped 1 rooms and 3 exits"
    )
    assert env.plugin._importing is False


def test_import_progress_lines(env: Env, db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A progress line is sent every IMPORT_PROGRESS items."""
    from aardwolf.mapper.plugin import _mapper

    monkeypatch.setattr(_mapper, "IMPORT_PROGRESS", 2)
    env.run_import(db)
    assert "Mapper import: rooms 2/5" in env.lines()
    assert "Mapper import: rooms 4/5" in env.lines()
    assert "Mapper import: exits 8/8" in env.lines()


def test_import_is_idempotent(env: Env, db: Path) -> None:
    """A second import finds everything present and writes nothing."""
    env.run_import(db)
    before = env.fake.state()
    env.fake.calls.clear()
    env.sent.clear()
    env.run_import(db)
    assert env.fake.state() == before
    assert env.fake.count("area.add", "room.add", "exit.add", "room.note.set") == 0
    assert env.lines()[-1].startswith(
        "Mapper import done: 0 areas, 0 rooms (flags added to 0 stored), 0 exits"
    )


def test_import_leaves_the_file_alone(env: Env, db: Path) -> None:
    """The file is the same bytes after an import."""
    before = hashlib.sha256(db.read_bytes()).hexdigest()
    env.run_import(db)
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before


def test_captured_data_wins(env: Env, db: Path) -> None:
    """A stored room, exit, note and area keep their data; only the gaps are filled."""
    fake = env.fake
    fake.areas["testarea"] = {"uid": "testarea", "name": "Captured", "flags": [], "details": {}}
    captured = room_from_gmcp(
        {"num": 101, "zone": "testarea", "details": "trainer, extra", "coord": {"id": 7}},
        "Captured Hall",
        [],
    )
    del captured["exits"]
    fake.rooms["101"] = captured
    fake.exits[("101", "n")] = {
        "fromuid": "101",
        "dir": "n",
        "touid": "555",
        "cost": 3,
        "requirement": None,
    }
    fake.rooms["100"] = {**captured, "uid": "100", "flags": ["noportal"]}
    fake.notes["100"] = "my own note"
    env.run_import(db)
    assert fake.areas["testarea"]["name"] == "Captured"
    assert fake.rooms["101"]["details"]["details"] == "trainer, extra"
    assert fake.rooms["101"]["name"] == "Captured Hall"
    assert fake.rooms["101"]["flags"] == ["norecall"]
    assert fake.exits[("101", "n")]["touid"] == "555"
    assert fake.exits[("101", "n")]["cost"] == 3
    assert fake.exits[("101", "n")]["requirement"] == {"level": 50}
    assert fake.rooms["100"]["flags"] == ["noportal"]
    assert fake.notes["100"] == "my own note"
    assert env.lines()[-1].startswith(
        "Mapper import done: 1 areas, 3 rooms (flags added to 1 stored)"
    )
    assert "(1 updated)" in env.lines()[-1]


def test_second_import_is_refused_while_running(env: Env, db: Path) -> None:
    """Only one import runs at a time; the flag clears when it finishes."""
    env.fake.args = {"path": str(db)}
    first = env.plugin._command_importmush()
    assert first.success
    second = env.plugin._command_importmush()
    assert not second.success
    assert "already running" in second.message[0]
    assert len(env.fake.tasks) == 1
    asyncio.run(env.fake.tasks.pop())
    assert env.plugin._command_importmush().success
    env.fake.tasks.pop().close()


def test_bad_path_is_refused_without_a_task(env: Env, tmp_path: Path) -> None:
    """A relative path, a missing file and a directory fail on the loop with no task."""
    for text in ("relative.db", str(tmp_path / "none.db"), str(tmp_path)):
        env.fake.args = {"path": text}
        assert not env.plugin._command_importmush().success
    assert env.fake.tasks == []
    assert env.plugin._importing is False


def test_bad_file_writes_nothing(env: Env, tmp_path: Path) -> None:
    """A file that is not a mapper database sends the error and writes nothing."""
    path = tmp_path / "bad.db"
    path.write_text("this is not a database, just some text to fill the header " * 4)
    result = env.run_import(path)
    assert result.success
    assert env.lines()[-1].startswith("Mapper import: not an SQLite database")
    assert env.fake.state() == {"areas": {}, "rooms": {}, "exits": {}, "notes": {}}
    assert env.plugin._importing is False


def test_unload_stops_the_writes(env: Env, db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An unload after the read stops the import before it writes."""
    real = asyncio.to_thread

    async def read_then_unload(func: Callable[[Path], object], arg: Path) -> object:
        result = await real(func, arg)
        env.plugin._unload_token += 1
        return result

    monkeypatch.setattr(asyncio, "to_thread", read_then_unload)
    env.run_import(db)
    assert env.fake.state() == {"areas": {}, "rooms": {}, "exits": {}, "notes": {}}
    assert env.plugin._importing is False


def test_unload_during_the_writes_stops(env: Env, db: Path) -> None:
    """An unload while writing stops at the next item."""
    original = env.fake.area_add

    def unload_on_first(
        uid: str, name: str = "", flags: Iterable[str] = (), details: object = None
    ) -> bool:
        env.plugin._unload_token += 1
        return original(uid, name, flags, details)

    env.fake.area_add = unload_on_first  # type: ignore[method-assign]
    env.run_import(db)
    assert len(env.fake.areas) == 1
    assert env.fake.rooms == {}
    assert not any(line.startswith("Mapper import done") for line in env.lines())


def test_write_failure_stops_with_a_line(env: Env, db: Path) -> None:
    """A sqlite error from an API stops the import, says where, and clears the flag."""
    env.fake.fail_exit_add = True
    env.run_import(db)
    assert env.lines()[-1] == "Mapper import stopped in exits at 0/8: disk is full"
    assert env.plugin._importing is False


def test_time_slicing_yields(env: Env, db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With a zero slice the import yields to the loop after every item."""
    from aardwolf.mapper.plugin import _mapper

    monkeypatch.setattr(_mapper, "IMPORT_SLICE", 0)
    sleeps: list[float] = []
    real_sleep = asyncio.sleep

    async def counting(delay: float) -> None:
        sleeps.append(delay)
        await real_sleep(delay)

    monkeypatch.setattr(asyncio, "sleep", counting)
    env.run_import(db)
    assert len(sleeps) == 2 + 5 + 8
    assert env.lines()[-1].startswith("Mapper import done")


def test_no_yield_inside_a_long_slice(env: Env, db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With a long slice the import never yields."""
    from aardwolf.mapper.plugin import _mapper

    monkeypatch.setattr(_mapper, "IMPORT_SLICE", 1000.0)
    sleeps: list[float] = []

    async def counting(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(asyncio, "sleep", counting)
    env.run_import(db)
    assert sleeps == []


# searches


def _imported(env: Env, db: Path) -> None:
    env.run_import(db)
    env.fake.current = "100"
    env.fake.calls.clear()


def test_shops_here(env: Env, db: Path) -> None:
    """Shops in the current room's area list the bank and shop rooms."""
    _imported(env, db)
    result = env.search("shops")
    assert result.success
    assert result.message == [
        "Mapper shops in testarea: 1 rooms",
        "uid | name | area | found",
        "100 | The Test Bank | testarea | Bank, Shop",
    ]


def test_train_and_quest_by_area_lowercased(env: Env, db: Path) -> None:
    """The area argument is lowercased and exact."""
    _imported(env, db)
    train = env.search("train", "TestArea")
    assert train.message[-1] == "101 | Training Hall | testarea | Trainer"
    quest = env.search("quest", "testarea")
    assert quest.message[-1] == "102 | Quest Office | testarea | Questor"


def test_notes_lists_note_text(env: Env, db: Path) -> None:
    """Notes lists the rooms with a note, with the note text."""
    _imported(env, db)
    result = env.search("notes", "testarea")
    assert result.message == [
        "Mapper notes in testarea: 2 rooms",
        "uid | name | area | found",
        "100 | The Test Bank | testarea | bookmark note",
        "102 | Quest Office | testarea | bookmark wins",
    ]


def test_search_in_other_area_uses_spaced_details(env: Env, db: Path) -> None:
    """Details with spaces and capitals still match."""
    _imported(env, db)
    result = env.search("shops", "otherarea")
    assert result.message[-1] == "200 | Far Hut | otherarea | Shop"


def test_search_here_without_current_room_fails(env: Env, db: Path) -> None:
    """With no current room, here fails."""
    _imported(env, db)
    env.fake.current = None
    result = env.search("shops")
    assert not result.success
    assert result.message == ["Mapper: the current room is not known"]


def test_search_unknown_area(env: Env, db: Path) -> None:
    """An area with no rooms says so."""
    _imported(env, db)
    result = env.search("shops", "nowhere")
    assert not result.success
    assert result.message == ["Mapper: area nowhere has no mapped rooms"]


def test_search_without_match(env: Env, db: Path) -> None:
    """An area with rooms but no match says none were found."""
    _imported(env, db)
    result = env.search("shops", "testarea")
    assert result.success
    env.fake.rooms["100"]["details"] = {"details": "", "coord_id": None, "cont": None}
    result = env.search("shops", "testarea")
    assert result.success
    assert result.message == ["No shops found in testarea"]


def test_search_works_on_captured_rooms(env: Env) -> None:
    """A room stored from GMCP matches the same way as an imported one."""
    room = room_from_gmcp(
        {"num": 1234, "zone": "aylor", "details": "bank,safe", "coord": {"id": 0}},
        "Aylor Bank",
        [],
    )
    del room["exits"]
    env.fake.rooms["1234"] = room
    result = env.search("shops", "aylor")
    assert result.message == [
        "Mapper shops in aylor: 1 rooms",
        "uid | name | area | found",
        "1234 | Aylor Bank | aylor | Bank",
    ]


def test_search_rows_are_in_numeric_uid_order(env: Env) -> None:
    """Rooms sort by number, not by text."""
    for uid in ("9", "10"):
        env.fake.rooms[uid] = {
            "uid": uid,
            "name": f"R{uid}",
            "area": "a",
            "details": {"details": "shop"},
        }
    result = env.search("shops", "a")
    assert [line.split(" | ")[0] for line in result.message[2:]] == ["9", "10"]


def test_search_escapes_names(env: Env) -> None:
    """Names and notes go through colorcode.escape."""
    env.fake.rooms["1"] = {
        "uid": "1",
        "name": "@RRed",
        "area": "a",
        "details": {"details": "shop"},
    }
    env.fake.notes["1"] = "@Gnote"
    original = env.fake.__call__

    def escaping(name: str) -> Callable[..., Any]:
        if name == "plugins.core.colors:colorcode.escape":
            return lambda text: text.replace("@", "@@")
        return original(name)

    env.plugin.api = MagicMock(side_effect=escaping)
    assert env.search("shops", "a").message[-1] == "1 | @@RRed | a | Shop"
    assert env.search("notes", "a").message[-1] == "1 | @@RRed | a | @@Gnote"


def test_command_arguments_are_declared(env: Env) -> None:
    """Each command declares its arguments, and the area defaults to here."""
    arguments = env.plugin._command_importmush.command_data.arguments
    assert [item["args"] for item in arguments] == [("path",)]
    for name in ("shops", "train", "quest", "notes"):
        arguments = getattr(env.plugin, f"_command_{name}").command_data.arguments
        assert [item["args"] for item in arguments] == [("area",)]
        parser = argparse.ArgumentParser(exit_on_error=False)
        parser.add_argument(*arguments[0]["args"], **arguments[0]["kwargs"])
        assert parser.parse_args([]).area == "here"
        assert parser.parse_args(["aylor"]).area == "aylor"


def room(uid: str, area: str, name: str = "A Room") -> dict[str, Any]:
    """Return a stored room."""
    return {"uid": uid, "name": name, "area": area, "flags": [], "details": None}


@pytest.fixture
def mapped(env: Env) -> Env:
    """Rooms 1 to 3 in area a and 9 in area b, standing in room 1."""
    for uid, area in (("1", "a"), ("2", "a"), ("3", "a"), ("9", "b")):
        env.fake.rooms[uid] = room(uid, area, f"Room {uid}")
    env.fake.exit_add("1", "n", "2")
    env.fake.exit_add("1", "open door;wait(2);e", "3", 1, {"level": 50})
    env.fake.exit_add("3", "pull lever", "9")
    env.fake.exit_add("9", "squeeze", "1")
    env.fake.current = "1"
    return env


def test_cexits_listing(mapped: Env) -> None:
    """here lists the area, thisroom the room, an area id that area; plain exits are left out."""
    here = mapped.run("cexits", where="here")
    assert here.success
    assert here.message[0] == "Mapper custom exits in here: 2"
    assert here.message[1] == "uid | name | area | command | to | level"
    assert here.message[2] == "1 | Room 1 | a | open door;wait(2);e | 3 | 50"
    assert here.message[3] == "3 | Room 3 | a | pull lever | 9 | 0"
    assert len(mapped.run("cexits", where="thisroom").message) == 3
    assert mapped.run("cexits", where="b").message[2].startswith("9 | Room 9 | b | squeeze")
    mapped.fake.exit_add("*", "enter", "1")
    assert len(mapped.run("cexits", where="here").message) == 4


def test_cexits_empty_and_unknown_room(mapped: Env) -> None:
    """An area with none gets a message; here needs a known room."""
    assert mapped.run("cexits", where="nowhere").message == ["No custom exits found in nowhere"]
    mapped.fake.current = None
    assert not mapped.run("cexits", where="here").success


def test_cexitdel(mapped: Env) -> None:
    """One named cexit, or all of the room's, are deleted; plain exits stay."""
    mapped.fake.exit_add("1", "pull rope", "2")
    assert not mapped.run("cexitdel", command=["nothing"]).success
    assert mapped.run("cexitdel", command=["pull", "rope"]).success
    assert ("1", "pull rope") not in mapped.fake.exits
    assert ("1", "open door;wait(2);e") in mapped.fake.exits
    assert mapped.run("cexitdel", command=[]).success
    assert set(mapped.fake.exits) >= {("1", "n"), ("3", "pull lever")}
    assert ("1", "open door;wait(2);e") not in mapped.fake.exits
    assert not mapped.run("cexitdel", command=[]).success
    mapped.fake.current = None
    assert not mapped.run("cexitdel", command=[]).success


def test_cexitpurge(mapped: Env) -> None:
    """Without --confirm nothing changes; with it only the named area is purged."""
    before = set(mapped.fake.exits)
    counted = mapped.run("cexitpurge", where="a", confirm=False)
    assert "2 custom exits in a" in counted.message[0]
    assert set(mapped.fake.exits) == before
    assert mapped.run("cexitpurge", where="here", confirm=True).success
    assert set(mapped.fake.exits) == {("1", "n"), ("9", "squeeze")}
    assert mapped.run("cexitpurge", where="here", confirm=True).message == [
        "No custom exits found in a"
    ]
    assert mapped.run("cexitpurge", where="all", confirm=True).success
    assert set(mapped.fake.exits) == {("1", "n")}
    mapped.fake.current = None
    assert not mapped.run("cexitpurge", where="here", confirm=True).success


def test_lockexit(mapped: Env) -> None:
    """List the exits, show a lock, set one keeping touid and cost, and remove it."""
    listed = mapped.run("lockexit", exit=[], room=None, level=None)
    assert listed.message[1:] == ["exit | to | level", "n | 2 | 0", "open door;wait(2);e | 3 | 50"]
    shown = mapped.run("lockexit", exit=["open", "door;wait(2);e"], room=None, level=None)
    assert "needs level 50" in shown.message[0]
    mapped.fake.exit_add("1", "s", "2", 4)
    assert mapped.run("lockexit", exit=["s"], room=None, level=100).success
    assert mapped.fake.exits[("1", "s")] == {
        "fromuid": "1",
        "dir": "s",
        "touid": "2",
        "cost": 4,
        "requirement": {"level": 100},
    }
    assert mapped.run("lockexit", exit=["s"], room="1", level=0).success
    assert mapped.fake.exits[("1", "s")]["requirement"] is None
    assert mapped.fake.exits[("1", "s")]["cost"] == 4
    assert mapped.run("lockexit", exit=["pull", "lever"], room="3", level=70).success
    assert mapped.fake.exits[("3", "pull lever")]["requirement"] == {"level": 70}


def test_lockexit_failures(mapped: Env) -> None:
    """A missing exit and an unknown room fail."""
    assert not mapped.run("lockexit", exit=["up"], room=None, level=5).success
    assert not mapped.run("lockexit", exit=["n"], room="77", level=5).success
    mapped.fake.current = None
    assert not mapped.run("lockexit", exit=[], room=None, level=None).success


def portal(
    env: Env, *command: str, level: int = 0, touid: str | None = None, recall: bool = False
) -> "CommandResult":
    """Run the portal command."""
    return env.run("portal", command=list(command), level=level, touid=touid, recall=recall)


def test_portal_adds(mapped: Env) -> None:
    """A portal goes under *, recall and home under **, --recall forces **; touid defaults here."""
    assert portal(mapped, "enter", "portal", level=20).success
    assert mapped.fake.exits[("*", "enter portal")]["touid"] == "1"
    assert mapped.fake.exits[("*", "enter portal")]["requirement"] == {"level": 20}
    assert portal(mapped, "Home", touid="2").success
    assert ("**", "Home") in mapped.fake.exits
    assert portal(mapped, "gate", recall=True, touid="3").success
    assert ("**", "gate") in mapped.fake.exits
    assert not portal(mapped, "gate", touid="77").success
    assert not portal(mapped, "x;wait(99)").success
    mapped.fake.current = None
    assert not portal(mapped, "gate").success


def test_portal_other_kind_is_replaced(mapped: Env) -> None:
    """Adding a command under the other kind removes the old exit."""
    portal(mapped, "gate")
    portal(mapped, "gate", recall=True)
    assert ("*", "gate") not in mapped.fake.exits
    assert ("**", "gate") in mapped.fake.exits


def add_portals(env: Env) -> None:
    """Three portals in two areas, added out of order."""
    portal(env, "zzz", touid="9", level=5)
    portal(env, "recall", touid="3")
    portal(env, "aaa", touid="2")


def test_portals_listing(mapped: Env) -> None:
    """Sorted by area, room number and command; numbers stay stable under a filter."""
    add_portals(mapped)
    result = mapped.run("portals", filter="")
    assert result.message[1] == "# | kind | area | name | to | command | level"
    assert result.message[2:] == [
        "#1 | portal | a | Room 2 | 2 | aaa | 0",
        "#2 | recall | a | Room 3 | 3 | recall | 0",
        "#3 | portal | b | Room 9 | 9 | zzz | 5",
    ]
    assert mapped.run("portals", filter="B").message[2:] == [
        "#3 | portal | b | Room 9 | 9 | zzz | 5"
    ]
    assert mapped.run("portals", filter="nope").message == ["No portals found"]


def test_portal_edits(mapped: Env) -> None:
    """Each edit works by #N and by command and keeps the other fields."""
    add_portals(mapped)
    assert mapped.run("portalchange", ref="#1", command=["bbb", "ccc"]).success
    assert ("*", "aaa") not in mapped.fake.exits
    assert mapped.fake.exits[("*", "bbb ccc")]["touid"] == "2"
    assert mapped.run("portallevel", ref="zzz", level=40).success
    assert mapped.fake.exits[("*", "zzz")]["requirement"] == {"level": 40}
    assert mapped.fake.exits[("*", "zzz")]["touid"] == "9"
    assert mapped.run("portallevel", ref="zzz", level=0).success
    assert mapped.fake.exits[("*", "zzz")]["requirement"] is None
    assert mapped.run("portalrecall", ref="zzz").success
    assert ("*", "zzz") not in mapped.fake.exits
    assert mapped.fake.exits[("**", "zzz")]["touid"] == "9"
    assert mapped.run("portalrecall", ref="zzz").success
    assert ("*", "zzz") in mapped.fake.exits
    assert ("**", "zzz") not in mapped.fake.exits
    assert mapped.run("portaldel", ref="recall").success
    assert ("**", "recall") not in mapped.fake.exits


def test_portal_unknown_reference(mapped: Env) -> None:
    """An unknown number or command fails, and a bad new command is refused."""
    add_portals(mapped)
    before = mapped.fake.state()
    assert not mapped.run("portalchange", ref="#9", command=["x"]).success
    assert not mapped.run("portalchange", ref="aaa", command=["wait(0)"]).success
    assert not mapped.run("portallevel", ref="nope", level=3).success
    assert not mapped.run("portalrecall", ref="nope").success
    assert not mapped.run("portaldel", ref="nope").success
    assert mapped.fake.state() == before


def test_portalpurge(mapped: Env) -> None:
    """It needs --confirm and leaves the exits of rooms alone."""
    assert mapped.run("portalpurge", confirm=False).message == ["No portals found"]
    add_portals(mapped)
    count = len(mapped.fake.exits)
    assert "3 portals" in mapped.run("portalpurge", confirm=False).message[0]
    assert len(mapped.fake.exits) == count
    assert mapped.run("portalpurge", confirm=True).success
    assert {f for f, _ in mapped.fake.exits} == {"1", "3", "9"}
