"""The eqdb schema: the 18 tables of the old proxy's eqdb database, version 1.

The CREATE statements are the old proxy's text, word for word and in the same column order,
so a database file written by the old plugin opens as it is (the same approach as statdb).
The old ``additemindexes`` postcreate did nothing and is dropped.
"""

from typing import Any

DB_NAME = "eqdb"
DB_VERSION = 1

ITEMS_SQL = """CREATE TABLE items(
          serial INTEGER NOT NULL,
          keywords TEXT,
          cname TEXT,
          name TEXT,
          level INT default 0,
          itype INT default 0,
          worth INT default 0,
          weight INT default 0,
          wearable TEXT,
          material INT default 0,
          score INT default 0,
          flags TEXT,
          foundat TEXT,
          fromclan TEXT,
          owner TEXT,
          leadsto TEXT,
          UNIQUE(serial),
          PRIMARY KEY(serial)
        );"""

IDENTIFIER_SQL = """CREATE TABLE identifier(
            serial INTEGER NOT NULL,
            identifier TEXT,
            UNIQUE(identifier),
            PRIMARY KEY(serial, identifier)
          );"""

RESISTMOD_SQL = """CREATE TABLE resistmod(
          rid INTEGER NOT NULL PRIMARY KEY,
          serial INTEGER NOT NULL,
          type TEXT,
          amount INT default 0,
          FOREIGN KEY(serial) REFERENCES items(serial)
        );"""

STATMOD_SQL = """CREATE TABLE statmod(
          sid INTEGER NOT NULL PRIMARY KEY,
          serial INTEGER NOT NULL,
          type TEXT,
          amount INT default 0,
          FOREIGN KEY(serial) REFERENCES items(serial)
        );"""

AFFECTMOD_SQL = """CREATE TABLE affectmod(
          aid INTEGER NOT NULL PRIMARY KEY,
          serial INTEGER NOT NULL,
          type TEXT,
          FOREIGN KEY(serial) REFERENCES items(serial)
        );"""

SKILLMOD_SQL = """CREATE TABLE skillmod(
          skid INTEGER NOT NULL PRIMARY KEY,
          serial INTEGER NOT NULL,
          skillnum INT,
          amount INT default 0,
          FOREIGN KEY(serial) REFERENCES items(serial)
        );"""

NOTES_SQL = """CREATE TABLE notes(
          nid INTEGER NOT NULL PRIMARY KEY,
          serial INTEGER NOT NULL,
          ntext TEXT,
          UNIQUE(serial),
          FOREIGN KEY(serial) REFERENCES items(serial)
        );"""

ADDEDNOTES_SQL = """CREATE TABLE addednotes(
          anid INTEGER NOT NULL PRIMARY KEY,
          serial INTEGER NOT NULL,
          ntext TEXT
        );"""

WEAPON_SQL = """CREATE TABLE weapon(
          wid INTEGER NOT NULL PRIMARY KEY,
          serial INTEGER NOT NULL,
          wtype TEXT,
          damtype TEXT,
          special TEXT,
          inflicts TEXT,
          avedam INT,
          UNIQUE(serial),
          FOREIGN KEY(serial) REFERENCES items(serial)
        );"""

CONTAINER_SQL = """CREATE TABLE container(
          cid INTEGER NOT NULL PRIMARY KEY,
          serial INTEGER NOT NULL,
          itemweightpercent INT,
          heaviestitem INT,
          capacity INT,
          holding INT,
          itemsinside INT,
          totalweight INT,
          itemburden INT,
          UNIQUE(serial),
          FOREIGN KEY(serial) REFERENCES items(serial)
        );"""

SPELLS_SQL = """CREATE TABLE spells(
          spid INTEGER NOT NULL PRIMARY KEY,
          serial INTEGER NOT NULL,
          uses INT,
          level INT,
          sn1 INT,
          sn2 INT,
          sn3 INT,
          sn4 INT,
          u1 INT,
          UNIQUE(serial),
          FOREIGN KEY(serial) REFERENCES items(serial)
        );"""

FOOD_SQL = """CREATE TABLE food(
          fid INTEGER NOT NULL PRIMARY KEY,
          serial INTEGER NOT NULL,
          percent INT,
          UNIQUE(serial),
          FOREIGN KEY(serial) REFERENCES items(serial)
        );"""

