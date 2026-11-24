---
title: The itemid Plugin
description: Identify an Aardwolf item with invdetails and identify, hand the result to eq and eqdb, and show it as an item box
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - itemid
---

# The itemid Plugin

The `itemid` plugin identifies an item. It sends `invdetails <serial>` and `identify <serial>`
through the mudcmds queue, reads both replies into one plain dict in the shape the
[eqdb plugin](eqdb.md) saves, hands it to the [eq plugin](eq.md), and raises one event when the
item is identified and back where it was. It also keeps the `id` command and the formatted item
box.

## Loading

The plugin id is `plugins.aardwolf.itemid`:

```text
#bp.core.pluginm.load plugins.aardwolf.itemid
```

It depends on the events, triggers, mudcmds, commands and colors core plugins and on the
[eq plugin](eq.md). It never imports another plugin: it keeps its own copies of the eq, eqdb and
skills API and event names, the way the [mobk plugin](mobk.md) does, and imports only
`aardwolf.libs.itemu`. The eqdb and skills plugins are optional and are called only when their API
exists.

## Behaviour

- **Queued commands only.** The reply is read only for a command this plugin queued. The trigger
  groups are turned on when the queue sends the command and off when it ends. A typed `invdetails`
  or `identify` is not parsed and is shown in full.
- **Hiding.** Each type hides from its first line and has no end line, so the window closes at the
  prompt after the command finishes and the prompt is hidden too, as eq does. Hiding is done by
  mudcmds, not by trigger omission.
- **Matching a reply to its serial.** The plugin keeps a first-in first-out list of the serials it
  queued, and does not queue one that is already pending. Both replies read the head of the list.
  The identify finish or its timeout takes the serial off. An `invheader` whose serial is not the
  head is logged and dropped.
- **invdetails.** The lines are `{header}data`, from `{invdetails}` to `{/invdetails}`. The header
  picks the layout in `aardwolf.libs.itemu`. Stat, resist and skill mods become `{name: int}`,
  enchants and temporary mods are lists, and everything else is a dict under its header. A line that
  does not parse is logged and skipped.
- **identify.** One catch-all trigger feeds a reader. Every line before the first divider is
  ignored, so a prompt left over from the command before cannot start or end the read. After the
  first divider a divider or a `|...|` line is data, and any other line, a blank line or a prompt,
  ends the read. The reader keeps Keywords, Found at, Material, Leads to, Affect Mods and Reward,
  joins their continuation lines, and takes every line that follows a divider with no label as a
  note. The labels invdetails already gave are skipped, and any other label is logged.
- **The item.** The two replies are joined into one dict: keywords split on spaces, flags and
  affect mods on `", "`, the reward as `{"rtext": ...}` and the notes as `{"ntext": ...}`. `cname`
  and `name` come from eq's copy of the item. The temporary mods stay in this plugin's cache and are
  not given to eq or eqdb, which have no table for them.
- **Identified means cached.** The plugin keeps its own cache, serial to item, cleared on
  disconnect, and an item is identified when it is in it. eq's `hasbeenided` is not consulted.
- **Saving.** The item goes to `plugins.aardwolf.eq:item.identify.add`, which saves it through eqdb.
  When eq does not know the item and eqdb is loaded, this plugin calls
  `plugins.aardwolf.eqdb:item.save` itself.
- **Fetch and put back.** An item that is not in the inventory is fetched first with
  `plugins.aardwolf.eq:item.fetch`, so a worn item is removed. The plugin notes where it came from
  itself, and after the identify calls `item.put` to put it back. The event waits for the put:
  `eq_put` with the same serial and container, or `eq_worn` for that serial when the item was
  worn. It is raised at once when nothing was fetched, when `item.put` returns `None`, or when the
  item is already back. A waiting item is also released by `eq_inventory_removed` for it, and
  everything is cleared on disconnect.
- **Failures.** A reply that never starts, such as a bad serial or an item that cannot be reached,
  ends at the mudcmds command timeout. The invdetails timeout drops what was read and turns the
  group off; its identify is still queued, so the serial stays pending, and an identify that
  finishes with no invdetails result is logged and not merged. The identify timeout turns the group
  off, takes the serial off the list and puts the item back, with no event.

