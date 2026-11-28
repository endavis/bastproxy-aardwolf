---
title: The gq Plugin
description: Follow the global quests of an Aardwolf character and raise their declaration, mobs left and end as events
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - gq
---

# The gq Plugin

The `gq` plugin follows the global quests of the character from the MUD output. It keeps the state of
the gquest on disk, raises the mobs left whenever they are known or change, and raises one event when
the character wins, finishes in extended time or leaves the gquest. The [statdb plugin](statdb.md)
records the gquests from these events.

## Loading

The plugin id is `plugins.aardwolf.gq`:

```text
#bp.core.pluginm.load plugins.aardwolf.gq
```

It depends on the events, triggers, mudcmds, watch, settings and web core plugins and on the
[connect plugin](connect.md). The [mobk plugin](mobk.md) is optional: without it the mobs left are only
refreshed by a new `gq check`.

## Behaviour

- **Triggers.** Their names carry a `gq_` prefix because trigger names are global. Eight are always on:
  `gq_declared`, `gq_joined`, `gq_started`, `gq_cancelled`, `gq_quit`, `gq_note`, `gq_maxkills` and
  `gq_wonannounce`.
  The others sit in three groups, named `<plugin id>.<suffix>`: `gqcheck` (`gq_none`, `gq_item`,
  `gq_notstarted` and `gq_wins`, the output of `gq check`), `gqin` (`gq_mobdead`, `gq_extended`,
  `gq_won` and `gq_extfin`, while in a gquest) and `gqrew` (`gq_reward`). No trigger
  omits its line, so a check the client types is shown.
- **Checking.** A `gq check` the client types is seen by the `gq_check` watch, which clears the mobs
  left and turns `gqcheck` on. The plugin's own checks go through a `gqcheck` command type in the
  mudcmds queue, which does the same before it sends `gq check`. The watch cannot see them, because
  they bypass the client input. A check is queued when a gquest the character joined starts, when a
  kill cannot be matched to a mob, on the first active event while joined, and when the plugin loads
  with an active character and a joined gquest.
- **Mobs.** Each `gq_item` line adds a mob with `name`, `nocolorname`, `location` and `num`. The mobs
  left are saved in `gqmobsleft.txt`. The first check of a gquest copies them to `mobs` in `gq.txt`, and
  every check raises `gq_mobsleft`.
- **Kills.** `gq_mobdead` adds 3 to `qpmobs`, unless the maxkills line was seen, and sets a flag. The
  next `mobk_kill` event, when the flag is set, counts down the first mob with that name: a mob with
  more than one kill left loses one, the last kill removes it. `gq_mobsleft` is raised. A name that is
  not in the list queues a check instead. When the name is at more than one location, a `gq check`
  is queued after `gq_mobsleft`, so the server's list corrects the guess.
- **Ending.** `gq_won` turns on the rewards group, and each `gq_reward` line sets `qp`, `trains`,
  `gold`, `tp` or `pracs`. A reward of an unknown type is logged at debug level and ignored. The
  announcement of a win by the character raises `gq_won` and leaves the gquest, whether or not a gquest
  is joined. It sets `won` (and `finishtime` when unset) first, so the win counts even when the
  `You were the first to complete this quest!` line was missed. Finishing in extended
  time after kills raises `gq_completed`. A quit, a cancel or the forum note of the joined gquest
  raises `gq_done` when mobs were killed. Each of them then leaves the gquest.
- **Leaving.** `joined` goes back to -1, `maxkills` to false, the state is cleared and every group is
  turned off. The gquest is taken off the declared ones, and `gq_available` or `gq_notavailable` is
  raised. `You are not in a global quest.` while joined leaves the gquest too, without events, so
  `joined` does not stay stale.
- **State.** `gq.txt` holds the keys of the payload and `gqmobsleft.txt` the mobs left. Both survive a
  reload and a restart. The settings `joined` and `maxkills` are kept by the settings plugin. The
  declared and started gquest numbers are kept in memory: they are state of the MUD and would be stale
  after a restart.
- **Disconnect.** All the groups are turned off and the kill flag is cleared.
- **Level.** The `level` of the state is the total level from
  `aardwolf._libs.aardu.actual_level_from_gmcp`, read when the gquest is joined.

## Events

