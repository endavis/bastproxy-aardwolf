"""The Aardwolf statdb plugin: a stats database filled from the Aardwolf events."""

import copy
import logging
import sqlite3
import time
from collections.abc import Callable
from typing import Any

from bastproxy.libs.logger import log_to
from bastproxy.libs.records import NetworkData, NetworkDataLine, SendDataDirectlyToClient
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.commands import AddArgument, AddCommand, AddParser, CommandResult
from bastproxy.plugins.core.events import RegisterToEvent

from aardwolf.libs.aardu import actual_level_from_gmcp

from ..libs import (
    DB_NAME,
    DB_VERSION,
    DEFAULT_MOBKILL_COUNT,
    MIGRATIONS,
    TABLES,
    Formatters,
    StatStore,
    compare_milestones,
    cp_report,
    gq_report,
    level_report,
    list_milestones,
    mob_report,
    mobkill_list,
    quest_report,
)

PREFIX = "ev_plugins.aardwolf."
EVENT_QUEST_COMP = f"{PREFIX}quest_comp"
EVENT_QUEST_FAILED = f"{PREFIX}quest_failed"
EVENT_CP_COMP = f"{PREFIX}cp_comp"
EVENT_CP_FAILED = f"{PREFIX}cp_failed"
EVENT_WHOIS = f"{PREFIX}whois_received"
EVENT_LEVEL_GAIN = f"{PREFIX}level_gain"
EVENT_LEVEL_HERO = f"{PREFIX}level_hero"
EVENT_LEVEL_SUPERHERO = f"{PREFIX}level_superhero"
EVENT_LEVEL_REMORT = f"{PREFIX}level_remort"
EVENT_LEVEL_TIER = f"{PREFIX}level_tier"
EVENT_MOBKILL = f"{PREFIX}mobk_kill"
EVENT_GQ_COMPLETED = f"{PREFIX}gq_completed"
EVENT_GQ_DONE = f"{PREFIX}gq_done"
EVENT_GQ_WON = f"{PREFIX}gq_won"

# every event statdb subscribes to from the other Aardwolf plugins
EVENTS = (
    EVENT_QUEST_COMP,
    EVENT_QUEST_FAILED,
    EVENT_CP_COMP,
    EVENT_CP_FAILED,
    EVENT_WHOIS,
    EVENT_LEVEL_GAIN,
    EVENT_LEVEL_HERO,
    EVENT_LEVEL_SUPERHERO,
    EVENT_LEVEL_REMORT,
    EVENT_LEVEL_TIER,
    EVENT_MOBKILL,
    EVENT_GQ_COMPLETED,
    EVENT_GQ_DONE,
    EVENT_GQ_WON,
)


DEAD_TRIGGER = "dead"
DEAD_REGEX = r"^You die\.$"

NO_DB = "The stats database is not available"


