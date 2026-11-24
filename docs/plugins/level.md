---
title: The level Plugin
description: Detect levels, powerups, hero, superhero, remort and tier on Aardwolf and raise them as events
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - level
---

# The level Plugin

The `level` plugin reads the output of Aardwolf for levels, powerups, superhero, remort and tier,
collects the gains in a saved record and raises an event with a copy when the level is finished.
The [statdb plugin](statdb.md) listens to `level_gain` and records the levels.

## Loading

The plugin id is `plugins.aardwolf.level`:

```text
#bp.core.pluginm.load plugins.aardwolf.level
```

It depends on the events, triggers, watch and settings core plugins and on the
[connect plugin](connect.md), which asks the MUD for the GMCP `char` module. Loading the plugin
loads `connect` too.

## Behaviour

- **Always-on triggers.** `lvlpup` and `lvlpupbless` (a powerup), `lvllevel` and `lvlbless` (a
  level) each start a record. `lvlshloud` sets the trains of a level 201 record being collected.
  `lvlsh` matches the superhero line and has no callback.
- **The `linfo` group.** `lvlgains`, `lvlpupgains`, `lvlblesstrain`, `lvlbonustrains`,
  `lvlbattlelearntrains` and `lvlbonusstat` are off until a record starts. They add the gains to
  the record: hit points, mana, moves, practices, trains, blessing trains, bonus trains,
  battle-learn trains and a bonus stat (`str`, `int`, `wis`, `dex`, `con` or `luc`, set to 1).
- **The `superhero` group.** `lvlshbadstar`, `lvlshbad`, `lvlshnogold`, `lvlshnoqp`, `lvlshnodbl`
  and `lvlshnot200` are off until a superhero command is typed. Any of them means the superhero
  failed: both groups go off, the empty-line callback is unregistered and nothing is raised.
- **The `remort` group.** `lvlpreremort`, `lvlremortcomp` and `lvltier` are always on.
- **Group names.** Trigger group names are global, so the groups are named
  `plugins.aardwolf.level.linfo`, `.superhero` and `.remort`.
- **Watches.** `superhero`, `superhero silent`, `superhero loud`, `superhero confirm` and
  `superhero loud confirm` start a level 201 record and turn the `superhero` group on. The watch
  names are `level_sh`, `level_shsilent`, `level_shloud`, `level_shconfirm` and
  `level_shloudconfirm`, because watch names are global. A bare `superhero` that fails is undone
  by the failure triggers.
- **Starting a record.** A record has the type (`level` or `pup`), the level, the total level from
  `aardwolf._libs.aardu.actual_level_from_gmcp`, the six stats at 0, every gain at 0, `starttime`
  and `finishtime` -1. A powerup takes its level from `char.status.level`. The plugin turns the
  `linfo` group on and registers `_finish` on the core empty-line trigger
  (`t_plugins.core.triggers_emptyline`).
- **Start time.** `starttime` is the time the level or powerup was reached: the current time when
  the record starts. For a level it is the "You raise a level" or "You gain a level" line, for a
  powerup the powerup line, for a superhero the time the superhero command was typed, for a
  remort the `* Remort transformation complete!` line, and for a tier the GMCP `char.base` frame
  after state 2 and then 3. A failed superhero never saves its record, so the next record takes
  its own time. The time spent at a level is the gap to the next record, which statdb works out.
- **Finish.** On an empty line the level finishes when trains were gained, or a remort is
  complete, or a tier is in progress. Otherwise the empty line is ignored and the plugin keeps
  waiting for the gains. A finish sets `finishtime`, which is when the gain lines ended and not the end of the level, saves the record, turns the `linfo` and
  `superhero` groups off, unregisters from the empty line and raises `level_gain`. Then it raises
  one more event: `level_hero` for a level of type `level` at 200, `level_superhero` at 201, and
  at level 1 `level_tier` when tiering, else `level_remort`. A powerup raises none of these.
- **Remort.** `lvlpreremort` sets `preremort` and raises `level_preremort`. `lvlremortcomp` clears
  `preremort`, sets `remortcomp` and starts a level 1 record, which finishes at the next empty
  line and clears `remortcomp`.
