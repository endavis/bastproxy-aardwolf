---
title: The statdb Plugin
description: Record Aardwolf character stats, quests, campaigns, global quests, levels and mob kills in a database, and report on them
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - database
---

# The statdb Plugin

The `statdb` plugin keeps a SQLite database of what a character does: stats and milestones,
quests, campaigns, global quests, levels and power-ups, and mob kills. Commands report on it. It
is a port of the old proxy's `statdb` plugin and keeps its schema, so a database written by the
old plugin is used as it is.

The plugin never imports another plugin. It listens to events that the other Aardwolf plugins
raise (whois, level, mobk, cp, gq and quest), so until those are loaded its tables get no new
rows. It loads and runs with none of them present.

## Loading

The plugin id is `plugins.aardwolf.statdb`:

```text
#bp.core.pluginm.load plugins.aardwolf.statdb
```

If the database cannot be opened, for example because it is older than the oldest version that
can be upgraded, the plugin logs the error and loads without a database. Its commands then say
"The stats database is not available" and its event callbacks do nothing.

## Behaviour

- **Whois.** The plugin does not queue a whois. The [whois plugin](whois.md) queues one each time
  the character is first active. The whois event it raises with the result fills the `stats` table.
- **Stats.** The `stats` table has a `current` row, kept up to date by the events, and a milestone
  row for each milestone: `start` (added with the first whois), a row named for each total level
  reached, and one named like `t2r3l10` for each hero, superhero, tier or remort level.
- **Deaths.** The trigger `^You die\.$` adds one to `timeskilled`.
- **Backups.** The `backupstart` setting is the time of day for the first backup and
  `backupinterval` the time between backups from then on. The backup is a zip in the `archive`
  directory next to the database, named `stats_<weekday>-<month>-<day>-<year>-<hour>-<minute>.sqlite.zip`.
  bastproxy's timer fires a time-of-day timer once a day and ignores its interval, so the plugin
  uses a one-time timer at `backupstart` whose callback backs up and then adds an interval timer.
  A change to either setting schedules both again. The time of day is **UTC**, because bastproxy's
  timers are; the old proxy used local time.

## Database

The database is `stats.sqlite` in the plugin's data directory,
`<BASTPROXY_HOME>/data/plugins/plugins.aardwolf.statdb/`. It is opened through bastproxy's
`plugins.core.sqldb:database.add` and its `user_version` is 17, the old plugin's final version.

A `BASTPROXY_HOME` holds one character. The `stats` rows carry the character's `name`, but the
other tables do not, so the plugin does not keep two characters apart. When a whois arrives for a
name other than the one in the `stats` row (compared without regard to case), the plugin logs a
warning and sends the same message to the client, then saves the whois as before. Use a separate
`BASTPROXY_HOME` for each character.

| Table | Holds | Filled by |
| :--- | :--- | :--- |
| `stats` | the current stats and one row per milestone | whois, and every event below |
| `quests` | one row per quest, completed or failed | quest events |
| `classes` | each class and the remort it was taken at, -1 when not taken | whois |
| `levels` | one row per level or power-up, with its gains; a row marks when the level or power-up was reached | level gain event |
| `campaigns`, `cpmobs` | one row per campaign and its mobs | cp events |
| `gquests`, `gqmobs` | one row per global quest and its mobs | gq events |
| `mobkills` | one row per mob kill | mob kill event |

The CREATE statements are the old version 17 text with the columns in the same order, because the
plugin inserts by position and a database from the old plugin must keep working. A test compares
them with a copy of the old text.

**Versions.** A file at version 17 opens with no change. A file at version 12 to 16 is rebuilt, one
table at a time, into the final layout, with its rows and ids kept, after a backup named
`stats_<version>` in the `archive` directory. The steps are ports of the old ones:

| Step | Table | Change |
| :--- | :--- | :--- |
| 13 | `mobkills` | adds `rarexp` |
| 14 | `mobkills` | adds `noexp` |
| 15 | `gquests` | adds `extended`, 1 for a completed global quest |
| 16 | `quests` | adds `tierqp` (from the old `tier`), `opk` and `hardcore` |
| 17 | `levels` | adds `battlelearntrains` |

A file older than version 12 is refused with an error naming its version: the old plugin could not
upgrade it either. A rebuild leaves a table that is already in its final layout alone, so the
steps can run again safely.

