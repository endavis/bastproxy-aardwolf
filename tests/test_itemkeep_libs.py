"""Tests for the pure helpers of the itemkeep plugin."""

import re

import pytest

from aardwolf._libs.itemu import OBJECTTYPES
from aardwolf.eq.libs import EVENT_INVENTORY_ADDED, EVENT_REMOVED, EVENT_TAKEN
from aardwolf.itemkeep.libs import (
    EVENT_EQ_INVENTORY_ADDED,
    EVENT_EQ_REMOVED,
    EVENT_EQ_TAKEN,
    KEEP_HIDE_START,
    KEEP_REGEX,
    KEEP_REPLIES,
    KEEP_TYPES,
    SETTINGS,
    TRIGGERS,
    is_kept,
    keep_serial,
    setting_name,
    should_keep,
    type_name,
)

SAMPLE_REPLIES = [
    "Keep status added to a test blade.",
    "Your a test blade is already kept. Use 'unkeep' to remove it.",
    "You do not have that item.",
]


def test_type_name_maps_a_valid_itype() -> None:
    assert type_name(5) == "weapon"
    assert type_name(len(OBJECTTYPES) - 1) == "campfire"


@pytest.mark.parametrize("value", [0, -1, len(OBJECTTYPES), True, "5", None, 5.0])
def test_type_name_rejects_bad_values(value: object) -> None:
    assert type_name(value) is None


def test_setting_name_replaces_spaces() -> None:
    assert setting_name("raw material") == "raw_material"
    assert setting_name("weapon") == "weapon"


def test_types_and_settings_leave_out_none() -> None:
    assert "none" not in KEEP_TYPES
    assert len(SETTINGS) == len(OBJECTTYPES) - 1 == 25
    assert "raw_material" in SETTINGS
    assert SETTINGS["weapon"] == "autokeep weapon"
    assert SETTINGS["raw_material"] == "autokeep raw material"


def test_is_kept() -> None:
    assert is_kept({"shortflags": "KG"})
    assert not is_kept({"shortflags": ""})
    assert not is_kept({"shortflags": None})
    assert not is_kept({})


def test_keep_serial() -> None:
    assert keep_serial({"serial": 12}) == 12
    for bad in (0, -3, True, "12", None):
        assert keep_serial({"serial": bad}) is None
    assert keep_serial({}) is None


def test_should_keep_returns_the_serial_for_an_enabled_type() -> None:
    asked: list[str] = []

    def enabled(name: str) -> bool:
        asked.append(name)
        return name == "weapon"

    item = {"serial": 1234, "itype": 5, "shortflags": "G"}
    assert should_keep(item, enabled) == 1234
    assert asked == ["weapon"]


def test_should_keep_asks_with_the_setting_name() -> None:
    asked: list[str] = []

    def enabled(name: str) -> bool:
        asked.append(name)
        return False

    should_keep({"serial": 1, "itype": OBJECTTYPES.index("raw material")}, enabled)
    assert asked == ["raw_material"]


def test_should_keep_returns_none_when_nothing_is_to_be_kept() -> None:
    on = {"serial": 1234, "itype": 5}
    assert should_keep(on, lambda name: False) is None
    assert should_keep({**on, "shortflags": "K"}, lambda name: True) is None
    assert should_keep({**on, "itype": 0}, lambda name: True) is None
    assert should_keep({**on, "itype": 99}, lambda name: True) is None
    assert should_keep({**on, "itype": "5"}, lambda name: True) is None
    assert should_keep({"itype": 5}, lambda name: True) is None
    assert should_keep({**on, "serial": 0}, lambda name: True) is None
    assert should_keep({**on, "serial": True}, lambda name: True) is None


def test_event_names_equal_eqs() -> None:
    assert EVENT_EQ_INVENTORY_ADDED == EVENT_INVENTORY_ADDED
    assert EVENT_EQ_TAKEN == EVENT_TAKEN
    assert EVENT_EQ_REMOVED == EVENT_REMOVED


def test_the_reply_patterns_match_the_sample_lines() -> None:
    for line in SAMPLE_REPLIES:
        assert re.match(KEEP_HIDE_START, line)
        assert any(re.match(regex, line) for regex in KEEP_REPLIES)
        assert any(re.match(trigger.regex, line) for trigger in TRIGGERS)
    assert not re.match(KEEP_HIDE_START, "You see nothing special.")


def test_the_keep_regex_matches_a_keep_command() -> None:
    assert re.match(KEEP_REGEX, "keep 1234")
    assert not re.match(KEEP_REGEX, "keep sword")
    assert not re.match(KEEP_REGEX, "keep 1234 5")
