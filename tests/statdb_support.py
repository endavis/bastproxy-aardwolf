"""Shared helpers for the statdb tests. Not a test module.

``make_db`` imports bastproxy, which raises unless ``BASTPROXY_HOME`` is an existing directory,
so a test sets that with ``monkeypatch.setenv`` before it calls ``make_db``.
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bastproxy.plugins.core.sqldb.libs._sqlite import Sqldb

    from aardwolf.statdb.libs import Formatters

OWNER = "plugins.aardwolf.statdb"


def make_db(directory: Path, *, journal_mode: str | None = None) -> "Sqldb":
    """Open the statdb database in a directory the way ``database.add`` does.

    ``journal_mode`` is passed on as ``database.add`` gets it; None leaves sqlite's default.
    """
    from bastproxy.plugins.core.sqldb.libs._sqlite import create_database

    from aardwolf.statdb.libs import DB_NAME, DB_VERSION, MIGRATIONS, TABLES

    return create_database(
        OWNER,
        DB_NAME,
        TABLES,
        version=DB_VERSION,
        migrations=MIGRATIONS,
        directory=directory,
        journal_mode=journal_mode,
    )


class TableRecorder:
    """A stand-in for table.format: records each call and returns the title as the one line."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, list[dict[str, str]], list[dict[str, str]]]] = []

    def __call__(
        self, title: str, data: list[dict[str, str]], columns: list[dict[str, str]]
    ) -> list[str]:
        for row in data:
            for column in columns:
                if column["key"] not in row:
                    raise KeyError(f"table {title!r}: row {row!r} lacks the key {column['key']!r}")
        self.calls.append((title, list(data), columns))
        return [title]


def formatters(line_length: int = 40, table: TableRecorder | None = None) -> "Formatters":
    """Return report formatters that need no bastproxy plugin.

    ``table`` records the table.format calls; without one a recorder is made.
    """
    from aardwolf.statdb.libs import Formatters

    return Formatters(
        format_time=lambda seconds: f"{int(seconds)}s",
        readable=lambda number: f"<{number}>",
        table=table if table is not None else TableRecorder(),
        line_length=line_length,
    )
