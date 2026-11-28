"""Every table column the Aardwolf plugins declare carries its full name."""

import re
from collections.abc import Mapping
from pathlib import Path

import pytest

# labels that are whole words already, so a column needs no long name
PLAIN_LABELS = {
    "Milestone",
    "Date (UTC)",
    "Time (UTC)",
    "Gold",
    "Result",
    "Mob",
    "Mobs",
    "Room",
    "Area",
    "Name",
    "Location",
    "Won",
    "Flags",
    "Kind",
    "Command",
    "Found",
    "Left",
    "Dead",
}
# short words a long name must not use ("Open PK" is the name of the game mode, so PK is not one)
SHORT_WORDS = {
    "ID",
    "QP",
    "MC",
    "TR",
    "LK",
    "HC",
    "DBL",
    "TL",
    "TP",
    "TN",
    "PR",
    "HP",
    "MN",
    "MV",
    "BT",
    "BN",
    "QM",
    "TXP",
    "XP",
    "RXP",
    "OXP",
    "Lvl",
    "Mins",
    "CP",
    "GQ",
    "Num",
}


@pytest.fixture(autouse=True)
def home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Importing bastproxy needs an existing BASTPROXY_HOME."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setenv("BASTPROXY_HOME", str(home_dir))


def _declared_tables() -> dict[str, list[dict[str, str]]]:
    """Return every web table the plugins declare, by name."""
    from aardwolf.cp.libs import MOBSLEFT_PROVIDER_COLUMNS as CP_COLUMNS
    from aardwolf.gq.libs import MOBSLEFT_PROVIDER_COLUMNS as GQ_COLUMNS
    from aardwolf.mapper.libs import CEXIT_COLUMNS, PLACE_COLUMNS, PORTAL_COLUMNS
    from aardwolf.statdb.libs import TABLE_PAGES

    tables = {f"statdb {route}": page.route_columns() for route, page in TABLE_PAGES.items()}
    tables["cp mobsleft"] = CP_COLUMNS
    tables["gq mobsleft"] = GQ_COLUMNS
    tables["mapper portals"] = PORTAL_COLUMNS
    tables["mapper cexits"] = CEXIT_COLUMNS
    tables["mapper places"] = PLACE_COLUMNS
    return tables


def test_every_declared_table_is_found() -> None:
    """The walk covers the statdb pages, the mobsleft providers and the mapper tables."""
    tables = _declared_tables()
    assert len(tables) >= 8 + 5
    assert "statdb milestones" in tables


def test_every_abbreviated_label_has_a_long_name() -> None:
    """A label that is not a whole word has a long name made of whole words."""
    problems: list[str] = []
    for table, columns in _declared_tables().items():
        for column in columns:
            label = column["label"]
            long = column.get("long", "")
            where = f"{table}.{column['name']}"
            if label in PLAIN_LABELS and not long:
                continue
            if not long.strip():
                problems.append(f"{where}: label {label!r} has no long name")
            elif long == label:
                problems.append(f"{where}: the long name repeats the label")
            elif SHORT_WORDS & set(re.findall(r"[A-Za-z]+", long)):
                problems.append(f"{where}: long name {long!r} uses a short word")
    assert problems == []


def test_core_accepts_every_declaration() -> None:
    """The column declarations pass the core validation, long names included."""
    from bastproxy.plugins.core.web.libs._table import make_columns

    for columns in _declared_tables().values():
        made = make_columns(columns)
        assert [c.long for c in made] == [c.get("long") for c in columns]


def test_route_columns_have_long_only_when_set() -> None:
    """A column without a long name has no long key."""
    from aardwolf.statdb.libs import TABLE_PAGES

    quests = {c["name"]: c for c in TABLE_PAGES["quests"].route_columns()}
    assert quests["mc"]["long"] == "MCCP quest points"
    assert "long" not in quests["gold"]
    assert all(c.get("long") != "" for c in quests.values())


def test_the_milestone_columns_carry_the_names_of_the_comparison() -> None:
    """The milestones page and the comparison name each field the same way."""
    from aardwolf.statdb.libs import FIELD_NAMES, FIELDSTOCOMP, TABLE_PAGES

    assert list(FIELD_NAMES) == FIELDSTOCOMP
    columns: Mapping[str, str] = {
        c["name"]: c["long"] for c in TABLE_PAGES["milestones"].route_columns() if "long" in c
    }
    assert columns == FIELD_NAMES


def test_the_levels_header_shows_the_long_name_over_the_short_one() -> None:
    """The core renders the long name, then the label in brackets."""
    from bastproxy.plugins.core.web.libs._render import render_table
    from bastproxy.plugins.core.web.libs._table import TableQuery, make_columns

    from aardwolf.statdb.libs import TABLE_PAGES

    columns = make_columns(TABLE_PAGES["levels"].route_columns())
    html = render_table(
        columns,
        [],
        query=TableQuery(),
        total=0,
        base_path="/levels",
        to_html=lambda text: text,
    )
    assert "<span class='long'>Level</span> <span class='short'>[Lvl]</span>" in html
    assert "<span class='long'>Bonus strength</span> <span class='short'>[S]</span>" in html
