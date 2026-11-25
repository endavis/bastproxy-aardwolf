"""Tests for the eq plugin's pure helpers: the item line parser, the commands and the state."""

import re
from typing import Any

import pytest

from aardwolf.eq.libs import (
    CONTAINER_ITYPE,
    INVENTORY,
    KEYRING,
    SUFFIX_INVENTORY_ADDED,
    SUFFIX_INVENTORY_REMOVED,
    SUFFIX_PUT,
    SUFFIX_REMOVED,
    SUFFIX_TAKEN,
    SUFFIX_WORN,
    VAULT,
    WORN,
    EqState,
    container_type,
    get_command,
    parse_item_line,
    put_command,
    quote_arg,
    tag_container,
    to_serial,
    type_for,
)


def strip(text: str) -> str:
    """A stand-in for the colour code stripper: remove @x### and @c codes."""
    import re

    return re.sub(r"@x\d{1,3}|@[A-Za-z]", "", text)


def item(serial: int, name: str = "a test sword", **kw: object) -> dict[str, Any]:
    """A parsed item line, with synthetic values."""
    data: dict[str, Any] = {
        "serial": serial,
        "shortflags": "",
        "cname": name,
        "name": name,
        "level": 10,
        "itype": 5,
        "unique": False,
        "wearslot": -1,
        "timer": -1,
    }
    data.update(kw)
    return data


# the parser


def test_parse_plain_line() -> None:
    parsed = parse_item_line("1001,KG,a test sword,25,5,0,24,-1", None, strip)
    assert parsed == {
        "serial": 1001,
        "shortflags": "KG",
        "cname": "a test sword",
        "name": "a test sword",
        "level": 25,
        "itype": 5,
        "unique": False,
        "wearslot": 24,
        "timer": -1,
    }


def test_parse_keeps_commas_in_the_name() -> None:
    parsed = parse_item_line("1002,,a ring, of tests, and more,5,7,1,-1,30", None, strip)
    assert parsed is not None
    assert parsed["name"] == "a ring, of tests, and more"
    assert parsed["unique"] is True
    assert parsed["timer"] == 30


def test_parse_allows_leading_spaces() -> None:
    parsed = parse_item_line("  1003,H,a cloak,1,7,0,7,-1", None, strip)
    assert parsed is not None
    assert parsed["serial"] == 1003


def test_parse_colorcoded_name_keeps_codes_and_name_is_stripped() -> None:
    colored = "@w1004,K,@Ra @Wtest @wshield@w,9,7,0,23,-1@w"
    parsed = parse_item_line("1004,K,a test shield,9,7,0,23,-1", colored, strip)
    assert parsed is not None
    assert parsed["cname"] == "@Ra @Wtest @wshield@w"
    assert parsed["name"] == "a test shield"


def test_parse_colorcoded_invitem_line() -> None:
    colored = "{invitem}1005,,@x196red @x46glow@w,3,1,0,-1,-1"
    parsed = parse_item_line("1005,,red glow,3,1,0,-1,-1", colored, strip)
    assert parsed is not None
    assert parsed["cname"] == "@x196red @x46glow@w"
    assert parsed["name"] == "red glow"


def test_parse_falls_back_to_the_plain_name() -> None:
    parsed = parse_item_line("1006,,a lamp,3,1,0,-1,-1", "garbled text", strip)
    assert parsed is not None
    assert parsed["cname"] == "a lamp"
    parsed = parse_item_line("1006,,a lamp,3,1,0,-1,-1", b"bytes", strip)
    assert parsed is not None
    assert parsed["cname"] == "a lamp"


@pytest.mark.parametrize("line", ["", "not an item", "1,2,3", "x,,name,1,1,0,-1,-1", "{eqdata}"])
def test_parse_rejects_malformed_lines(line: str) -> None:
    assert parse_item_line(line, None, strip) is None


# containers and commands


