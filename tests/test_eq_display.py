"""Tests for the pure eq and inv table builders."""

import itertools
import re
from typing import Any

from aardwolf._libs.itemu import WEARLOCS, WEARLOCSREV
from aardwolf.eq.libs import (
    OPTIONAL_SLOTS,
    SCORE_DEFAULT,
    DisplayOptions,
    container_lines,
    inventory_extra_lines,
    vault_count_lines,
    worn_lines,
)
from aardwolf.eq.libs._display import RULE, keyring_count_line

SLOTS = len(WEARLOCS)


def strip(text: str) -> str:
    """Remove the colour codes."""
    return re.sub(r"@x\d{1,3}|@[A-Za-z]", "", text)


def item(serial: int, name: str = "a test sword", **kw: object) -> dict[str, Any]:
    """A synthetic item."""
    data: dict[str, Any] = {
        "serial": serial,
        "shortflags": "",
        "cname": name,
        "name": name,
        "level": 10,
    }
    data.update(kw)
    return data


def worn(*placed: tuple[int, dict[str, Any]]) -> tuple[list[int | None], dict[int, dict[str, Any]]]:
    """Slots and items for the placed (slot, item) pairs."""
    slots: list[int | None] = [None] * SLOTS
    items: dict[int, dict[str, Any]] = {}
    for slot, data in placed:
        slots[slot] = data["serial"]
        items[data["serial"]] = data
    return slots, items


def test_worn_default_layout_and_colours() -> None:
    slots, items = worn(
        (WEARLOCSREV["wielded"], item(1)),
        (WEARLOCSREV["light"], item(2)),
        (WEARLOCSREV["above"], item(3)),
        (WEARLOCSREV["portal"], item(4)),
        (WEARLOCSREV["sleeping"], item(5)),
        (WEARLOCSREV["head"], item(6)),
    )
    lines = worn_lines(slots, items, DisplayOptions())
    assert lines[0] == "You are using:"
    assert "Location" in lines[1]
    assert "Lvl" in lines[1]
    assert "Item Name" in lines[1]
    assert lines[2] == RULE
    assert lines[-1] == ""
    text = "\n".join(lines)
    assert "@Rwielded" in text
    assert "@Wlight" in text
    assert "@Wabove" in text
    assert "@Cportal" in text
    assert "@Csleeping" in text
    assert "@chead" in text
    assert "@x " not in text


def test_optional_empty_slots_are_hidden_and_filled_ones_shown() -> None:
    slots, items = worn((WEARLOCSREV["medal1"], item(1, "a test medal")))
    text = "\n".join(strip(line) for line in worn_lines(slots, items, DisplayOptions()))
    assert "medal1" in text
    for slot in OPTIONAL_SLOTS - {WEARLOCSREV["medal1"]}:
        assert WEARLOCS[slot] not in text
    assert "< empty >" in text
    assert re.search(r"head\s+\] .*< empty >", text)


def test_second_hides_shield_and_hold_only_when_filled() -> None:
    empty = "\n".join(worn_lines(*worn(), DisplayOptions()))
    assert "shield" in empty
    assert "hold" in empty
    slots, items = worn((WEARLOCSREV["second"], item(1)))
    text = "\n".join(worn_lines(slots, items, DisplayOptions()))
    assert "second" in text
    assert "shield" not in text
    assert "hold" not in text


def test_noflags_and_flag_cells() -> None:
    slots, items = worn(
        (WEARLOCSREV["wielded"], item(1, shortflags="KG")),
        (WEARLOCSREV["head"], item(2)),
    )
    plain = worn_lines(slots, items, DisplayOptions(noflags=True))
    assert "@RK" not in "\n".join(plain)
    assert plain[1].count("(") == 1
    full = worn_lines(slots, items, DisplayOptions())
    wielded = next(line for line in full if "wielded" in line)
    head = next(line for line in full if "head" in line)
    assert "@RK" in wielded
    assert "@WG" in wielded
    assert len(strip(wielded).split("a test sword")[0]) == len(strip(head).split("a test sword")[0])


def test_serial_and_score_columns() -> None:
    slots, items = worn(
        (WEARLOCSREV["wielded"], item(1001, score=1234)),
        (WEARLOCSREV["head"], item(2)),
    )
    lines = worn_lines(slots, items, DisplayOptions(serial=True, score=True))
    assert "Serial" in lines[1]
    assert "Score" in lines[1]
    wielded = next(line for line in lines if "wielded" in line)
    head = next(line for line in lines if "head" in line)
    assert f"{1001:<12}" in wielded
    assert " 1234" in wielded
    assert SCORE_DEFAULT in head


