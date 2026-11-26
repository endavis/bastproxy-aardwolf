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


def formatters(line_length: int = 40) -> "Formatters":
    """Return report formatters that need no bastproxy plugin."""
    from aardwolf.statdb.libs import Formatters

    return Formatters(
        format_time=lambda seconds: f"{int(seconds)}s",
        readable=lambda number: f"<{number}>",
        line_length=line_length,
    )
