"""Tests for the pure helpers of the itemid plugin."""

import copy
import re
from typing import Any

import pytest

from aardwolf.itemid.libs import (
    DIVIDER,
    WIDTH,
    IdentifyReader,
    InvdetailsReader,
    build_item,
    format_item,
    format_resist,
    format_stats,
    item_type_name,
    stats_header,
    to_int,
)


def strip(text: str) -> str:
    """Remove colour codes, as the colors plugin does."""
    return re.sub(r"@x\d{1,3}|@[A-Za-z]", "", text)


def skill_name(sn: int | str) -> str | None:
    """A skill table with one skill."""
    return "test skill" if sn == 5 else None


HEADER = "{invheader}12345|50|5|12000|7|wielded|glow, hum|Nobody|Example|-1|0|0|0|123"


def read(lines: list[tuple[str, str]]) -> dict[str, Any]:
    """Read (header, data) lines with a new reader."""
    reader = InvdetailsReader()
    reader.start()
    for header, data in lines:
        reader.line(header, data)
    return reader.result()


# InvdetailsReader


def test_invheader_and_the_mods_are_read() -> None:
    item = read(
        [
            ("invheader", HEADER.split("}")[1]),
            ("statmod", "Strength|2"),
            ("statmod", "Hit roll|-3"),
            ("resistmod", "Bash|5"),
            ("skillmod", "5|2"),
        ]
    )
    assert item["serial"] == 12345
    assert item["itype"] == 5
    assert item["flags"] == "glow, hum"
    assert item["statmod"] == {"Strength": 2, "Hit roll": -3}
    assert item["resistmod"] == {"Bash": 5}
    assert item["skillmod"] == {5: 2}


def test_enchant_and_tempmod_lines_are_collected() -> None:
    item = read(
        [
            ("enchant", "Brand,1,Hit roll,2,x,E"),
            ("enchant", "Brand,1,Damage roll,3,x,E"),
            ("tempmod", "7,0,0,Strength,30"),
            ("tempmod", "8,0,0,Wisdom,20"),
        ]
    )
    assert [e["stat"] for e in item["enchant"]] == ["Hit roll", "Damage roll"]
    assert [t["sn"] for t in item["tempmod"]] == [7, 8]


def test_the_single_detail_headers_are_read() -> None:
    item = read(
        [
            ("weapon", "dagger|17|Slice|Pierce|sharp"),
            ("container", "100|20|3|2|30|5|50"),
            ("light", "30"),
            ("portal", "4"),
            ("food", "12"),
            ("drink", "3|water|100|2|5|1|0"),
            ("furniture", "10|20|0"),
            ("spells", "3|10|7|0|0|0|0"),
        ]
    )
    assert item["weapon"]["avedam"] == 17
    assert item["container"]["capacity"] == 100
    assert item["light"] == {"duration": 30}
    assert item["portal"] == {"uses": 4}
    assert item["food"] == {"percent": 12}
    assert item["drink"]["liquid"] == "water"
    assert item["furniture"]["manaregen"] == 20
    assert item["spells"]["sn1"] == 7


def test_bad_lines_raise_value_error() -> None:
    reader = InvdetailsReader()
    with pytest.raises(ValueError, match="not found"):
        reader.line("nosuchheader", "1|2")
    with pytest.raises(ValueError, match="fields"):
        reader.line("weapon", "dagger|17")
    with pytest.raises(ValueError, match="eqdata"):
        reader.line("eqdata", "1,,x,1,1,0,-1,-1")
    with pytest.raises(ValueError):
        reader.line("statmod", "Strength|many")


def test_start_forgets_the_item_before() -> None:
    reader = InvdetailsReader()
    reader.line("invheader", "12345|50|5|12000|7|wielded|glow|Nobody|Example|-1|0|0|0|123")
    before = reader.has_header
    reader.start()
    assert (before, reader.has_header) == (True, False)
    assert reader.result() == {}


def test_result_is_a_copy() -> None:
    reader = InvdetailsReader()
    reader.line("statmod", "Strength|2")
    reader.result()["statmod"]["Strength"] = 99
    assert reader.result()["statmod"] == {"Strength": 2}


def test_to_int() -> None:
    assert to_int(" 5 ") == 5
    assert to_int(7) == 7
    with pytest.raises(ValueError):
        to_int(True)
    with pytest.raises(ValueError):
        to_int("x")


# IdentifyReader

BORDER = "+-----------------------------------------------------------------+"
IDENTIFY = [
    BORDER,
    "| Keywords   : gleaming test                                      |",
    "|            : blade                                              |",
    "|              flat                                               |",
    "| Name       : a gleaming test blade                              |",
    "| Id         : 12345                                              |",
    "| Type       : Weapon     Level : 50                              |",
    BORDER,
    "| Found at   : A test place                                       |",
    "| Material   : steel                                              |",
    "| Leads to   : Elsewhere                                          |",
    "| Reward.....: a test reward                                      |",
    BORDER,
    "| Affect Mods: haste, sanctuary                                   |",
    BORDER,
    "|   A first synthetic note and                                    |",
    "|   a second note line.                                           |",
    BORDER,
]


