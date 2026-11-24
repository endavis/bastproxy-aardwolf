---
title: The mobk Plugin
description: Follow the combat output of Aardwolf and raise an event for each mob kill
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - mobk
---

# The mobk Plugin

The `mobk` plugin follows the combat output of Aardwolf and GMCP `char.status`, collects the facts of
a kill (experience, gold, damage, special kills) and raises one event with a copy when the kill is
over. The [statdb plugin](statdb.md) listens to `mobk_kill` and records the kills.

## Loading

The plugin id is `plugins.aardwolf.mobk`:

```text
#bp.core.pluginm.load plugins.aardwolf.mobk
```

It depends on the events, triggers and colors core plugins and on the [connect plugin](connect.md),
which asks the MUD for the GMCP `char` module. Loading the plugin loads `connect` too.

## Behaviour

- **Triggers.** All are always on, and their names carry a `mobk_` prefix because trigger names are
  global: `mobk_xp`, `mobk_rarexp`, `mobk_blessxp`, `mobk_bonusxp`, `mobk_xpptless`, `mobk_switch`,
  `mobk_flee`, `mobk_retreat`, `mobk_gold`, `mobk_splitgold`, `mobk_corpseget`, `mobk_sac`,
  `mobk_consume`, `mobk_trivia`, `mobk_trivia2`, `mobk_vorpal`, `mobk_assassin`, `mobk_deathblow`,
  `mobk_slit`, `mobk_disintegrate`, `mobk_banish`, `mobk_damage`, `mobk_damage2` and
  `mobk_bsincombat`.
- **Experience.** `mobk_xp` sets `xp` to the sum of a line such as `123+45` (168) and marks the kill
  as worth raising; a `don't receive` line also sets `noexp` to 1. `mobk_xpptless` sets `xp` to 0
  and marks the kill too. `mobk_rarexp`, `mobk_blessxp` and `mobk_bonusxp` set `rarexp`,
  `blessingxp` and `bonusxp`. `totalxp` is the sum of the four when the kill is raised.
- **Blessing and bonus.** The daily blessing line also reads like a bonus line. `mobk_bonusxp` has a
  negative lookahead for ` from your daily blessing`, so each line reaches one trigger and no
  trigger needs a priority or stops the evaluation of the others.
- **The mob.** GMCP `char.status.enemy` sets the name when none is set. The string carries `@`
  colour codes (the connect plugin turns on `rawcolor`), so the plugin strips them with
  `plugins.core.colors:colorcode.strip`. `mobk_switch` sets the name and resets the damage;
  `mobk_flee` and `mobk_retreat` clear the name and the damage. A damage line with no name set
  takes the enemy from the line. `mobk_gold` sets the name from the corpse when none is set.
- **Damage.** `mobk_damage` and `mobk_damage2` parse the line with
  `aardwolf.libs.aardu.parse_damage_line` and add it to `damage`, by damage type, as `hits`, `misses`
  and `damage`. A critical hit has a leading `*`, which both triggers accept (before `Your`, and for
  the counted form before or after the `[n]`). A live fight gave `*Your stab ERADICATES a lazy pupil.
  [40]` next to `Your stab mars a lazy pupil. [26]`; both add to the `stab` damage. The first damage
  line sets `starttime`. Damage to an enemy other than the current
  mob goes to a cache; when the plugin switches to that enemy, the cache entry becomes its damage.
  `mobk_bsincombat` adds `damage["backstab"]` with `incombat` set to true.
- **Gold.** `mobk_gold` takes the gold from a corpse, `mobk_splitgold` the share of a split. A value
  that is not a number is logged at debug level and the old value stays.
- **Special kills.** `mobk_trivia` and `mobk_trivia2` set `tp`; `mobk_vorpal`, `mobk_assassin` and
  `mobk_deathblow` set their flags. `mobk_corpseget` (`You get ... corpse of`) only logs at debug
  level.
- **When a kill is raised.** On `mobk_sac` or `mobk_consume` when a name is set, and at once on
  `mobk_slit`, `mobk_disintegrate` and `mobk_banish`. The event is raised only when an experience
  line was seen for the kill; either way the kill is then reset, so a kill raises once.
- **Weapons.** `wielded_weapon` and `second_weapon` are the serials of the items in slots 24 and 25.
  The [eq plugin](eq.md) provides `plugins.aardwolf.eq:eq.worn.get`. The plugin calls it only when
  `libs.api:api.exists` says it exists, and leaves the serials empty otherwise. The API name is the
  constant `EQ_WORN_API` of the `mobk` libs, which the eq plugin matches.
  The result may be an object with a `serial` attribute or a mapping with a `serial` key.
- **Room and level.** `room_id` is GMCP `room.info.num`, -1 when it is missing. `level` is the
  total level from `aardwolf.libs.aardu.actual_level_from_gmcp`.

## Commands

| Command | What it does |
| :--- | :--- |
| `#bp.aard.mobk.last` | show the last kill the plugin raised |

`last` shows the mob name, room, level, xp (normal, rare, bonus, blessing and total), gold, the
special-kill flags that are set, the fight time and the damage table (type, hits, misses, damage).
The plugin keeps a copy of the last raised kill in memory only, so it is gone when the plugin
unloads. With no kill since the plugin loaded, the command says so.

## Events

| Event | When | Payload keys |
| :--- | :--- | :--- |
| `ev_plugins.aardwolf.mobk_kill` | a kill is over | `name`, `xp`, `rarexp`, `bonusxp`, `blessingxp`, `totalxp`, `noexp`, `gold`, `tp`, `time`, `vorpal`, `banishment`, `assassinate`, `slit`, `disintegrate`, `deathblow`, `wielded_weapon`, `second_weapon`, `room_id`, `level`, `damage`, `immunities`, `starttime`, `finishtime` |

The payload is a deep copy; changing it does not change the next kill. statdb stores the columns of
its `mobkills` table and ignores the keys it has no column for (`damage`, `immunities`, `starttime`
and `finishtime`). `immunities` is always empty: the old plugin could fill it, but no trigger called
it.

## From the old plugin

| Old | New |
| :--- | :--- |
| event `aard_mobkill` | `ev_plugins.aardwolf.mobk_kill` |
| `GMCP:char.status` | `ev_libs.net.mud_gmcp_char.status` |
| `aardu.parsedamageline`, `aardu.getactuallevel` and `GMCP.getv` | `aardwolf.libs.aardu.parse_damage_line`, `actual_level_from_gmcp` and `libs.net.protocols:gmcp.value.get` |
| `colors.stripansi` on GMCP | `plugins.core.colors:colorcode.strip` |
| `eq.getworn` | `plugins.aardwolf.eq:eq.worn.get`, when it exists |
| `send.msg` echoes | debug log lines |
| the `raised` key | a plugin attribute; it is not in the payload |

Fixes in the port:

- **Summed experience.** `123+45` was added up and then thrown away. It is now `xp`, and the kill is
  marked as worth raising.
- **Immunity.** The `immunity` handler is dropped: no trigger called it.
- **Settings.** `instatext` and `instaback` are dropped; nothing used them.
- **Blessing line.** The old trigger used `priority=99` and `stopevaluating`, which also hid the
  line from every other plugin. A lookahead in `mobk_bonusxp` replaces it.