def test_tag_container() -> None:
    assert tag_container("invdata", None) == INVENTORY
    assert tag_container("invdata", "") == INVENTORY
    assert tag_container("invdata", "4321") == "4321"
    assert tag_container("eqdata", None) == WORN
    assert tag_container("keyring", None) == KEYRING
    assert tag_container("vault", None) == VAULT
    assert tag_container("vault", "5") is None
    assert tag_container("other", None) is None


def test_container_type_spec() -> None:
    spec = container_type(4321)
    assert spec.cmdtype == "eq_container_4321"
    assert spec.cmd == "invdata 4321"
    assert spec.regex == r"^invdata 4321$"
    assert spec.hide_start == r"^\{invdata 4321\}$"
    assert type_for("4321") == spec
    assert re.match(type_for(VAULT).hide_start, "{vault}")
    assert re.match(
        type_for(VAULT).hide_start,
        "You do not have a vault. See 'help vault' for how to acquire one.",
    )
    assert not re.match(type_for(VAULT).hide_start, "{vaultcounts}1,1,50{/vaultcounts}")
    assert type_for(WORN).cmdtype == "eq_worn"


def test_get_commands() -> None:
    assert get_command(INVENTORY, 7) is None
    assert get_command(WORN, 7) == "remove 7"
    assert get_command(KEYRING, 7) == "keyring get 7"
    assert get_command(VAULT, 7) == "vault get 7"
    assert get_command("99", 7) == "get 7 99"


def test_put_commands() -> None:
    assert put_command(INVENTORY, 7) is None
    assert put_command(WORN, 7) == "wear 7"
    assert put_command(WORN, 7, "wielded") == "wear 7 wielded"
    assert put_command(KEYRING, 7) == "keyring put 7"
    assert put_command(VAULT, 7) == "vault put 7"
    assert put_command("99", 7) == "put 7 99"


def test_quote_arg_and_to_serial() -> None:
    assert quote_arg("sword") == "sword"
    assert quote_arg("two words") == "'two words'"
    assert to_serial("12") == 12
    assert to_serial(12) == 12
    assert to_serial("x") is None
    assert to_serial("-3") is None
    assert to_serial(True) is None
    assert to_serial(None) is None


# the state


def test_commit_inventory_keeps_order_and_marks_container() -> None:
    state = EqState()
    state.commit(INVENTORY, [item(1), item(2), item(3)])
    assert state.container_copy(INVENTORY) == {"cid": INVENTORY, "items": [1, 2, 3]}
    assert state.items[2]["container"] == INVENTORY


def test_commit_worn_places_by_slot_including_slot_zero() -> None:
    state = EqState()
    state.commit(WORN, [item(1, wearslot=0), item(2, wearslot=24), item(3, wearslot=1)])
    assert state.worn[0] == 1
    assert state.worn[1] == 3
    assert state.worn[24] == 2
    worn = state.container_copy(WORN)
    assert worn is not None
    assert worn["items"] == [1, 3, 2]
    assert state.worn_at(0) is not None


def test_commit_worn_skips_an_out_of_range_slot() -> None:
    state = EqState()
    state.commit(WORN, [item(1, wearslot=99), item(2, wearslot=-1), item(3, wearslot=4)])
    assert state.serials(WORN) == [3]
    assert 1 not in state.items


def test_recommit_clears_container_of_items_that_left() -> None:
    state = EqState()
    state.commit(INVENTORY, [item(1), item(2)])
    state.commit(INVENTORY, [item(2)])
    assert state.items[1]["container"] is None
    assert state.items[2]["container"] == INVENTORY


def test_commit_returns_new_bags_once() -> None:
    state = EqState()
    bag = item(50, "a test bag", itype=CONTAINER_ITYPE)
    assert state.commit(INVENTORY, [item(1), bag]) == ["50"]
    assert state.commit(INVENTORY, [item(1), bag]) == []
    assert state.commit("50", [item(2)]) == []
    assert state.container_copy(50) == {"cid": "50", "items": [2]}


def test_commit_into_a_bag_finds_nested_bags() -> None:
    state = EqState()
    state.commit(INVENTORY, [item(50, itype=CONTAINER_ITYPE)])
    assert state.commit("50", [item(51, itype=CONTAINER_ITYPE)]) == ["51"]