The `skills` and `recoveries` tables, which another old plugin wrote into the same file, are never
touched.

### Using a database from the old proxy

The core opens the old file as it is, so there is no converter. To use an old database:

1. Stop the proxy.
2. Copy the old plugin's `stats.sqlite` (with any `-wal` and `-shm` files beside it) into
   `<BASTPROXY_HOME>/data/plugins/plugins.aardwolf.statdb/`. To use one of the old backups,
   extract the `.sqlite` file from its `stats_*.sqlite.zip` and rename it `stats.sqlite`.
3. Start the proxy and load the plugin.

Keep the old file until the commands show the data you expect.

## Commands

The commands are `#bp.aardwolf.statdb.<command>`.

| Command | Description |
| :--- | :--- |
| `list` | List the milestones: the range of level milestones, then the named ones three to a line. |
| `comp [milestone1] [milestone2]` | Compare two milestones. With one name it compares that milestone to `current`; with none, `start` to `current`. |
| `quests [count] [-n number]` | Quest totals and averages, the last `count` quests, or the quest with the id `number`. |
| `levels [count] [-n number]` | Level and power-up totals, averages and times, the last `count` rows, or the row with the id `number`. "Time" is each row's gap to the next row's `starttime` in `level_id` order, rows of either type; the last row has none. |
| `cps [count] [-n number]` | Campaign totals and averages, the last `count` campaigns, or one campaign with its mobs. |
| `gqs [count] [-n number]` | Global quest totals and averages, the last `count`, or one global quest with its mobs. |
| `mobs [count]` | Mob kill totals and averages, and the last `count` kills. |
| `mobkills [-c count]` | List the last `count` kills (default 10), newest first, with time (UTC), name, level, total XP, gold, room and special-kill flags (B, V, A, S, D, I). An empty table says "No kills recorded". |

The `-n` option shows one row; a number that is not in the table reports "No such ..." instead of
failing. The `db*` commands that bastproxy's sqldb plugin adds work on this database too.

## Web pages

The plugin serves the same data as pages of the core web plugin (`plugins.core.web`, a dependency
of this plugin). A browser needs a login session first: run the web plugin's login command in the
client and open the link it prints. The web plugin enforces this and allows GET only, so the pages
change nothing. The routes are removed when this plugin unloads.

The pages are under `/aardwolf/statdb/`, and `/aardwolf/statdb/` itself lists them as text. `comp` is the one page the core `/` index leaves out,
because it needs a query; `/aardwolf/statdb/` still lists it.

| Route | Mirrors | Columns |
| :--- | :--- | :--- |
| `milestones` | `list` | milestone, date (UTC, `Now` for the current row), then each compared stat |
| `quests` | `quests` | id, qp, mc, tr, lk, pk, hc, dbl, tl, tp, tn, pr, gold, lvl, mins, result, mob, room, area |
| `levels` | `levels` | id, lvl, type (L or P), tr, bt, pr, hp, mn, mv, s, i, w, c, d, l, mins |
| `cps` | `cps` | id, lvl (`T R L`), qp, bn, tp, tn, pr, gold, mobs, mins, result |
| `cpmobs` | `cps -n` | cp_id, name, location |
| `gqs` | `gqs` | id, lvl (`T R L`), qp, qm, tp, tn, pr, gold, mobs, mins, won |
| `gqmobs` | `gqs -n` | gq_id, num, name, location |
| `mobs` | `mobs` | lvl, mob, txp, xp, rxp, oxp, tp, s, gold |
| `mobkills` | `mobkills` | time (UTC), name, lvl, txp, gold, room, flags |
| `comp?first=&second=` | `comp` | the comparison text; both names are required (400), an unknown one is 404 |
| `chart/qp-per-day` | | quest points per day, the newest 30 days |
| `chart/gold-per-day` | | gold per day, the newest 30 days |
| `chart/level-time` | | minutes per level, the last 50 timed levels |
| `chart/area-kills` | | kills per area, the top 20 |

**Tables.** `quests`, `levels`, `cps`, `gqs` and `mobs` show the summary of their text command above
the table. Without a sort a table lists the newest row first, so page 1 with `count=N` is the rows
of `<command> N`. The table parameters are the web plugin's: `sort`, `dir`, `page`, `count` and one
`f_<column>` filter per column. An unknown column, a bad `dir`, `page` or `count`, an unparsable
number or a text filter over 200 characters is answered with 400 before this plugin runs. A text
filter is a case-insensitive part of the value (`%` and `_` match themselves); a number filter is
exact.

