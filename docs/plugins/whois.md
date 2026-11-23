---
title: The whois Plugin
description: Parse the output of the Aardwolf whois command into a saved state and raise it as an event
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - whois
---

# The whois Plugin

The `whois` plugin reads the output of the Aardwolf `whois` command, builds a state of the
character from it and from GMCP, saves the state and raises an event with a copy. The
[statdb plugin](statdb.md) listens to that event and fills its `stats` table from it.

## Loading

The plugin id is `plugins.aardwolf.whois`:

```text
#bp.core.pluginm.load plugins.aardwolf.whois
```

It depends on the events, triggers, watch and mudcmds core plugins.

## Behaviour

- **Start.** A whois starts in one of two ways, and both clear the saved state and turn the
  trigger group on:
    - A client types `whois` (or `whoi`). The core watch `whois` matches it and raises
      `watch_whois`. The watch sees only lines a client typed.
    - Another plugin queues the command with `plugins.core.mudcmds:command.queue("whois")`. The
      plugin adds a `whois` command type with `plugins.core.mudcmds:type.add`, and mudcmds calls
      its `beforef` just before it sends the line. This plugin queues its own whois this way, see
      below.

  The queued path also arms hiding (see Hiding); the typed path does not.
- **Automatic whois.** The plugin queues one `whois` each time the character becomes first active
  (`ev_libs.api_character_active` with `is_character_active` true), and once after it loads when
  `libs.api:character.is.active` is already true. It does not depend on the statdb plugin or on
  what the stats database holds.
- **Parsing.** The group holds the triggers `whoisheader`, `whoisclasses`, `whois1`, `whois2`,
  `whois3` and `whoispowerup`; all are off until a whois starts. The header sets the name, level,
  tiers, redos, race, subclass and remorts from GMCP (`char.base.*` and `char.status.level`) and
  the sex from the line. A character with one remort gets its class from `char.base.class`. A
  multiclass line sets the classes (one per remort, as abbreviations) and the remort count from
  the line. Each stat line adds one key per stat, named for the stat in lower case without spaces,
  such as `questscomplete`, with the value as text. The power-up line sets `powerupsall` and
  `powerupsmort`.
- **Hiding.** Every queued whois is hidden from the client, whether this plugin or another plugin
  queued it through `mudcmds`. The window is the `hide_output` option of the `whois` command type,
  with the 74-dash line as `hide_start`. mudcmds arms it when it sends the whois, opens it at the
  first 74-dash line of the reply and hides every following line, blank lines and the prompt
  included. The closing dashes call `command.finish`, and the window closes at the prompt (marked
  by promptfix). It also closes at the cap (the type passes `HIDE_MAX_LINES` + 1 because mudcmds
  counts the opening line) with a WARNING from mudcmds, at the command timeout, or on disconnect.
  A typed `whois` or `whoi` is shown in full, and parsing and the event are the same either way.
  One difference: mudcmds cannot tell a typed reply from the queued one, so a whois typed after a
  queued whois was sent and before its reply arrived is hidden, and the window ends when the whois
  finishes or times out.
- **End.** The trigger `whoisend` matches the line of 74 dashes. It is not in the group: it is
  turned on at the header, so the dashed line above the header cannot end the whois. At the end
  line the plugin sets `totallevels`, saves the state, turns the triggers off, raises the event and
  calls `plugins.core.mudcmds:command.finish("whois")`. The call does nothing when the current
  command is not a queued whois, as for a typed whois.
- **Disconnect.** A MUD disconnect turns the group and `whoisend` off, so a whois cut off by a disconnect does not leave
  the triggers on. mudcmds closes the hide window.
- **Persistence.** The state is a `PersistentDict` in `whois.txt` in the plugin's data directory.
  It is synced at the end line and by the `save` hook, which runs on unload and reload.

## Events

| Event | Payload keys |
| :--- | :--- |
| `ev_plugins.aardwolf.whois_received` | `name`, `level`, `tiers`, `redos`, `race`, `sex`, `subclass`, `remorts`, `classes` (a list of `remort` and `class`), `powerupsall`, `powerupsmort`, `totallevels`, and `stats`, a dict with one key per stat line |

The payload is a plain dict copy of the state, with the stat lines nested under `stats` so every
top-level key is described in the event's `arg_descriptions`; changing it does not change the saved
state, which keeps the stat lines at the top level.

## From the old plugin

| Old | New |
| :--- | :--- |
| event `aard_whois` | `ev_plugins.aardwolf.whois_received` |
| `triggers.togglegroup` | `plugins.core.triggers:group.toggle.enable` |
| `send.msg` echo of the state | a debug log line |
| `aardu.classabb()` | `aardwolf.libs.aardu.CLASSABBREV` |
| `plugin_whois_savestate` | the `save` plugin hook |
| `GMCP.getv` | `libs.net.protocols:gmcp.value.get` |
| a whois sent by a plugin | a queued command type, so the plugin parses it too |
| the old plugin never sent a whois itself | a queued whois is hidden from the client |

Fixes in the port:

- A missing GMCP value no longer raises an error.
- A class name that is not in the table passes through instead of raising an error.
- The event gets a plain copy of the state; the old deep copy of a persistent dict returned the
  live object.
- A whois sent by another plugin is parsed. The core watch sees only lines a client typed.