| Event | When | Payload keys |
| :--- | :--- | :--- |
| `ev_plugins.aardwolf.gq_declared` | a gquest is declared | `gqnum`, `lowlev`, `highlev` |
| `ev_plugins.aardwolf.gq_joined` | the character joins a gquest | `gqnum` |
| `ev_plugins.aardwolf.gq_started` | a gquest starts | `gqnum` |
| `ev_plugins.aardwolf.gq_cancelled` | a gquest is cancelled | `gqnum` |
| `ev_plugins.aardwolf.gq_mobsleft` | after `gq check`, and when a target mob is killed | `mobsleft` |
| `ev_plugins.aardwolf.gq_won` | the character won | `mobs`, `trains`, `pracs`, `gold`, `tp`, `qp`, `qpmobs`, `level`, `starttime`, `finishtime`, `length`, `won`, `completed`, `extended` |
| `ev_plugins.aardwolf.gq_completed` | the character finished in extended time | the same keys as `gq_won` |
| `ev_plugins.aardwolf.gq_done` | the gquest ended otherwise, with gquest mobs killed | the same keys as `gq_won` |
| `ev_plugins.aardwolf.gq_available` | a gquest is declared | none |
| `ev_plugins.aardwolf.gq_notavailable` | no gquest is declared any more | none |

Each payload is a deep copy; changing it does not change the state. statdb stores the columns of its
`gquests` table and the mobs, and ignores the keys it has no column for.

## Web data providers

The plugin registers two data providers with the core web plugin (`plugins.core.web:web.provider.add`), so
the web client can show them. The web plugin removes them when this plugin unloads, and
`#bp.core.web.status` lists them. Every change raises `web.provider.changed.raise` for the
provider, so a page updates without polling.

| Topic | Page path | Kind |
| :--- | :--- | :--- |
| `aardwolf.gq.mobsleft` | `/data/aardwolf/gq/mobsleft` | table |
| `aardwolf.gq.summary` | `/data/aardwolf/gq/summary` | json |

`mobsleft` has one row for each target mob and these columns:

| Column | Label | Type |
| :--- | :--- | :--- |
| `name` | Mob | text |
| `location` | Location | text |
| `count` | Left | int (the kills left of this mob) |

The table is empty when no global quest is joined. Every label is a whole word, so the columns have no separate full name.

`summary` is json with `joined`, `gqnum`, `level` (the total level when it was joined),
`starttime`, `extended` (true in extended time) and `mobsleft` (the sum of the kills left). The
plugin does not know when a global quest ends, so the summary has no end time and no time left.
When no global quest is joined `joined` and `extended` are false, the count is 0 and the other
fields are null.

## Changes from the old plugin

- **Kill listener.** The old plugin registered `_mobkillevent` again instead of unregistering it, so
  it handled every later kill. The plugin registers once for `mobk_kill` and uses a flag.
- **First mob.** The old plugin tested the index of the mob to remove for truth, so the mob at index 0
  was never removed. `count_down` tests it with `is not None` semantics.
- **One mob per kill.** The old loop counted down every mob with the killed name. Only the first is
  counted down now. The kill carries only the name, so with the name at several locations the
  first is a guess and a check is queued; cp does the same.
- **Win announcement.** The old trigger was in the `gqin` group, which is off while `joined` is -1,
  and the new one checked the gquest number against `joined`. The trigger is always on now and the
  plugin raises `gq_won` whenever the winner is the character, logging a number mismatch at debug
  level. The winner and the ordinal tail follow the old loose regex; the number is digits only,
  because the `int` argument type needs them.
- **`joined` reset.** The old plugin set the integer setting to the string `'default'`. It is -1 now.
- **Mobs left type.** The old plugin set it to a dict in one place and a list in another. It is a list.
- **Level.** The old plugin passed only `char.status.level` to its level helper. The level is now
  `actual_level_from_gmcp`, which also reads the remorts, the tier and the redos.
- **Checking.** The old plugin sent `gq check` through `send.execute`. The plugin's own checks go
  through the mudcmds queue, because the watch does not see them.
- **Not in a gquest.** It leaves the gquest quietly when `joined` was set.
- **Unknown reward type.** It is ignored instead of raising `KeyError`.
- **Echoes.** The `send.msg` echoes are gone; the plugin logs at debug level.
- **Events.** `aard_gq_*` events are now `ev_plugins.aardwolf.gq_*`. `gq_declared` is raised before
  `gq_available`, not after.
