"""The part of the bastproxy ``Sqldb`` class that the eqdb library uses."""

from collections.abc import Mapping, Sequence
from typing import Any, Protocol


class EqDb(Protocol):
    """A database object with the ``Sqldb`` methods eqdb calls.

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

    def checkdictforcolumns(self, _tablename: str, _temp_dict: dict[str, Any], /) -> dict[str, Any]:
        """Return a dict with every column of the table, filling defaults."""
        ...

    def converttoinsert(
        self, _tablename: str, _keynull: bool = False, _replace: bool = False, /
    ) -> str:
        """Return an INSERT statement for the table."""
        ...

    def backupdb(self, _postname: str | int, /) -> bool:
        """Back the database up into its archive directory."""
        ...
