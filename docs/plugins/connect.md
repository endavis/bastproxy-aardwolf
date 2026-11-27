---
title: The connect Plugin
description: Set up Aardwolf GMCP, press return at login prompts and detect when the character is first active
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - gmcp
---

# The connect Plugin

The `connect` plugin gets an Aardwolf session ready. It turns on the GMCP data Aardwolf sends,
gets past the login pager, and tells bastproxy when the character is active and ready for
commands.

## Loading

The plugin id is `plugins.aardwolf.connect`:

```text
#bp.core.pluginm.load plugins.aardwolf.connect
```

It works when loaded mid-session too: if the MUD is connected and the character is already active,
it sets GMCP up and detects first active straight away.

## Behaviour

- **GMCP.** It asks the MUD for the GMCP modules `Char 1`, `Room 1`, `Comm 1`, `Group 1` and
  `Core 1`. After the first GMCP message it sends `rawcolor on` and `group on`. When a client logs
  in while the character is connected, it requests the room, quest and character data again.
- **Press Return.** It presses return at each `[ Press Return to continue ]` prompt until the
  character is first active.
- **First active.** The character is first active when the character, room and quest GMCP data
  have arrived and `char.status.state` is 3. The plugin then sends `look` and `map` and sets
  bastproxy's character-active flag (`libs.api:character.active.set`).
- **Disconnect.** A MUD disconnect resets the plugin, so the next login is detected again.
  bastproxy itself clears the character-active flag on disconnect.

## APIs

| API | Description |
| :--- | :--- |
| `plugins.aardwolf.connect:character.is.first.active() -> bool` | True once the character has been first active on this connection. |

## Events

The plugin raises no events of its own. Setting the character-active flag raises bastproxy's
`ev_libs.api_character_active`. A plugin that needs to act once the character is active uses
bastproxy's `@RegisterPluginHook("character_active")` hook, which runs then, at load when the
character is already active, and again after each new login. The hook needs a bastproxy that
includes endavis/bastproxy#589; when `uv.lock` pins an older commit, upgrade it with
`uv lock --upgrade-package bastproxy`.

## Web data provider

The plugin offers the character vitals through bastproxy's web plugin (ADR-0025):

| | |
| :--- | :--- |
| Provider | `vitals` |
| Topic | `aardwolf.connect.vitals` |
| Page | `/aardwolf/connect/vitals` |

The data is a JSON object built from the cached GMCP `char.vitals`, `char.maxstats`,
`char.status` and `char.base`. A value that is not cached is `null`. Values pass through as the
MUD sent them.

| Field | GMCP source |
| :--- | :--- |
| `hp`, `mana`, `moves` | `char.vitals` |
| `maxhp`, `maxmana`, `maxmoves` | `char.maxstats` |
| `level`, `tnl`, `align`, `state`, `pos`, `enemy`, `enemypct` | `char.status` |
| `tier`, `remorts` | `char.base` |

A change is raised once per `char.vitals`, `char.maxstats`, `char.status` or `char.base` message,
and once when the MUD disconnects (the GMCP cache clears). This needs a bastproxy that includes
`web.provider.add`; when `uv.lock` pins an older commit, upgrade it with
`uv lock --upgrade-package bastproxy`.

## From the old plugin

| Old | New |
| :--- | :--- |
| API `connect.firstactive` | `plugins.aardwolf.connect:character.is.first.active`, or bastproxy's `libs.api:character.is.active` |
| event `firstactive` | `ev_libs.api_character_active` (bastproxy core) |
| `afterfirstactive()` override in a plugin | `@RegisterPluginHook("character_active")` |

Changes from the old plugin:

- **Changed: no empty line at first active.** The old plugin sent `look`, `map` and then an empty
  line. The port sends `look` and `map` only.