## Events

| Event | Arguments |
| :--- | :--- |
| `ev_plugins.aardwolf.itemid_identified` | `serial`, `item` (a copy of the identified item) |

One event for every item. A listener filters on `serial`; there is no event per serial.

## APIs

All are `plugins.aardwolf.itemid:<name>`.

| API | Does |
| :--- | :--- |
| `item.identify(serial, force=False)` | returns a copy of the cached item, or queues invdetails and identify and returns `None`; the event says when it is done |
| `item.format(item, location=None)` | returns the lines of the item box; the location defaults to where eq has the item |
| `item.show(serial, database=False)` | sends the item box to the client; an uncached item is identified first. With `database` the item is read from eqdb |

## Commands

| Command | Does |
| :--- | :--- |
| `#bp.aardwolf.itemid.id [serial] [-f/--force] [-d/--database]` | shows the item box, identifying the item first when it is not cached; `-f` identifies again, `-d` reads eqdb and needs no eq entry |

The messages are `Please supply a serial #`, `<x> is not a serial number`, `Could not find <n>`
(eq does not know the item and it is not cached), `<n> is not in the database`, `The eqdb plugin
is not loaded, so there is no database to read` and `Could not identify <n>`.

## MUD output

The forms below are the ones the plugin reads. The values are made up.

```text
{invdetails}
{invheader}1001|50|5|12000|7|wielded|glow, hum|Nobody|Example|-1|0|0|0|123
{statmod}Strength|2
{weapon}dagger|17|Slice|Pierce|sharp
{/invdetails}
+-----------------------------------------------------------------+
| Keywords   : gleaming test blade                                |
| Name       : a gleaming test blade                              |
| Id         : 1001                                               |
+-----------------------------------------------------------------+
| Material   : steel                                              |
+-----------------------------------------------------------------+
|   A synthetic note.                                             |
+-----------------------------------------------------------------+
```

The item box is 67 columns wide. It shows the keywords, name, id and location, the type and level,
worth and weight, the duration of a light, the wearable slot, score, material, flags, owner, clan,
found at and leads to, the notes and affects, and a section for the container, weapon, portal,
stats, resists, skill mods, enchants, spells, food, reward, drink and furniture data the item has.

## From the old plugin

| Old | New |
| :--- | :--- |
| `eq.addidentify` | `plugins.aardwolf.eq:item.identify.add` |
| `eq.getitem` | `plugins.aardwolf.eq:item.get` |
| `eq.get`, `eq.put` | `plugins.aardwolf.eq:item.fetch`, `item.put` |
| `eq.itemclass` | dropped; an item is a dict, and `plugins.aardwolf.eqdb:item.get` returns a saved one |
| `cmdq.addcmdtype`, `cmdq.addtoqueue` | `plugins.core.mudcmds:type.add`, `command.queue` |
| events `itemid_<serial>`, `itemid_all` | `ev_plugins.aardwolf.itemid_identified`, with `serial` and `item` |
| `skills.gets` | `plugins.aardwolf.skills:skill.get` |
| API `itemid.identify`, `format`, `show` | `plugins.aardwolf.itemid:item.identify`, `item.format`, `item.show` |
| command `#bp.itemid.id` | `#bp.aardwolf.itemid.id` |

## Changes from the old plugin

Each of these was a bug in the old plugin unless it says changed.

- **Fixed: `format` crashed.** `item.itype.capitalize()` ran on an int type, so the box raised for
  every item with a type and level and `id` never showed anything. The type name now comes from
  the object type table.
- **Fixed: Light and Portal.** `itype == 'Light'` and `'Portal'` compared an int with a string, so
  "Duration: permanent" and the uses of a portal were never shown.
- **Fixed: zeros in the item.** `formatstats` and `formatresist` wrote a zero for every missing
  stat into the item's own `statmod` and `resistmod`, which then went into eqdb as zero rows.
  Formatting no longer changes the item.
