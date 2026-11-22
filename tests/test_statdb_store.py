"""Tests for the statdb store, over a real database in a temporary directory."""

import copy
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from statdb_support import make_db

if TYPE_CHECKING:
    from bastproxy.plugins.core.sqldb.libs._sqlite import Sqldb

    from aardwolf.statdb.libs import StatStore


@pytest.fixture(autouse=True)
def home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Importing bastproxy needs an existing BASTPROXY_HOME."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setenv("BASTPROXY_HOME", str(home_dir))


@pytest.fixture
def db(tmp_path: Path) -> "Iterator[Sqldb]":
    """A fresh statdb database."""
    database = make_db(tmp_path / "db")
    yield database
    database.close()


@pytest.fixture
def store(db: "Sqldb") -> "StatStore":
    """A store over the fresh database."""
    from aardwolf.statdb.libs import StatStore

    return StatStore(db)


WHOIS: dict[str, Any] = {
    "name": "Tester",
    "level": 10,
    "totallevels": 10,
    "remorts": 2,
    "tiers": 0,
    "race": "elf",
    "sex": "female",
    "subclass": "none",
    "powerupsall": 2,
    "powerupsmort": 1,
    "classes": [{"remort": 1, "class": "mag"}, {"remort": 2, "class": "thief"}],
}


def _current(db: "Sqldb") -> dict[str, Any]:
    return db.select("SELECT * FROM stats WHERE milestone = 'current'")[0]


def test_whois_first_inserts_current_and_start(store: "StatStore", db: "Sqldb") -> None:
    """The first whois inserts the current row and a start milestone."""
    store.save_whois(WHOIS)
    rows = db.select("SELECT milestone, name, totaltrivia, time FROM stats ORDER BY stat_id")
    assert [row["milestone"] for row in rows] == ["current", "start"]
    assert rows[0]["name"] == "Tester"
    assert rows[0]["totaltrivia"] == 0
    assert rows[1]["time"] > 0


def test_whois_classes_from_abbreviations_and_full_names(store: "StatStore", db: "Sqldb") -> None:
    """Abbreviated and full class names both set the remort of the full-name row."""
    store.save_whois(WHOIS)
    assert store.get_classes() == ["mage", "thief"]
    whois = copy.deepcopy(WHOIS)
    whois["classes"] = [
        {"remort": 1, "class": "mage"},
        {"remort": 2, "class": "thi"},
        {"remort": 3, "class": "warrior"},
    ]
    store.save_whois(whois)
    assert store.get_classes() == ["mage", "thief", "warrior"]
    assert db.select("SELECT remort FROM classes WHERE class = 'warrior'") == [{"remort": 3}]


def test_whois_again_updates_current_and_keeps_trivia(store: "StatStore", db: "Sqldb") -> None:
    """A later whois updates the current row, keeps its trivia and adds no row."""
    store.save_whois(WHOIS)
    store.add_to_stat("totaltrivia", 7)
    store.save_whois({**WHOIS, "totallevels": 12, "level": 12, "bogus": "ignored"})
    current = _current(db)
    assert (current["totallevels"], current["totaltrivia"], current["time"]) == (12, 7, 0)
    assert len(db.select("SELECT * FROM stats")) == 2


def test_quest_complete_and_failed(store: "StatStore", db: "Sqldb") -> None:
    """A quest counts completed or failed, adds qp and trivia and saves the row."""
    store.save_whois(WHOIS)
    done = store.save_quest({"totqp": 25, "tp": 2, "qp": 20, "failed": 0, "mobname": "a rat"})
    failed = store.save_quest({"totqp": 99, "tp": 9, "failed": 1})
    assert (done, failed) == (1, 2)
    current = _current(db)
    assert (current["questscomplete"], current["questsfailed"]) == (1, 1)
    assert (current["qpearned"], current["totaltrivia"]) == (25, 2)
    assert db.select("SELECT mobname, failed FROM quests ORDER BY quest_id") == [
        {"mobname": "a rat", "failed": 0},
        {"mobname": "Unknown", "failed": 1},
    ]


