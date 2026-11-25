"""Tests for the event name helpers that build a plugin's own event names."""

from aardwolf._libs.eventu import own_event, own_events


def test_own_event_joins_the_id_and_the_suffix() -> None:
    assert own_event("plugins.aardwolf.daily", "available") == "ev_plugins.aardwolf.daily_available"


def test_own_events_rekeys_to_full_names_in_order() -> None:
    first = {"description": ["one"], "arg_descriptions": {}}
    second = {"description": ["two"], "arg_descriptions": {"a": "b"}}
    result = own_events("plugins.aardwolf.x", {"zeta": first, "alpha": second})
    assert list(result) == ["ev_plugins.aardwolf.x_zeta", "ev_plugins.aardwolf.x_alpha"]
    assert result["ev_plugins.aardwolf.x_zeta"] is first
    assert result["ev_plugins.aardwolf.x_alpha"] is second


def test_own_events_of_nothing_is_empty() -> None:
    assert own_events("plugins.aardwolf.x", {}) == {}


def test_own_events_does_not_change_its_input() -> None:
    events = {"one": {"description": ["d"], "arg_descriptions": {}}}
    own_events("plugins.aardwolf.x", events)
    assert list(events) == ["one"]
