---
title: The skills Plugin
description: Keep the skills, spells and recoveries of an Aardwolf character up to date from slist and raise their changes as events
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - skills
---

# The skills Plugin

The `skills` plugin keeps a table of the skills, spells and recoveries of the character. It reads
them from `slist`, which it sends through the mudcmds queue, and keeps them current from the
`{affon}`, `{affoff}`, `{recon}`, `{recoff}`, `{skillgain}` and `{sfail}` tags that Aardwolf sends
once option 102 is on. It raises an event for each change and answers questions about the skills
through APIs. The table is kept in memory only.

## Loading

The plugin id is `plugins.aardwolf.skills`:

```text
#bp.core.pluginm.load plugins.aardwolf.skills
```

It depends on the events, triggers, mudcmds and commands core plugins and on the
[connect plugin](connect.md) and the [a102 plugin](a102.md), so loading it loads those too. It
listens to the level plugin's events by name and does not depend on it.

## Behaviour

- **Triggers.** Their names carry a `skills_` prefix because trigger names are global. The six tag
  triggers are always on and are omitted, so the tag lines never reach the client. The slist triggers sit in three
  groups, named `<plugin id>.<suffix>` and off by default: `slist` (the start and end tags),
  `slist_spells` (a spell line) and `slist_recoveries` (a recovery line). They are omitted.
- **Queue.** Two `slist` command types, `slist` and `slistspellup`, run through the mudcmds queue. A
  refresh queues `slist noprompt` and then `slist spellup noprompt`, the second under its own type. Before one is sent the groups `slist` and
  `slist_spells` are turned on; the block ends at its end tag, which turns the groups off and
  finishes the command. An `slist` the player types is not queued, so its groups are off and its
  output is shown.
- **Block kinds.** The start tag `{spellheaders [kind] noprompt}` gives the kind:
    - Full (no kind): resets the table, then adds each skill and each recovery. The block ends at
      `{/recoveries}`. Raises `skills_affected_update` when it finishes.
    - `affected`: zeroes the durations, then sets the ones the lines give. Ends at
      `{/recoveries}`. Raises `skills_affected_update`.
    - `learned`: sets the percents. Ends at `{/spellheaders}`, with no recoveries.
    - `spellup`: flags the spellups. Ends at `{/spellheaders}`. The first one since a reset raises
      `skills_uptodate`.
- **Hide window.** The window is the `hide_output` option of the two mudcmds types. Each has its
  own `hide_start` and `hide_end`: `slist` opens at `{spellheaders noprompt}` and ends at
  `{/recoveries}`, `slistspellup` opens at `{spellheaders spellup noprompt}` and ends at
  `{/spellheaders}`. The types are separate because a full slist prints `{/spellheaders}` partway
  through, and one end regex would close its window there. The window hides every line of the
  block, including the `{/spellheaders}` line of a full slist, and the end tag closes it. It does
  not run to the prompt, because `noprompt` asks for none and a window that waited for one could
  swallow the next lines of the player. A prompt after the block is shown. If the end tag is lost,
  the window ends at the cap (mudcmds counts the opening line, so the types pass `HIDE_MAX_LINES`
  + 1, which is 1001) with a WARNING from mudcmds, or at the command timeout, and a disconnect ends
  it too.
- **a102 toggles.** When it loads the plugin asks the a102 plugin for `SPELLUPTAGS` and
  `SKILLGAINTAGS`, and takes the requests back in an `uninitialize` hook, on reload and unload
  alike, so the counts stay balanced.
- **First active.** The `character_active` plugin hook queues a refresh when the table is empty or
  not up to date. It also fires when the plugin loads with an active character. A remort or a tier
  (`ev_plugins.aardwolf.level_remort`, `ev_plugins.aardwolf.level_tier`) queues a refresh.
- **Failed skills.** A `{sfail}` with the reason `dontknow` for a skill that has a percent above 0
  queues a refresh.
- **Disconnect.** The table and the up-to-date flag are cleared, the hide window ends, and the
  groups are turned off, which abandons a block in progress.
