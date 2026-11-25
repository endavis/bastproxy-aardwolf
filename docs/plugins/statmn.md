---
title: The statmn Plugin
description: Show a report of recent Aardwolf stats and a message when a quest, campaign, global quest or level ends
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - statmn
---

# The statmn Plugin

The `statmn` plugin does two things. It shows a table of what the character earned in the last
while: quests, campaigns, global quests and mob kills, with their count, experience, quest points,
trains and gold. It also writes a one-line message each time a quest, campaign, global quest, level
or powerup ends. It is ported from the `statmn` plugin of the old bastproxy and reads its numbers
from the [statdb plugin](statdb.md).

## Loading

The plugin id is `plugins.aardwolf.statmn`:

```text
#bp.core.pluginm.load plugins.aardwolf.statmn
```

It depends on the events, settings, triggers, timers, commands, utils and proxy core plugins and on
the [statdb plugin](statdb.md). It never imports another plugin: it keeps its own copies of the
event names and reads the database through the statdb API `plugins.aardwolf.statdb:stats.select`.
It checks that the API exists before each use, because statdb leaves it out when it cannot open its
database. It is not required, so it does not load until asked.

## Behaviour

- **The report.** A table of the last `reportminutes` of the quests (not failed), campaigns (not
  failed), global quests and mob kills. A kind with nothing in the window shows zeros. A last row
  adds up the experience, quest points, trains and gold. It is shown by the `rep` command and by a
  timer.
- **The timer.** A repeating timer shows the report every `show`; the default is 0, which is off. It starts at load when `show` is
  above 0, and starts again when `show` changes. A `show` of 0 turns it off and tells the client.
  While the MUD is not connected the timer shows nothing.
- **Completion messages.** A quest, campaign, global quest, level or powerup that ends queues a
  message. The messages are held until the next empty line from the MUD and then shown together, so
  they do not land in the middle of other output. A message queued while an empty line is being
  processed (a level or powerup is finished at an empty line) is shown at once with whatever is
  held, rather than waiting for the next one. A MUD disconnect shows what is held.
- **The quest message** lists the quest points and each bonus (lucky, mccp, tier, opk, hardcore,
  `E` daily, `D` double), the total, the trains, practices and trivia points, and how long it
  took. With more than one quest in the database it adds the average quest points and the number of
  quests that did not fail.
- **The level message** lists the gains of a level (hp, mn, mv, trains, practices) or a powerup,
  the bonus stats, and the time the level took. When mobs were killed for experience in that time
  it adds how many, their average experience and the experience per minute, from GMCP
  `char.base.perlevel`. The experience per minute shows only above the `exppermin` setting.
- **Trains.** The trains are shown as the trains of the level, then each `+E` (blessing),
  `+B` (bonus) and `+L` (battle learning) part, then the total when any part was added.
- **Priority.** The completion callbacks run at priority 60, after statdb saves the same event at
  priority 50, so the quest average always includes the quest that just ended.

Example report:

```text
--------------  Stats for 01h  -----------------
Type       |  Total     XP    QP    TP       Gold
--------------------------------------------------
Quests     |      1      0    12     0       2899
CPs        |      0      0     0     0          0
GQs        |      0      0     0     0          0
Mobs       |      4     72     0     0       1104
--------------------------------------------------
Total      |            72    12     0       4003
```

## Settings

| Setting | Default | Meaning |
| :--- | :--- | :--- |
| `statcolor` | `@W` | The colour of the numbers. |
| `infocolor` | `@x33` | The colour of the labels. |
| `show` | `0` | Show the report every this long; `0`, the default, turns it off. |
| `reportminutes` | `60m` | The length of time the report covers. |
| `exppermin` | `20` | The experience per minute that must be exceeded to show it on a level message. |
| `linelength` | `50` | The width of the report, 1 to 500; read each time, a value out of range is refused. |

```text
#bp.aardwolf.statmn.set show 10m
```

## Commands

| Command | Meaning |
| :--- | :--- |
| `rep [length]` | Show the report. `length` is a time length such as `30m` or `2h`; without it the `reportminutes` setting is used. |

```text
#bp.aardwolf.statmn.rep 30m
```

When the stats database is not available the command says so.

## Events

