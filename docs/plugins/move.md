---
title: The move Plugin
description: Raise an event when the character moves to another room on Aardwolf
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - move
---

# The move Plugin

The `move` plugin watches the GMCP `room.info` messages of Aardwolf and raises an event when the
character moves to another room, with the room left, the room entered and the exit used.

## Loading

The plugin id is `plugins.aardwolf.move`:

```text
#bp.core.pluginm.load plugins.aardwolf.move
```

It depends on the events core plugin and on the [connect plugin](connect.md), which sets up GMCP
and requests the room, so loading it loads `connect` too.

## Behaviour

The plugin registers to `ev_libs.net.mud_gmcp_room.info` and remembers the last room.

- **First room.** Remembered, nothing is raised.
- **Same room.** A message with the same `num` raises nothing.
- **Move.** A different `num` raises `move_room`. The direction is the last exit of the old room
  whose value is the new `num`, or `unknown`.
- **No num.** A message that is not a dict, or has no `num`, is ignored and does not replace the
  last room.
- **Mid-session load.** When the plugin loads, the room in the GMCP cache is the last room.
- **Disconnect.** `ev_libs.net.mud_muddisconnect` clears the last room, so the first room after a
  reconnect raises nothing.

## Events

| Event | Payload keys |
| :--- | :--- |
| `ev_plugins.aardwolf.move_room` | `from` (the room.info of the room left), `to` (the room.info of the room entered), `direction` (the exit used, or `unknown`) |

Every payload holds copies; changing it does not change the plugin's state.

## From the old plugin

| Old | New |
| :--- | :--- |
| event `moved_room` | `ev_plugins.aardwolf.move_room` |
| `GMCP:room.info` | `ev_libs.net.mud_gmcp_room.info` |
| `GMCP.getv` | the `data` of the event record (and `libs.net.protocols:gmcp.value.get` for the seed) |
| `events.eraise` | `plugins.core.events:event.raise` |
| `send.msg` echo | a debug log line |
| `afterfirstactive` `request room` | done by `connect` |

## Changes in the port

1. The `roominfo` payload key is dropped. It duplicated `to`.
2. The last room is cleared on disconnect. Before, the first room after a reconnect raised a move
   from the room of the previous session.
3. The `request room` on first active is dropped; `connect` already requests the room.
4. A message with no `num` is ignored, where the old code raised a `KeyError`. Missing or non-dict
   `exits` gives direction `unknown`, where the old code raised a `KeyError`.
5. The `send.msg` echo of each move is a debug log line.
6. The last room is seeded from the GMCP cache on a mid-session load. The old plugin swallowed the
   first move after a load.
7. Payloads are deep copies, so a listener cannot change the plugin's state.
