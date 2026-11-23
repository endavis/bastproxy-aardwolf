"""Read and write items in the eqdb database.

Ported from the old ``EqDb`` class. An item is a plain mapping, not an ``Item`` object: the
keys of the ``items`` row, plus an optional key for each detail table (see
``MULTI_DETAILS`` and ``SINGLE_DETAILS``). Every value goes in as a bound parameter, and a
table name only ever comes from a constant of ``_schema``. The caller's mapping is never
changed.
"""

import copy
from collections.abc import Iterable, Mapping
from typing import Any

from ._db import EqDb
from ._schema import MULTI_DETAILS, SINGLE_DETAILS, TABLES

# the key column of each table that has one
_KEYFIELDS = {table["name"]: table["keyfield"] for table in TABLES if "keyfield" in table}


def _split(value: object) -> list[str]:
    """Return a comma separated column as a list; an empty or missing value is ``[]``."""
    if not isinstance(value, str) or not value:
        return []
    return value.split(",")


def _join(value: object) -> str:
    """Return a list as a comma separated string.

    ``None`` is stored as an empty string and a string is stored as it is.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, Iterable):
        return ",".join(str(part) for part in value)
    return str(value)


class ItemStore:
    """Read and write items through a ``Sqldb``."""

    def __init__(self, db: EqDb) -> None:
        """Keep the database."""
        self.db = db

    @staticmethod
    def parse_serial(ident: object) -> int | None:
        """Return ident as a serial, or None when it is not a whole number."""
        if isinstance(ident, bool):
            return None
        if isinstance(ident, int):
            return ident
        if isinstance(ident, str) and ident.isascii() and ident.isdigit():
            return int(ident)
        return None

    # reading

    def get_by_serial(self, serial: int) -> dict[str, Any] | None:
        """Return the ``items`` row of a serial, or None."""
        rows = self.db.select("SELECT * FROM items WHERE serial = ?", (serial,))
        return rows[0] if len(rows) == 1 else None

    def get_by_identifier(self, identifier: str) -> dict[str, Any] | None:
        """Return the ``items`` row an identifier points at, or None."""
        rows = self.db.select("SELECT * FROM identifier WHERE identifier = ?", (identifier,))
        if len(rows) != 1:
            return None
        return self.get_by_serial(rows[0]["serial"])

    def get_item(self, ident: object, details: bool = True) -> dict[str, Any] | None:
        """Return an item by serial, then by identifier, or None.

        ``flags`` and ``keywords`` come back as lists. With details, the detail keys come back
        in the shapes ``save_item`` takes.
        """
        item: dict[str, Any] | None = None
        serial = self.parse_serial(ident)
        if serial is not None:
            item = self.get_by_serial(serial)
        if item is None and isinstance(ident, str):
            item = self.get_by_identifier(ident)
        if item is None:
            return None
        if details:
            item.update(self.get_details(int(item["serial"])))
        item["flags"] = _split(item.get("flags"))
        item["keywords"] = _split(item.get("keywords"))
        return item

    def _rows(self, table: str, serial: int) -> list[dict[str, Any]]:
        """Return the rows of a detail table for a serial."""
        # The table name comes from the schema's constant tuples; the serial is a parameter.
        return self.db.select(
            "SELECT * FROM {} WHERE serial = ?".format(table),  # noqa: UP032  # nosec B608  # schema table
            (serial,),
        )

    def _single(self, table: str, serial: int) -> dict[str, Any] | None:
        """Return the one row of a detail table without its serial and key, or None."""
        rows = self._rows(table, serial)
        if not rows:
            return None
        row = rows[0]
        row.pop("serial", None)
        row.pop(_KEYFIELDS[table], None)
        return row

    def get_details(self, serial: int) -> dict[str, Any]:
        """Return the details of an item; a detail with no rows is left out."""
        details: dict[str, Any] = {}
        for table in ("statmod", "resistmod"):
            rows = self._rows(table, serial)
            if rows:
                details[table] = {row["type"]: row["amount"] for row in rows}
        rows = self._rows("skillmod", serial)
        if rows:
            details["skillmod"] = {row["skillnum"]: row["amount"] for row in rows}
        rows = self._rows("affectmod", serial)
        if rows:
            details["affectmod"] = [row["type"] for row in rows]
        rows = self._rows("enchant", serial)
        if rows:
            enchants = []
            for row in rows:
                row.pop("serial", None)
                row.pop(_KEYFIELDS["enchant"], None)
                enchants.append(row)
            details["enchant"] = enchants
        for table in SINGLE_DETAILS:
            row_data = self._single(table, serial)
            if row_data is not None:
                details[table] = row_data
        return details

    # writing

    def _replace_rows(self, table: str, serial: int, rows: list[dict[str, Any]]) -> None:
        """Delete the rows of a detail table for a serial, then insert the new ones."""
        if table not in (*MULTI_DETAILS, *SINGLE_DETAILS):
            msg = f"not a detail table: {table}"
            raise ValueError(msg)
        # The table name was checked against the schema's constants above.
        self.db.modify(
            "DELETE FROM {} WHERE serial = ?".format(table),  # noqa: UP032  # nosec B608  # schema table
            (serial,),
        )
        if not rows:
            return
        data = []
        for row in rows:
            new_row = self.db.checkdictforcolumns(table, copy.deepcopy(row))
            new_row["serial"] = serial
            data.append(new_row)
        self.db.modifymany(self.db.converttoinsert(table, True), data)

    @staticmethod
    def _detail_rows(table: str, value: object) -> list[dict[str, Any]]:
        """Return the rows to insert for a detail value, in the shape ``get_item`` returns."""
        if not value:
            return []
        if table in ("statmod", "resistmod") and isinstance(value, Mapping):
            return [{"type": name, "amount": amount} for name, amount in value.items()]
        if table == "skillmod" and isinstance(value, Mapping):
            return [{"skillnum": num, "amount": amount} for num, amount in value.items()]
        if table == "affectmod" and not isinstance(value, Mapping | str):
            return [{"type": name} for name in value]  # type: ignore[attr-defined]
        if table == "enchant" and not isinstance(value, Mapping | str):
            return [dict(row) for row in value]  # type: ignore[attr-defined]
        if table in SINGLE_DETAILS and isinstance(value, Mapping):
            return [dict(value)]
        msg = f"the {table} detail has the wrong shape"
        raise ValueError(msg)

    def save_item(self, item: Mapping[str, Any]) -> bool:
        """Save an item and the details it holds. Returns False when it has no valid serial.

        A detail key that is present replaces that table's rows for the item, and an empty
        value clears them. A key that is absent leaves the table alone.
        """
        serial = self.parse_serial(item.get("serial"))
        if serial is None:
            return False
        # build every detail first, so a wrong shape raises before anything is written
        details = {
            table: self._detail_rows(table, item[table])
            for table in (*MULTI_DETAILS, *SINGLE_DETAILS)
            if table in item
        }
        row = copy.deepcopy(dict(item))
        row["serial"] = serial
        row["keywords"] = _join(row.get("keywords"))
        row["flags"] = _join(row.get("flags"))
        new_row = self.db.checkdictforcolumns("items", row)
        self.db.modify(self.db.converttoinsert("items", False, True), new_row)
        for table, rows in details.items():
            self._replace_rows(table, serial, rows)
        return True
