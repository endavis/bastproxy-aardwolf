---
title: Plugins
description: The Aardwolf plugins this package adds to bastproxy, and how to load them
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
---

# Plugins

`bastproxy-aardwolf` is a bastproxy plugin source. It registers itself in the `bastproxy.plugins`
entry-point group (`aardwolf = "aardwolf"` in `pyproject.toml`), so bastproxy discovers its plugins
and gives them IDs of the form `plugins.aardwolf.<name>`.

## Loading a plugin

From a client connected to the proxy:

```text
#bp.core.pluginm.load plugins.aardwolf.<name>
```

The command takes several names at once, and `aardwolf` (or `plugins.aardwolf`) loads every
Aardwolf plugin that is not loaded yet, with its dependencies:

```text
#bp.core.pluginm.load aardwolf
```

A loaded plugin is remembered and loaded again when bastproxy starts. `#bp.core.pluginm.list`
lists every discovered plugin, loaded or not.

## Available plugins

| Plugin | ID | Description |
| :--- | :--- | :--- |
| [config](config.md) | `plugins.aardwolf.config` | Keeps the settings several Aardwolf plugins share, starting with the list of questmasters. |
| [connect](connect.md) | `plugins.aardwolf.connect` | Sets up Aardwolf GMCP, presses return at login prompts and detects when the character is first active. |
| [a102](a102.md) | `plugins.aardwolf.a102` | Toggles Aardwolf telnet option 102 features with shared counts and publishes the MUD's option 102 reports. |
| [statdb](statdb.md) | `plugins.aardwolf.statdb` | Records character stats, quests, campaigns, global quests, levels and mob kills in a database, and reports on them. |
| [eqdb](eqdb.md) | `plugins.aardwolf.eqdb` | Keeps the character's identified items in a database and lets other plugins save and get an item. |
| [eq](eq.md) | `plugins.aardwolf.eq` | Tracks the items the character wears, carries, keeps on the keyring and stores in the vault, and raises the changes as events. |
| [itemid](itemid.md) | `plugins.aardwolf.itemid` | Identifies an item with `invdetails` and `identify`, saves the result through eq and eqdb, and shows it as an item box with the `id` command. |
| [itemkeep](itemkeep.md) | `plugins.aardwolf.itemkeep` | Keeps items of chosen types with a hidden `keep` when they reach the inventory. |
| [quest](quest.md) | `plugins.aardwolf.quest` | Turns the GMCP quest messages into quest events and keeps the current quest. |
| [whois](whois.md) | `plugins.aardwolf.whois` | Parses the output of the `whois` command into a saved state and raises it as an event. |
| [level](level.md) | `plugins.aardwolf.level` | Detects levels, powerups, hero, superhero, remort and tier from the MUD output and raises them as events. |
| [mobk](mobk.md) | `plugins.aardwolf.mobk` | Follows the combat output and raises an event for each mob kill, with its experience, gold, damage and special kills. |
| [cp](cp.md) | `plugins.aardwolf.cp` | Follows the campaigns of the character and raises the mobs left, the completion and the failure as events. |
| [gq](gq.md) | `plugins.aardwolf.gq` | Follows the global quests of the character and raises the declaration, the mobs left and the end as events. |
| [promptfix](promptfix.md) | `plugins.aardwolf.promptfix` | Makes the prompt and the battle prompt end in `%c`, so the next line from the MUD never sticks to them, and marks the prompt lines as prompts. |
| [scanh](scanh.md) | `plugins.aardwolf.scanh` | Highlights the campaign, global quest and quest mobs in the `scan` output. |
| [move](move.md) | `plugins.aardwolf.move` | Raises an event when the character moves to another room, with the rooms and the direction. |
| [skills](skills.md) | `plugins.aardwolf.skills` | Keeps the character's skills, spells and recoveries up to date from `slist` and raises events when an affect or recovery turns on or off. |
| [repop](repop.md) | `plugins.aardwolf.repop` | Sends a message to a channel when an area repops, from GMCP `comm.repop`. |
| [iceage](iceage.md) | `plugins.aardwolf.iceage` | Raises an event, with the minutes left, for each Ice Age and reboot countdown line. |

Libraries that plugins share, such as `aardwolf.libs.aardu` and `aardwolf.libs.itemu`, are documented in the
[API Reference](../reference/api.md).

## Adding a plugin

A new or migrated plugin gets its own page in this section. See
[Adding a Plugin](../development/adding-a-plugin.md).