- **Command timeout.** The core times out a queued command (5 seconds by default). A lost `slist`
  reply makes mudcmds finish the command without running `afterf`, close its hide window and send
  the next command. The plugin does not listen to `cmd_<type>_timeout`, so its trigger groups stay
  on until a later block ends or the link drops.

## MUD output

The block forms below were checked against Aardwolf's own `slist noprompt` and
`slist spellup noprompt` output. A full list is about 680 lines; the spellup list ends at
`{/spellheaders}` with no recoveries section, and neither sends a prompt:

```text
{spellheaders noprompt}                      # also: affected, learned and spellup before noprompt
3,acid blast,1,0,0,-1,1                      # sn,name,target,duration,pct,rcvy,type
{/spellheaders}
{recoveries noprompt}                        # full and affected only
0,Augmentation,0                             # sn,name,duration
{/recoveries}
```

A typed `slist` without `noprompt` starts with a bare `{spellheaders}`, which the plugin does not
match, so its output is shown.

These tags are inferred from the old plugin's regexes and were not captured from Aardwolf:
`{affon}14,600`, `{affoff}14`, `{recon}4,300`, `{recoff}4`, `{skillgain}14,86` and
`{sfail}14,0,2,-1` (sn, target, reason, recovery). Target codes 0 to 5 are `special`, `attack`,
`spellup`, `selfonly`, `object` and `other`; type 1 is a spell and 2 a skill. A code the plugin
does not know is kept as its number.

## Events

| Event | When | Payload keys |
| :--- | :--- | :--- |
| `ev_plugins.aardwolf.skills_affon` | an affect started | `sn`, `duration` (the time it ends, in seconds since the epoch) |
| `ev_plugins.aardwolf.skills_affoff` | an affect ended | `sn` |
| `ev_plugins.aardwolf.skills_recon` | a recovery started | `sn`, `duration` (the time it ends) |
| `ev_plugins.aardwolf.skills_recoff` | a recovery ended | `sn` |
| `ev_plugins.aardwolf.skills_gain` | the percent of a skill changed | `sn`, `percent` |
| `ev_plugins.aardwolf.skills_fail` | a skill or spell failed | `sn`, `reason`, `target`, `recovery` |
| `ev_plugins.aardwolf.skills_affected_update` | a full or affected slist set the durations | none |
| `ev_plugins.aardwolf.skills_uptodate` | the skills are known and the spellups flagged | none |

Tags for an sn the table does not know raise nothing and are logged at debug level. Each payload is
a copy.

## APIs

A key is an sn, a digit string or a name. A name is an exact match, else the one name that starts
with it, else the one name that contains it.

| API | Returns |
| :--- | :--- |
| `plugins.aardwolf.skills:skill.get` | a copy of the skill with its recovery resolved, or None |
| `plugins.aardwolf.skills:recovery.get` | a copy of the recovery, or None |
| `plugins.aardwolf.skills:skill.is.affected` | True when an affect is running |
| `plugins.aardwolf.skills:skill.is.blocked.by.recovery` | True when its recovery is running |
| `plugins.aardwolf.skills:skill.is.practiced` | True when more than 10 percent is learned |
| `plugins.aardwolf.skills:skill.can.use` | True when practiced, not affected and not blocked |
| `plugins.aardwolf.skills:skill.is.spellup` | True for a spellup |
| `plugins.aardwolf.skills:skill.is.bad` | True for an attack or special skill that is not a spellup |
| `plugins.aardwolf.skills:spellups.get` | copies of the spellups |
| `plugins.aardwolf.skills:is.up.to.date` | True once a spellup slist was read since the last reset |
| `plugins.aardwolf.skills:skill.send` | sends `cast <sn>` for a spell, the first word of the name for a skill; False for an unknown skill |

A skill is a dict with `sn`, `name`, `target`, `type`, `percent`, `duration` (the time the affect
ends, or 0), `spellup` and `recovery`.

## Commands

| Command | Does |
| :--- | :--- |
| `#bp.aardwolf.skills.refresh` | queues the full and the spellup slist |
| `#bp.aardwolf.skills.lu <skill>` | shows the sn, name, percent, duration, target, spellup, type and recovery of a skill, or `Could not find: <skill>` |

