---
title: The itemkeep Plugin
description: Keep Aardwolf items of chosen types automatically when they reach the inventory
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - itemkeep
---

# The itemkeep Plugin

The `itemkeep` plugin sends `keep <serial>` for an item of a chosen type when the item reaches the
inventory and is not already kept. It is ported from the `itemkeep` plugin of the old bastproxy.

## Loading

The plugin id is `plugins.aardwolf.itemkeep`:

```text
#bp.core.pluginm.load plugins.aardwolf.itemkeep
```

It depends on the events, settings, triggers and mudcmds core plugins and on the [eq plugin](eq.md).
It never imports another plugin: it keeps its own copies of the eq event names. It is not required,
so it does not load until asked.

## Behaviour

- It listens to four eq events, `eq_inventory_added`, `eq_taken`, `eq_removed` and
  `eq_inventory_removed`, each carrying the item as a dict. The first three queue a keep;
  `eq_inventory_removed` only makes the plugin forget the serial. An item that is not a dict (eq
  did not know it) is skipped.
- The item's `itype` names its type. When the setting for that type is on and the item's
  `shortflags` has no `K`, the plugin queues `keep <serial>`.
- **The `K` guard.** An item already kept is skipped. Aardwolf follows a keep with an
  `{invitem}` line carrying the `K` flag, and eq updates its cached item from it. The plugin also
  remembers the serials it sent `keep` for and skips them, so a second item event before that
  line arrives sends no second `keep`. A second `keep` would do no harm: Aardwolf's `keep` does not
  toggle, it answers that the item is already kept. An entry is forgotten when eq raises
  `eq_inventory_removed` for its serial (invmon 3 or 7: dropped, given, sold or consumed), and the
  whole memory is cleared on disconnect. So an item you unkeep, drop and pick up again is kept
  again. An unkept item that stays with the character (worn, or moved through a bag, the keyring
  or the vault) stays unkept.
- **The `keep` is a hidden queued command.** It goes through the mudcmds queue as the type
  `itemkeep_keep`, so the client does not see the command's reply. The hide window opens at the
  reply line and closes at the prompt after the command finishes, so that prompt is hidden too,
  as in eq and itemid. A `keep` you type yourself is never hidden or parsed.
- **Finishing.** A trigger group is on only while the command is in flight. A reply line finishes
  the command. When no reply matches, the mudcmds timeout frees the queue and the group is turned
  off.
- Logging in does not keep anything: eq's first read of the inventory raises no events.

## Settings

There is one setting per item type, 25 in all, each false by default. A type with a space in its
name uses an underscore, so `raw material` is `raw_material`. The type `none` has no setting.

```text
#bp.aardwolf.itemkeep.set weapon true
#bp.aardwolf.itemkeep.set raw_material true
#bp.aardwolf.itemkeep.list
```

## MUD output

The replies are the lines that finish the queued `keep` and open its hide window. The regexes are
in `src/aardwolf/itemkeep/libs/_itemkeep.py` (`KEEP_REPLIES`):

```text
Keep status added to torch.
**NOTE: This is NOT the same as a 'keepflag' which is a trivia point
        option that makes an item not count towards your item limit.
{invitem}3001,KG,a torch,1,1,0,-1,-1
Your white Piano Key is already kept. Use 'unkeep' to remove it.
You do not have that item.
```

These were recorded on a live character. The first line of each reply finishes the command; the
note lines and the `{invitem}` line that follow a keep are hidden with the reply, up to and
including the prompt. A reply that matches none is shown to the client and the timeout ends the
command.

## Events

The plugin listens only. It raises no events.

## Commands

None beyond the settings commands `set` and `list`.

## Changes from the old plugin

1. A setting was added for every object type, including `none`. The port drops `none`.
2. `raw material` contains a space, so it could not be named in the set command. It is now
   `raw_material`.
3. `itemtypesrev[item.itype]` raised `IndexError` for an out-of-range itype, accepted a negative
   one, and did not handle a non-int. A bool, a non-int, 0 and an out-of-range itype are now
   skipped with a debug log.
4. The item was read through attributes (`item.itype`, `item.shortflags`). It is now a plain dict,
   and a missing key means no type or no flags.
5. `keep` went out as a visible plain send. It is now a hidden queued command.
6. Only `eq_inventory_added` was handled. Items taken from a bag, the vault or the keyring, and
   worn items taken off, are now covered too.
7. The class docstring said "handle aardwolf cp events".
8. The old plugin sent `keep` on every `eq_inventory_added` without `K`. The port remembers its
   keeps, forgets one when the item leaves the inventory, and so re-keeps only an item that left
   and came back.

The old `AUTOLOAD = False` is now `PLUGIN_REQUIRED = False`.

## Known gaps

- An item that leaves while eq did not have it in the inventory raises no `eq_inventory_removed`,
  so its entry stays until disconnect.
- An item whose serial eq has not cached when invmon 4 arrives is missed: eq raises only `eq_put`
  with no item and refreshes, and the refreshed read raises nothing.
- A `keep` reply other than the three recorded ones is shown, and the command waits for the
  timeout.