def feed_all(reader: IdentifyReader, lines: list[str]) -> list[bool]:
    """Feed lines, returning what feed said for each."""
    return [reader.feed(line) for line in lines]


def test_identify_fields_are_read_and_it_ends_at_a_blank_line() -> None:
    reader = IdentifyReader()
    results = feed_all(reader, [*IDENTIFY, ""])
    assert results == [False] * len(IDENTIFY) + [True]
    assert reader.fields == {
        "keywords": "gleaming test blade flat",
        "foundat": "A test place",
        "material": "steel",
        "leadsto": "Elsewhere",
        "reward": "a test reward",
        "affectmod": "haste, sanctuary",
    }
    assert reader.notes == ["A first synthetic note and", "a second note line."]
    assert reader.unknown == []


def test_a_prompt_ends_the_read() -> None:
    reader = IdentifyReader()
    assert feed_all(reader, [*IDENTIFY, "<100/100hp 50/50mn 90/90mv> "])[-1] is True


def test_lines_before_the_first_divider_are_ignored() -> None:
    reader = IdentifyReader()
    assert feed_all(reader, ["<100/100hp 50/50mn 90/90mv> ", "", "stray text"]) == [False] * 3
    assert not reader.started
    assert reader.feed(BORDER) is False
    assert reader.started


def test_result_has_the_notes_only_when_there_are_some() -> None:
    reader = IdentifyReader()
    feed_all(reader, IDENTIFY[:5])
    assert "notes" not in reader.result()
    feed_all(reader, IDENTIFY[5:])
    assert reader.result()["notes"] == ["A first synthetic note and", "a second note line."]


def test_an_unknown_label_is_reported_once_and_known_ones_are_skipped() -> None:
    reader = IdentifyReader()
    feed_all(
        reader,
        [
            BORDER,
            "| Mystery    : something                                          |",
            "|            : more                                               |",
            "| Mystery    : again                                              |",
            "| Weight     : 7                                                  |",
        ],
    )
    assert reader.unknown == ["mystery"]
    assert reader.fields == {}
    assert reader.notes == []


def test_reset_forgets_everything() -> None:
    reader = IdentifyReader()
    feed_all(reader, IDENTIFY)
    reader.reset()
    assert reader.result() == {}
    assert not reader.started


# build_item


def test_build_item_wraps_and_splits() -> None:
    details = read([("invheader", HEADER.split("}")[1])])
    idfields = {
        "keywords": "gleaming  test blade",
        "foundat": "A test place",
        "reward": "a test reward",
        "affectmod": "haste, sanctuary",
        "notes": ["one", "two"],
    }
    item = build_item(details, idfields)
    assert item["keywords"] == ["gleaming", "test", "blade"]
    assert item["flags"] == ["glow", "hum"]
    assert item["foundat"] == "A test place"
    assert item["reward"] == {"rtext": "a test reward"}
    assert item["notes"] == {"ntext": "one two"}
    assert item["affectmod"] == ["haste", "sanctuary"]
    assert "material" not in item
    assert details["flags"] == "glow, hum"


def test_build_item_without_keywords_or_flags_does_not_raise() -> None:
    item = build_item({"serial": 5}, {})
    assert item == {"serial": 5, "keywords": [], "flags": []}


# format_item


def full_item() -> dict[str, Any]:
    """A synthetic item with every section."""
    return {
        "serial": 12345,
        "keywords": ["gleaming", "test", "blade"],
        "cname": "@Ga gleaming test blade@w",
        "level": 50,
        "itype": 5,
        "worth": 12000,
        "weight": 7,
        "wearable": "wielded",
        "score": 123,
        "material": "steel",
        "flags": ["glow", "precious", "noshare"],
        "owner": "Nobody",
        "fromclan": "Example",
        "foundat": "A test place",
        "leadsto": "Elsewhere",
        "notes": {"ntext": "A synthetic note that is long enough to wrap onto a second line"},
        "affectmod": ["haste", "sanctuary"],
        "container": {
            "capacity": 100,
            "heaviestitem": 20,
            "holding": 3,
            "itemsinside": 2,
            "totalweight": 30,
            "itemburden": 5,
            "itemweightpercent": 50,
        },
        "weapon": {
            "wtype": "dagger",
            "avedam": 17,
            "inflicts": "Slice",
            "damtype": "Pierce",
            "special": "sharp",
        },
        "statmod": {"Strength": 2, "Hit roll": -3},
        "resistmod": {"Bash": 3, "Fire": -4, "All physical": 2},
        "skillmod": {5: 2, 6: -1},
        "enchant": [
            {
                "spell": "Brand",
                "etype": 1,
                "stat": "Hit roll",
                "mod": 2,
                "char": "x",
                "removable": "E",
            },
            {"spell": "Mark", "etype": 1, "stat": "Luck", "mod": -1, "char": "x", "removable": "N"},
        ],
        "spells": {"uses": 3, "level": 10, "sn1": 5, "sn2": 6, "sn3": 0, "sn4": 0},
        "food": {"percent": 12},
        "reward": {"rtext": "a test reward"},
        "drink": {
            "servings": 3,
            "liquid": "water",
            "liquidmax": 100,
            "thirstpercent": 5,
            "hungerpercent": 1,
        },
        "furniture": {"hpregen": 10, "manaregen": 20},
        "light": {"duration": 30},
    }


