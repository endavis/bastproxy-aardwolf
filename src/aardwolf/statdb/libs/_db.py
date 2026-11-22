"""The part of the bastproxy ``Sqldb`` class that the statdb library uses."""

from collections.abc import Mapping, Sequence
from typing import Any, Protocol


class StatsDb(Protocol):
    """A database object with the ``Sqldb`` methods statdb calls.

    The library takes this instead of importing bastproxy, so tests and tools can pass any
    object that has these methods.
    """

    def select(
        self, _sql_statement: str, _params: Sequence[Any] | Mapping[str, Any] = (), /
    ) -> list[dict[str, Any]]:
        """Run a select statement and return its rows."""
        ...

    def modify(self, _sql_statement: str, _data: object = None, /) -> tuple[int | None, Any]:
        """Run one modifying statement and return ``(lastrowid, None)``."""
        ...

    def modifymany(self, _sql_statement: str, _data: object = None, /) -> tuple[int | None, Any]:
        """Run one modifying statement once for each item of data."""
        ...

    def modifyscript(self, _sql_statement: str, /) -> tuple[int | None, Any]:
        """Run a script of statements, all or none."""
        ...

    def checkdictforcolumns(self, _tablename: str, _temp_dict: dict[str, Any], /) -> dict[str, Any]:
        """Return a dict with every column of the table, filling defaults."""
        ...

    def converttoinsert(
        self, _tablename: str, _keynull: bool = False, _replace: bool = False, /
    ) -> str:
        """Return an INSERT statement for the table."""
        ...

    def checkcolumnexists(self, _table: str, _columnname: str, /) -> bool:
        """Return True when the table has the column."""
        ...

    def checktableexists(self, _tablename: str, /) -> bool:
        """Return True when the table exists in the file."""
        ...

    def getlast(
        self, _table_name: str, _num: int, _where: str | Mapping[str, Any] = "", /
    ) -> list[dict[str, Any]] | dict[str, Any]:
        """Return the last rows of a table, newest first."""
        ...

    def getrow(self, _row_id: int, _table_name: str, /) -> list[dict[str, Any]] | dict[str, Any]:
        """Return the row with a key, as a list."""
        ...

    def getlastrowid(self, _table_name: str, /) -> int:
        """Return the highest key of a table, or -1 when it is empty."""
        ...

    def selectbykeyword(self, _selectstmt: str, _keyword: str, /) -> dict[Any, dict[str, Any]]:
        """Return the rows of a select keyed by one column."""
        ...

    def backupdb(self, _postname: str | int, /) -> bool:
        """Back the database up into its archive directory."""
        ...