class StatdbPlugin(BasePlugin):
    """Record Aardwolf stats, quests, campaigns, global quests, levels and mob kills."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Initialize the instance."""
        self.statdb: StatStore | None = None

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
        """Add the settings, open the database, add the death trigger and schedule backups."""
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
            log_to(self.plugin_id, logging.ERROR, "could not open the stats database: %s", exc)
            self.statdb = None
        else:
            self.statdb = StatStore(db)

        result = self.api("plugins.core.triggers:trigger.add")(DEAD_TRIGGER, DEAD_REGEX)
        if result.success:
            self.api("plugins.core.triggers:trigger.register")(
                result.trigger.trigger_id, self._trigger_dead
            )
        else:
            log_to(self.plugin_id, logging.ERROR, "could not add the %s trigger", DEAD_TRIGGER)

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
        if self.statdb is None:
            return False
        return bool(self.statdb.db.backupdb(time.strftime("%a-%b-%d-%Y-%H-%M")))

    @RegisterToEvent(event_name="ev_{plugin_id}_var_backupstart_modified")
    @RegisterToEvent(event_name="ev_{plugin_id}_var_backupinterval_modified")
    def _eventcb_backup_setting_modified(self) -> None:
        """A backup setting changed: schedule the backups again."""
        self._schedule_backup()

    # events

    def _payload(self) -> dict[str, Any]:
        """Return a copy of the current event's data."""
        record = self.api("plugins.core.events:event.current.record.get")()
        return copy.deepcopy(dict(record)) if record else {}

    def _store(self, action: Callable[[StatStore, dict[str, Any]], object]) -> None:
        """Run an action with the store and the event data; log a database failure."""
        if self.statdb is None:
            return
        try:
            action(self.statdb, self._payload())
        except sqlite3.Error:
            log_to(self.plugin_id, logging.ERROR, "could not save the event data", exc_info=True)

    @RegisterToEvent(event_name=EVENT_QUEST_COMP)
    @RegisterToEvent(event_name=EVENT_QUEST_FAILED)
    def _eventcb_quest(self) -> None:
        """Save a quest."""
        self._store(lambda store, info: store.save_quest(info))

    @RegisterToEvent(event_name=EVENT_CP_COMP)
    @RegisterToEvent(event_name=EVENT_CP_FAILED)
    def _eventcb_cp(self) -> None:
        """Save a campaign."""
        self._store(lambda store, info: store.save_cp(info))

    @RegisterToEvent(event_name=EVENT_GQ_COMPLETED)
    @RegisterToEvent(event_name=EVENT_GQ_DONE)
    @RegisterToEvent(event_name=EVENT_GQ_WON)
    def _eventcb_gq(self) -> None:
        """Save a global quest."""
        self._store(lambda store, info: store.save_gq(info))

    @RegisterToEvent(event_name=EVENT_WHOIS)
    def _eventcb_whois(self) -> None:
        """Save the whois data, warning when it is for a different character."""
        self._store(self._save_whois)

    def _save_whois(self, store: StatStore, info: dict[str, Any]) -> None:
        """Warn when the whois is not for the stored character, then save it."""
        stored = store.stored_name()
        new = info.get("name")
        if (
            stored is not None
            and isinstance(new, str)
            and stored.strip().casefold() != new.strip().casefold()
        ):
            msg = (
                f"The stats database holds {stored}, but this whois is for {new}. "
                "A BASTPROXY_HOME holds one character: use a separate BASTPROXY_HOME "
                "for each character."
            )
            log_to([self.plugin_id], logging.WARNING, msg)
            SendDataDirectlyToClient(
                NetworkData([NetworkDataLine(msg)], owner_id=f"{self.plugin_id}:whois_mismatch")
            )()
        store.save_whois(info)

    @RegisterToEvent(event_name=EVENT_LEVEL_GAIN)
    def _eventcb_level_gain(self) -> None:
        """Save a level or a pup."""
        self._store(lambda store, info: store.save_level(info))

    @RegisterToEvent(event_name=EVENT_MOBKILL)
    def _eventcb_mobkill(self) -> None:
        """Save a mob kill."""
        self._store(lambda store, info: store.save_mobkill(info))

    def _actual_level(self) -> int:
        """Return the total level from GMCP."""
        return actual_level_from_gmcp(self.api("libs.net.protocols:gmcp.value.get"))

    @RegisterToEvent(event_name=EVENT_LEVEL_HERO)
    @RegisterToEvent(event_name=EVENT_LEVEL_SUPERHERO)
    @RegisterToEvent(event_name=EVENT_LEVEL_TIER)
    def _eventcb_hero(self) -> None:
        """Add a milestone for the new hero, superhero or tier level."""
        if self.statdb is None:
            return
        self.statdb.add_milestone(self.statdb.hero_milestone(self._actual_level()))

    @RegisterToEvent(event_name=EVENT_LEVEL_REMORT)
    def _eventcb_remort(self) -> None:
        """Set the stats for the new remort, then add a milestone."""
        if self.statdb is None:
            return
        gmcp = self.api("libs.net.protocols:gmcp.value.get")
        total = self._actual_level()
        self.statdb.apply_remort(gmcp("char.base.remorts"), gmcp("char.base.tier"), total)
        self.statdb.add_milestone(self.statdb.hero_milestone(total))

    def _trigger_dead(self) -> None:
        """Count a death."""
        if self.statdb is not None:
            self.statdb.record_death()

    # commands

    def _formatters(self) -> Formatters:
        """Return the bastproxy helpers the reports use."""
        return Formatters(
            format_time=self.api("plugins.core.utils:timelength.format"),
            readable=self.api("plugins.core.utils:number.to.readable"),
            line_length=int(self.api("plugins.core.proxy:line.length.get")()),
        )

    def _args(self) -> dict[str, Any]:
        """Return the arguments of the running command."""
        args = self.api("plugins.core.commands:command.current.args.get")()
        return dict(args) if args else {}

    @AddCommand(group="Milestones")
    @AddParser(description="list milestones")
    def _command_list(self) -> CommandResult:
        """List milestones."""
        if self.statdb is None:
            return CommandResult(True, [NO_DB])
        return CommandResult(True, list_milestones(self.statdb))

    @AddCommand(group="Milestones")
    @AddParser(description="compare milestones")
    @AddArgument("milestone1", help="the first milestone", default="", nargs="?")
    @AddArgument("milestone2", help="the second milestone", default="", nargs="?")
    def _command_comp(self) -> CommandResult:
        """Compare milestones."""
        if self.statdb is None:
            return CommandResult(True, [NO_DB])
        args = self._args()
        return CommandResult(
            True,
            compare_milestones(
                self.statdb, args["milestone1"], args["milestone2"], self._formatters()
            ),
        )

    @AddCommand(group="Stats")
    @AddParser(description="show quest stats")
    @AddArgument("count", help="the number of quests to show", type=int, default=0, nargs="?")
    @AddArgument("-n", "--number", help="show info for quest number", type=int, default=0)
    def _command_quests(self) -> CommandResult:
        """Show quest stats."""
        if self.statdb is None:
            return CommandResult(True, [NO_DB])
        args = self._args()
        return CommandResult(
            True, quest_report(self.statdb, args["count"], args["number"], self._formatters())
        )

    @AddCommand(group="Stats")
    @AddParser(description="show level stats")
    @AddArgument("count", help="the number of levels to show", type=int, default=0, nargs="?")
    @AddArgument("-n", "--number", help="show info for level number", type=int, default=0)
    def _command_levels(self) -> CommandResult:
        """Show level stats."""
        if self.statdb is None:
            return CommandResult(True, [NO_DB])
        args = self._args()
        perlevel = self.api("libs.net.protocols:gmcp.value.get")("char.base.perlevel")
        return CommandResult(
            True,
            level_report(
                self.statdb,
                args["count"],
                args["number"],
                self._formatters(),
                float(perlevel) if isinstance(perlevel, int | float) else None,
            ),
        )

    @AddCommand(group="Stats")
    @AddParser(description="show cp stats")
    @AddArgument("count", help="the number of cps to show", type=int, default=0, nargs="?")
    @AddArgument("-n", "--number", help="show info for cp number", type=int, default=0)
    def _command_cps(self) -> CommandResult:
        """Show campaign stats."""
        if self.statdb is None:
            return CommandResult(True, [NO_DB])
        args = self._args()
        return CommandResult(
            True, cp_report(self.statdb, args["count"], args["number"], self._formatters())
        )

    @AddCommand(group="Stats")
    @AddParser(description="show gq stats")
    @AddArgument("count", help="the number of gqs to show", type=int, default=0, nargs="?")
    @AddArgument("-n", "--number", help="show info for gq number", type=int, default=0)
    def _command_gqs(self) -> CommandResult:
        """Show global quest stats."""
        if self.statdb is None:
            return CommandResult(True, [NO_DB])
        args = self._args()
        return CommandResult(
            True, gq_report(self.statdb, args["count"], args["number"], self._formatters())
        )

    @AddCommand(group="Stats")
    @AddParser(description="show mob stats")
    @AddArgument("count", help="the number of mobkills to show", type=int, default=0, nargs="?")
    def _command_mobs(self) -> CommandResult:
        """Show mob kill stats."""
        if self.statdb is None:
            return CommandResult(True, [NO_DB])
        args = self._args()
        return CommandResult(True, mob_report(self.statdb, args["count"], self._formatters()))

    @AddCommand(group="Stats")
    @AddParser(description="list the most recent mob kills, newest first")
    @AddArgument(
        "-c",
        "--count",
        help="the number of mobkills to list",
        type=int,
        default=DEFAULT_MOBKILL_COUNT,
    )
    def _command_mobkills(self) -> CommandResult:
        """List the most recent mob kills."""
        if self.statdb is None:
            return CommandResult(True, [NO_DB])
        args = self._args()
        return CommandResult(True, mobkill_list(self.statdb, args["count"], self._formatters()))