## From the old plugin

| Old | New |
| :--- | :--- |
| `skills.gets` | `plugins.aardwolf.skills:skill.get` |
| `skills.getr` | `plugins.aardwolf.skills:recovery.get` |
| `skills.isaffected` | `plugins.aardwolf.skills:skill.is.affected` |
| `skills.isblockedbyrecovery` | `plugins.aardwolf.skills:skill.is.blocked.by.recovery` |
| `skills.ispracticed` | `plugins.aardwolf.skills:skill.is.practiced` |
| `skills.canuse` | `plugins.aardwolf.skills:skill.can.use` |
| `skills.isspellup` | `plugins.aardwolf.skills:skill.is.spellup` |
| `skills.isbad` | `plugins.aardwolf.skills:skill.is.bad` |
| `skills.getspellups` | `plugins.aardwolf.skills:spellups.get` |
| `skills.isuptodate` | `plugins.aardwolf.skills:is.up.to.date` |
| `skills.sendcmd` | `plugins.aardwolf.skills:skill.send` |
| event `aard_skill_affon`, `aard_skill_affoff` | `ev_plugins.aardwolf.skills_affon`, `skills_affoff` |
| event `aard_skill_recon`, `aard_skill_recoff` | `ev_plugins.aardwolf.skills_recon`, `skills_recoff` |
| event `aard_skill_gain` | `ev_plugins.aardwolf.skills_gain` |
| event `skill_fail` | `ev_plugins.aardwolf.skills_fail` |
| event `skills_affected_update`, `skills_uptodate` | `ev_plugins.aardwolf.skills_affected_update`, `skills_uptodate` |
| events `aard_skill_affon_<sn>`, `aard_skill_affoff_<sn>`, `aard_skill_recon_<sn>`, `aard_skill_recoff_<sn>`, `skill_fail_<sn>` | dropped: no consumer was found |
| `cmdq.addtoqueue` | `plugins.core.mudcmds:command.queue` |
| `A102.toggle` | `plugins.aardwolf.a102:option.toggle` |
| `aard_level_remort`, `aard_level_tier` | `ev_plugins.aardwolf.level_remort`, `ev_plugins.aardwolf.level_tier` |
| `afterfirstactive` | the `character_active` plugin hook |

## Changes from the old plugin

- **Fixed: `isbad`.** It called `skill.gets`, a typo, so it always crashed.
- **Fixed: unknown sn.** `{affon}`, `{affoff}`, `{recon}`, `{recoff}` and `{skillgain}` for an
  unknown sn raised `KeyError`; they are now ignored and logged at debug level. `{sfail}` raised
  `TypeError`; it now raises the event.
- **Fixed: unknown codes.** An unknown fail reason, target or type code raised `KeyError` (reason 7
  is missing from the table); it now falls back to the number.
- **Fixed: echo.** The refresh echo said "slist learned" while it sent `slist spellup`; the echoes
  are gone and the plugin logs at debug level.
- **Fixed: leak.** The `{/spellheaders}` line of a full or affected slist reached the client.
- **Fixed: `skills_affected_update`.** Other plugins listened for it, but nothing raised it. It is
  raised when a full or affected slist finishes.
- **Dropped.** `refreshaffected` and `refreshlearned` were never called. The `affected` and
  `learned` blocks are still read when they arrive.
- **No `QUIETTAGS` off.** The old plugin turned `QUIETTAGS` off on every first active. The a102
  plugin counts requests, and an off at count 0 does nothing, so the plugin no longer sends it and
  cannot force off another plugin's or a client's request.
- **No aliases in `skill.send`.** The old `send.execute` expanded aliases; the command now goes
  straight to the MUD.
- **In-memory state.** The old plugin kept no saved state either; a disconnect clears the table and
  the first active event rebuilds it.
- **Tag lines hidden.** The old plugin did not omit the `{affon}`, `{affoff}`, `{recon}`,
  `{recoff}`, `{skillgain}` and `{sfail}` tag lines, so they reached the client. They are omitted
  now; the events still fire.
- **Anchored start tag.** The start regex is anchored to the whole line.