def test_campaign_saves_mobs_with_its_id(store: "StatStore", db: "Sqldb") -> None:
    """A campaign adds to the counters and saves its mobs under its id."""
    store.save_whois(WHOIS)
    mobs = [{"name": "a goblin", "location": "Forest"}, {"name": "an orc", "location": "Hills"}]
    info = {"qp": 30, "tp": 1, "failed": 0, "mobs": mobs}
    before = copy.deepcopy(info)
    assert store.save_cp(info) == 1
    assert store.save_cp({"failed": 1, "mobs": []}) == 2
    assert info == before
    current = _current(db)
    assert (current["campaignsdone"], current["campaignsfld"], current["qpearned"]) == (1, 1, 30)
    assert [row["cp_id"] for row in db.select("SELECT cp_id FROM cpmobs")] == [1, 1]


def test_gquest_won_counts_only_when_won(store: "StatStore", db: "Sqldb") -> None:
    """A global quest adds its qp and mobs, and counts a win only when won."""
    store.save_whois(WHOIS)
    mobs = [{"num": 3, "name": "a troll", "location": "Cave"}]
    store.save_gq({"qp": 40, "qpmobs": 10, "tp": 2, "won": 1, "mobs": mobs})
    store.save_gq({"qp": 0, "qpmobs": 5, "tp": 0, "won": 0, "mobs": []})
    current = _current(db)
    assert (current["gquestswon"], current["qpearned"], current["totaltrivia"]) == (1, 55, 2)
    assert db.select("SELECT gq_id, num FROM gqmobs") == [{"gq_id": 1, "num": 3}]


def test_level_with_a_total_sets_the_stats(store: "StatStore", db: "Sqldb") -> None:
    """A level event with a total level sets totallevels and level, and adds its milestone."""
    store.save_whois(WHOIS)
    assert store.save_level({"type": "level", "totallevels": 11, "level": 11, "starttime": 50}) == 1
    current = _current(db)
    assert (current["totallevels"], current["level"]) == (11, 11)
    assert db.select("SELECT level, finishtime FROM levels") == [{"level": 11, "finishtime": -1}]
    assert store.get_milestone("11") is not None


def test_level_without_a_total_adds_one(store: "StatStore", db: "Sqldb") -> None:
    """Without a total level, the level adds one and takes the stored total."""
    store.save_whois(WHOIS)
    store.save_level({"type": "level", "starttime": 50})
    current = _current(db)
    assert (current["totallevels"], current["level"]) == (11, 11)
    assert db.select("SELECT level FROM levels") == [{"level": 11}]
    assert store.get_milestone("11") is not None


def test_pup_and_finish_time_of_previous_row(store: "StatStore", db: "Sqldb") -> None:
    """A pup counts, adds no milestone, and the next row closes the previous one."""
    store.save_whois(WHOIS)
    store.save_level({"type": "level", "totallevels": 11, "starttime": 50})
    store.save_level({"type": "pup", "totallevels": 11, "starttime": 80})
    assert _current(db)["powerupsall"] == 3
    assert db.select("SELECT finishtime FROM levels ORDER BY level_id") == [
        {"finishtime": 80},
        {"finishtime": -1},
    ]
    assert [row["milestone"] for row in db.select("SELECT milestone FROM stats")].count("11") == 1


def test_mobkill(store: "StatStore", db: "Sqldb") -> None:
    """A mob kill adds a kill and its trivia."""
    store.save_whois(WHOIS)
    store.save_mobkill({"name": "a rat", "tp": 1, "xp": 5})
    store.save_mobkill({"name": "a bat", "tp": 0})
    current = _current(db)
    assert (current["monsterskilled"], current["totaltrivia"]) == (2, 1)
    assert db.select("SELECT name, xp FROM mobkills")[0] == {"name": "a rat", "xp": 5}


