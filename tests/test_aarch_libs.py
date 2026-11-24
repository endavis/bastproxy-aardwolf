"""Tests for the pure helpers of the aarch plugin."""

from pathlib import Path

import pytest

import aardwolf
from aardwolf.aarch.libs import (
    AARCH_BY_NAME,
    AARCH_ITEMS,
    AARCH_TAG,
    API_EQ_FIND_BY_NAME,
    count_items,
    need_lines,
    needed,
    normalise,
)


def tagged(name: str) -> str:
    """A name as eq holds it."""
    return f"{AARCH_TAG} {name}"


def test_table_has_fifty_numbered_pieces() -> None:
    assert list(AARCH_ITEMS) == list(range(1, 51))
    assert len(AARCH_BY_NAME) == 50
    assert all(AARCH_BY_NAME[normalise(name)] == number for number, name in AARCH_ITEMS.items())


@pytest.mark.parametrize(
    "name",
    [
        "(Aarchaeology) An Ancient Skull",
        "(Aarchaeology)   An  Ancient   Skull",
        "(Aarchaeology)An Ancient Skull",
        "(aarchaeology) an ANCIENT skull",
        "  An Ancient Skull  ",
        "An Ancient Skull",
    ],
)
def test_normalise(name: str) -> None:
    assert normalise(name) == "an ancient skull"


def test_count_known_item() -> None:
    count = count_items([tagged("An Ancient Skull")])
    assert (count.items, count.distinct, count.pamphlets) == (1, 1, 0)
    assert count.have == {2}
    assert count.unknown == ()


def test_count_duplicates() -> None:
    count = count_items([tagged("An Ancient Skull"), tagged("An Ancient Skull")])
    assert (count.items, count.distinct) == (2, 1)


@pytest.mark.parametrize(
    "name",
    [
        tagged("Collectable Pamphlet #12"),
        tagged("Collectable Pamphlet # 12"),
        tagged("Collectable Pamphlet #12 (used)"),
        tagged("collectable pamphlet #12"),
    ],
)
def test_pamphlet_counts_for_its_piece(name: str) -> None:
    count = count_items([name])
    assert (count.items, count.pamphlets) == (0, 1)
    assert count.have == {12}


@pytest.mark.parametrize("name", [tagged("Collectable Pamphlet"), tagged("Collectable Pamphlet #")])
def test_pamphlet_without_a_number_does_not_crash(name: str) -> None:
    """The old plugin raised on int(name.split('#')[1])."""
    count = count_items([name])
    assert count.pamphlets == 1
    assert count.have == frozenset()


def test_pamphlet_out_of_range_adds_no_piece() -> None:
    count = count_items([tagged("Collectable Pamphlet #99")])
    assert count.pamphlets == 1
    assert count.have == frozenset()


def test_unknown_name_is_kept() -> None:
    count = count_items([tagged("A  Strange   Thing")])
    assert count.unknown == ("A Strange Thing",)
    assert count.items == 0


def test_non_string_names_are_skipped() -> None:
    count = count_items([None, 5, tagged("Fox Tooth")])
    assert count.items == 1


def test_needed() -> None:
    assert needed([]) == list(range(1, 51))
    assert needed(range(1, 50)) == [50]
    assert needed(range(1, 51)) == []


def test_need_lines_without_filter() -> None:
    lines = need_lines(count_items([tagged("Johnny's Appleseed")]))
    assert lines[0] == "You have 1 Aarchaeology items (1 different) and 0 Pamphlets"
    assert lines[1] == "You need 49 pieces:"
    assert lines[2] == "2  - An Ancient Skull"
    assert len(lines) == 2 + 49


def test_row_format_pads_the_number() -> None:
    lines = need_lines(count_items([]))
    assert lines[2] == "1  - Johnny's Appleseed"
    assert lines[11] == "10 - An Old Coyote's Tooth"


@pytest.mark.parametrize("text", ["skull", "SKULL", "Skull", " skull "])
def test_filter_is_case_insensitive(text: str) -> None:
    """The old plugin compared the typed text to lower case names, so 'Skull' matched nothing."""
    lines = need_lines(count_items([]), text)
    assert lines[1] == f"You need 50 pieces, 1 match '{text.strip()}':"
    assert lines[2:] == ["2  - An Ancient Skull"]


def test_filter_with_several_matches() -> None:
    lines = need_lines(count_items([]), "rusted")
    assert lines[1] == "You need 50 pieces, 4 match 'rusted':"
    assert len(lines) == 6


def test_filter_with_no_match() -> None:
    lines = need_lines(count_items([]), "zzz")
    assert lines[1:] == ["You need 50 pieces, none match 'zzz'"]


def test_filter_counts_only_missing_pieces() -> None:
    lines = need_lines(count_items([tagged("An Ancient Skull")]), "skull")
    assert lines[1] == "You need 49 pieces, none match 'skull'"


def test_full_set() -> None:
    names = [tagged(name) for name in AARCH_ITEMS.values()]
    for text in ("", "skull"):
        lines = need_lines(count_items(names), text)
        assert lines == [
            "You have 50 Aarchaeology items (50 different) and 0 Pamphlets",
            "Congratulations! You have a full set of Aarchaeology items.",
        ]


def test_one_piece_left_is_singular() -> None:
    names = [tagged(AARCH_ITEMS[n]) for n in range(1, 50)]
    assert need_lines(count_items(names))[1] == "You need 1 piece:"


def test_unknown_names_are_listed() -> None:
    lines = need_lines(count_items([tagged("Mystery")]))
    assert lines[-1] == "Not a known piece: Mystery"


def test_spelling() -> None:
    assert "Aarcheology" not in "\n".join(need_lines(count_items([])))


def test_eq_still_provides_the_api() -> None:
    """The API name is a copy; eq's source must still register it."""
    plugin, name = API_EQ_FIND_BY_NAME.split(":")
    assert plugin == "plugins.aardwolf.eq"
    source = (Path(aardwolf.__file__).resolve().parent / "eq" / "plugin" / "_eq.py").read_text(
        encoding="utf-8"
    )
    assert f'"{name}"' in source
