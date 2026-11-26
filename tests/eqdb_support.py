"""Shared helpers for the eqdb tests. Not a test module.

``make_db`` imports bastproxy, which raises unless ``BASTPROXY_HOME`` is an existing directory,
so a test sets that with ``monkeypatch.setenv`` before it calls ``make_db``. All data here is
made up.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bastproxy.plugins.core.sqldb.libs._sqlite import Sqldb

OWNER = "plugins.aardwolf.eqdb"


def make_db(directory: Path, *, journal_mode: str | None = None) -> "Sqldb":
    """Open the eqdb database in a directory the way ``database.add`` does.

    ``journal_mode`` is passed on as ``database.add`` gets it; None leaves sqlite's default.
    """
    from bastproxy.plugins.core.sqldb.libs._sqlite import create_database

    from aardwolf.eqdb.libs import DB_NAME, DB_VERSION, MIGRATIONS, TABLES

    return create_database(
        OWNER,
        DB_NAME,
        TABLES,
        version=DB_VERSION,
        migrations=MIGRATIONS,
        directory=directory,
        journal_mode=journal_mode,
    )


def sample_item(serial: int = 1001) -> dict[str, Any]:
    """Return a made-up item the way itemid builds it, using the itemu parser."""
    from aardwolf._libs.itemu import parse_item_data

    header = parse_item_data(
        f"{serial}|25|5|1200|7|wield|glow,hum|tester|0|-1|0|0|0|40", "invheader"
    )
    item: dict[str, Any] = {
        "serial": header["serial"],
        "level": header["level"],
        "itype": header["itype"],
        "worth": header["worth"],
        "weight": header["weight"],
        "wearable": header["wearable"],
        "flags": ["glow", "hum"],
        "owner": header["owner"],
        "fromclan": "",
        "score": header["score"],
        "keywords": ["sword", "test"],
        "cname": "@wA Test Sword@w",
        "name": "A Test Sword",
        "foundat": "Nowhere",
        "leadsto": "",
        "material": 3,
    }
    stat = parse_item_data("Strength|3", "statmod")
    item["statmod"] = {stat["name"]: stat["value"]}
    resist = parse_item_data("Fire|2", "resistmod")
    item["resistmod"] = {resist["name"]: resist["value"]}
    skill = parse_item_data("44|5", "skillmod")
    item["skillmod"] = {skill["name"]: skill["value"]}
    item["affectmod"] = ["sanctuary", "haste"]
    enchant = parse_item_data("fire,Enchant,hp,10,Tester,1", "enchant")
    # the column is TEXT, so a number would come back as a string
    item["enchant"] = [{**enchant, "removable": str(enchant["removable"])}]
    item["weapon"] = dict(parse_item_data("sword|55|none|slash|sharp", "weapon"))
    item["notes"] = {"ntext": "a note"}
    item["reward"] = {"rtext": "a reward"}
    return item