The plugin listens to `ev_plugins.aardwolf.quest_comp`, `cp_comp`, `gq_won`, `gq_completed`,
`gq_done` and `level_gain`, to `ev_libs.net.mud_muddisconnect`, and to its own
`ev_plugins.aardwolf.statmn_var_show_modified`. It registers on the core empty-line trigger
(`t_plugins.core.triggers_emptyline`) only while a message is held, and reads `plugins.core.events:event.stack.get` to tell when that
event is running, so it does not register on it then. It raises no events.

## Old to new

| Old | New |
| :--- | :--- |
| the old `statmn` plugin module | `src/aardwolf/statmn/` |
| `AUTOLOAD = False` | `PLUGIN_REQUIRED = False` |
| `statdb.select(sql)` | `plugins.aardwolf.statdb:stats.select(sql, params)`, with bound parameters |
| `plugins.isloaded('statdb')` | `libs.api:api.exists` for the select API |
| events `aard_quest_comp`, `aard_cp_comp`, `aard_level_gain`, `aard_gq_*` | the same events with the `ev_plugins.aardwolf.` prefix |
| event `var_statmn_show` | `ev_plugins.aardwolf.statmn_var_show_modified` |
| event `trigger_emptyline`, registered and unregistered as an event | the core empty-line trigger, through `trigger.register` and `trigger.unregister` |
| timer `statrep`, which ran `send.execute('#bp.statmn.rep')` | a timer named after the plugin that builds the report directly |
| `utils.timedeltatostring` | `timelength.format` and a local colour helper |
| `utils.center` | `string.center.colored` |
| `utils.verify(value, 'timelength')` | `value.verify` |
| `GMCP.getv('char.base.perlevel')` | `gmcp.value.get('char.base.perlevel')` |
| `send.client` | a direct send to the client |

## Changes from the old plugin

Each of these changes what the old plugin did. They are listed for review.

Bugs fixed:

1. The `show` timer was only added from the setting callback, so it never started at load. It
   starts at load only when `show` is above 0. A saved non-zero `show` therefore keeps its report after a restart. By default `show` is `0`, so
   no timed report runs, as the old plugin behaved in practice (its timer only started after `show`
   was changed).
2. `rep` ignored `reportminutes`: its argument defaulted to `60m`. The argument defaults to empty,
   which means the setting.
3. The level message counted mobs and experience between the `starttime` and `finishtime` of the
   level event. In the ported [level plugin](level.md) those are only the span of the gain lines.
   The window now runs from the start of the previous `levels` row to the start of this level, as
   the statdb `levels` report does. The time shown on the message is that window too. A level with
   no earlier level in the database shows no time and no mobs.
4. `battlelearntrains` was shown (`+L`) but not added to the total. It is added.
5. The experience per minute failed when GMCP `char.base.perlevel` was missing. It is skipped
   unless the value is positive.
6. The Quests row of the report counted failed quests. It counts only `failed = 0`, as the
   campaigns row always did.
7. The check for statdb asked only whether the plugin was loaded, so a statdb without a database
   failed later. The plugin checks that the API exists, and `rep` says the database is not
   available. A failing select is logged and shown the same way.
8. The quest average depended on whether statdb had already saved the quest that just ended. The
   callback runs at priority 60, after statdb at 50.
9. The SQL was built with `%` formatting. It uses bound `?` parameters.
10. `SUM(...)` of no rows is `NULL`, which broke the report. Each sum is wrapped in `COALESCE(..., 0)`.
11. NOEXP kills (`noexp = 1`) store the experience they would have given. The report's Mobs XP and
    the level message's mob count and average leave them out. The report's Mobs count, gold and
    TP still include them.

Behaviour changes that are not bug fixes:

- The timer builds the report directly instead of running the `rep` command through
  `send.execute`, and skips when the MUD is not connected.
- The `send.msg` dumps of the event data are dropped.
- The empty-line trigger is registered once for a batch of messages, not once per message.
- The time text is made by `timelength.format` plus a local helper that colours the numbers in
  `statcolor` and the rest in `infocolor`.
- A MUD disconnect shows the held messages, so none is lost.
- `rep` with a time length that cannot be read, or of less than a second, fails with a message.

## Known gaps

- The report and the messages need the statdb database; without it only the messages that need no
  query are shown.
- The `rep` output and the completion messages were not compared with the old plugin on a live
  character.
