"""Tests for the pure helpers of the quest plugin."""

import copy
from typing import Any

from aardwolf.quest.libs import ACTION_EVENTS, EVENTS, start_state


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
