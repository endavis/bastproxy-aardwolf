---
title: The su Plugin
description: Cast the spellups of an Aardwolf character on itself again when they wear off
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - su
---

# The su Plugin

The `su` plugin keeps a list of spells in a cast order. When a spell on the list is missing from
the character, it casts it, one spell at a time, as long as a cast can work. It is ported from the
`su` plugin of the old bastproxy.

## Loading

The plugin id is `plugins.aardwolf.su`:

```text
#bp.core.pluginm.load plugins.aardwolf.su
```

It depends on the events, settings, commands and timers core plugins and on the
[connect](connect.md), [skills](skills.md) and [move](move.md) plugins. It never imports another
plugin: it uses their APIs and events by name. It is not required, so it does not load until asked.
Casting is on by default once it is loaded (`enabled` is `True`, as in the old plugin).

## Behaviour

- **The gate.** A spell is cast only when all of these hold: the `enabled` setting is on, the MUD
  is connected, the character is active, the GMCP `char.status.state` is 3, the skills plugin is up
  to date (`is.up.to.date`), no cast is waiting, and none of `nocast`, `nomana` and `nomoves` is set.
- **The pick.** The plugin casts the first spell in the list that is enabled, is not blocked by a
  recovery in this session, and passes `skill.can.use` of the skills plugin (practiced, not
  affected, not blocked by a recovery). The cast is `skill.send`, which sends `cast <sn>`.
- **When it looks.** After an affect or a recovery ends, when the affects are read, when the skills
  are up to date, when a listed skill is practiced, when mana or moves come back, when the character
  state becomes active, when the character becomes active, when the character leaves a nocast room,
  and when `enabled` is turned on, and after a command that adds or enables a spell.
- **Waiting.** After a cast the plugin waits for the answer. The affect starting for that spell ends
  the wait and the next spell is cast. The wait also ends after `waittimeout` seconds (15 by default) with no answer (a debug
  log, and no cast at once: the next event casts). A cast that fails ends the wait too.
- **Casts are not queued.** They do not go through the mudcmds queue. The reply of a cast differs
  per spell and you should see it, and the end of a cast is read from the `{affon}` and `{sfail}`
  tags, not from the reply text.
- **No mana or no moves.** The plugin stops casting and remembers the mana (or moves) at that
  moment. It casts again once the GMCP `char.vitals` show more than that.
- **Nocast rooms.** A cast that fails with `nocastroom` stops casting and saves the room (from GMCP
  `room.info.num`) in `nocastrooms`. Entering a saved room stops casting; entering any other room
  starts it again.
- **Fighting or not active.** The wait ends and nothing is disabled. The next `char.status` with
  state 3 casts again.
- **Lost concentration.** The cast is sent again and the wait restarts.
- **Disabled spells.** A cast that fails with `alreadyaff`, `disabled` or `wrongtarget` disables
  the spell, saves the list and tells the client `Spellup - disabled <name> because ...`.
- **Recoveries.** A cast blocked by a recovery (`recblock`) skips that spell until any recovery
  ends or the connection drops.
- **Not known.** `dontknow` and any other reason end the wait and nothing else; the skills plugin
  refreshes itself, and its up-to-date event casts again.
- **A failure of a spell that is not the one waited on** is ignored, except `nomana`, `nomoves`,
  `nocastroom`, `fighting` and `notactive`, which hold for any spell.
- **Disconnect.** The wait, the timer, `nocast`, `nomana`, `nomoves` and the blocked spells are
  forgotten.

## Settings

| Setting | Default | Meaning |
| :--- | :--- | :--- |
| `enabled` | `True` | Cast the spellups. |
| `nocastrooms` | empty | The rooms where casting failed. Read only; kept by the plugin. |
| `practicedabove` | `10` | A spell at this percent or less (0 to 100) is shown as not practiced (`NP`) by `list`. |
| `waittimeout` | `15` | Seconds (1 to 3600) to wait for the result of a cast. |

Both are read when used, so a change needs no reload; a value out of range is refused and the old one kept.

```text
#bp.aardwolf.su.set enabled False
```

The old settings `waiting`, `nocast`, `nomana`, `nomoves` and `currentroom` are kept in memory only,
so a restart cannot leave them stuck.

## Commands

All commands are in the group `Spellups on Self`.

| Command | Meaning |
| :--- | :--- |
| `add <spell>...` | Add spells. `name:place` puts a spell at a place (0 is the first), `all` adds every practiced spellup, `-o` adds a spell the MUD does not flag as a spellup. |
| `list [match]` | List the spells, optionally only those with `match` in the name. |
| `rem <spell>...` | Remove spells; `all` clears the list. |
| `en <spell>...` | Enable spells; `all` enables every one. |
| `dis <spell>...` | Disable spells; `all` disables every one. |
| `check` | Show each condition for casting and whether it holds. |

A spell is given by name or by sn. The columns of `list`:

| Column | Meaning |
| :--- | :--- |
| `A` | the spell is affecting the character |
| `P` | the spell was cast and its answer is awaited |
| `B` | a recovery blocks the spell |
| `D` | the spell is disabled |
| `NP` | the spell is not practiced (the `practicedabove` percent or less, 10 by default) |
| `NL` | the spell is not learned (0 percent) |

