"""Write the Aardwolf events into the stats database.

Ported from the old ``Statdb`` class. Every value goes in as a bound parameter, and a stat
name is checked against the ``stats`` columns before it is put in a statement. Each ``save_*``
method takes an event payload and leaves it unchanged.
"""

import time
from collections.abc import Mapping
from typing import Any

from aardwolf.libs.aardu import CLASSABB, convert_level

from ._db import StatsDb

CURRENT = "current"


def _int(value: object) -> int:
    """Return value as an int, or 0 when it is missing or not a number."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int | float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0


def class_names(classes: object) -> list[dict[str, Any]]:
    """Return whois classes with each class as its full name.

    The whois plugin sends abbreviations such as ``mag``; the table holds full names.
    A full name stays as it is.
    """
    result: list[dict[str, Any]] = []
    if not isinstance(classes, list | tuple):
        return result
    for item in classes:
        if isinstance(item, Mapping) and "class" in item and "remort" in item:
            name = str(item["class"]).lower()
            result.append({"class": CLASSABB.get(name, name), "remort": item["remort"]})
    return result


class StatStore:
    """Read and write the statdb tables through a ``Sqldb``."""

    def __init__(self, db: StatsDb) -> None:
        """Keep the database."""
        self.db = db

    # stats table

    def current_row(self) -> dict[str, Any] | None:
        """Return the ``current`` row of the stats table, or None."""
        rows = self.db.select("SELECT * FROM stats WHERE milestone = ?", (CURRENT,))
        return rows[0] if rows else None

    def get_stat(self, stat: str) -> object:
        """Return one stat of the current row, or None."""
        row = self.current_row()
        if row is None:
            return None
        return row.get(stat)

    def stored_name(self) -> str | None:
        """Return the character name of the current row, or None when there is none."""
        name = self.get_stat("name")
        return name if isinstance(name, str) and name.strip() else None

    def set_stat(self, stat: str, value: object) -> bool:
        """Set one stat of the current row. Returns False for an unknown stat."""
        if not self.db.checkcolumnexists("stats", stat):
            return False
        self.db.modify(
            # The column name cannot be a parameter; it was checked against the table above.
            "UPDATE stats SET {} = ? WHERE milestone = ?".format(stat),  # noqa: UP032  # nosec B608  # column checked
            (value, CURRENT),
        )
        return True

    def add_to_stat(self, stat: str, add: object) -> bool:
        """Add to one stat of the current row.

        Returns True when nothing needed adding (zero or less) or the stat was added to, and
        False for an unknown stat.
        """
        amount = _int(add)
        if amount <= 0:
            return True
        if not self.db.checkcolumnexists("stats", stat):
            return False
        self.db.modify(
            # The column name cannot be a parameter; it was checked against the table above.
            "UPDATE stats SET {0} = {0} + ? WHERE milestone = ?".format(stat),  # noqa: UP032  # nosec B608  # column checked
            (amount, CURRENT),
        )
        return True

    def get_milestone(self, milestone: str) -> dict[str, Any] | None:
        """Return the stats row of a milestone, or None."""
        rows = self.db.select("SELECT * FROM stats WHERE milestone = ?", (milestone,))
        return rows[0] if rows else None

    def add_milestone(self, milestone: str) -> int:
        """Copy the current stats into a new milestone row.

        Returns the new row id, or -1 when the name is empty or exists, or there is no
        current row.
        """
        if not milestone or self.get_milestone(milestone) is not None:
            return -1
        current = self.current_row()
        if not current:
            return -1
        current["milestone"] = milestone
        current["time"] = self._now()
        rowid, _ = self.db.modify(self.db.converttoinsert("stats", True), current)
        return -1 if rowid is None else rowid

    @staticmethod
    def _now() -> float:
        """Return the current time in seconds since the epoch."""
        return time.time()

    # classes table

    def add_classes(self, classes: object) -> None:
        """Record the remort of each class from a whois."""
        self.db.modifymany(
            "UPDATE classes SET remort = :remort WHERE class = :class", class_names(classes)
        )

    def get_classes(self) -> list[str]:
        """Return the classes the character has taken, in remort order."""
        rows = self.db.select("SELECT * FROM classes ORDER BY remort ASC")
        return [row["class"] for row in rows if row["remort"] != -1]

    def reset_classes(self) -> None:
        """Set every class back to remort -1."""
        self.db.modify("UPDATE classes SET remort = -1")

    # event saves

    def save_whois(self, info: Mapping[str, Any]) -> None:
        """Save a whois: update the current stats, or start them with a ``start`` milestone.

        The stat lines of the whois are nested under ``stats`` in the payload; they are read
        as columns next to the other keys.
        """
        flat = {key: value for key, value in info.items() if key != "stats"}
        flat.update(info.get("stats") or {})
        info = flat
        current = self.current_row()
        if current:
            merged = dict(current)
            merged.update({key: value for key, value in info.items() if key in current})
            merged["milestone"] = CURRENT
            merged["time"] = 0
            skip = {"stat_id", "totaltrivia", "milestone"}
            columns = [name for name in current if name not in skip]
            assignments = ", ".join(f"{name} = :{name}" for name in columns)
            self.db.modify(
                # The column names come from the current row, which the table itself supplied.
                "UPDATE stats SET {} WHERE milestone = :milestone".format(assignments),  # noqa: UP032  # nosec B608  # table columns
                merged,
            )
        else:
            row = dict(info)
            row["milestone"] = CURRENT
            row["totaltrivia"] = 0
            row["time"] = 0
            row = self.db.checkdictforcolumns("stats", row)
            self.db.modify(self.db.converttoinsert("stats", True), row)
            self.add_milestone("start")
        self.add_classes(info.get("classes"))

    def save_quest(self, info: Mapping[str, Any]) -> int:
        """Save a quest and add it to the stats. Returns the new row id."""
        if _int(info.get("failed")) == 1:
            self.add_to_stat("questsfailed", 1)
        else:
            self.add_to_stat("questscomplete", 1)
            self.add_to_stat("qpearned", info.get("totqp"))
            self.add_to_stat("totaltrivia", info.get("tp"))
        return self._insert("quests", info)

    def save_cp(self, info: Mapping[str, Any]) -> int:
        """Save a campaign and its mobs and add it to the stats. Returns the new row id."""
        if _int(info.get("failed")) == 1:
            self.add_to_stat("campaignsfld", 1)
        else:
            self.add_to_stat("campaignsdone", 1)
            self.add_to_stat("qpearned", info.get("qp"))
            self.add_to_stat("totaltrivia", info.get("tp"))
        rowid = self._insert("campaigns", info)
        self._insert_many("cpmobs", info.get("mobs"), {"cp_id": rowid})
        return rowid

    def save_gq(self, info: Mapping[str, Any]) -> int:
        """Save a global quest and its mobs and add it to the stats. Returns the new row id."""
        self.add_to_stat("qpearned", _int(info.get("qp")) + _int(info.get("qpmobs")))
        self.add_to_stat("totaltrivia", info.get("tp"))
        if _int(info.get("won")) == 1:
            self.add_to_stat("gquestswon", 1)
        rowid = self._insert("gquests", info)
        self._insert_many("gqmobs", info.get("mobs"), {"gq_id": rowid})
        return rowid

    def save_level(self, info: Mapping[str, Any]) -> int:
        """Save a level or a pup and update the stats. Returns the new row id.

        A level adds a ``totallevels`` milestone.
        """
        row = dict(info)
        total = _int(row.get("totallevels"))
        if row.get("type") == "level":
            if total > 0:
                self.set_stat("totallevels", total)
                self.set_stat("level", row.get("level"))
            else:
                self.add_to_stat("totallevels", 1)
                self.add_to_stat("level", 1)
        elif row.get("type") == "pup":
            self.add_to_stat("powerupsall", 1)
        row["level"] = total if total > 0 else self.get_stat("totallevels")
        row["finishtime"] = -1
        rowid = self._insert("levels", row)
        if rowid > 1:
            self.db.modify(
                "UPDATE levels SET finishtime = ? WHERE level_id = ?",
                (row.get("starttime"), rowid - 1),
            )
        if row.get("type") == "level":
            self.add_milestone(str(row["level"]))
        return rowid

    def save_mobkill(self, info: Mapping[str, Any]) -> int:
        """Save a mob kill and add it to the stats. Returns the new row id."""
        self.add_to_stat("totaltrivia", info.get("tp"))
        self.add_to_stat("monsterskilled", 1)
        return self._insert("mobkills", info)

    def recent_mobkills(self, count: int) -> list[dict[str, Any]]:
        """Return the last ``count`` mob kills, newest first."""
        return self.db.select("SELECT * FROM mobkills ORDER BY mk_id DESC LIMIT ?", (count,))

    def record_death(self) -> None:
        """Count a death."""
        self.add_to_stat("timeskilled", 1)

    def hero_milestone(self, total_level: int) -> str:
        """Return the milestone name for a total level, such as ``t2r3l10``."""
        parts = convert_level(total_level)
        if parts["tier"] == 9:
            return f"t9+{parts['redos']}r{parts['remort']}l{parts['level']}"
        return f"t{parts['tier']}r{parts['remort']}l{parts['level']}"

    def apply_remort(self, remorts: object, tier: object, total: int) -> None:
        """Set the stats after a remort: remorts, tier and total level, back to level 1."""
        self.set_stat("remorts", _int(remorts))
        self.set_stat("tiers", _int(tier))
        self.set_stat("totallevels", total)
        self.set_stat("level", 1)

    # helpers

    def _insert(self, table: str, info: Mapping[str, Any]) -> int:
        """Insert one row, with defaults for the columns info lacks. Returns the row id."""
        row = self.db.checkdictforcolumns(table, dict(info))
        rowid, _ = self.db.modify(self.db.converttoinsert(table, True), row)
        return -1 if rowid is None else rowid

    def _insert_many(self, table: str, items: object, extra: Mapping[str, Any]) -> None:
        """Insert a row for each mapping in items, with the extra values added."""
        if not isinstance(items, list | tuple):
            return
        rows = [
            self.db.checkdictforcolumns(table, {**item, **extra})
            for item in items
            if isinstance(item, Mapping)
        ]
        self.db.modifymany(self.db.converttoinsert(table, True), rows)
