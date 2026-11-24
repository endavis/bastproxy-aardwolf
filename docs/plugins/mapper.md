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
  A run of one step is sent as the bare direction. Any other step, such as `enter aylor` or a custom
  exit, is split on `;` and each part is sent as a command. A `wait(N)` part (N seconds, up to 40,
  fractions allowed) ends the commands sent now: the ones after it are sent N seconds later, with
  the client told `Mapper: waiting N seconds`. A new movement, a walk that is stopped, cleared or
  fails (`ev_plugins.client.mapper_walk_failed`), a disconnect and an unload drop the commands still
  waiting.
- **Custom exits.** An exit whose command is not a plain direction and does not leave from `*` or
  `**`. `cexit` stores one. A wait is part of the command, as in MUSHclient:
  `open north;wait(2);north`. The commands of an imported MUSHclient custom exit already have this
  form.
- **Exit locks.** `lockexit` sets the level an exit needs, on any exit, plain or custom. A lock is
  the same `{"level": n}` requirement the import writes, so the path search honours it.
- **Portals and recall.** `portal` stores the portal under `*`, and recall under `**`. The commands
  `recall`, `home` and `hom` are stored as recalls without a flag. The path search uses a portal
  from the first room that is not `noportal`, and a recall from the first that is not `norecall`.
- **Bounce.** From a `noportal` room the cheapest recall is chained into a portal, and from a
  `norecall` room the cheapest portal into a recall, with no setting. A room that is both walks out
  first.
- **Mismatch.** On `ev_plugins.client.mapper_room_mismatch` the client gets the area and exit
  differences with the `#bp.client.mapper.purge` commands that clear them.
- **Disconnect.** Clears the current room and the pending area requests.

### Limitations

- A large import takes minutes, because the core mapper has no bulk add and commits every room and
  exit on its own. The proxy stays responsive: the file is read in a thread and the writes run in
  short slices.
- No search covers all areas; `here` or one area id only.
- `|` is the proxy command separator and cannot be part of a custom exit or portal command; use
  `;`. Quote words with an apostrophe.
- `goto` and the `walk_step` event report only the commands before the first wait of a step.
- A blind character may see the noportal and norecall lines differently; the old MUSHclient plugin
  checked for blindness first, this one does not.
- If the core mapper is reloaded without this plugin, the callbacks are lost until the plugin is
  reloaded.

## Commands

The commands are `#bp.aardwolf.mapper.<command>`.

| Command | Output |
| :--- | :--- |
| `importmush <path>` | Copy a MUSHclient `Aardwolf.db` into the map, with progress lines and a summary. |
| `shops [here\|<area>]` | The rooms of an area with a `shop` or `bank` detail. |
| `train [here\|<area>]` | The rooms of an area with a `trainer` detail. |
| `quest [here\|<area>]` | The rooms of an area with a `questor` detail. |
| `notes [here\|<area>]` | The rooms of an area that have a note, with the note text. |
| `cexit <command> [-l LEVEL] [-T SECONDS] [-t TOUID] [-f FROMUID]` | Record a custom exit, or add it with `-t`. |
| `cexits [here\|thisroom\|<area>]` | The custom exits of the current area, the current room or an area. |
| `cexitdel [command]` | Delete a custom exit of the current room, or all of them. |
| `cexitpurge [here\|all\|<area>] [-c]` | Count, or with `-c` delete, the custom exits of an area or of every area. |
| `lockexit [exit] [-r ROOM] [-l LEVEL]` | List the exits of a room, show the lock of one, or set it. |
| `portal <command> [-l LEVEL] [-t TOUID] [-r]` | Add a portal that leads to a room. |
| `portals [filter]` | The numbered portals and recalls, sorted by area. |
| `portalchange <#N\|command> <new command>` | Change the command of a portal. |
| `portallevel <#N\|command> <level>` | Set the level a portal needs; 0 for none. |
| `portalrecall <#N\|command>` | Switch a portal between portal and recall. |
| `portaldel <#N\|command>` | Delete a portal. |
| `portalpurge [-c]` | Count, or with `-c` delete, every portal and recall. |

A search defaults to `here`, the area of the current room, and fails with "the current room is not
known" when there is none. An area id is lowercased and matched exactly. The table follows the core
`find` command, in room uid order:

```text
Mapper shops in aylor: 2 rooms
uid | name | area | found
32418 | The Aylor Bank | aylor | Bank
```