def test_column_widths_line_up_for_every_option_combination() -> None:
    slots, items = worn(
        (WEARLOCSREV["wielded"], item(1001, "NAME", shortflags="KG", score=12)),
        (WEARLOCSREV["head"], item(2, "NAME", level=0)),
    )
    for noflags, score, serial in itertools.product([False, True], repeat=3):
        opts = DisplayOptions(noflags=noflags, score=score, serial=serial)
        lines = worn_lines(slots, items, opts)
        offset = strip(lines[1]).index("Item Name")
        rows = [strip(line) for line in lines[3:-1]]
        assert any("wielded" in row for row in rows)
        for row in rows:
            name = "NAME" if "NAME" in row else "< empty >"
            assert row.index(name) == offset


def test_missing_item_is_shown_as_empty() -> None:
    slots: list[int | None] = [None] * SLOTS
    slots[WEARLOCSREV["head"]] = 999
    lines = worn_lines(slots, {}, DisplayOptions())
    assert any("head" in line and "< empty >" in line for line in lines)


def test_empty_container() -> None:
    lines = container_lines("Keyring", [], {}, DisplayOptions())
    assert lines == [
        "Items in Keyring:",
        lines[1],
        RULE,
        "You have nothing in Keyring",
        "",
    ]


def potions(count: int = 3) -> tuple[list[int], dict[int, dict[str, Any]]]:
    """Identical potions with different serials."""
    serials = list(range(100, 100 + count))
    return serials, {s: item(s, "a test potion") for s in serials}


def test_grouping_folds_like_items() -> None:
    serials, items = potions()
    lines = container_lines("Inventory", serials, items, DisplayOptions(nogroup=False))
    rows = lines[3:-1]
    assert len(rows) == 1
    assert rows[0].startswith("(  3) ")
    assert strip(lines[1]).startswith("   #  ")
    lines = container_lines("Inventory", serials, items, DisplayOptions(nogroup=False, serial=True))
    assert f"{'Many':<12}" in lines[3]
    assert "100" not in lines[3]


def test_nogroup_gives_a_row_per_item_without_count() -> None:
    serials, items = potions()
    lines = container_lines("Inventory", serials, items, DisplayOptions(nogroup=True))
    rows = lines[3:-1]
    assert len(rows) == 3
    assert "#" not in lines[1]
    assert all("(  3)" not in row for row in rows)


def test_different_level_or_flags_do_not_group() -> None:
    items = {
        1: item(1, "a test potion"),
        2: item(2, "a test potion", level=11),
        3: item(3, "a test potion", shortflags="K"),
        4: item(4, "a test potion"),
    }
    lines = container_lines("Inventory", [1, 2, 3, 4], items, DisplayOptions(nogroup=False))
    assert len(lines[3:-1]) == 3
    assert lines[3].startswith("(  2) ")


def test_container_widths_line_up() -> None:
    serials, items = potions(2)
    items[200] = item(200, "a test sword", shortflags="KG", level=0, score=7)
    serials.append(200)
    for noflags, score, serial, nogroup in itertools.product([False, True], repeat=4):
        opts = DisplayOptions(noflags=noflags, score=score, serial=serial, nogroup=nogroup)
        lines = container_lines("Inventory", serials, items, opts)
        offset = strip(lines[1]).index("Item Name")
        for row in (strip(r) for r in lines[3:-1]):
            assert row.index("a test") == offset


def test_level_zero_is_blank_in_containers() -> None:
    lines = container_lines("Inventory", [1], {1: item(1, level=0)}, DisplayOptions())
    assert "(   )" in strip(lines[3])


def test_vault_counts_are_compared_as_ints() -> None:
    lines = vault_count_lines({"items": 9, "total": 10, "max": 50})
    assert len(lines) == 3
    assert "Including keep flagged items, you have @Y10@w" in lines[1]
    assert lines[-1] == ""
    same = vault_count_lines({"items": 10, "total": 10, "max": 50})
    assert len(same) == 2


def test_inventory_extra_lines() -> None:
    assert inventory_extra_lines(0, None) == []
    assert inventory_extra_lines(2, None) == ["@C( 2)@W ** Item(s) on Keyring **@w", ""]
    assert keyring_count_line(2) == "@C( 2)@W ** Item(s) on Keyring **@w"
    assert inventory_extra_lines(0, {"items": 0, "total": 0, "max": 50}) == []
    lines = inventory_extra_lines(0, {"items": 1, "total": 1, "max": 50})
    assert "@Y1@w of @Y50@w" in lines[0]