**Durations and dates.** "Mins" is a float number of minutes (empty when a time is unknown), where
the text commands show a formatted length. Dates are UTC. `result` is `Done` or `Failed`; the
`levels` gap is the same one the `levels` command shows.

**Links and detail views.** Some cells are links, each a path on this site:

- `quests` and `levels` `id` link to `?f_id=<id>` on the same page.
- `cps` `id` links to `cpmobs?f_cp_id=<id>` and `gqs` `id` to `gqmobs?f_gq_id=<id>`.
- `mobkills` `room` links to the core mapper's `/client/mapper/room?uid=<room>`. The cell is plain
  and empty when no room is set.

A link cell keeps its column's name and type, so sorting, filtering and paging work as before. A
page the web plugin refused to add has no link to it, and the cell stays a plain value. The `-n`
detail views are filters: `quests?f_id=3`, `levels?f_id=3`, `cpmobs?f_cp_id=3` and
`gqmobs?f_gq_id=3`. The per-level kill summary of `levels -n` has no web page.

**The comparison.** `comp` needs `first` and `second`. A missing or empty name is answered with 400.
A name that does not exist is answered with 404 and the text "milestone X does not exist", the same
text as the command. Two names that exist give the comparison.

**Charts.** Each chart is an SVG bar chart with every label escaped; it holds no script and no
link. With no rows it says "No data". `chart/area-kills` has to map each room to an area: it asks
the core mapper (`plugins.client.mapper:room.get` and `area.get`) on the event loop, a room the
mapper does not know counts under "Unknown", and with no mapper loaded every kill does.

**Queries.** Every page reads in a worker thread on its own read-only connection, so it never blocks
the proxy and cannot write. The SQL is a fixed fragment per column; a request value is only ever
a bound parameter. A page says "The stats database is not available" when the database did not
open, and "The stats database could not be read" when a read fails (the error is logged).

## Settings

| Setting | Default | Description |
| :--- | :--- | :--- |
| `backupstart` | `0000` | The time of day (HHMM, UTC) of the first backup each day. |
| `backupinterval` | `4h` | The time between backups after the first. |

## Events consumed

The plugin listens to these events. Each event name starts with `ev_plugins.aardwolf.`, and the
payload keys are those the old plugins put in their `aard_*` events. If a source plugin's port
names an event or a key differently, statdb is changed to match. The store never changes the
payload it is given, and a column that is not in the payload takes its SQL default.

| Event | Payload keys | Store method |
| :--- | :--- | :--- |
| `whois_received` | `name`, `level`, `totallevels`, `tiers`, `redos`, `remorts`, `race`, `sex`, `subclass`, `powerupsall`, `classes` (a list of `class` and `remort`), and `stats`, a dict of the stat lines, each key a `stats` column | `save_whois` |
| `quest_comp`, `quest_failed` | `starttime`, `finishtime`, `mobname`, `mobarea`, `mobroom`, `qp`, `double`, `daily`, `totqp`, `gold`, `tierqp`, `mccp`, `lucky`, `opk`, `hardcore`, `tp`, `trains`, `pracs`, `level`, `failed` | `save_quest` |
| `cp_comp`, `cp_failed` | `starttime`, `finishtime`, `qp`, `bonusqp`, `gold`, `tp`, `trains`, `pracs`, `level`, `failed`, `mobs` (a list of `name` and `location`) | `save_cp` |
| `gq_done`, `gq_completed`, `gq_won` | `starttime`, `finishtime`, `qp`, `qpmobs`, `gold`, `tp`, `trains`, `pracs`, `level`, `extended`, `won`, `completed`, `mobs` (a list of `num`, `name` and `location`) | `save_gq` |
| `level_gain` | `type` (`level` or `pup`), `level`, `totallevels`, `starttime`, `str`, `int`, `wis`, `dex`, `con`, `luc`, `hp`, `mp`, `mv`, `pracs`, `trains`, `bonustrains`, `blessingtrains`, `battlelearntrains` | `save_level` |
| `level_hero`, `level_superhero`, `level_tier` | none; the total level comes from GMCP | `hero_milestone` and `add_milestone` |
| `level_remort` | none; `char.base.remorts`, `char.base.tier` and the total level come from GMCP | `apply_remort`, then a milestone |
| `mobk_kill` | `name`, `xp`, `rarexp`, `bonusxp`, `blessingxp`, `totalxp`, `noexp`, `gold`, `tp`, `time`, `vorpal`, `banishment`, `assassinate`, `slit`, `disintegrate`, `deathblow`, `wielded_weapon`, `second_weapon`, `room_id`, `level` | `save_mobkill` |

