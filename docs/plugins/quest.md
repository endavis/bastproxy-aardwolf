---
title: The quest Plugin
description: Turn the GMCP quest messages of Aardwolf into quest events and keep the current quest
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - quest
---

# The quest Plugin

The `quest` plugin reads the GMCP `comm.quest` messages of Aardwolf, keeps the current quest in a
saved state and raises one event per action. The [statdb plugin](statdb.md) listens to the
completed and failed events and records the quests.

## Loading

The plugin id is `plugins.aardwolf.quest`:

```text
#bp.core.pluginm.load plugins.aardwolf.quest
```

It depends on the events core plugin and on the [connect plugin](connect.md), which sets up GMCP,
so loading it loads `connect` too.

## Behaviour

The plugin registers to `ev_libs.net.mud_gmcp_comm.quest` and reads the `action` of the message.

- **ready.** Raises `quest_ready` with no data.
- **start.** Clears the state and sets it from the message: `mobname`, `mobarea`, `mobroom` and
  `stimer` from `targ`, `area`, `room` and `timer`, `starttime` to now, `finishtime` and
  `killedtime` to -1, `failed` to 0 and `level` to the total level from GMCP
  (`aardwolf.libs.aardu.actual_level_from_gmcp`). Raises `quest_start`.
- **killed.** Sets `killedtime` and raises `quest_killed`.
- **comp.** Sets `finishtime`, merges every key of the message into the state and raises
  `quest_comp`.
- **fail, timeout.** Set `finishtime` and `failed` to 1 and raise `quest_failed`.
- **status.** Raises `quest_status` with the message. The state does not change.
- **reset.** Raises `quest_reset` with no data.
- **Other input.** A message that is not a dict, has no `action` or has an unknown one raises
  nothing. Every message is logged at debug level.
- **Persistence.** The state is a `PersistentDict` in `quest.txt` in the plugin's data directory.
  It is synced after each message and by the `save` hook, which runs on unload and reload.

## Events

| Event | Payload keys |
| :--- | :--- |
| `ev_plugins.aardwolf.quest_ready` | none |
| `ev_plugins.aardwolf.quest_start` | `starttime`, `finishtime`, `killedtime`, `mobname`, `mobarea`, `mobroom`, `stimer`, `level`, `failed` |
| `ev_plugins.aardwolf.quest_killed` | the state keys |
| `ev_plugins.aardwolf.quest_comp` | the state keys plus the keys of the GMCP comp message: `action`, `qp`, `double`, `daily`, `totqp`, `gold`, `tierqp`, `mccp`, `lucky`, `opk`, `hardcore`, `tp`, `trains`, `pracs`, `completed` (quests completed) and `wait` (minutes until the next quest) |
| `ev_plugins.aardwolf.quest_failed` | the state keys, with `failed` 1 |
| `ev_plugins.aardwolf.quest_status` | `action` and `status` of the GMCP status message |
| `ev_plugins.aardwolf.quest_reset` | none |

Every payload is a plain dict copy; changing it does not change the saved state.

## From the old plugin

| Old | New |
| :--- | :--- |
| events `aard_quest_*` | `ev_plugins.aardwolf.quest_*` |
| `GMCP:comm.quest` | `ev_libs.net.mud_gmcp_comm.quest` |
| `aardu.getactuallevel` and `GMCP.getv` | `aardwolf.libs.aardu.actual_level_from_gmcp` |
| `send.msg` echo of each message | a debug log line |
| `plugin_quest_savestate` | the `save` plugin hook |
| `events.eraise` | `plugins.core.events:event.raise` |

Fixes in the port:

- A message that is not a dict, or has no action, no longer raises an error.
- Every payload is a plain copy of the state; the old `start` and `killed` events got the live
  state.
