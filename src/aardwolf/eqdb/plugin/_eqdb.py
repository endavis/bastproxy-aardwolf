"""The Aardwolf eqdb plugin: a database of the character's identified items."""

import logging
import sqlite3
import time
from collections.abc import Mapping
from typing import Any

from bastproxy.libs.api import AddAPI
from bastproxy.libs.logger import log_to
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.commands import AddArgument, AddCommand, AddParser, CommandResult
from bastproxy.plugins.core.events import RegisterToEvent

from ..libs import DB_NAME, DB_VERSION, MIGRATIONS, TABLES, ItemStore

NO_DB = "The eq database is not available"
NO_ITEM = "There is no item with that serial or identifier"
NO_ID = "Give the serial or identifier of an item"


class EqdbPlugin(BasePlugin):
    """Keep the character's identified items in a database."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Initialize the instance."""
        self.store: ItemStore | None = None

    @property
    def _backup_start_timer(self) -> str:
        """The name of the timer that makes the first backup."""
        return f"{self.plugin_id}_backup_start"

    @property
    def _backup_timer(self) -> str:
        """The name of the timer that repeats the backup."""
        return f"{self.plugin_id}_backup"

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the settings, open the database and schedule backups."""
        add_setting = self.api("plugins.core.settings:setting.add")
        add_setting(
            self.plugin_id,
            "backupstart",
            "0000",
            "miltime",
            "the time (UTC) for the first db backup of a day, ex. 1200 or 2000",
        )
        add_setting(
            self.plugin_id,
            "backupinterval",
            "4h",
            "timelength",
            "the interval to backup the db, default every 4 hours",
        )

        try:
            db = self.api("plugins.core.sqldb:database.add")(
                self.plugin_id, DB_NAME, TABLES, version=DB_VERSION, migrations=MIGRATIONS
            )
        except (ValueError, sqlite3.Error) as exc:
            log_to(self.plugin_id, logging.ERROR, "could not open the eq database: %s", exc)
            self.store = None
        else:
            self.store = ItemStore(db)

        self._schedule_backup()

    # backups

    def _setting(self, name: str) -> object:
        """Return the value of one of this plugin's settings."""
        return self.api("plugins.core.settings:setting.get")(self.plugin_id, name)

    def _schedule_backup(self) -> None:
        """Replace the backup timers: one at the start time, which then adds the interval."""
        for name in (self._backup_start_timer, self._backup_timer):
            # timer.remove logs an error for a timer that does not exist, as on first load.
            if self.api("plugins.core.timers:timer.exists")(name):
                self.api("plugins.core.timers:timer.remove")(name)
        self.api("plugins.core.timers:timer.add")(
            self._backup_start_timer,
            self._timer_backup_start,
            86400,
            time=self._setting("backupstart"),
            onetime=True,
        )

    def _timer_backup_start(self) -> None:
        """Back up at the start time, then back up every interval."""
        self._backup()
        interval = self._setting("backupinterval")
        if isinstance(interval, int) and interval >= 1:
            self.api("plugins.core.timers:timer.add")(
                self._backup_timer, self._timer_backup, interval
            )

    def _timer_backup(self) -> None:
        """Back up from the interval timer."""
        self._backup()

    def _backup(self) -> bool:
        """Back the database up, named by the time. Returns True when it was saved."""
        if self.store is None:
            return False
        return bool(self.store.db.backupdb(time.strftime("%a-%b-%d-%Y-%H-%M")))

    @RegisterToEvent(event_name="ev_{plugin_id}_var_backupstart_modified")
    @RegisterToEvent(event_name="ev_{plugin_id}_var_backupinterval_modified")
    def _eventcb_backup_setting_modified(self) -> None:
        """A backup setting changed: schedule the backups again."""
        self._schedule_backup()

    # APIs

    @AddAPI(
        "item.get",
        description="return an item by serial or identifier, with its details, or None",
    )
    def _api_item_get(self, ident: int | str, details: bool = True) -> dict[str, Any] | None:
        """Return a new dict for the item, or None when there is none or no database."""
        if self.store is None:
            return None
        return self.store.get_item(ident, details)

    @AddAPI("item.save", description="save an item and its details; return True when saved")
    def _api_item_save(self, item: Mapping[str, Any]) -> bool:
        """Save an item mapping. Returns False on a missing serial, a wrong detail shape or a
        database failure."""
        if self.store is None:
            return False
        try:
            return self.store.save_item(item)
        except (ValueError, sqlite3.Error):
            log_to(self.plugin_id, logging.ERROR, "could not save the item", exc_info=True)
            return False

    # commands

    def _args(self) -> dict[str, Any]:
        """Return the arguments of the running command."""
        args = self.api("plugins.core.commands:command.current.args.get")()
        return dict(args) if args else {}

    @AddCommand()
    @AddParser(description="show an item from the database")
    @AddArgument("id", help="the serial or identifier", default="", nargs="?")
    def _command_getitem(self) -> CommandResult:
        """Show an item, one sorted ``key: value`` line per field."""
        if self.store is None:
            return CommandResult(True, [NO_DB])
        ident = str(self._args().get("id", ""))
        if not ident:
            return CommandResult(True, [NO_ID])
        item = self.store.get_item(ident)
        if item is None:
            return CommandResult(True, [NO_ITEM])
        lines = [f"Item {item['serial']}"]
        lines.extend(f"{key}: {item[key]}" for key in sorted(item) if key != "serial")
        return CommandResult(True, lines)
