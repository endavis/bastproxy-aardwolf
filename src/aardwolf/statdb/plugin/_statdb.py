"""The Aardwolf statdb plugin: a stats database filled from the Aardwolf events."""

import asyncio
import copy
import logging
import sqlite3
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from bastproxy.libs.logger import log_to
from bastproxy.libs.records import NetworkData, NetworkDataLine, SendDataDirectlyToClient
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.commands import AddArgument, AddCommand, AddParser, CommandResult
from bastproxy.plugins.core.events import RegisterToEvent

from aardwolf._libs.aardu import actual_level_from_gmcp
from aardwolf._libs.validate import int_validator, time_format_error

from ..libs import (
    AREA_CHART_TITLE,
    CHART_AREAS,
    CHART_DAYS,
    CHART_LEVELS,
    CHARTS,
    DB_NAME,
    DB_VERSION,
    DEFAULT_MOBKILL_COUNT,
    MAPPER_ROOM_PATH,
    MIGRATIONS,
    SETTING_CHART_AREAS,
    SETTING_CHART_DAYS,
    SETTING_CHART_LEVELS,
    SETTING_MOBKILL_COUNT,
    SETTING_TIME_FORMAT,
    TABLE_PAGES,
    TABLES,
    TIME_FORMAT,
    Formatters,
    StatStore,
    TablePage,
    WebRequest,
    aggregate_areas,
    bar_chart_svg,
    compare_milestones,
    comparison_lines,
    cp_report,
    gq_report,
    level_report,
    link_rows,
    list_milestones,
    mob_report,
    mobkill_list,
    page_lines,
    quest_report,
    read_chart,
    read_milestone_rows,
    read_room_kills,
    read_table,
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
DB_UNREADABLE = "The stats database could not be read"
MAPPER = "plugins.client.mapper"
MAX_MILESTONE_NAME = 200
LOOKUPS_PER_YIELD = 50


class StatdbPlugin(BasePlugin):
    """Record Aardwolf stats, quests, campaigns, global quests, levels and mob kills."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Initialize the instance."""
        self.statdb: StatStore | None = None
        self._web_pages: list[tuple[str, str]] = []
        self._web_paths: dict[str, str] = {}

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
        add_setting(
            self.plugin_id,
            SETTING_MOBKILL_COUNT,
            DEFAULT_MOBKILL_COUNT,
            int,
            "the number of kills the mobkills command lists when it is given no count",
            validator=int_validator(1, 1000),
        )
        for name, default, text, maximum in (
            (SETTING_CHART_DAYS, CHART_DAYS, "the number of days the day charts show", 3650),
            (
                SETTING_CHART_LEVELS,
                CHART_LEVELS,
                "the number of levels the level chart shows",
                1000,
            ),
            (SETTING_CHART_AREAS, CHART_AREAS, "the number of areas the area chart shows", 500),
        ):
            add_setting(
                self.plugin_id,
                name,
                default,
                int,
                text,
                validator=int_validator(1, maximum),
            )
        add_setting(
            self.plugin_id,
            SETTING_TIME_FORMAT,
            TIME_FORMAT,
            str,
            "the strftime pattern of the dates the reports show",
            nocolor=True,
            validator=time_format_error,
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
        self._add_web_routes()

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
            time_format=str(self._setting(SETTING_TIME_FORMAT)),
        )

    def _chart_limit(self, setting: str) -> int:
        """Return the number of bars a chart setting asks for."""
        return int(str(self._setting(setting)))

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
        help="the number of mobkills to list, default the mobkillcount setting",
        type=int,
        default=None,
    )
    def _command_mobkills(self) -> CommandResult:
        """List the most recent mob kills."""
        if self.statdb is None:
            return CommandResult(True, [NO_DB])
        count = self._args()["count"]
        if count is None:
            count = int(str(self._setting(SETTING_MOBKILL_COUNT)))
        return CommandResult(True, mobkill_list(self.statdb, count, self._formatters()))

    # web pages

    def _db_path(self) -> Path | None:
        """Return the path of the database file, or None when the database is not open."""
        if self.statdb is None:
            return None
        path = getattr(self.statdb.db, "db_file", None)
        return path if isinstance(path, Path) else None

    def _add_web_routes(self) -> None:
        """Serve the tables, the milestone comparison and the charts under the plugin's path."""
        add = self.api("plugins.core.web:web.route.add")
        self._web_pages = []
        self._web_paths = {"mapper-room": MAPPER_ROOM_PATH}

        def register(
            subpath: str,
            handler: Callable[[WebRequest], Any],
            title: str,
            columns: list[dict[str, str]] | None = None,
            *,
            listed: bool = True,
        ) -> None:
            path = add(self.plugin_id, subpath, handler, title, columns, listed=listed)
            if path:
                self._web_pages.append((path, title))
                self._web_paths[subpath] = path

        add(self.plugin_id, "", self._web_index, "Stats pages", None)
        for page in TABLE_PAGES.values():
            register(page.route, self._table_handler(page), page.title, page.route_columns())
        register(
            "comp",
            self._web_comp,
            "Compare two milestones (?first=&second=)",
            listed=False,
        )
        for name, spec in CHARTS.items():
            register(f"chart/{name}", self._chart_handler(name), spec.title)
        register("chart/area-kills", self._web_area_chart, AREA_CHART_TITLE)

    @staticmethod
    def _message_page(title: str, message: str) -> dict[str, Any]:
        """Return a page that only says a message."""
        return {"kind": "html", "title": title, "lines": [message]}

    def _unreadable(self, title: str) -> dict[str, Any]:
        """Log a database failure and return the page that says so."""
        log_to(self.plugin_id, logging.ERROR, "could not read the stats database", exc_info=True)
        return self._message_page(title, DB_UNREADABLE)

    def _web_index(self, request: WebRequest) -> dict[str, Any]:
        """List the pages as plain text."""
        lines = [f"{title}: {path}" for path, title in self._web_pages]
        return {"kind": "html", "title": "Stats pages", "lines": lines}

    def _table_handler(self, page: TablePage) -> Callable[[WebRequest], Awaitable[dict[str, Any]]]:
        """Return the handler of a table page."""

        async def handler(request: WebRequest) -> dict[str, Any]:
            return await self._table_page(page, request)

        return handler

    async def _table_page(self, page: TablePage, request: WebRequest) -> dict[str, Any]:
        """Read one page of a table in a thread and return it for the web plugin."""
        table = request.table
        if table is None:
            msg = f"the route {page.route} has no table query"
            raise ValueError(msg)
        path = self._db_path()
        if path is None:
            return self._message_page(page.title, NO_DB)
        try:
            result = await asyncio.to_thread(read_table, path, page, table)
        except sqlite3.Error:
            return self._unreadable(page.title)
        if result.message:
            return self._message_page(page.title, result.message)
        return {
            "kind": "table",
            "title": page.title,
            "rows": link_rows(page, result.rows or [], self._web_paths),
            "total": result.total,
            "lines": page_lines(page, result, self._formatters()),
        }

    async def _web_comp(self, request: WebRequest) -> dict[str, Any]:
        """Compare two milestones; a name that does not exist is said so."""
        title = "Compare milestones"
        names = (
            request.query.get("first", "")[:MAX_MILESTONE_NAME],
            request.query.get("second", "")[:MAX_MILESTONE_NAME],
        )
        if not all(names):
            return {
                "kind": "error",
                "status": 400,
                "message": "first and second milestone names are required",
            }
        path = self._db_path()
        if path is None:
            return self._message_page(title, NO_DB)
        try:
            rows = await asyncio.to_thread(read_milestone_rows, path, names)
        except sqlite3.Error:
            return self._unreadable(title)
        if any(not row for row in rows):
            return {
                "kind": "error",
                "status": 404,
                "message": "; ".join(comparison_lines(names, rows, self._formatters())),
            }
        return {
            "kind": "html",
            "title": title,
            "lines": comparison_lines(names, rows, self._formatters()),
        }

    def _chart_handler(self, name: str) -> Callable[[WebRequest], Awaitable[dict[str, Any]]]:
        """Return the handler of a chart that one query gives the bars of."""

        async def handler(request: WebRequest) -> dict[str, Any]:
            spec = CHARTS[name]
            path = self._db_path()
            if path is None:
                return {"kind": "svg", "svg": bar_chart_svg(NO_DB, [], "")}
            limit = self._chart_limit(spec.setting)
            try:
                bars = await asyncio.to_thread(read_chart, path, name, limit)
            except sqlite3.Error:
                log_to(self.plugin_id, logging.ERROR, "could not read the chart", exc_info=True)
                return {"kind": "svg", "svg": bar_chart_svg(DB_UNREADABLE, [], "")}
            return {"kind": "svg", "svg": bar_chart_svg(spec.heading(limit), bars, spec.unit)}

        return handler

    async def _room_areas(self, rooms: list[int]) -> dict[int, str]:
        """Map rooms to area names with the mapper; empty when the mapper is not loaded.

        The lookups are API calls, so they run on the event loop, yielding every
        ``LOOKUPS_PER_YIELD`` rooms.
        """
        exists = self.api("libs.api:api.exists")
        if not (exists(f"{MAPPER}:room.get") and exists(f"{MAPPER}:area.get")):
            return {}
        room_get = self.api(f"{MAPPER}:room.get")
        area_get = self.api(f"{MAPPER}:area.get")
        area_names: dict[str, str] = {}
        areas: dict[int, str] = {}
        for number, room in enumerate(rooms):
            if number and number % LOOKUPS_PER_YIELD == 0:
                await asyncio.sleep(0)
            info = room_get(str(room)) if room > 0 else None
            uid = str(info.get("area") or "") if isinstance(info, dict) else ""
            if not uid:
                continue
            if uid not in area_names:
                area = area_get(uid)
                name = area.get("name") if isinstance(area, dict) else None
                area_names[uid] = str(name) if name else uid
            areas[room] = area_names[uid]
        return areas

    async def _web_area_chart(self, request: WebRequest) -> dict[str, Any]:
        """Chart the kills of each area, with the rooms mapped to areas by the mapper."""
        path = self._db_path()
        if path is None:
            return {"kind": "svg", "svg": bar_chart_svg(NO_DB, [], "")}
        try:
            counts = await asyncio.to_thread(read_room_kills, path)
        except sqlite3.Error:
            log_to(self.plugin_id, logging.ERROR, "could not read the chart", exc_info=True)
            return {"kind": "svg", "svg": bar_chart_svg(DB_UNREADABLE, [], "")}
        areas = await self._room_areas(list(counts))
        limit = self._chart_limit(SETTING_CHART_AREAS)
        return {
            "kind": "svg",
            "svg": bar_chart_svg(
                f"{AREA_CHART_TITLE} (top {limit})",
                aggregate_areas(counts, areas, limit),
                "kills",
            ),
        }