A global quest event counts a win in `gquestswon` only when `won` is 1. A level event with
`totallevels` above zero sets `totallevels` and `level` in the stats, and adds one to each
otherwise; a `pup` adds one to `powerupsall`; a `level` also adds a milestone named for the total
level. `save_level` writes `finishtime` -1 and never changes an earlier row; the column stays for old databases.

It also listens to the two setting events
`ev_plugins.aardwolf.statdb_var_backupstart_modified` and
`ev_plugins.aardwolf.statdb_var_backupinterval_modified`.

## APIs

The plugin adds none of its own. `database.add` registers these under the plugin:

| API | Description |
| :--- | :--- |
| `plugins.aardwolf.statdb:stats.select(sql, params)` | Run a select against the database. |
| `plugins.aardwolf.statdb:stats.modify(sql, data)` | Run one modifying statement. |
| `plugins.aardwolf.statdb:stats.modify.many(sql, data)` | Run a modifying statement for each item of `data`. |
| `plugins.aardwolf.statdb:stats.row.get(row_id, table)` | Get one row of a table by its key. |

Known gap: the `dbremove` command removes one row and does not remove the `cpmobs` or `gqmobs` rows
of a removed campaign or global quest. The old plugin did. The schema has no cascade and the
plugin adds no SQL triggers, because the file must stay as the old plugin wrote it.

## From the old plugin

| Old | New |
| :--- | :--- |
| `sqldb.baseclass` and the `Statdb` subclass | `plugins.core.sqldb:database.add` with plain table and migration data |
| `stats.select`, `stats.modify`, `stats.modifymany`, `stats.getrow` | `plugins.aardwolf.statdb:stats.select`, `.modify`, `.modify.many`, `.row.get` |
| events `aard_quest_comp`, `aard_quest_failed`, `aard_cp_comp`, `aard_cp_failed`, `aard_whois`, `aard_level_*`, `aard_mobkill`, `aard_gq_*` | the events in the table above, with the `ev_plugins.aardwolf.` prefix |
| event `GMCP:char.status`, unregistered after the first active state | the whois plugin queues the whois on `ev_libs.api_character_active`; statdb does not |
| `send.execute('whois')` | the [whois plugin](whois.md) queues it with `plugins.core.mudcmds:command.queue`; statdb does not |
| event `trigger_dead` | a trigger on `^You die\.$` |
| timer `stats_backup` at local time | UTC, with a one-time timer that adds the interval timer |
| plugin version 2, which moved the files from the old `data/db` layout | dropped; copy the file as above |
| `send.msg` logging of every save | dropped |

Bugs fixed in the port:

- **Whois classes never matched.** The old table held full class names and whois sent
  abbreviations, so no row was updated. The table keeps full names and abbreviations are converted,
  so both forms work.
- **Remort wrote a column that does not exist.** The old handler set `tier`; the column is `tiers`.
- **Dead stat names.** The old code added to `questpoints` and `triviapoints`, which are not
  columns, and did nothing. Those calls are dropped; nothing changes.
- **Time checks never fired.** The old code compared a finish time to the text `'-1'`, so the check
  was always true. It compares to the number -1.
- **Crashes on missing rows.** `-n` with an unknown number, a campaign or global quest with no
  mobs, and a table with only failed rows no longer fail.
- **A level event without a total level** named its milestone `None`; it is named for the total
  level now.
- **SQL injection.** The old code pasted values into its SQL. Every value is a bound parameter,
  and a stat name is checked against the `stats` columns first.
- **NOEXP kills counted as experience.** Kills with `noexp = 1` store the experience they would
  have given. They are left out of the level report's xp/mob and mob count, the `mobs` XP totals
  and averages, and the Bonus and Blessing Mobs counts. They show no D/E in the `mobs` list or on
  the `mobs` web page. Rare Mobs and the Overall count still include them.
