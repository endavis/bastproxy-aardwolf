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

A loaded plugin is remembered and loaded again when bastproxy starts. `#bp.core.pluginm.list`
lists every discovered plugin, loaded or not.

## Available plugins

| Plugin | ID | Description |
| :--- | :--- | :--- |
| [connect](connect.md) | `plugins.aardwolf.connect` | Sets up Aardwolf GMCP, presses return at login prompts and detects when the character is first active. |
| [a102](a102.md) | `plugins.aardwolf.a102` | Toggles Aardwolf telnet option 102 features with shared counts and publishes the MUD's option 102 reports. |
| [statdb](statdb.md) | `plugins.aardwolf.statdb` | Records character stats, quests, campaigns, global quests, levels and mob kills in a database, and reports on them. |
| [quest](quest.md) | `plugins.aardwolf.quest` | Turns the GMCP quest messages into quest events and keeps the current quest. |
| [whois](whois.md) | `plugins.aardwolf.whois` | Parses the output of the `whois` command into a saved state and raises it as an event. |
| [level](level.md) | `plugins.aardwolf.level` | Detects levels, powerups, hero, superhero, remort and tier from the MUD output and raises them as events. |
| [mobk](mobk.md) | `plugins.aardwolf.mobk` | Follows the combat output and raises an event for each mob kill, with its experience, gold, damage and special kills. |

Libraries that plugins share, such as `aardwolf.libs.aardu`, are documented in the
[API Reference](../reference/api.md).

## Adding a plugin

A new or migrated plugin gets its own page in this section. See
[Adding a Plugin](../development/adding-a-plugin.md).
