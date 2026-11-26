"""Tests for the pure helpers of the hunger plugin."""

import re

import pytest

from aardwolf.hunger.libs import (
    DRINK_CMD,
    FILL_CMD,
    FILL_FROM_CMD,
    GULP_CMD,
    REPLY_TRIGGERS,
    STAGE_TRIGGERS,
    choose_item,
    cooldown_ok,
    fill_command,
    parse_item_setting,
    room_num,
    should_autofill,
)

STAGE_LINES = [
    "You start to feel hungry.",
    "You are very hungry; your healing is reduced.",
    "You are starving; your healing is greatly reduced.",
    "You start to feel thirsty.",
    "You are very thirsty; your healing is reduced.",
    "You are dehydrated; your healing is greatly reduced.",
]
REPLY_LINES = {
    "hunger_drank": "You drink some orange juice from Sacramental Carafe.",
    "hunger_empty": "Sacramental Carafe is empty.",
    "hunger_filled": "You fill Sacramental Carafe with orange juice.",
    "hunger_full": "Sacramental Carafe is already full.",
    "hunger_nosource": "There is no liquid source here.",
}
NEAR_MISSES = [
    "You are now full.",
    "You pour out Sacramental Carafe, spilling orange juice onto the ground.",
    "You start to feel hungry",
    "You are very hungry; your healing is greatly reduced.",
    "You are starving; your healing is reduced.",
    "You feel hungry.",
    "",
]


def matching(specs: tuple[object, ...], line: str) -> list[str]:
    """Return the names of the triggers whose regex matches the line."""
    return [s.name for s in specs if re.match(s.regex, line)]  # type: ignore[attr-defined]


@pytest.mark.parametrize("prefix", ["", "## "])
@pytest.mark.parametrize("line", STAGE_LINES)
def test_stage_line_matches_one_stage_trigger(prefix: str, line: str) -> None:
    assert len(matching(STAGE_TRIGGERS, prefix + line)) == 1
    assert matching(REPLY_TRIGGERS, prefix + line) == []


@pytest.mark.parametrize(("name", "line"), REPLY_LINES.items())
def test_reply_line_matches_only_its_trigger(name: str, line: str) -> None:
    assert matching(REPLY_TRIGGERS, line) == [name]
    assert matching(STAGE_TRIGGERS, line) == []


@pytest.mark.parametrize("line", NEAR_MISSES)
def test_near_misses_match_nothing(line: str) -> None:
    assert matching(STAGE_TRIGGERS, line) == []
    assert matching(REPLY_TRIGGERS, line) == []


def test_reply_groups() -> None:
    drank = re.match(REPLY_TRIGGERS[0].regex, REPLY_LINES["hunger_drank"])
    assert drank is not None
    assert drank.group("liquid") == "some orange juice"
    assert drank.group("container") == "Sacramental Carafe"
    empty = re.match(REPLY_TRIGGERS[1].regex, REPLY_LINES["hunger_empty"])
    assert empty is not None
    assert empty.group("container") == "Sacramental Carafe"


@pytest.mark.parametrize(
    ("value", "expected"),
    [("", None), ("  ", None), (None, None), ("123", 123), (" 45 ", 45), ("cara", "cara")],
)
def test_parse_item_setting(value: object, expected: object) -> None:
    assert parse_item_setting(value) == expected


def test_choose_item_prefers_inventory_then_bag() -> None:
    bag = {"serial": 2, "container": "900"}
    inventory = {"serial": 3, "container": "Inventory"}
    assert choose_item([bag, inventory]) == 3
    assert choose_item([bag]) == 2
    assert choose_item([]) is None


@pytest.mark.parametrize("place", ["Worn", "Vault", "Keyring", "", None])
def test_choose_item_skips_other_places(place: str | None) -> None:
    assert choose_item([{"serial": 1, "container": place}]) is None


def test_choose_item_skips_bad_serials() -> None:
    assert choose_item([{"serial": True, "container": "Inventory"}]) is None
    assert choose_item([{"serial": "5", "container": "Inventory"}]) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1234, "1234"),
        ("1234", "1234"),
        (" 07 ", "7"),
        (None, None),
        (0, None),
        (-1, None),
        ("-1", None),
        (True, None),
        ("abc", None),
        ("", None),
        (1.5, None),
    ],
)
def test_room_num(value: object, expected: str | None) -> None:
    assert room_num(value) == expected


def test_cooldown_ok_boundaries() -> None:
    assert cooldown_ok(None, 0.0, 60)
    assert not cooldown_ok(100.0, 159.9, 60)
    assert cooldown_ok(100.0, 160.0, 60)
    assert cooldown_ok(100.0, 500.0, 60)


@pytest.mark.parametrize(
    ("room", "fillroom", "empty", "busy", "expected"),
    [
        ("1", "1", True, False, True),
        ("1", "1", False, False, False),
        ("1", "1", True, True, False),
        ("2", "1", True, False, False),
        (None, "1", True, False, False),
        ("1", "", True, False, False),
        (None, "", True, False, False),
    ],
)
def test_should_autofill(
    room: str | None, fillroom: str, empty: bool, busy: bool, expected: bool
) -> None:
    assert should_autofill(room, fillroom, empty, busy) is expected


def test_commands() -> None:
    assert DRINK_CMD.format(item=5) == "drink 5"
    assert FILL_CMD.format(item=5) == "fill 5"
    assert FILL_FROM_CMD.format(item=5, source="fountain") == "fill 5 fountain"
    assert fill_command(5) == "fill 5"
    assert fill_command(5, "fountain") == "fill 5 fountain"


def test_gulp_command() -> None:
    assert GULP_CMD.format(item=5) == "gulp 5"


GULP_LINE = "You gulp down some orange juice from Sacramental Carafe."


@pytest.mark.parametrize("line", [REPLY_LINES["hunger_drank"], GULP_LINE])
def test_drank_trigger_matches_drink_and_gulp(line: str) -> None:
    assert matching(REPLY_TRIGGERS, line) == ["hunger_drank"]
    drank = re.match(REPLY_TRIGGERS[0].regex, line)
    assert drank is not None
    assert drank.group("liquid") == "some orange juice"
    assert drank.group("container") == "Sacramental Carafe"


def test_now_full_line_matches_no_reply_trigger() -> None:
    assert matching(REPLY_TRIGGERS, "You are now full.") == []