def test_commit_inventory_drops_a_bag_that_left() -> None:
    state = EqState()
    state.commit(INVENTORY, [item(50, itype=CONTAINER_ITYPE)])
    state.commit("50", [item(2)])
    state.commit(INVENTORY, [])
    assert state.container_copy(50) is None
    assert 2 not in state.items


def test_commit_keeps_identify_data_and_hasbeenided() -> None:
    state = EqState()
    state.commit(INVENTORY, [item(1)])
    state.items[1]["hasbeenided"] = True
    state.items[1]["material"] = "test"
    state.commit(INVENTORY, [item(1, level=11)])
    assert state.items[1]["level"] == 11
    assert state.items[1]["material"] == "test"
    assert state.items[1]["hasbeenided"] is True


def test_move_keeps_a_single_location() -> None:
    state = EqState()
    state.commit(INVENTORY, [item(1), item(2)])
    assert state.move(1, KEYRING, 0)
    assert state.move(1, VAULT)
    assert state.serials(INVENTORY) == [2]
    assert state.serials(KEYRING) == []
    assert state.serials(VAULT) == [1]
    assert state.items[1]["container"] == VAULT
    assert state.move(1, WORN, 3)
    assert state.serials(VAULT) == []
    assert state.worn[3] == 1
    assert not state.move(99, INVENTORY)
    assert not state.move(2, WORN, 99)
    assert not state.move(2, WORN, None)
    assert state.serials(INVENTORY) == [2]


def test_move_to_an_occupied_slot_sends_the_occupant_to_the_inventory() -> None:
    state = EqState()
    state.commit(INVENTORY, [item(1), item(2)])
    state.move(1, WORN, 5)
    state.move(2, WORN, 5)
    assert state.worn[5] == 2
    assert state.items[1]["container"] == INVENTORY


def test_move_clears_origcontainer_when_the_item_returns() -> None:
    state = EqState()
    state.commit(WORN, [item(1, wearslot=24)])
    state.set_origin(1)
    assert state.items[1]["origcontainer"] == WORN
    state.move(1, INVENTORY, 0)
    assert state.items[1]["origcontainer"] == WORN
    state.move(1, WORN, 24)
    assert state.items[1]["origcontainer"] is None


def test_set_origin_ignores_the_inventory_and_unknown_items() -> None:
    state = EqState()
    state.commit(INVENTORY, [item(1)])
    state.set_origin(1)
    state.set_origin(99)
    assert state.items[1]["origcontainer"] is None


def test_worn_at_never_raises() -> None:
    state = EqState()
    state.commit(WORN, [item(1, wearslot=24)])
    for good in (24, "24", "wielded", " Wielded "):
        found = state.worn_at(good)
        assert found is not None
        assert found["serial"] == 1
    for bad in (25, "second", "nowhere", "", -1, 999, "999", True, None, 2.5, "-1"):
        assert state.worn_at(bad) is None  # type: ignore[arg-type]


def test_reads_return_copies() -> None:
    state = EqState()
    state.commit(INVENTORY, [item(1, "a test sword")])
    copied = state.item_copy(1)
    assert copied is not None
    copied["name"] = "changed"
    assert state.items[1]["name"] == "a test sword"
    found = state.find_by_name("test")
    assert [f["serial"] for f in found] == [1]
    found[0]["name"] = "changed"
    assert state.items[1]["name"] == "a test sword"
    assert state.find_by_name("TEST") == []
    container = state.container_copy(INVENTORY)
    assert container is not None
    container["items"].append(99)
    assert state.serials(INVENTORY) == [1]
    worn = state.container_copy(WORN)
    assert worn is not None
    worn["slots"][0] = 5
    assert state.worn[0] is None
    assert state.item_copy(404) is None
    assert state.container_copy("404") is None