- **Fixed: negative magic resists.** The magic resist rows were shown only when one was above
  zero, so negative-only resists were hidden.
- **Fixed: `xrange`.** The spells block raised a Python 2 `NameError`.
- **Fixed: float division.** `drink['liquidmax']/20` is a float in Python 3.
- **Fixed: a stale `currentitem`.** An invdetails with no invheader left the item before, so the
  identify was merged into, and credited to, the wrong serial. The reader starts empty every time,
  and an invheader for another serial is dropped.
- **Fixed: temporary mods.** The `tempmod` branch of `addmod` was never reached, so several lines
  overwrote each other. The port keeps a list. eqdb has no table for them, so they are not saved.
- **Fixed: unknown or bad serials.** `api_identify` and `cmd_id` raised `AttributeError` for a
  serial eq did not know, and `cmd_id` raised `ValueError` for one that was not a number, because
  the `except` was commented out. They now answer with a message.
- **Fixed: `id -d`** needed the item in eq's cache although it read the database.
- **Fixed: `show` from the database.** It identified the item when the database lacked it, and for
  an uncached item showed nothing and said nothing.
- **Fixed: missing fields.** `dataafter` raised a `KeyError` when `keywords` or `flags` were
  missing, and splitting on one space left empty keywords after a double space.
- **Fixed: a reply that never ends.** An identify with no blank line never finished, and the old
  queue had no timeout, so it stopped. The command now ends at the mudcmds timeout, and a prompt
  ends the read as a blank line does.
- **Fixed: timing.** `cmdq.cmdstart` ran on every divider, so the timing restarted. It runs once,
  when the queue sends the command.
- **Fixed: a worn item's event.** The put back of a worn item waited for `eq_put_<serial>_Worn`,
  which the old eq never raised, since a wear raised `eq_worn`. The event of a worn item never
  fired. It now waits for `eq_worn` with that serial.
- **Fixed: `origcontainer`.** The put back trusted it, and the old eq never cleared it, so a later
  identify of an inventory item could put it into an old bag. The plugin notes where it fetched the
  item from itself.
- **Fixed: notes with colour codes.** The notes were `colorline[1:-1]`, which cuts a colour code
  when codes come before the `|`. They are taken from the plain text.
- **Fixed: the waiting list.** `waitingforid` was keyed by whatever type the caller passed and
  deleted with `int(...)`. It was written and never read, and is gone.
- **Dropped: the `idcmd` setting,** which was never read, and the dead state `showid`,
  `fulllinelength`, `linelength` and `pastkeywords`.
- **Changed: events.** One event for every item replaces `itemid_<serial>` and `itemid_all`.
- **Changed: where the item is shown.** The location and the wear slot come from eq when the box is
  shown, not from the item.
- **Changed: the box layout.** Every line is now 67 columns wide. The enchant line that has
  "(removable by enchanter)" was longer than the box and is now shortened. The stat and resist
  tables are laid out on one column grid, so the header and the values line up, and the physical
  resists are shown when the item has any of them, as before.
- **Changed: line `{...}` with no data.** The invdetails line trigger needs some data after the
  closing brace, so the `{invdetails}` start tag is not read as a line.
- **Kept, and to check live: notes with a colon.** A line is a label when it has a colon and a
  character right after the space that follows the bar. A note written that way is read as a label
  and lost from the notes, as in the old plugin.

## Known gaps

These cannot be checked from code and need a live check on a character:

- The exact `{invdetails}` header names and fields, whether the `flags` field is separated by
  `", "`, and whether the name of a skill mod is the sn of the skill.
- Whether a blank line, or only the prompt, follows the last identify divider, trailing spaces on
  the `|` lines, the `Id` and `Reward.....` labels, and whether a continuation line repeats the
  colon of the label column (the reader strips one).
- What Aardwolf answers for an unknown serial for each command. The plugin relies on the timeout.
- Whether `invdetails` and `identify` work on worn and bagged items without fetching them. If they
  do, a follow-up could stop removing worn items.
- Items in a vault outside a bank, where the fetch fails and the read times out.
- A put back that the MUD refuses: the event then waits until disconnect.
