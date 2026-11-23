"""Tests for the eqdb schema and store, over a real database in a temporary directory."""

import copy
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from eqdb_support import make_db, sample_item

if TYPE_CHECKING:
    from bastproxy.plugins.core.sqldb.libs._sqlite import Sqldb

    from aardwolf.eqdb.libs import ItemStore

OLD_TABLES = {
    "items": "serial",
    "identifier": None,
    "resistmod": "rid",
    "statmod": "sid",
    "affectmod": "aid",
    "skillmod": "skid",
    "notes": "nid",
    "addednotes": "anid",
    "weapon": "wid",
    "container": "cid",
    "spells": "spid",
    "food": "fid",
    "drink": "did",
    "furniture": "fuid",
    "light": "lid",
    "portal": "portid",
    "enchant": "enchantid",
    "reward": "rewardid",
}


@pytest.fixture(autouse=True)
def home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Importing bastproxy needs an existing BASTPROXY_HOME."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setenv("BASTPROXY_HOME", str(home_dir))


@pytest.fixture
def db(tmp_path: Path) -> "Iterator[Sqldb]":
    """A fresh eqdb database."""
    database = make_db(tmp_path / "db")
    yield database
    database.close()


@pytest.fixture
def store(db: "Sqldb") -> "ItemStore":
    """A store over the fresh database."""
    from aardwolf.eqdb.libs import ItemStore

    return ItemStore(db)


def _count(db: "Sqldb", table: str) -> int:
    rows = db.select(f"SELECT COUNT(*) AS n FROM {table}")
    return int(rows[0]["n"])


def test_tables_are_the_old_ones() -> None:
    """The schema holds the old tables with their key fields."""
    from aardwolf.eqdb.libs import DB_NAME, DB_VERSION, TABLES

    assert DB_NAME == "eqdb"
    assert DB_VERSION == 1
    assert {t["name"]: t.get("keyfield") for t in TABLES} == OLD_TABLES
    assert len(TABLES) == 18


def test_database_is_created(db: "Sqldb") -> None:
    """Every table exists and the version is 1."""
    for name in OLD_TABLES:
        assert db.checktableexists(name)
    assert db.getversion() == 1


def test_items_columns_match_the_old_create_text() -> None:
    """The items table has the old text's columns, in order."""
    from aardwolf.eqdb.libs import TABLES

    sql = next(t["sql"] for t in TABLES if t["name"] == "items")
    connection = sqlite3.connect(":memory:")
    try:
        connection.executescript(sql)
        names = [r[1] for r in connection.execute("PRAGMA table_info(items)")]
    finally:
        connection.close()
    assert names == [
        "serial",
        "keywords",
        "cname",
        "name",
        "level",
        "itype",
        "worth",
        "weight",
        "wearable",
        "material",
        "score",
        "flags",
        "foundat",
        "fromclan",
        "owner",
        "leadsto",
    ]


def test_save_then_get_round_trips(store: "ItemStore") -> None:
    """A saved item comes back with lists, mods and one-row details."""
    item = sample_item()
    assert store.save_item(item) is True
    got = store.get_item(1001)
    assert got is not None
    assert got == item


def test_get_by_string_serial(store: "ItemStore") -> None:
    """A serial given as a digit string finds the item."""
    store.save_item(sample_item())
    got = store.get_item("1001")
    assert got is not None
    assert got["serial"] == 1001


def test_single_details_are_saved_for_every_type(store: "ItemStore") -> None:
    """The one-row details do not depend on itype (old bug 1)."""
    item: dict[str, Any] = {
        "serial": 5,
        "itype": 1,
        "container": {"capacity": 10, "heaviestitem": 2, "holding": 3},
        "light": {"duration": 50},
        "portal": {"uses": 4},
        "drink": {"servings": 2, "liquid": 1},
        "food": {"percent": 80},
        "furniture": {"hpregen": 5, "manaregen": 6, "u1": 0},
        "spells": {"uses": 3, "level": 20, "sn1": 1, "sn2": 2, "sn3": 3, "sn4": 4, "u1": 0},
        "weapon": {"wtype": "axe", "avedam": 12},
    }
    store.save_item(item)
    got = store.get_item(5)
    assert got is not None
    for key in ("container", "light", "portal", "drink", "food", "furniture", "spells", "weapon"):
        assert key in got
        for field, value in item[key].items():
            assert got[key][field] == value
        assert "serial" not in got[key]
    assert got["light"] == {"duration": 50}
    assert got["food"] == {"percent": 80}


def test_details_false_returns_only_the_row(store: "ItemStore") -> None:
    """Without details, only the items columns come back."""
    store.save_item(sample_item())
    got = store.get_item(1001, details=False)
    assert got is not None
    assert "statmod" not in got
    assert "weapon" not in got
    assert got["flags"] == ["glow", "hum"]