def test_vault_counts_in_the_container_copy() -> None:
    state = EqState()
    state.vault_counts = {"items": 2, "total": 5, "max": 100}
    vault = state.container_copy(VAULT)
    assert vault is not None
    assert vault["counts"] == {"items": 2, "total": 5, "max": 100}
    vault["counts"]["items"] = 9
    assert state.vault_counts["items"] == 2


# invmon


def seeded() -> EqState:
    """Inventory 1, 2 and bag 50 (holding 3), worn 10 at slot 24, keyring 20, vault 30."""
    state = EqState()
    state.commit(INVENTORY, [item(1), item(2), item(50, "a test bag", itype=CONTAINER_ITYPE)])
    state.commit("50", [item(3)])
    state.commit(WORN, [item(10, wearslot=24)])
    state.commit(KEYRING, [item(20, itype=13)])
    state.commit(VAULT, [item(30)])
    return state


def test_invmon_remove() -> None:
    state = seeded()
    out = state.apply_invmon(1, 10, -1, 24)
    assert state.serials(INVENTORY)[0] == 10
    assert state.worn[24] is None
    assert state.lastworn == {10: 24}
    assert out.refresh == []
    assert [e[0] for e in out.events] == [SUFFIX_REMOVED]
    assert out.events[0][1]["location"] == 24
    assert out.events[0][1]["item"]["serial"] == 10


def test_invmon_remove_of_an_item_not_worn_refreshes() -> None:
    state = seeded()
    out = state.apply_invmon(1, 1, -1, 24)
    assert out.refresh == [WORN, INVENTORY]
    assert out.events == []


def test_invmon_wear() -> None:
    state = seeded()
    out = state.apply_invmon(2, 1, -1, 0)
    assert state.worn[0] == 1
    assert 1 not in state.serials(INVENTORY)
    assert out.events[0][0] == SUFFIX_WORN
    assert out.events[0][1]["location"] == 0


def test_invmon_wear_of_an_item_not_in_the_inventory_refreshes() -> None:
    state = seeded()
    assert state.apply_invmon(2, 30, -1, 3).refresh == [INVENTORY, WORN]
    assert state.apply_invmon(2, 1, -1, 99).refresh == [INVENTORY, WORN]
    assert state.worn_at(3) is None


@pytest.mark.parametrize("action", [3, 7])
def test_invmon_removed_or_consumed(action: int) -> None:
    state = seeded()
    out = state.apply_invmon(action, 1, -1, -1)
    assert 1 not in state.items
    assert state.serials(INVENTORY) == [2, 50]
    assert out.events == [(SUFFIX_INVENTORY_REMOVED, {"item": out.events[0][1]["item"]})]
    assert out.events[0][1]["item"]["serial"] == 1


def test_invmon_removed_bag_drops_container_and_items() -> None:
    state = seeded()
    out = state.apply_invmon(3, 50, -1, -1)
    assert out.dropped_containers == ["50"]
    assert state.container_copy(50) is None
    assert 3 not in state.items
    assert 50 not in state.items


def test_invmon_removed_item_not_in_inventory_refreshes() -> None:
    state = seeded()
    out = state.apply_invmon(3, 999, -1, -1)
    assert out.refresh == [INVENTORY]
    assert out.events == []


def test_invmon_added_known_item() -> None:
    state = seeded()
    state.upsert(item(60))
    out = state.apply_invmon(4, 60, -1, -1)
    assert state.serials(INVENTORY)[0] == 60
    assert [e[0] for e in out.events] == [SUFFIX_INVENTORY_ADDED, SUFFIX_PUT]
    assert out.events[1][1]["serial"] == 60
    assert out.events[1][1]["container"] == INVENTORY
    assert out.events[1][1]["item"]["serial"] == 60
    assert out.refresh == []


def test_invmon_added_unknown_item_raises_put_with_no_item() -> None:
    state = seeded()
    out = state.apply_invmon(4, 999, -1, -1)
    assert out.refresh == [INVENTORY]
    assert out.events == [(SUFFIX_PUT, {"serial": 999, "container": INVENTORY, "item": None})]


