"""End to end paths over a test map, with the real core pathfinder."""

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

import pytest
from mapper_support import Env, FakeMapper, room
from test_mapper_commands import env  # noqa: F401  # env is a fixture pytest finds by name

if TYPE_CHECKING:
    from bastproxy.plugins.client.mapper.libs._graph import MapGraph

LEVEL = "char.status.level"
TIER = "char.base.tier"


def graph_from(fake: FakeMapper) -> "MapGraph":
    """Load the rooms and exits of the fake into the core graph."""
    from bastproxy.plugins.client.mapper.libs._graph import Exit, MapGraph

    graph = MapGraph()
    for uid, stored in fake.rooms.items():
        graph.set_room(uid, stored.get("flags") or [])
    for item in fake.exits.values():
        graph.set_exit(
            Exit(item["fromuid"], item["dir"], item["touid"], item["cost"], item["requirement"])
        )
    return graph


def find(mapper: Env, start: str, target: str) -> list[dict[str, Any]] | None:
    """Return the dict steps of the cheapest path, using the adapter's requirement check."""
    from bastproxy.plugins.client.mapper.libs._graph import Exit, find_path

    def allowed(exit_: Exit) -> bool:
        if exit_.requirement is None:
            return True
        return mapper.plugin._requirement(exit_.requirement, exit_.to_dict())

    result = find_path(graph_from(mapper.fake), start, target, max_depth=50, allowed=allowed)
    return None if result is None else [step.to_dict() for step in result.steps]


@pytest.fixture
def world(env: Env) -> Iterator[Env]:  # noqa: F811  # the env argument is the imported fixture
    """A line of rooms 1 to 4 in area a, a made-up character of level 50 and tier 0."""
    for uid in ("1", "2", "3", "4", "5"):
        env.fake.rooms[uid] = room(uid, "a")
    for here, there in (("1", "2"), ("2", "3"), ("3", "4")):
        env.fake.exit_add(here, "e", there)
    env.fake.gmcp.update({LEVEL: 50, TIER: 0})
    yield env
    for task in env.fake.tasks:
        task.close()


def commands(mapper: Env, steps: list[dict[str, Any]] | None) -> list[str]:
    """Return the commands the movement callback sends first."""
    assert steps is not None
    return mapper.plugin._movement(steps)


def test_cexit_is_used_when_cheaper(world: Env) -> None:
    """A waited custom exit shortens the walk; its wait becomes a delayed chunk."""
    assert commands(world, find(world, "1", "4")) == ["run 3e"]
    world.fake.current = "1"
    world.run("cexit", command=["open", "door;wait(2);jump"], level=0, timeout=0, touid="4")
    steps = find(world, "1", "4")
    assert steps is not None
    assert [s["dir"] for s in steps] == ["open door;wait(2);jump"]
    assert commands(world, steps) == ["open door"]
    assert len(world.fake.tasks) == 1
    from aardwolf.mapper.libs import movement_chunks

    assert movement_chunks(steps) == [(0.0, ["open door"]), (2.0, ["jump"])]


def test_lockexit_forces_a_detour(world: Env) -> None:
    """A lock above the level blocks the exit; at or below the level it is used."""
    for uid in ("6", "7"):
        world.fake.rooms[uid] = room(uid, "a")
    for here, direction, there in (
        ("1", "n", "5"),
        ("5", "n", "6"),
        ("6", "n", "7"),
        ("7", "s", "4"),
    ):
        world.fake.exit_add(here, direction, there)
    world.fake.current = "1"
    world.run("lockexit", exit=["e"], room="3", level=100)
    steps = find(world, "1", "4")
    assert steps is not None
    assert [s["dir"] for s in steps] == ["n", "n", "n", "s"]
    world.fake.gmcp[LEVEL] = 100
    steps = find(world, "1", "4")
    assert steps is not None
    assert [s["dir"] for s in steps] == ["e", "e", "e"]
    world.run("lockexit", exit=["e"], room="3", level=0)
    world.fake.gmcp[LEVEL] = 1
    assert find(world, "1", "4") is not None


def test_level_locked_portal(world: Env) -> None:
    """A portal needing level 60 is refused at 50 and allowed with a tier of 1."""
    world.fake.current = "4"
    world.run("portal", command=["enter", "gate"], level=60, touid=None, recall=False)
    assert [s["dir"] for s in find(world, "1", "4") or []] == ["e", "e", "e"]
    world.fake.gmcp[TIER] = 1
    steps = find(world, "1", "4")
    assert steps is not None
    assert [s["dir"] for s in steps] == ["enter gate"]


def flag(mapper: Env, uid: str, *flags: str) -> None:
    """Flag a room."""
    mapper.fake.rooms[uid]["flags"] = list(flags)


def test_bounce_recall_from_noportal_room(world: Env) -> None:
    """From a noportal room a recall chains into a portal."""
    world.fake.exit_add("**", "recall", "1")
    world.fake.exit_add("*", "enter portal", "4")
    flag(world, "5", "noportal")
    steps = find(world, "5", "4")
    assert steps is not None
    assert [(s["fromuid"], s["dir"]) for s in steps] == [("**", "recall"), ("*", "enter portal")]


def test_bounce_portal_from_norecall_room(world: Env) -> None:
    """From a norecall room a portal chains into a recall."""
    world.fake.exit_add("**", "recall", "1")
    world.fake.exit_add("*", "enter portal", "4")
    flag(world, "5", "norecall")
    steps = find(world, "5", "1")
    assert steps is not None
    assert [(s["fromuid"], s["dir"]) for s in steps] == [
        ("*", "enter portal"),
        ("**", "recall"),
    ]


def test_blocked_room_walks_out_first(world: Env) -> None:
    """In a room with both flags only its own exits work; with none there is no path."""
    world.fake.exit_add("**", "recall", "1")
    world.fake.exit_add("*", "enter portal", "4")
    world.fake.exit_add("5", "w", "1")
    flag(world, "5", "noportal", "norecall")
    steps = find(world, "5", "4")
    assert steps is not None
    assert steps[0]["dir"] == "w"
    del world.fake.exits[("5", "w")]
    assert find(world, "5", "4") is None