DRINK_SQL = """CREATE TABLE drink(
          did INTEGER NOT NULL PRIMARY KEY,
          serial INTEGER NOT NULL,
          servings INT,
          liquid INT,
          liquidmax INT,
          liquidleft INT,
          thirstpercent INT,
          hungerpercent INT,
          u1 INT,
          UNIQUE(serial),
          FOREIGN KEY(serial) REFERENCES items(serial)
        );"""

FURNITURE_SQL = """CREATE TABLE furniture(
          fuid INTEGER NOT NULL PRIMARY KEY,
          serial INTEGER NOT NULL,
          hpregen INT,
          manaregen INT,
          u1 INT,
          UNIQUE(serial),
          FOREIGN KEY(serial) REFERENCES items(serial)
        );"""

LIGHT_SQL = """CREATE TABLE light(
          lid INTEGER NOT NULL PRIMARY KEY,
          serial INTEGER NOT NULL,
          duration INT,
          UNIQUE(serial),
          FOREIGN KEY(serial) REFERENCES items(serial)
        );"""

PORTAL_SQL = """CREATE TABLE portal(
          portid INTEGER NOT NULL PRIMARY KEY,
          serial INTEGER NOT NULL,
          uses INT,
          UNIQUE(serial),
          FOREIGN KEY(serial) REFERENCES items(serial)
        );"""

ENCHANT_SQL = """CREATE TABLE enchant(
          enchantid INTEGER NOT NULL PRIMARY KEY,
          serial INTEGER NOT NULL,
          etype TEXT,
          spell TEXT,
          stat TEXT,
          mod INT default 0,
          char text,
          removable text,
          FOREIGN KEY(serial) REFERENCES items(serial)
        );"""

REWARD_SQL = """CREATE TABLE reward(
          rewardid INTEGER NOT NULL PRIMARY KEY,
          serial INTEGER NOT NULL,
          rtext TEXT,
          UNIQUE(serial),
          FOREIGN KEY(serial) REFERENCES items(serial)
      );"""

TABLES: list[dict[str, Any]] = [
    {"name": "items", "sql": ITEMS_SQL, "keyfield": "serial"},
    {"name": "identifier", "sql": IDENTIFIER_SQL},
    {"name": "resistmod", "sql": RESISTMOD_SQL, "keyfield": "rid"},
    {"name": "statmod", "sql": STATMOD_SQL, "keyfield": "sid"},
    {"name": "affectmod", "sql": AFFECTMOD_SQL, "keyfield": "aid"},
    {"name": "skillmod", "sql": SKILLMOD_SQL, "keyfield": "skid"},
    {"name": "notes", "sql": NOTES_SQL, "keyfield": "nid"},
    {"name": "addednotes", "sql": ADDEDNOTES_SQL, "keyfield": "anid"},
    {"name": "weapon", "sql": WEAPON_SQL, "keyfield": "wid"},
    {"name": "container", "sql": CONTAINER_SQL, "keyfield": "cid"},
    {"name": "spells", "sql": SPELLS_SQL, "keyfield": "spid"},
    {"name": "food", "sql": FOOD_SQL, "keyfield": "fid"},
    {"name": "drink", "sql": DRINK_SQL, "keyfield": "did"},
    {"name": "furniture", "sql": FURNITURE_SQL, "keyfield": "fuid"},
    {"name": "light", "sql": LIGHT_SQL, "keyfield": "lid"},
    {"name": "portal", "sql": PORTAL_SQL, "keyfield": "portid"},
    {"name": "enchant", "sql": ENCHANT_SQL, "keyfield": "enchantid"},
    {"name": "reward", "sql": REWARD_SQL, "keyfield": "rewardid"},
]

# detail tables that hold many rows for an item
MULTI_DETAILS = ("statmod", "resistmod", "skillmod", "affectmod", "enchant")
# detail tables that hold one row for an item
SINGLE_DETAILS = (
    "notes",
    "reward",
    "weapon",
    "light",
    "portal",
    "furniture",
    "container",
    "drink",
    "food",
    "spells",
)