The detail searches match the comma separated details of a room, whether it was captured from GMCP or
imported. An area with no stored rooms reports "area <x> has no mapped rooms"; an area with no match
reports "No shops found in aylor".

### Custom exits, locks and portals

- **Recording.** `cexit open north;wait(2);north -l 50` needs a known current room and no other
  recording. Every `wait(N)` must be over 0 and at most 40, and a bad command is refused before
  anything is sent. The command is sent the way a walk sends it. The next room that differs from the
  one it left stores the exit, at cost 1, with the requirement of `-l`, and the client gets
  `Mapper: custom exit <from> (<command>) -> <to>`. With no new room after the timeout
  (`-T`, 2 to 40 seconds, default 5, plus the waits) the client is told and nothing is stored. An
  exit that leads back to the same room therefore times out.
- **Direct.** With `-t` the exit is stored from `-f` (default the current room) to that room and
  nothing is sent. Both rooms must be known and differ.
- **`cexitpurge`.** Without `-c` it only counts. With `-c` the removal runs in short slices, so
  `all` does not stall the proxy.
- **`lockexit`.** With no exit it lists the room's exits and their levels. With an exit and no `-l` it
  shows the level. `-l N` keeps the target and cost and sets the level; `-l 0` removes the lock.
- **`portal`.** The target defaults to the current room. `--recall` stores the portal as a recall.
  Adding a command under the other kind removes the old one. `portals` numbers the full list, and a
  filter (part of an area id) keeps those numbers. `#N` or the exact command, in quotes when it has
  spaces, names a portal in the other portal commands. `portalpurge` and `cexitpurge` need `-c`.
- **Bounce.** There are no bounce portal or bounce recall commands: the core path search already
  picks the cheapest portal or recall to leave a `noportal` or `norecall` room.

### Importing a MUSHclient map

- **Path.** One argument, an absolute path or one starting with `~` (the home directory of the user
  running the proxy). Quote a path with spaces. A relative path is refused, because the proxy's
  working directory means nothing to a client.
- **Read-only and checked first.** The file is opened read-only and validated before anything is
  written: a file that is not SQLite, or lacks the `rooms`, `exits` or `areas` tables and their
  columns, is refused and nothing is written. Older databases without `noportal`, `norecall`,
  `exits.level` or `bookmarks` import too.
- **Captured data wins.** The import only fills gaps, so importing again is safe and writes nothing.
  An area is added only when unknown. A room is added only when unknown; a stored room only gains the
  `norecall` and `noportal` flags it lacks. A stored exit keeps its target (unless unexplored), its
  requirement (unless it has none) and its cost. A note is set only when the room has none.
- **Progress.** The client gets `Mapper import: <phase> <done>/<total>` at the start of the areas,
  rooms and exits phases and every 2000 items, then a summary. Only one import runs at a time.

| MUSH | Mapper |
| :--- | :--- |
| `rooms` name, area, terrain, x, y, z | the same room fields |
| `rooms.info` | `details["details"]`, the shape of a captured room |
| `rooms.noportal`, `rooms.norecall` | the `noportal` and `norecall` flags |
| `exits` dir, fromuid, touid | an exit; `*` and `**` portals and recall carry over |
| `exits.level` above 0 | the requirement `{"level": n}` |
| `bookmarks.notes`, else `rooms.notes` | the room note |
| `areas` name, flags, texture, color | the area name, flags and details |

A room whose uid is not a positive integer (such as `nomap_...`), and its exits and notes, is skipped
and counted, as are exits to or from a room that is not imported.

**Not imported:** `storage` (the bounce portal and bounce recall, which are serialised Lua; the core
path search chains recall and portals itself, so no setting is needed), `environments`, `rooms.building` and `ignore_exits_mismatch`.

## Events used

| Event | Use |
| :--- | :--- |
| `ev_plugins.aardwolf.move_room` | store the room entered and make it current |
| `ev_libs.net.mud_gmcp_room.info` | take the first room when there is no current room |
| `ev_libs.net.mud_gmcp_room.area` | store the area the MUD sent |
| `ev_plugins.client.mapper_room_mismatch` | tell the client about a contradicting room |
| `ev_libs.net.mud_muddisconnect` | forget the room, the pending areas and waiting commands |
| `ev_plugins.client.mapper_walk_failed` | drop the commands still waiting after a wait |