def box(
    item: dict[str, Any], location: str | None = "Inventory", slot: int | None = None
) -> list[str]:
    """Format an item with the test helpers."""
    return format_item(item, location, slot, skill_name, strip)


def test_every_line_of_a_full_item_is_the_box_width() -> None:
    lines = box(full_item())
    assert lines[0] == lines[-1] == DIVIDER
    assert [len(strip(line)) for line in lines] == [WIDTH] * len(lines)


def test_the_type_name_is_shown_not_the_number() -> None:
    text = "\n".join(strip(line) for line in box(full_item()))
    assert re.search(r"Type\s+: Weapon\s+Level\s+: 50", text)
    assert item_type_name({"itype": 5}) == "Weapon"
    assert item_type_name({"itype": 999}) is None
    assert item_type_name({"itype": "Weapon"}) is None


def test_a_light_with_no_detail_is_permanent_and_a_portal_shows_its_uses() -> None:
    light = {"serial": 1, "itype": 1, "level": 1}
    assert "Duration   : permanent" in "\n".join(strip(line) for line in box(light))
    portal = {"serial": 2, "itype": 20, "level": 1, "portal": {"uses": 4}}
    assert "Portal     : 4 uses remaining." in "\n".join(strip(line) for line in box(portal))
    not_a_portal = {"serial": 3, "itype": 5, "level": 1, "portal": {"uses": 4}}
    assert "uses remaining" not in "\n".join(box(not_a_portal))


def test_formatting_does_not_change_the_item() -> None:
    item = full_item()
    item["statmod"] = {"Strength": 2}
    item["resistmod"] = {"Bash": 3}
    before = copy.deepcopy(item)
    box(item)
    assert item == before


def test_negative_only_magic_resists_are_shown() -> None:
    rows = [strip(row) for row in format_resist({"Fire": -4})]
    assert any("Fire" in row for row in rows)
    assert any("-4" in row for row in rows)
    assert format_resist({}) == []
    assert all("Acid" not in row for row in format_resist({"Bash": 3}))


def test_stat_rows() -> None:
    assert strip(stats_header()).split() == [
        "|",
        "DR",
        "HR",
        "Str",
        "Int",
        "Wis",
        "Dex",
        "Con",
        "Luc",
        "Sav",
        "HP",
        "MN",
        "MV",
        "|",
    ]
    row = format_stats({"Strength": 2, "Hit roll": -3})
    assert "@G2" in row
    assert "@R-3" in row
    assert strip(row).split().count("-") == 10
    assert len(strip(row)) == len(strip(stats_header())) == WIDTH


def test_spells_drink_and_skill_names() -> None:
    text = "\n".join(strip(line) for line in box(full_item()))
    assert "3 uses of level 10 'test skill'" in text
    assert "3 uses of level 10 'sn 6'" in text
    assert "3 servings of water. Max: 5" in text
    assert "Modifies Test skill by +2" in text
    assert "Modifies sn 6 by -1" in text
    assert "(removable by enchanter)" in text


def test_worn_location_names_the_slot() -> None:
    text = "\n".join(strip(line) for line in box({"serial": 1}, "Worn", 24))
    assert "Location   : Worn - wielded" in text
    assert "Location   : Worn" in "\n".join(
        strip(line) for line in box({"serial": 1}, "Worn", None)
    )
    assert "Location   : 2002" in "\n".join(strip(line) for line in box({"serial": 1}, "2002"))
    assert "Location" not in "\n".join(box({"serial": 1}, None))


def test_a_sparse_item_does_not_raise() -> None:
    lines = box({"serial": 7}, None)
    assert [strip(line) for line in lines] == [
        DIVIDER,
        "| Id         : 7" + " " * 50 + "|",
        DIVIDER,
    ]
    item = {"serial": 8, "keywords": "one two", "flags": "glow", "drink": {"liquidmax": 0}}
    assert all(len(strip(line)) == WIDTH for line in box(item))