def test_invmon_added_bag_gets_a_container_and_a_refresh() -> None:
    state = seeded()
    state.upsert(item(61, "another bag", itype=CONTAINER_ITYPE))
    out = state.apply_invmon(4, 61, -1, -1)
    assert out.new_containers == ["61"]
    assert out.refresh == ["61"]
    assert state.container_copy(61) == {"cid": "61", "items": []}


def test_invmon_taken_out_of_a_bag() -> None:
    state = seeded()
    out = state.apply_invmon(5, 3, 50, -1)
    assert state.serials("50") == []
    assert state.serials(INVENTORY)[-1] == 3
    assert [e[0] for e in out.events] == [SUFFIX_TAKEN]
    assert out.events[0][1]["container"] == "50"
    assert out.refresh == []


def test_invmon_taken_from_an_unknown_bag_does_not_raise() -> None:
    state = seeded()
    out = state.apply_invmon(5, 3, 777, -1)
    assert out.new_containers == ["777"]
    assert out.refresh == ["777", INVENTORY]
    assert out.events[0][0] == SUFFIX_TAKEN
    assert out.events[0][1]["container"] == "777"


def test_invmon_put_into_a_bag() -> None:
    state = seeded()
    out = state.apply_invmon(6, 1, 50, -1)
    assert state.serials("50")[0] == 1
    assert 1 not in state.serials(INVENTORY)
    assert out.events[0][0] == SUFFIX_PUT
    assert out.events[0][1]["container"] == "50"
    assert out.refresh == []


def test_invmon_put_into_an_unknown_bag_does_not_raise() -> None:
    state = seeded()
    out = state.apply_invmon(6, 1, 777, -1)
    assert out.refresh == ["777", INVENTORY]
    assert 1 in state.serials(INVENTORY)
    assert out.events[0][1]["container"] == "777"


def test_invmon_bag_put_with_a_bad_container_does_not_raise() -> None:
    state = seeded()
    out = state.apply_invmon(6, 1, -1, -1)
    assert out.refresh == [INVENTORY]
    assert out.events[0][1]["container"] == "-1"


def test_invmon_vault_put_removes_the_item_from_the_inventory() -> None:
    state = seeded()
    out = state.apply_invmon(9, 1, -1, -1)
    assert 1 not in state.serials(INVENTORY)
    assert state.serials(VAULT)[-1] == 1
    assert out.events[0][0] == SUFFIX_PUT
    assert out.events[0][1]["container"] == VAULT


def test_invmon_vault_put_of_an_unknown_item_refreshes() -> None:
    state = seeded()
    out = state.apply_invmon(9, 999, -1, -1)
    assert out.refresh == [VAULT, INVENTORY]
    assert out.events[0][1]["item"] is None


def test_invmon_vault_take_adds_the_item_to_the_inventory() -> None:
    state = seeded()
    out = state.apply_invmon(10, 30, -1, -1)
    assert state.serials(VAULT) == []
    assert state.serials(INVENTORY)[0] == 30
    assert out.events[0][0] == SUFFIX_TAKEN
    assert out.events[0][1]["container"] == VAULT


def test_invmon_vault_take_of_a_missing_item_refreshes() -> None:
    state = seeded()
    out = state.apply_invmon(10, 999, -1, -1)
    assert out.refresh == [VAULT, INVENTORY]


def test_invmon_keyring_put_and_take() -> None:
    state = seeded()
    out = state.apply_invmon(11, 1, -1, -1)
    assert state.serials(KEYRING)[0] == 1
    assert out.events[0][0] == SUFFIX_PUT
    assert out.events[0][1]["container"] == KEYRING
    out = state.apply_invmon(12, 20, -1, -1)
    assert state.serials(INVENTORY)[0] == 20
    assert out.events[0][0] == SUFFIX_TAKEN
    assert out.events[0][1]["container"] == KEYRING


def test_invmon_keyring_not_where_expected_refreshes() -> None:
    state = seeded()
    assert state.apply_invmon(11, 30, -1, -1).refresh == [INVENTORY, KEYRING]
    assert state.apply_invmon(12, 1, -1, -1).refresh == [KEYRING, INVENTORY]