def test_second_save_updates(store: "ItemStore", db: "Sqldb") -> None:
    """Saving a serial again updates the row and does not duplicate it."""
    item = sample_item()
    store.save_item(item)
    item["cname"] = "@gChanged@w"
    item["level"] = 99
    store.save_item(item)
    assert _count(db, "items") == 1
    assert _count(db, "weapon") == 1
    assert _count(db, "statmod") == 1
    got = store.get_item(1001)
    assert got is not None
    assert (got["cname"], got["level"]) == ("@gChanged@w", 99)


def test_empty_detail_clears_and_absent_detail_keeps(store: "ItemStore") -> None:
    """An empty mods value clears the rows (old bug 5); an absent key leaves them."""
    item = sample_item()
    store.save_item(item)
    without = {k: v for k, v in item.items() if k != "statmod"}
    store.save_item(without)
    got = store.get_item(1001)
    assert got is not None
    assert got["statmod"] == {"Strength": 3}
    store.save_item({**without, "statmod": {}, "affectmod": [], "enchant": [], "weapon": {}})
    got = store.get_item(1001)
    assert got is not None
    for key in ("statmod", "affectmod", "enchant", "weapon"):
        assert key not in got
    assert got["resistmod"] == {"Fire": 2}


def test_missing_flags_and_keywords(store: "ItemStore") -> None:
    """None or missing flags and keywords save and come back as empty lists (old bug 3)."""
    store.save_item({"serial": 7, "flags": None})
    got = store.get_item(7)
    assert got is not None
    assert got["flags"] == []
    assert got["keywords"] == []
    store.save_item({"serial": 7, "flags": "a,b", "keywords": "x"})
    got = store.get_item(7)
    assert got is not None
    assert (got["flags"], got["keywords"]) == (["a", "b"], ["x"])


def test_null_flags_row_can_be_read_and_saved(store: "ItemStore", db: "Sqldb") -> None:
    """A row stored with NULL flags and keywords does not break get or save."""
    db.modify("INSERT INTO items (serial) VALUES (?)", (9,))
    got = store.get_item(9)
    assert got is not None
    assert (got["flags"], got["keywords"]) == ([], [])
    assert store.save_item({"serial": 9, "name": "x"}) is True


def test_callers_mapping_is_unchanged(store: "ItemStore") -> None:
    """Saving does not change the mapping or its enchant dicts (old bug 6)."""
    item = sample_item()
    before = copy.deepcopy(item)
    store.save_item(item)
    assert item == before
    assert "serial" not in item["enchant"][0]


def test_lookup_by_identifier(store: "ItemStore", db: "Sqldb") -> None:
    """An identifier row finds the item; an unknown one gives None."""
    store.save_item(sample_item())
    db.modify("INSERT INTO identifier VALUES (?, ?)", (1001, "myid"))
    got = store.get_item("myid")
    assert got is not None
    assert got["serial"] == 1001
    assert store.get_item("nope") is None
    assert store.get_item(424242) is None
    assert store.get_item("424242") is None


def test_parse_serial() -> None:
    """Whole numbers parse; booleans, text and None do not."""
    from aardwolf.eqdb.libs import ItemStore

    assert ItemStore.parse_serial("123") == 123
    assert ItemStore.parse_serial(123) == 123
    for bad in ("abc", True, None, "", "1.5", "-3", 1.5):
        assert ItemStore.parse_serial(bad) is None


def test_save_without_serial_writes_nothing(store: "ItemStore", db: "Sqldb") -> None:
    """An item with no valid serial is refused."""
    for item in ({}, {"serial": None}, {"serial": "abc"}, {"serial": True, "name": "x"}):
        assert store.save_item(item) is False
    assert _count(db, "items") == 0


def test_a_quote_is_stored_literally(store: "ItemStore", db: "Sqldb") -> None:
    """SQL in a value or an identifier is data, not a statement."""
    evil = "x'); DROP TABLE items;--"
    store.save_item({"serial": 3, "cname": evil, "name": evil})
    db.modify("INSERT INTO identifier VALUES (?, ?)", (3, evil))
    got = store.get_item(evil)
    assert got is not None
    assert got["cname"] == evil
    assert _count(db, "items") == 1


def test_wrong_detail_shape_is_refused(store: "ItemStore") -> None:
    """A detail of the wrong shape raises instead of writing nonsense."""
    with pytest.raises(ValueError, match="wrong shape"):
        store.save_item({"serial": 4, "statmod": "bad"})
    with pytest.raises(ValueError, match="wrong shape"):
        store.save_item({"serial": 4, "weapon": ["bad"]})
    # refused before anything was written
    assert store.get_item(4) is None


def test_wrong_detail_shape_leaves_the_stored_item_alone(store: "ItemStore") -> None:
    """A refused save does not change the item row or its other details."""
    assert store.save_item({"serial": 5, "name": "old", "statmod": {"str": 1}})
    with pytest.raises(ValueError, match="wrong shape"):
        store.save_item({"serial": 5, "name": "new", "statmod": {"str": 9}, "weapon": "bad"})
    item = store.get_item(5)
    assert item is not None
    assert item["name"] == "old"
    assert item["statmod"] == {"str": 1}
