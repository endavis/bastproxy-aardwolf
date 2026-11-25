---
title: The ct Plugin
description: Show a table of the damage done, by damage type, after each Aardwolf mob kill
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - ct
---

# The ct Plugin

The `ct` plugin (the combat tracker) shows a table of the damage done after each mob kill. It
listens to the `mobk_kill` event of the [mobk plugin](mobk.md) and builds the table from the kill. It
is ported from the `ct` plugin of the old bastproxy.

## Loading

The plugin id is `plugins.aardwolf.ct`:

```text
#bp.core.pluginm.load plugins.aardwolf.ct
```

It depends on the events, settings, triggers, colors and utils core plugins and on the
[mobk plugin](mobk.md). It never imports another plugin: it keeps its own copy of the event name. It
is not required, so it does not load until asked. It has no commands and sends nothing to the MUD.

## Behaviour

- **A table for each kill.** The table is `linelength` columns wide (72 by default): a divider, a title with the mob name, the
  fight time and the experience, a header, one row for each damage type, and a `Total` row.
- **The time** is shown only when the kill has both a start and a finish time.
- **The rows** are sorted by damage type. A `backstab` entry with an `incombat` key is labelled
  `backstab (in)`.
- **Each row** shows the hits, the damage, its share of the total damage, the misses and the average
  damage per hit (a whole number, rounded down). The `Total` row is 100%; its average is the total
  damage divided by the total hits.
- **The table is shown at the next empty line**, not at once, so it does not land in the middle of
  the output of the kill. The old plugin did the same. Tables of kills that happen before that line
  are sent in the order of the kills. The plugin listens to empty lines only while a table waits.
- **No preamble.** The table goes to the clients without the plugin preamble.

### Example output

```text
------------------------------------------------------------------------
-----------------  the dwarven barkeeper : 06s - 72xp  -----------------
------------------------------------------------------------------------
Dam Type             :    Hits      Damage   (  0%)   Misses    Average
------------------------------------------------------------------------
backstab             :     2         982     ( 37%)     1         491
cleave               :     3         976     ( 37%)     2         325
pierce               :     2         665     ( 25%)     0         332
------------------------------------------------------------------------
Total                :     7         2623    (100%)     3         374
------------------------------------------------------------------------
```

## Settings

| Setting | Default | Meaning |
| :--- | :--- | :--- |
| `statcolor` | `@W` | the color of the stats |
| `infocolor` | `@x033` | the color of the dividers and the labels |
| `linelength` | `72` | the width of the table, 1 to 500; read for each kill, a value out of range is refused |

## Events

The plugin raises no event. It consumes `ev_plugins.aardwolf.mobk_kill`; the keys it reads are
`name`, `totalxp`, `damage`, `starttime` and `finishtime`.

## From the old plugin

| Old | New |
| :--- | :--- |
| event `aard_mobkill` | `ev_plugins.aardwolf.mobk_kill` |
| event `trigger_emptyline` | the empty line trigger `t_plugins.core.triggers_emptyline` |
| `utils.center` | `plugins.core.utils:string.center.colored` |
| `utils.timedeltatostring` | `plugins.core.utils:timedelta.to.string` |
| `setting.gets` | `plugins.core.settings:setting.get` |
| `send.client` with `preamble=False` | the same, through a directly sent `NetworkData` |

The old plugin showed the table on the next empty line, and so does the port. A live fight on a
real Aardwolf character confirmed that the table prints after the kill's lines.

Fixes in the port:

- **Sorting.** `tkeys = damages.keys(); tkeys.sort()` works only in Python 2. The port uses
  `sorted`.
- **Averages.** The old `/` was a floor division in Python 2. The port uses `//`, so the example
  above still gives 491, 325, 332 and 374.
- **No damage.** With a total damage of 0 the old plugin took the `ZeroDivisionError` path and sent
  an error message. The share is now 0 and there is no error.
- **Dead code.** The skip of the `enemy`, `starttime` and `finishtime` keys inside `damage` is
  dropped: mobk never puts them there.
- **Escaping.** The mob name and the damage types are escaped, so an `@` in them is not read as a
  color code. The label padding is counted on the raw text, so the columns stay aligned.