@pytest.mark.parametrize("action", [0, 8, 13, 99])
def test_invmon_unknown_action_is_ignored(action: int) -> None:
    state = seeded()
    before = {cid: state.serials(cid) for cid in (INVENTORY, KEYRING, VAULT, WORN, "50")}
    out = state.apply_invmon(action, 1, -1, -1)
    assert out == ([], [], [], [])
    assert before == {cid: state.serials(cid) for cid in before}


def test_invmon_put_clears_origcontainer_of_the_target() -> None:
    state = seeded()
    state.items[1]["origcontainer"] = "50"
    state.apply_invmon(6, 1, 50, -1)
    assert state.items[1]["origcontainer"] is None


def test_wear_clears_origcontainer_worn() -> None:
    state = seeded()
    state.apply_invmon(1, 10, -1, 24)
    state.set_origin(10)
    state.items[10]["origcontainer"] = WORN
    state.apply_invmon(2, 10, -1, 24)
    assert state.items[10]["origcontainer"] is None


def test_drop_container_drops_nested_bags() -> None:
    state = seeded()
    state.commit("50", [item(51, itype=CONTAINER_ITYPE)])
    state.commit("51", [item(52)])
    dropped = state.drop_container("50")
    assert sorted(dropped) == [51, 52]
    assert state.container_copy(51) is None
    assert 52 not in state.items


def test_parse_colorcoded_line_unescapes_literal_at_signs() -> None:
    plain = "3984146950,,@WGueldar's@w crafted leather pants@w,1,7,0,21,-1"
    colored = "3984146950,,@@WGueldar's@@w crafted leather pants@@w,1,7,0,21,-1"
    parsed = parse_item_line(plain, colored, strip)
    assert parsed is not None
    assert parsed["cname"] == "@WGueldar's@w crafted leather pants@w"
    assert parsed["name"] == "Gueldar's crafted leather pants"


def test_parse_colorcoded_line_keeps_ansi_codes_beside_escaped_ones() -> None:
    plain = "1,,@Ra @Wbag@w,1,7,0,21,-1"
    colored = "@R1,,@Ra @@Wbag@@w,1,7,0,21,-1@w"
    parsed = parse_item_line(plain, colored, strip)
    assert parsed is not None
    assert parsed["cname"] == "@Ra @Wbag@w"
    assert parsed["name"] == "a bag"


def vault_read(state: EqState) -> bool:
    """The flag, read through a call so mypy does not narrow it between the steps."""
    return state.vault_read


def test_vault_read_follows_the_vault_commit() -> None:
    state = EqState()
    assert vault_read(state) is False
    state.commit(INVENTORY, [item(1)])
    assert vault_read(state) is False
    state.commit(VAULT, [item(2)])
    assert vault_read(state) is True
    state.reset()
    assert vault_read(state) is False
    state.commit(VAULT, [])
    assert vault_read(state) is True


# bags seen in any block (#146)


@pytest.mark.parametrize("cid", [WORN, INVENTORY, KEYRING, VAULT])
def test_commit_creates_a_container_for_a_bag_in_any_block(cid: str) -> None:
    state = EqState()
    bag = item(5001, "a test bag", itype=CONTAINER_ITYPE, wearslot=24 if cid == WORN else -1)
    assert state.commit(cid, [bag]) == ["5001"]
    assert state.container_copy(5001) == {"cid": "5001", "items": []}


def test_a_worn_or_vault_bag_survives_an_inventory_commit() -> None:
    state = EqState()
    state.commit(WORN, [item(5001, "a worn bag", itype=CONTAINER_ITYPE, wearslot=24)])
    state.commit(VAULT, [item(5002, "a vault bag", itype=CONTAINER_ITYPE)])
    state.commit(INVENTORY, [item(1)])
    assert sorted(state.bag_cids()) == ["5001", "5002"]
    state.commit(WORN, [])
    state.commit(INVENTORY, [item(1)])
    assert state.bag_cids() == ["5002"]
