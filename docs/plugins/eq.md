---
title: The eq Plugin
description: Keep track of the items an Aardwolf character wears, carries, keeps on the keyring and stores in the vault, and raise the changes as events
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - eq
---

# The eq Plugin

The `eq` plugin keeps a cache of the items of the character and where each one is: worn, in the
inventory, in a bag, on the keyring or in the vault. It reads them from Aardwolf's `eqdata`,
`invdata`, `keyring data` and `vault data` commands, which it sends through the mudcmds queue, and
keeps them current from the `{invmon}` and `{invitem}` lines. It raises an event for each change
and answers questions about the items through APIs. The state is kept in memory only.

It also shows the worn and carried items as tables, with the `eq` and `inv` commands; see
[Commands](#commands).

## Loading

The plugin id is `plugins.aardwolf.eq`:

```text
#bp.core.pluginm.load plugins.aardwolf.eq
```

It depends on the events, triggers, mudcmds, commands and colors core plugins and on the
[connect plugin](connect.md). It never imports another plugin: the [eqdb plugin](eqdb.md) is
called through its API, and only when it is loaded.

The plugin turns on Aardwolf's invmon tags when it loads, by asking the `a102` plugin for option 102
feature `INVMONTAGS` (20), the setting the `invmon` command toggles. It takes the request back when
it unloads. The old plugin left this to the player. The `{invmon}` and `{invitem}` lines are
kept from the client: the plugin still reads them, and other lines are shown as usual.

## Behaviour

- **Containers.** `Inventory`, `Worn`, `Keyring` and `Vault`, and one container per bag the
  character carries, named by the serial of the bag as text. An item is in one place: a move takes
  it out of wherever it was. An item that was only seen in an `{invitem}` line has no place yet.
- **Items are plain dicts.** The keys are `serial`, `shortflags`, `cname` (with colour codes),
  `name` (without), `level`, `itype`, `unique`, `wearslot` and `timer`, plus `container` (the
  container id or `None`), `origcontainer` (where `item.fetch` took it from), `hasbeenided` and
  anything `item.identify.add` merged in. The APIs return copies.
- **Item lines.** `serial,shortflags,cname,level,itype,unique,wearslot,timer`. The name is taken
  greedily, so a name that has commas is kept whole. Aardwolf sends its colour codes in the name
  as text (`@WGueldar's@w ...`), and the proxy's colour coded copy of the line escapes each `@` as
  `@@`, so `cname` turns `@@` back into `@`.
- **Data commands.** Four mudcmds types, `eq_worn` (`eqdata`), `eq_inventory` (`invdata`),
  `eq_keyring` (`keyring data`) and `eq_vault` (`vault data`), plus one `eq_container_<serial>`
  (`invdata <serial>`) for each bag. The names carry an `eq_` prefix because type names are global.
  The tag triggers `{invdata}`, `{invdata <serial>}`, `{eqdata}`, `{keyring}` and `{vault}` are
  always on. The start tag turns the item line trigger on and the end tag turns it off. The lines
  are kept until the end tag, which replaces the contents of the container in one step. This
  happens for a typed command too.
- **Hiding.** A queued data command is hidden and a typed one is shown in full, though both update
  the state; the old plugin hid by trigger omission instead. Each type hides from its start tag to
  the first prompt after the command finishes at its end tag, and that prompt is hidden too, so a
  refresh leaves no stray prompts. For the vault this also hides
  `{vaultcounts}...{/vaultcounts}`, which comes after `{/vault}`. Without prompt marking
  (promptfix not loaded) a window closes at the end tag and the prompt is shown.
- **Bags.** A bag (item type 11) gets a container and a type the first time it is seen in any
  read (worn, inventory, keyring, vault or another bag), and its contents are queued. Both go when
  the bag leaves the inventory.
- **Reading.** When the character becomes active, and for `refresh`, the plugin queues worn,
  inventory and keyring, then the vault when GMCP `room.info.details` contains `bank`, then the
  bags. A missing value is not a bank. A mismatch that `invmon` shows queues the containers
  involved again.
- **No vault.** A character without a vault gets "You do not have a vault." instead of a vault
  block. That line finishes the vault read at once and records an empty vault. When the read was
  queued, the line and its prompt are hidden.
- **Death.** The `^You die\.$` trigger (`eq_dead`, the line is still shown) forgets what is worn
  and carried: Worn, Inventory, Keyring, the bags and their items. The vault stays, with its
  counts, whether it was read and the bags in it, because it lives in the bank and death cannot
  change it. Eq then drops a block being read and queues the same reads as `refresh`. The reads
  are queued at once. This is inferred, not checked live: Aardwolf prints `You die.` from inside
  its death routine and reads the next command only on a later pulse, after the corpse is made, so
  `eqdata` and `invdata` sent after the line are answered with the inventory after death.
- **Disconnect.** The state is cleared, a block that was being read is dropped and the bag types
  are removed.

### invmon

`{invmon}action,serial,container,location`. An action not listed is logged at debug level and
ignored; a line with anything but integers does not match.

| Action | Meaning | Expected place | Event |
| :--- | :--- | :--- | :--- |
| 1 | take off | in Worn: goes to the front of the inventory and `lastworn` is noted | `eq_removed` |
| 2 | wear | in Inventory: goes to Worn at `location` | `eq_worn` |
| 3, 7 | left the inventory, consumed | in Inventory: dropped from the cache; a bag also drops its container and what it held | `eq_inventory_removed` |
| 4 | added to the inventory | in the cache: goes to the front; a bag gets a container and a read | `eq_inventory_added` when cached, and `eq_put` with container `Inventory` always |
| 5 | taken out of a bag | the bag is known and holds it: goes to the end of the inventory | `eq_taken` |
| 6 | put into a bag | in Inventory and the bag is known: goes to the front of the bag | `eq_put` |
| 9 | put into the vault | in the cache: goes to the end of the vault | `eq_put` with container `Vault` |
| 10 | taken from the vault | in the vault: goes to the front of the inventory | `eq_taken` with container `Vault` |
| 11 | put on the keyring | in Inventory: goes to the front of the keyring | `eq_put` with container `Keyring` |
| 12 | taken off the keyring | on the keyring: goes to the front of the inventory | `eq_taken` with container `Keyring` |

When the item is not where the table expects it, the containers involved are read again. A bag that
is not known yet is created and read. A put into a container clears `origcontainer` when it is the
place the item came from, and so does wearing an item that came from Worn.

The action numbers 9 to 12 and which of them are followed by a 3 or a 4 were taken from the old
plugin and have not been checked against Aardwolf; see the live check in the pull request.

## MUD output

The forms below are the ones the plugin matches. The item values are made up.

```text
{eqdata}
1001,KG,a test sword,25,5,0,24,-1     # serial,flags,name,level,itype,unique,wearslot,timer
{/eqdata}
{invdata}                             # {invdata 2002} for a bag
{/invdata}
{keyring}
{/keyring}
{vault}
{/vault}
{vaultcounts}1,1,50{/vaultcounts}     # items, total, maximum; after {/vault}
You do not have a vault. See 'help vault' for how to acquire one.   # vault data, no vault
You die.                              # the death message
{invitem}6001,,a new thing,3,6,0,-1,-1
{invmon}6,2001,2002,-1                # action,serial,container,location
```

## Events

| Event | Arguments |
| :--- | :--- |
| `ev_plugins.aardwolf.eq_worn` | `item`, `location` |
| `ev_plugins.aardwolf.eq_removed` | `item`, `location` |
| `ev_plugins.aardwolf.eq_inventory_added` | `item` |
| `ev_plugins.aardwolf.eq_inventory_removed` | `item` |
| `ev_plugins.aardwolf.eq_put` | `serial`, `container`, `item` (`None` when not cached) |
| `ev_plugins.aardwolf.eq_taken` | `serial`, `container`, `item` (`None` when not cached) |

The item is a copy. A listener registers to the one event name and filters on `serial` and
`container`; there is no event per serial.

## APIs

All are `plugins.aardwolf.eq:<name>`.

| API | Returns |
| :--- | :--- |
| `item.get(serial)` | a copy of the item, or `None`; the serial may be an int or text |
| `item.find.by.name(name)` | copies of the items with `name` in their name, case sensitive |
| `container.get(cid)` | `{cid, items}`, with `slots` for Worn and `counts` for Vault, or `None`; `items` are serials |
| `eq.worn.get(location)` | a copy of the item worn at a slot number or location name, or `None`; never raises |
| `item.fetch(serial)` | `True` when the item is known: sends the command that takes it out of its container and notes where it came from |
| `item.put(serial, container=None, location=None)` | the container id, or `None` when nothing was done: puts the item in `container`, or back where it came from, fetching it first when it is in another container |
| `item.equip(serial, location=None)` | `True` when it was sent; a `location` of `lastworn` uses the place it was last worn |
| `item.unequip(serial)` | `True` when the item is worn and the remove was sent |
| `item.identify.add(serial, attributes)` | `True` when the item is known: merges the attributes except the place keys (`container`, `origcontainer`, `hasbeenided`) and `serial`, sets `hasbeenided` and saves a copy through `plugins.aardwolf.eqdb:item.save` when that API exists. The saved copy has no place keys, and the attributes are laid over it, so an identify `container` detail (capacity and so on) is saved as the detail, not as the place |

`eq.worn.get` is the API the [mobk plugin](mobk.md) calls, by the name in its `EQ_WORN_API`. It
returns a dict with a `serial`.

Commands go to the MUD with `SendDataDirectlyToMud`.

## Commands

| Command | Does |
| :--- | :--- |
| `#bp.aardwolf.eq.refresh` | queues worn, inventory, keyring, the vault in a bank, and the bags |
| `#bp.aardwolf.eq.icache <serial>` | shows `Item <serial>` and one sorted `key: value` line per field, or says it is not cached or not a serial |
| `#bp.aardwolf.eq.get <item> [words]` | with a known serial, fetches the item; otherwise sends `get <item> [words]`, quoting words that hold spaces |
| `#bp.aardwolf.eq.put <item> [bag]` | with a known item and no bag, puts it back where it came from; with a known bag serial, puts it there; otherwise sends `put <item> [words]` |
| `#bp.aardwolf.eq.eq [-n] [-c] [-s]` | shows what is worn, one row per slot with its location, flags, level and name. `-n` leaves out the flags, `-c` adds the score and `-s` the serial. Empty optional locations (the medals, `second`, the floating, tattoo, `above`, `portal` and `sleeping` slots) are hidden, and so are the empty `shield` and `hold` while `second` is filled |
| `#bp.aardwolf.eq.inv [container] [-n] [-c] [-s] [-g]` | shows `Inventory` (the default), `Worn`, `Keyring`, `Vault` or the bag with that serial; names are not case sensitive. Identical items (same name, flags and level) fold into one row counted as `(  n)`, with the serial `Many` under `-s`; `-g` turns grouping off. The inventory ends with the keyring count and, once the vault was read and it holds items, the vault counts. An empty container says `You have nothing in <container>`, an unread vault says to go to a bank and use `#bp.aardwolf.eq.refresh`, and an unknown container says `container <x> does not exist` |

## From the old plugin

| Old | New |
| :--- | :--- |
| `eq.getitem` | `plugins.aardwolf.eq:item.get` |
| `eq.getcontainer` | `plugins.aardwolf.eq:container.get` |
| `eq.findname` | `plugins.aardwolf.eq:item.find.by.name` |
| `eq.getworn` | `plugins.aardwolf.eq:eq.worn.get` |
| `eq.get` | `plugins.aardwolf.eq:item.fetch` |
| `eq.put` | `plugins.aardwolf.eq:item.put` |
| `eq.equip`, `eq.unequip` | `plugins.aardwolf.eq:item.equip`, `item.unequip` |
| `eq.addidentify` | `plugins.aardwolf.eq:item.identify.add` |
| `eq.itemclass` | dropped; an item is a dict, and `plugins.aardwolf.eqdb:item.get` returns a saved one |
| event `eq_worn`, `eq_removed` | `ev_plugins.aardwolf.eq_worn`, `eq_removed` |
| event `eq_inventory_added`, `eq_inventory_removed` | `ev_plugins.aardwolf.eq_inventory_added`, `eq_inventory_removed` |
| events `eq_put_<serial>_<cid>`, `eq_put_Inventory_<serial>`, `eq_put_<serial>_Vault`, `eq_put_<serial>_Keyring` | `ev_plugins.aardwolf.eq_put`, with `serial` and `container` |
| event `eq_remove_<cid>_<serial>` | `ev_plugins.aardwolf.eq_taken`, with `serial` and `container` |
| `cmdq.addcmdtype`, `cmdq.addtoqueue` | `plugins.core.mudcmds:type.add`, `command.queue` |
| `afterfirstactive` | the `character_active` plugin hook |
| commands `eq`, `inv` | the same names |
| `Item.score` default `Unkn` | a display-only default, `Unkn` when an item has no `score` |
| commands `refresh`, `get`, `put`, `icache` | the same names |
| `dead`, event `trigger_dead` | the `eq_dead` trigger, which eq handles itself |

## Changes from the old plugin

- **Fixed: bad invmon data.** The error was logged but the code went on with unbound variables.
  Now it is logged and the line is dropped, and the trigger takes only integers.
- **Fixed: wear slot 0.** An item in slot 0 skipped a delete and shifted every slot by one, and a
  missing place raised a `TypeError`.
- **Fixed: removing a missing item from Worn,** which caught the wrong exception and set the
  container to a string.
- **Fixed: container removes.** A missing item raised a `ValueError` that the actions did not
  catch, and an unknown bag raised again inside its own fallback.
- **Fixed: vault put.** The item stayed in the inventory, and one that was not cached raised.
- **Fixed: vault take.** The item was never added to the inventory, and a missing one raised.
- **Fixed: no vault.** The old plugin waited for a vault block that never came for a character
  without a vault, and the old queue had no timeout, so the queue stopped. The no-vault answer now
  ends the read.
- **Fixed: events.** Taking from the vault or the keyring raised nothing, and the names used three
  orders. There are now six fixed names.
- **Fixed: a removed bag.** Its command type and the items in it stayed behind.
- **Fixed: `eq.get`.** An item with no container, or a serial that was not a number, raised.
- **Fixed: `put <item> <bag>`.** With both known it passed a serial where a container was needed
  and always raised, and the raw fallback sent the item twice.
- **Fixed: `lastworn`.** It added a string to an int and stored a slot number where Aardwolf wants
  a location name.
- **Fixed: `getworn`.** A digit string indexed the list with text, and an empty slot given by name
  looked up the item `-1`.
- **Fixed: the vault without GMCP `room.info`** raised.
- **Fixed: `eq.addidentify` and the place.** The old plugin kept an item's place as an object, so
  an identify could not overwrite it. In the port the place is the `container` string, and eqdb
  reads a `container` key as the container detail (a mapping), so saving an item that had a place
  raised inside eqdb and the identify was lost. The place keys are no longer overwritten by an
  identify, and the copy saved to eqdb leaves them out.
- **Fixed: `origcontainer`** was never cleared, so a later put sent the item to an old place.
- **Fixed: a put into the inventory** sent `put <serial> Inventory`; now it only fetches.
- **Changed: death.** The old handler emptied the containers without a read, and nothing in this
  repo raised `trigger_dead`, so #75 (plan item 18) dropped it. Aardwolf leaves many items in the
  corpse, so eq now has its own `^You die\.$` trigger. Unlike the old handler it keeps the vault
  and reads everything else again; unlike #75 it does not leave the state stale until the next
  connect. The timing of the reads is inferred, not checked live (see Death above).
- **Fixed: vault counts compared as strings.** The old inventory showed the vault line even for an
  empty vault (a string is always above an int in Python 2), and the keep-flagged line compared the
  total with the item count as text, so `10` was not above `9`. Both compare ints now.
- **Dropped: the Python 2 `print item`** in the worn row, which ran inside a broad `except`.
- **Fixed: the unread-vault message** named `#bp.eq.refresh -c Vault`, an option `refresh` never
  had. It now says `#bp.aardwolf.eq.refresh`.
- **Fixed: the vault message** was one entry holding newlines and a trailing blank; it is separate
  lines now.
- **Fixed: `@x` with no digits** in the header flag cells and the location cell, which the colour
  tokenizer drops as invalid. They use `@w`.
- **Fixed: the rule line** left its blue colour on; it ends with `@w`.
- **Dropped: the debug `send.msg` output** that `build`, `cmd_eq` and `cmd_inv` printed on every run.
- **Fixed: bags by serial.** The old command turned the container into an int to find a bag; bag
  ids are strings now, and the serial is normalised.
- **Changed: container names are not case sensitive,** so `inv vault` and `inv keyring` work.
- **Changed: a character with no vault** sees an empty vault, not "has not been refreshed". The
  state has a new `vault_read` flag, set when a vault read ends (including the no-vault answer) and
  cleared on reset, because `vault_counts` is `None` in both cases.
- **Dropped: dead code.** The four `badinvdata` triggers, which had no callbacks, `checkvaliditem`,
  `queue`, `currentcmd` and the `*all` flags.
- **Dropped: `find_item` identifiers.** The old plugin mapped the word `tokenbag` to the serial of
  one character's item. A word that is not a serial is now sent to the MUD as it is.
- **Changed: invmon.** The plugin turns on the invmon tags itself, through `a102`'s
  `INVMONTAGS`, instead of relying on the player to type `invmon`, and hides the `{invmon}` and
  `{invitem}` lines from the client. The old plugin showed them.
- **Changed: typed data commands.** A typed `eqdata` or `invdata` also updates the state, and is
  shown in full, because mudcmds never hides a typed command.
- **Changed: a new bag is read when first seen,** and each bag has its own command type, so a typed
  `invdata` cannot open the hide window of a queued `invdata <serial>`. As in the old plugin this
  covers bags in Worn, on the keyring and in the vault. Nobody has checked whether Aardwolf
  answers `invdata <serial>` for a bag in the vault or on the keyring; a refusal is shown and the
  mudcmds timeout frees the queue.
- **Known issue of `itemu`, not fixed here.** `itemu.parse_item_data` splits the comma `eqdata`
  layout on every comma, so a name with a comma is misparsed. The eq plugin does not use it for
  item lines.