- **Tier.** `lvltier` sets `tiering` and registers a callback on `ev_libs.net.mud_gmcp_char.status`.
  On state 2 the callback sets `seen2`, unregisters itself and registers a callback on
  `ev_libs.net.mud_gmcp_char.base`. On the first base message with state 3 that callback
  unregisters itself and starts a level 1 record. The next empty line finishes it, raises
  `level_tier` and clears `tiering` and `seen2`. If bastproxy restarts in the middle of a tier,
  the matching callback is registered again when the plugin loads.
- **Settings.** `preremort`, `remortcomp`, `tiering` and `seen2`, all booleans that default to
  false. They hold state; they are not meant to be changed by hand.
- **Disconnect.** A MUD disconnect turns the `linfo` and `superhero` groups off and unregisters
  from the empty line, so a level cut off by a disconnect does not leave them on.
- **Persistence.** The record is a `PersistentDict` in `level.txt` in the plugin's data
  directory. It is synced at the finish and by the `save` hook, which runs on unload and reload.

## Events

| Event | When | Payload keys |
| :--- | :--- | :--- |
| `ev_plugins.aardwolf.level_gain` | a level or powerup finished | `type`, `level`, `totallevels`, `starttime`, `finishtime`, `str`, `int`, `wis`, `dex`, `con`, `luc`, `hp`, `mp`, `mv`, `pracs`, `trains`, `bonustrains`, `blessingtrains`, `battlelearntrains` |
| `ev_plugins.aardwolf.level_hero` | after `level_gain`, level 200 reached by levelling | none |
| `ev_plugins.aardwolf.level_superhero` | after `level_gain`, level 201 reached | none |
| `ev_plugins.aardwolf.level_remort` | after `level_gain`, a remort is complete | none |
| `ev_plugins.aardwolf.level_tier` | after `level_gain`, a tier is complete | none |
| `ev_plugins.aardwolf.level_preremort` | the character is flagged as remorting | none |

The `level_gain` payload is a plain dict copy of the record; changing it does not change the saved
record.

## From the old plugin

| Old | New |
| :--- | :--- |
| events `aard_level_*` | `ev_plugins.aardwolf.level_*` |
| `GMCP:char.status` and `GMCP:char.base` | `ev_libs.net.mud_gmcp_char.status` and `.base` |
| `aardu.getactuallevel` and `GMCP.getv` | `aardwolf._libs.aardu.actual_level_from_gmcp` and `libs.net.protocols:gmcp.value.get` |
| `triggers.togglegroup` | `plugins.core.triggers:group.toggle.enable` |
| `setting.change` and `setting.gets` | `plugins.core.settings:setting.set` and `setting.get` |
| `trigger_emptyline` event | `plugins.core.triggers:trigger.register` on the empty-line trigger id |
| `send.client` and `send.msg` | debug log lines |
| `plugin_level_savestate` | the `save` plugin hook |

Fixes in the port:

- **`lvlshloud` regex.** The trains group was empty, so it never captured a number. It is now
  `\d+`, and the trigger has a callback that sets the trains of a level 201 record.
- **`lvlgains` argtypes.** They named `mn`, the group is `mp`; mana is now converted.
- **Finish rule.** The old guard returned whenever `tiering` was set, so the tier event could not
  be raised. A level now finishes when trains were gained, or a remort or tier is in progress.
  *The rule is pending a live check against Aardwolf's tier output.*
- **Tier GMCP.** The base callback unregistered the status callback from the base event instead of
  itself. It now unregisters itself, so repeated base messages do not restart the record.
- **API name.** The old call to a misspelled client-output API is gone: the state 2 message goes to the debug
  log.
- **`starttime`.** A failed superhero no longer loses the previous finish time.
- **Superhero group.** A finished superhero turns the group off; the old plugin left it on.
- **Bonus stats.** A bonus stat that is not one of the six adds no key to the record.
- **Disconnect and restart.** A disconnect in the middle of a level turns the collecting off, and a
  restart in the middle of a tier registers the GMCP callback again.
- **Watches.** `superhero silent`, which the old plugin watched, is kept next to the four commands
  the migration issue listed, and a bare `superhero` is watched too.
