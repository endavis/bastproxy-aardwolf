"""Tests for the pure helpers of the quest plugin."""

import copy
from typing import Any

from aardwolf.quest.libs import ACTION_EVENTS, EVENTS, quest_current, start_state


def test_start_state_maps_the_message() -> None:
    """The message keys become the state keys."""
    data = {"action": "start", "targ": "a rat", "area": "Sewers", "room": "Dark Hall", "timer": 30}
    state = start_state(data, 12.5, 99)
    assert state == {
        "starttime": 12.5,
        "finishtime": -1,
        "killedtime": -1,
        "mobname": "a rat",
        "mobarea": "Sewers",
        "mobroom": "Dark Hall",
        "stimer": 30,
        "level": 99,
        "failed": 0,
    }


def test_start_state_defaults_and_does_not_mutate() -> None:
    """Missing keys get defaults and the input is unchanged."""
    data: dict[str, Any] = {"action": "start"}
    before = copy.deepcopy(data)
    state = start_state(data, 1.0, 0)
    assert state["mobname"] == state["mobarea"] == state["mobroom"] == ""
    assert state["stimer"] == -1
    assert data == before


def test_every_action_event_is_declared() -> None:
    """Each event an action raises has an entry."""
    assert set(ACTION_EVENTS.values()) == set(EVENTS)
    assert set(EVENTS) == {"ready", "start", "killed", "comp", "failed", "status", "reset"}
    assert ACTION_EVENTS["fail"] == ACTION_EVENTS["timeout"]


def test_descriptions_have_no_braces() -> None:
    """Descriptions go through str.format, so a brace would break them."""
    for info in EVENTS.values():
        assert info["description"]
        args = info["arg_descriptions"]
        texts = [*info["description"], *args, *args.values()]
        assert not any("{" in text or "}" in text for text in texts)


START_DATA = {
    "action": "start",
    "targ": "a rat",
    "area": "Sewers",
    "room": "Dark Hall",
    "timer": 30,
}


def test_quest_current_of_an_empty_state() -> None:
    """With no quest every value is None and every flag False."""
    assert quest_current({}, 1000.0) == {
        "active": False,
        "target": None,
        "area": None,
        "room": None,
        "starttime": None,
        "endtime": None,
        "timeleft": None,
        "killed": False,
        "complete": False,
        "failed": False,
    }


def test_quest_current_after_the_start() -> None:
    """A started quest is active, with its end from the timer and the time left."""
    state = start_state(START_DATA, 1000.0, 50)
    current = quest_current(state, 1060.0)
    assert current["active"] is True
    assert (current["target"], current["area"], current["room"]) == ("a rat", "Sewers", "Dark Hall")
    assert current["starttime"] == 1000.0
    assert current["endtime"] == 1000.0 + 30 * 60
    assert current["timeleft"] == 30 * 60 - 60
    assert (current["killed"], current["complete"], current["failed"]) == (False, False, False)


def test_quest_current_time_left_stops_at_zero() -> None:
    """Past the end the time left is 0."""
    state = start_state(START_DATA, 1000.0, 50)
    assert quest_current(state, 1000.0 + 31 * 60)["timeleft"] == 0


def test_quest_current_after_the_kill() -> None:
    """The kill sets killed, and the quest stays active until it is completed."""
    state = start_state(START_DATA, 1000.0, 50)
    state["killedtime"] = 1100.0
    current = quest_current(state, 1200.0)
    assert current["killed"] is True
    assert current["active"] is True
    assert current["complete"] is False


def test_quest_current_after_the_completion() -> None:
    """A completed quest is not active, has no time left, and is complete."""
    state = start_state(START_DATA, 1000.0, 50)
    state["killedtime"] = 1100.0
    state["finishtime"] = 1150.0
    current = quest_current(state, 1200.0)
    assert (current["active"], current["complete"], current["failed"]) == (False, True, False)
    assert current["timeleft"] is None
    assert current["target"] == "a rat"


def test_quest_current_after_a_failure() -> None:
    """A failed quest is not active and not complete."""
    state = start_state(START_DATA, 1000.0, 50)
    state["finishtime"] = 1150.0
    state["failed"] = 1
    current = quest_current(state, 1200.0)
    assert (current["active"], current["complete"], current["failed"]) == (False, False, True)
    assert current["timeleft"] is None


def test_quest_current_without_a_timer() -> None:
    """A timer of -1 gives no end time and no time left."""
    state = start_state({**START_DATA, "timer": -1}, 1000.0, 50)
    current = quest_current(state, 1200.0)
    assert current["active"] is True
    assert current["endtime"] is None
    assert current["timeleft"] is None