def test_payload_is_not_changed(store: "StatStore") -> None:
    """No save method changes the dict it is given."""
    store.save_whois(WHOIS)
    payloads: list[dict[str, Any]] = [
        {"totqp": 1, "tp": 1, "failed": 0},
        {"qp": 1, "tp": 0, "mobs": [{"name": "a"}]},
        {"qp": 1, "qpmobs": 1, "won": 1, "mobs": [{"num": 1, "name": "a"}]},
        {"type": "level", "totallevels": 12, "starttime": 3},
        {"name": "a", "tp": 1},
    ]
    methods = [
        store.save_quest,
        store.save_cp,
        store.save_gq,
        store.save_level,
        store.save_mobkill,
    ]
    for method, payload in zip(methods, payloads, strict=True):
        before = copy.deepcopy(payload)
        method(payload)
        assert payload == before
    before_whois = copy.deepcopy(WHOIS)
    store.save_whois(WHOIS)
    assert before_whois == WHOIS


def test_unknown_stat_runs_no_sql(
    store: "StatStore", db: "Sqldb", monkeypatch: pytest.MonkeyPatch
) -> None:
    """set_stat and add_to_stat refuse an unknown column and an injection attempt."""
    store.save_whois(WHOIS)
    calls: list[str] = []
    original = db.modify

    def spy(sql: str, data: object = None) -> tuple[int | None, Any]:
        calls.append(sql)
        return original(sql, data)

    monkeypatch.setattr(db, "modify", spy)
    assert store.set_stat("nothing", 1) is False
    assert store.add_to_stat("nothing", 1) is False
    assert store.set_stat("level = 1; DROP TABLE stats; --", 1) is False
    assert calls == []
    assert len(db.select("SELECT * FROM stats")) == 2


def test_add_to_stat_ignores_zero_and_negative(store: "StatStore", db: "Sqldb") -> None:
    """Adding zero or less changes nothing and counts as done."""
    store.save_whois(WHOIS)
    assert store.add_to_stat("timeskilled", 0) is True
    assert store.add_to_stat("timeskilled", -3) is True
    assert store.add_to_stat("timeskilled", None) is True
    assert store.get_stat("timeskilled") == 0
    store.record_death()
    assert store.get_stat("timeskilled") == 1


def test_values_are_bound_not_pasted(store: "StatStore", db: "Sqldb") -> None:
    """Quotes in an event value are stored as text."""
    store.save_whois(WHOIS)
    store.save_mobkill({"name": "a\"b'; DROP TABLE stats; --", "tp": 0})
    assert db.select("SELECT name FROM mobkills")[0]["name"] == "a\"b'; DROP TABLE stats; --"
    assert len(db.select("SELECT * FROM stats")) == 2
    assert store.get_milestone("x' OR '1'='1") is None


def test_duplicate_and_empty_milestones_are_refused(store: "StatStore") -> None:
    """A milestone name that exists, an empty one, or one with no stats returns -1."""
    assert store.add_milestone("early") == -1
    store.save_whois(WHOIS)
    assert store.add_milestone("early") > 0
    assert store.add_milestone("early") == -1
    assert store.add_milestone("") == -1


def test_hero_milestone_names(store: "StatStore") -> None:
    """The milestone name is tier, remort and level, and shows redos at tier 9."""
    assert store.hero_milestone(1) == "t0r1l1"
    assert store.hero_milestone(1407 + 201 + 5) == "t1r2l5"
    assert store.hero_milestone(9 * 1407 + 3) == "t9+0r1l3"
    assert store.hero_milestone(10 * 1407 + 202) == "t9+1r2l1"


def test_apply_remort(store: "StatStore", db: "Sqldb") -> None:
    """A remort sets remorts, tiers and the total level, and puts the level back to 1."""
    store.save_whois(WHOIS)
    store.apply_remort("3", 1, 1700)
    current = _current(db)
    assert (current["remorts"], current["tiers"], current["totallevels"], current["level"]) == (
        3,
        1,
        1700,
        1,
    )


def test_classes_reset(store: "StatStore") -> None:
    """Resetting the classes takes every remort back to -1."""
    store.save_whois(WHOIS)
    store.reset_classes()
    assert store.get_classes() == []


def test_class_names_ignores_bad_items() -> None:
    """Whois classes that are not a list of class and remort mappings give nothing."""
    from aardwolf.statdb.libs import class_names

    assert class_names(None) == []
    assert class_names([1, {"class": "mag"}]) == []
    assert class_names([{"class": "MAG", "remort": 1}]) == [{"class": "mage", "remort": 1}]
