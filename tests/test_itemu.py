"""Tests for the itemu helper library."""

import re

import pytest
from hypothesis import given
from hypothesis import strategies as st

from aardwolf._libs.itemu import (
    COMMA_LAYOUTS,
    INVLAYOUT,
    ITEMFLAGS,
    ITEMFLAGSCOLORS,
    ITEMFLAGSNAME,
    OBJECTTYPES,
    OBJECTTYPESREV,
    WEARLOCS,
    WEARLOCSREV,
    parse_item_data,
)


def _strip(text: str) -> str:
    """Remove ``@x`` colour codes."""
    return re.sub(r"@.", "", text)


def test_table_lengths() -> None:
    """The tables have the sizes of the old plugin."""
    assert len(OBJECTTYPES) == 26
    assert len(WEARLOCS) == 33
    assert len(ITEMFLAGS) == 5
    assert len(INVLAYOUT) == 15


def test_table_spot_values() -> None:
    """Values other plugins rely on."""
    assert OBJECTTYPES[11] == "container"
    assert WEARLOCS[0] == "light"
    assert WEARLOCS[-1] == "sleeping"


def test_reverse_tables_round_trip() -> None:
    """The reverse tables invert the lists."""
    assert [OBJECTTYPESREV[n] for n in OBJECTTYPES] == list(range(len(OBJECTTYPES)))
    assert [WEARLOCSREV[n] for n in WEARLOCS] == list(range(len(WEARLOCS)))


def test_flag_tables_share_keys() -> None:
    """Colour and name tables cover exactly the flags."""
    assert set(ITEMFLAGSCOLORS) == set(ITEMFLAGS)
    assert set(ITEMFLAGSNAME) == set(ITEMFLAGS)


def test_invheader() -> None:
    """A pipe layout gives ints for numbers and keeps text."""
    item = parse_item_data("12345|201|5|1000|10|1|0|Bast|0|0|0|0|0|300", "invheader")
    assert item == {
        "serial": 12345,
        "level": 201,
        "itype": 5,
        "worth": 1000,
        "weight": 10,
        "wearable": 1,
        "flags": 0,
        "owner": "Bast",
        "fromclan": 0,
        "timer": 0,
        "u1": 0,
        "u2": 0,
        "u3": 0,
        "score": 300,
    }


def test_other_pipe_layouts() -> None:
    """Container, weapon, statmod and drink parse."""
    assert parse_item_data("1|2|3|4|5|6|7", "container")["itemweightpercent"] == 7
    assert parse_item_data("axe|10|slash|sharp|flaming", "weapon") == {
        "wtype": "axe",
        "avedam": 10,
        "inflicts": "slash",
        "damtype": "sharp",
        "special": "flaming",
    }
    assert parse_item_data("Strength|5", "statmod") == {"name": "Strength", "value": 5}
    assert parse_item_data("1|water|10|5|1|2|0", "drink")["liquid"] == "water"


def test_eqdata() -> None:
    """eqdata splits on commas, keeps cname raw and adds a stripped name."""
    item = parse_item_data("12345,K,@Ra @Wsword@w,201,5,1,24,-1", "eqdata", _strip)
    assert item["name"] == "a sword"
    assert item["cname"] == "@Ra @Wsword@w"
    assert item["timer"] == -1
    assert item["shortflags"] == "K"


def test_comma_layouts() -> None:
    """tempmod and enchant split on commas."""
    assert parse_item_data("1,2,3,4,5", "tempmod")["duration"] == 5
    assert parse_item_data("bless,1,hit,2,x,y", "enchant")["spell"] == "bless"


def test_empty_field_stays_string() -> None:
    """An empty field is kept as an empty string."""
    assert parse_item_data("|5", "statmod") == {"name": "", "value": 5}


def test_extra_fields_ignored() -> None:
    """Fields beyond the layout are dropped."""
    assert parse_item_data("a|1|extra|more", "statmod") == {"name": "a", "value": 1}


def test_short_line_raises() -> None:
    """A short line raises and names the line."""
    with pytest.raises(ValueError, match="1\\|2"):
        parse_item_data("1|2", "container")


def test_unknown_layout_raises() -> None:
    """An unknown layout raises."""
    with pytest.raises(ValueError, match="nolayout"):
        parse_item_data("1|2", "nolayout")


def test_eqdata_without_strip_color_raises() -> None:
    """eqdata needs strip_color."""
    with pytest.raises(ValueError, match="strip_color"):
        parse_item_data("1,K,x,1,1,1,1,1", "eqdata")


@pytest.mark.property
@given(st.sampled_from(sorted(INVLAYOUT)), st.data())
def test_round_trip_every_layout(layout: str, data: st.DataObject) -> None:
    """Round-trip: values joined with the layout's separator parse back to the layout names."""
    names = INVLAYOUT[layout]
    values: list[int | str] = list(
        data.draw(st.lists(st.integers(), min_size=len(names), max_size=len(names)))
    )
    if layout == "eqdata":
        # letters only, so the text can never be read back as an int
        values[names.index("cname")] = data.draw(st.text(alphabet="abc xyz", min_size=1))
    sep = "," if layout in COMMA_LAYOUTS else "|"
    item = parse_item_data(sep.join(str(v) for v in values), layout, _strip)
    if layout == "eqdata":
        item.pop("name")
    assert item == dict(zip(names, values, strict=True))


def test_invheader_type_name_becomes_the_number() -> None:
    """Real Aardwolf sends the type as a name; it is mapped to the number, any case."""
    base = "3984278750|1|{}|15|2|wield|melt-drop, v3|||||||16"
    assert parse_item_data(base.format("Weapon"), "invheader")["itype"] == 5
    assert parse_item_data(base.format("Armor"), "invheader")["itype"] == 7
    assert parse_item_data(base.format("Light"), "invheader")["itype"] == 1
    assert parse_item_data(base.format("Container"), "invheader")["itype"] == 11
    assert parse_item_data(base.format("weapon"), "invheader")["itype"] == 5
    assert parse_item_data(base.format("Raw Material"), "invheader")["itype"] == 24
    assert parse_item_data(base.format("Mystery"), "invheader")["itype"] == "Mystery"
    assert parse_item_data(base.format("5"), "invheader")["itype"] == 5
