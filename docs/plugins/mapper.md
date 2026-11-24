---
title: The mapper Plugin
description: Feed the core client mapper with the rooms, areas, room flags and walking rules of Aardwolf
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - mapper
---

# The mapper Plugin

The `mapper` plugin is the Aardwolf adapter of the core client mapper. The core mapper owns the map
database, the pathfinding and the walking; this plugin only tells it what Aardwolf sends. It talks to
the mapper through its API and events, never through its modules.

See the core documentation:
[the mapper](https://github.com/endavis/bastproxy/blob/main/docs/client/mapper.md),
[the mapper system](https://github.com/endavis/bastproxy/blob/main/docs/claude/mapper_system.md) and
[ADR-0021](https://github.com/endavis/bastproxy/blob/main/docs/decisions/0021-the-mapper-owns-the-map-and-walking-and-game-plugins-adapt-it-through-callbacks.md).

## Loading

The plugin id is `plugins.aardwolf.mapper`:

```text
#bp.core.pluginm.load plugins.aardwolf.mapper
```

It depends on the events, triggers and colors core plugins, on the [move plugin](move.md) and on the
core `plugins.client.mapper`, so loading it loads them too.

## Behaviour

- **Capture.** On `ev_plugins.aardwolf.move_room` the room in `to` is added with `room.add` and made
  the current room with `room.current.set`. The room dict maps `num` to `uid`, `zone` to `area`,
  `coord.x` and `coord.y` to `x` and `y` (`z` is 0), and keeps `details`, the coord id and the
  continent in `details`. The name has its colour codes stripped. The exits go inside the `room.add`
  payload, as `{direction: uid}`; an exit to an unknown room is `-1`. The core stores each exit and
  compares them with the stored ones.
- **First room.** The first room after a load or a reconnect raises no `move_room`, so the plugin
  takes it from the GMCP cache at load, or from the first `room.info` while it has no current room.
- **Nomap rooms.** A room whose `num` is missing, 0 or -1 is skipped.
- **Area.** When the area of a room is unknown to the mapper, the plugin sends `request area` once
  per area and connection. The `room.area` reply is stored with `area.add`; its `flags` become the
  flag list and the other keys go to `details`.
- **Room flags.** `Magic walls bounce you back.` marks the current room `noportal`, and
  `You cannot recall from this room.` or `You cannot return home from this room.` marks it
  `norecall`. The stored flags are kept when the room is added again. The client gets a line.
- **Requirement.** An exit requirement is `{"level": n, "tier": t}`, each key optional. The exit is
  allowed when the character tier, from GMCP `char.base.tier`, is at least `tier` and the level, from
  `char.status.level`, is at least `level`. For an exit from `*` or `**` (a portal or an
  anywhere command), the level counts as `level + 10 * tier`. An unknown level counts as 201 and an
  unknown tier as 0. A requirement that is not a dict of ints blocks the exit.
- **Movement.** Plain directions (`n s e w u d`) are joined into `run` speedwalks, as in `run 3n2e`.
  A run of one step is sent as the bare direction, and any other step, such as `enter aylor`, is
  sent as it is.
- **Mismatch.** On `ev_plugins.client.mapper_room_mismatch` the client gets the area and exit
  differences with the `#bp.client.mapper.purge` commands that clear them.
- **Disconnect.** Clears the current room and the pending area requests.

### Limitations

- A blind character may see the noportal and norecall lines differently; the old MUSHclient plugin
  checked for blindness first, this one does not.
- If the core mapper is reloaded without this plugin, the callbacks are lost until the plugin is
  reloaded.

## Events used

| Event | Use |
| :--- | :--- |
| `ev_plugins.aardwolf.move_room` | store the room entered and make it current |
| `ev_libs.net.mud_gmcp_room.info` | take the first room when there is no current room |
| `ev_libs.net.mud_gmcp_room.area` | store the area the MUD sent |
| `ev_plugins.client.mapper_room_mismatch` | tell the client about a contradicting room |
| `ev_libs.net.mud_muddisconnect` | forget the room and the pending areas |
