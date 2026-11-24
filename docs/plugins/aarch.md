---
title: The aarch Plugin
description: Show which Aardwolf Aarchaeology items and pamphlets are still needed to complete the set
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - aarch
---

# The aarch Plugin

The `aarch` plugin reads the items the [eq plugin](eq.md) has cached, counts the Aarchaeology items
and Collectable Pamphlets, and lists the pieces of the 50 piece set that are still needed. It is
ported from the `aarch` plugin of the old bastproxy.

## Loading

The plugin id is `plugins.aardwolf.aarch`:

```text
#bp.core.pluginm.load plugins.aardwolf.aarch
```

It depends on the commands core plugin and on the eq plugin. It never imports another plugin: it
calls the eq API `plugins.aardwolf.eq:item.find.by.name` by name. It is not required, so it does
not load until asked.

## Behaviour

- The `need` command asks eq for the items with `(Aarchaeology)` in their name. eq searches its
  whole cache, so an item worn, in the inventory, in a bag, on the keyring or in the vault counts.
- A known piece counts as an item. A pamphlet numbered N counts as a pamphlet and as holding piece
  N.
- The first line gives the items held, how many of them are different, and the pamphlets. Then it
  lists each piece still needed as `number - name`, or says the set is full.
- A filter keeps the needed pieces with its words in their name, in any case.
- An `(Aarchaeology)` name that is not one of the 50 is listed as `Not a known piece: <name>`.

```text
You have 3 Aarchaeology items (2 different) and 1 Pamphlets
You need 47 pieces, 1 match 'skull':
2  - An Ancient Skull
```

## Commands

| Command | What it does |
| :--- | :--- |
| `need [filter ...]` | Lists the pieces still needed; the words of the filter are joined. |

```text
#bp.aardwolf.aarch.need
#bp.aardwolf.aarch.need ancient skull
```

## MUD output

The plugin sends no MUD command and has no triggers, so it needs no mudcmds command type. The old
plugin also sent nothing: it read the items from the eq plugin's cache.

## Events

The plugin listens to and raises no events. It has no settings.

## From the old plugin

The old plugin had the `need` command only, with the 50 pieces in a table and `eq.findname` to
read the cache.

## Changes from the old plugin

1. The filter was compared as typed against lower case names, so `need Skull` matched nothing. Both
   are lower cased now.
2. A pamphlet without a number, or with text after it, raised an error (`int(name.split('#')[1])`).
   The number is read with a regex; a pamphlet without one counts as a pamphlet and adds no piece.
3. With a filter the header said `You need 45 pieces:` and listed only the matches. It now says
   `You need 45 pieces, 2 match 'skull':`, or `none match 'skull'`.
4. A duplicate item counted in the held count, hiding that it adds nothing. The line now also gives
   the number of different items.
5. An `(Aarchaeology)` item not in the table was dropped silently. It is now listed.
6. The name was matched after removing the tag with one exact space, and case sensitively. Spaces
   are collapsed and the lookup ignores case.
7. "Aarcheology" is spelled "Aarchaeology".
8. A filter of several words was an error (`nargs='?'`); the words are joined.
9. `AUTOLOAD = False` is now `PLUGIN_REQUIRED = False`, and `dependency.add` is
   `PLUGIN_DEPENDENCIES`.

## Kept as it was

A pamphlet numbered N counts toward piece N, as in the old plugin. Please confirm that this is how
the Collectable Pamphlets work on Aardwolf.

## Known gaps

- Before eq's first read of the inventory its cache is empty, so every piece shows as needed.
- eq's search is case sensitive on the tag, so only names with `(Aarchaeology)` as written are
  found.