## Storage

The list is kept in `spellups.txt` in the plugin data directory, with the keys of the old plugin:
`sorder` (the list of sn in cast order) and `self` (an sn to `{"enabled": bool}`). An old file can be
copied in. On load the unused keys `oorder` and `other` are dropped, digit strings become numbers,
a spell with no `self` entry is enabled, an entry for a spell not in the order is dropped and
duplicates are removed. The file is written after every change and when the proxy saves.

## Events

The plugin listens to the skills events `ev_plugins.aardwolf.skills_affon`, `_affoff`, `_recoff`,
`_gain`, `_fail`, `_affected_update` and `_uptodate`, to `ev_plugins.aardwolf.move_room`, to the
GMCP events `ev_libs.net.mud_gmcp_char.vitals` and `ev_libs.net.mud_gmcp_char.status`, to
`ev_libs.net.mud_muddisconnect`, to `ev_plugins.aardwolf.su_var_enabled_modified`, and to the
character active hook. It raises no events.

## APIs used

`plugins.aardwolf.skills`: `skill.get`, `skill.send`, `skill.can.use`, `skill.is.affected`,
`skill.is.blocked.by.recovery`, `skill.is.practiced`, `skill.is.spellup`, `spellups.get` and
`is.up.to.date`. Also `plugins.core.proxy:mud.is.connected`, `libs.api:character.is.active`, the
settings, timers and GMCP value APIs. The plugin adds none.

## MUD output

The plugin matches no MUD text itself. These come from the old plugin and the skills plugin.

Confirmed on a real character (Underwater breathing, sn 333):

1. `cast 333` casts the spell by number.
2. A lost concentration sends `{sfail}333,0,1,-1` (fail code 1, `lostconc`) before "You lost your
   concentration while trying to cast underwater breathing."; the plugin cast again at once.
3. The spell taking hold sends `{affon}333,300` before "You feel gills growing on your neck!"; the
   wait ended and `list` showed the spell as `A`.

Still **unconfirmed** on a real character:

1. The tags `{affoff}`, `{recoff}` and `{skillgain}`, and the fail codes 2 to 12.
2. The GMCP `char.vitals` keys `mana` and `moves`.

These are taken as confirmed by other plugins: `char.status.state` 3 is active, and `room.info.num`
is the room number.

## From the old plugin

| Old | New |
| :--- | :--- |
| the old `su` plugin module | `src/aardwolf/su/` |
| `AUTOLOAD = False` | `PLUGIN_REQUIRED = False` |
| `skills.sendcmd`, `skills.canuse`, `skills.isuptodate` | `skill.send`, `skill.can.use`, `is.up.to.date` |
| settings `waiting`, `nocast`, `nomana`, `nomoves`, `currentroom` | memory only |
| `moved_room`, `skill_fail`, `aard_skill_*` events | the `ev_plugins.aardwolf` events of move and skills |
| `savestate` event | the `save` hook |
| `reset` | not ported; `rem all` clears the list |

## Changes from the old plugin

1. `rem all` returned nothing and never saved (the save and the return were in the `else`), so the
   command failed; it also said "Removed X" for a spell not in the list. (`savestate` is guessed not
   to have been a method of the old plugin; its base class was not checked.)
2. The `dis` docstring and its message for no argument said "enable".
3. A `nomoves` failure stored the moves in `lastmana`, not `lastmoves`.
4. The `P` column compared the waiting spell with the sn; a type mismatch is guessed, not
   reproduced.
5. A spell in `sorder` with no `self` entry raised a `KeyError` in the pick.
6. The skill gain handler read its arguments unchecked, and its threshold of 50 percent kept
   casting blocked once a skill became practiced (over 10 percent). Any gain of a listed spell now
   looks again.
7. `waiting` was never cleared when a cast got no `{affon}` or `{sfail}`, which stopped casting for
   good. A 15 second timer clears it.
8. `other` and `oorder` were never used (apart from one write in the `disabled` branch) and are
   dropped.
9. Not saved: the transient state was in saved settings, so a stuck `waiting`, `nomana` or `nocast`
   survived a restart; `en` and `dis` never saved; `nocastrooms` was changed in place on a readonly
   setting.
10. `wrongtarget` and `recblock` looked again at once and could loop on the same spell, and
    `dontknow` did the same while the refresh was queued. `wrongtarget` now disables the spell,
    `recblock` skips it until a recovery ends, and `dontknow` waits for the refresh.
11. `nocastroom` used `currentroom`, set only on a move, so it was -1 after a load in mid session.
    The room now comes from GMCP.
12. `add` looked once per spell and raised a `ValueError` for a bad `name:place`.
13. The `send.msg` debug messages and `@timeit` are debug logs.
14. The `NP` column says 10 percent or less, the limit the skills plugin uses for practiced, where
    the old plugin tested for exactly 1 percent.

## Known gaps

- The MUD texts still listed as unconfirmed above need a check on a real character.
- Casts are not queued, so a cast typed by a client at the same time as the plugin's may confuse the
  wait; the `waittimeout` timer (15 seconds by default) frees it.
- The spell lists for other characters (the old `other` list) were never used and are not ported.
