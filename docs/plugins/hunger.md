---
title: The hunger Plugin
description: Drink from a container when the Aardwolf character is hungry or thirsty
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - hunger
---

# The hunger Plugin

The `hunger` plugin drinks from a container you name when Aardwolf says the character is hungry or
thirsty. Orange juice satisfies both hunger and thirst (`help drink` on Aardwolf), so the plugin only
drinks. It has no eating.

## Loading

The plugin id is `plugins.aardwolf.hunger`:

```text
#bp.core.pluginm.load plugins.aardwolf.hunger
```

It depends on the events, settings, triggers, commands and timers core plugins, on the
[eq plugin](eq.md) and on the move plugin. It never imports another plugin: eq is used through its
APIs and events, and the mapper is optional. It is not required, so it does not load until asked.

## Behaviour

- **Stage lines.** Any of the six hunger or thirst lines (see below) makes the plugin drink, when the
  `drink` setting is on. It is off by default.
- **Fetch, drink, put back.** The container is taken out with eq's `item.fetch`, the plugin waits for
  the eq event `eq_taken` for that serial (eq moves the item only when the mud's `{invmon}` line
  arrives, and `item.put` returns early while it still thinks the item is in the bag), sends
  `drink <serial>`, and then calls `item.put`. When the container is already in the inventory, or eq
  knows no container for it, `drink` goes out at once with no put back. A timer of 10 seconds
  (`PENDING_TIMEOUT`) drops the action when no `eq_taken` arrives, and tells the client.
- **Cooldown.** After one attempt, stage lines wait `cooldown` seconds (default 60). The line that
  repeats while nothing is done therefore sets off one attempt, not a burst. Every stage line,
  "start to feel" included, waits out the cooldown. A line while a drink or fill is pending sends
  nothing.
- **Nothing left.** When the container is not found, or the mud says `<container> is empty.`, the
  client gets one message and the plugin does nothing more. The block is cleared by a change to the
  `container` setting, by eq reporting an item the setting resolves to (for a missing container), and
  by a successful fill (for an empty one).
- **The container.** The `container` setting is a serial (all digits, looked up with `item.get`), or a
  piece of the item's name for `item.find.by.name`. That match is case sensitive and matches part of
  the name. An item in the inventory wins, then one in a bag; worn, vault and keyring items are
  skipped.
- **Reply triggers.** The replies to a drink or fill the plugin sent are read by a trigger group that
  is on only while one is awaited. It is turned off by the reply or after 10 seconds. This keeps the
  broad `is empty` pattern from matching unrelated lines.
- **Fill source.** `fillsource` stores the room the character is in (the GMCP `room.info.num`, which
  is the mapper's uid) and, optionally, the source object. `fill` fills the container in that room.
  Elsewhere it walks there through the core mapper with `walk.start` and fills once on arrival.
  It refuses when the mapper is not loaded, the room is not mapped, or another walk is searching or
  walking. A failed or stopped walk is reported and nothing more is sent. A walk the player starts
  elsewhere cancels the pending fill; a manual `walkto` to the same room keeps it.
- **Automatic fill.** When the character enters the fill room and the last drink found the container
  empty, the plugin fills once. It does so only when the character is already there, and not when a
  fill walk is pending or a fill is under way, so an arrival at the end of a `fill` walk fills once,
  whichever of `move_room` and `walk_done` comes first.
- **Never travels by itself.** Only the `fill` command starts a walk. No trigger, timer, event or
  other plugin does, and tests check that.
- **Disconnect.** Clears the pending action, its timers, the reply triggers, the pending fill walk and
  the cooldown clock.

## Settings

| Setting | Default | Meaning |
| :--- | :--- | :--- |
| `drink` | `False` | Drink when hungry or thirsty. |
| `container` | empty | The container to drink from: its serial, or a piece of its name. |
| `cooldown` | `60` | Seconds to wait after a drink attempt, 1 to 3600. |
| `fillroom` | empty | The room uid of the liquid source. Set by `fillsource`. |
| `fillobject` | empty | The source object; empty lets the mud find it. Set by `fillsource`. |

```text
#bp.aardwolf.hunger.set drink True
#bp.aardwolf.hunger.set container 4521
```

## Commands

| Command | Meaning |
| :--- | :--- |
| `fillsource [object]` | Store the current room as the fill room, and the object when given; without one the object is cleared. `--show` shows the stored values. |
| `fill` | Fill the container here, or walk to the fill room and fill on arrival. |
| `status` | Show the plugin state. |

## Events used

- eq: `eq_taken`, `eq_put`, `eq_inventory_added`.
- move: `move_room`.
- mapper: `walk_started`, `walk_done`, `walk_failed`.
- `ev_libs.net.mud_muddisconnect` and `ev_plugins.aardwolf.hunger_var_container_modified`.

## APIs used

eq: `item.get`, `item.find.by.name`, `item.fetch`, `item.put`. Mapper (optional, found with
`api.exists`): `walk.start`, `walk.get`, `room.get`. GMCP `room.info.num`.

## MUD output

The stage lines, with the `##` the log shows after the colour is stripped (the plugin matches it as
an optional prefix):

```text
## You start to feel hungry.
## You are very hungry; your healing is reduced.
## You are starving; your healing is greatly reduced.
## You start to feel thirsty.
## You are very thirsty; your healing is reduced.
## You are dehydrated; your healing is greatly reduced.
```

The replies, recorded on a live character with a Sacramental Carafe of orange juice:

```text
You drink some orange juice from Sacramental Carafe.
Sacramental Carafe is empty.
You fill Sacramental Carafe with orange juice.
There is no liquid source here.
```

## Known gaps

- `drink <serial>`, `fill <serial>` and `fill <serial> <object>` still need a live check on
  Aardwolf. The live check used the keyword, and the two argument fill is unconfirmed.
- The name lookup is case sensitive.
- There is no eating.
