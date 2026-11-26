---
title: The eqdb Plugin
description: Keep the character's identified items in a database, and give other plugins an API to save and get an item
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - database
---

# The eqdb Plugin

The `eqdb` plugin keeps a SQLite database of the items a character has identified: the item row
and its details (stat, resist and skill mods, affects, enchants, notes, rewards, and the weapon,
container, light, portal, furniture, drink, food and spells data). It is a port of the old
proxy's `eqdb` plugin and keeps its schema, so a database written by the old plugin is used as it
is.

The plugin never imports another plugin. The [eq plugin](eq.md) calls its save API from
`item.identify.add`, when this plugin is loaded, and the [itemid plugin](itemid.md) calls it
directly when eq does not know the item. The itemkeep port is a planned caller too; until an
identify is added the tables stay empty.

## Loading

The plugin id is `plugins.aardwolf.eqdb`:

```text
#bp.core.pluginm.load plugins.aardwolf.eqdb
```

If the database cannot be opened, the plugin logs the error and loads without a database.
`item.get` then returns `None`, `item.save` returns `False` and the command says "The eq database
is not available".

## Behaviour

- **An item is a plain mapping.** `item.save` takes a dict, not an `Item` object. The keys of the
  `items` row are `serial`, `keywords`, `cname`, `name`, `level`, `itype`, `worth`, `weight`,
  `wearable`, `material`, `score`, `flags`, `foundat`, `fromclan`, `owner` and `leadsto`. Other
  keys are ignored. `keywords` and `flags` may be a list or a string: a list is joined with `,`,
  `None` is stored as an empty string and a string is stored as it is.
- **Details.** Each detail is an optional key of the mapping:

  | Key | Shape |
  | :--- | :--- |
  | `statmod`, `resistmod` | `{name: amount}` |
  | `skillmod` | `{skillnum: amount}` |
  | `affectmod` | `[name]` |
  | `enchant` | `[{etype, spell, stat, mod, char, removable}]` |
  | `notes` | `{"ntext": text}` |
  | `reward` | `{"rtext": text}` |
  | `weapon`, `container`, `spells`, `food`, `drink`, `furniture`, `light`, `portal` | a dict of the columns of that table, the same fields as `aardwolf._libs.itemu.INVLAYOUT` has for it |

- **Replacing details.** A detail key that is present replaces that table's rows for the serial:
  the old rows are deleted and the new ones inserted. A present but empty value clears the rows. A
  key that is absent leaves the table alone, so a save with no details, such as one made from a
  cached item, does not wipe the stored details. The one-row tables are saved whenever their key
  is present, whatever the item type.
- **Getting an item.** `item.get` finds an item by serial, then by identifier, and returns a new
  dict: the `items` row with `flags` and `keywords` as lists (an empty or `NULL` value is `[]`),
  and, unless `details` is false, the detail keys in the shapes above. The `serial` and the row
  key are left out of each detail. A save then a get gives back what was saved.
- **Backups.** The `backupstart` setting is the time of day for the first backup and
  `backupinterval` the time between backups from then on. The backup is a zip in the `archive`
  directory next to the database, named
  `eqdb_<weekday>-<month>-<day>-<year>-<hour>-<minute>.sqlite.zip`. The plugin uses a one-time
  timer at `backupstart` whose callback backs up and then adds an interval timer, as the
  [statdb plugin](statdb.md) does. A change to either of eqdb's own settings schedules both again.
  The time of day is **UTC**, because bastproxy's timers are.

## Database

The database is `eqdb.sqlite` in the plugin's data directory,
`<BASTPROXY_HOME>/data/plugins/plugins.aardwolf.eqdb/`. It is opened through bastproxy's
`plugins.core.sqldb:database.add` and its `user_version` is 2. Version 1 is the old
plugin's. An old version 1 file is upgraded on the first open, after the core writes `archive/eqdb_1.sqlite.zip` as a backup.

The tables are `items`, `identifier`, `statmod`, `resistmod`, `skillmod`, `affectmod`, `enchant`,
`notes`, `addednotes`, `reward`, `weapon`, `container`, `spells`, `food`, `drink`, `furniture`,
`light` and `portal`. The CREATE statements are the old text, word for word and in the same column
order, so a database from the old plugin opens as it is.

- **`itype` is a number.** It is the `OBJECTTYPES` number (`5` for a weapon). The version 2 step
  finds every `items` row whose `itype` is text and replaces the name, stripped and lower-cased,
  with its number. A name that is not an object type stays text, and a number is left alone.
- **The old proxy should not use the upgraded file.** It stored and compared the type name.
  Keep the version 1 backup.
- **No foreign keys.** The tables declare `FOREIGN KEY` clauses, but bastproxy's core sqldb does
  not turn foreign key enforcement on, so they are not checked. The old plugin turned them on.
- **No atomic save.** Each statement is atomic, but a save that writes several tables is not one
  transaction. The old save was not either.

### Using a database from the old proxy

1. Stop the proxy.
2. Copy the old plugin's `eqdb.sqlite` (with any `-wal` and `-shm` files beside it) into
   `<BASTPROXY_HOME>/data/plugins/plugins.aardwolf.eqdb/`. To use one of the old backups, extract
   the `.sqlite` file from its zip and rename it `eqdb.sqlite`.
3. Start the proxy and load the plugin.

Keep the old file until the commands show the data you expect.

## Commands

The command is `#bp.aardwolf.eqdb.getitem`.

| Command | Description |
| :--- | :--- |
| `getitem [id]` | Show an item by serial or identifier: an `Item <serial>` line, then one sorted `key: value` line for each field. |

The `db*` commands that bastproxy's sqldb plugin adds work on this database too.

## Settings

| Setting | Default | Description |
| :--- | :--- | :--- |
| `backupstart` | `0000` | The time of day (HHMM, UTC) of the first backup each day. |
| `backupinterval` | `4h` | The time between backups after the first. |

The plugin listens to the two setting events `ev_plugins.aardwolf.eqdb_var_backupstart_modified`
and `ev_plugins.aardwolf.eqdb_var_backupinterval_modified`, and to no other event.

## APIs

| API | Description |
| :--- | :--- |
| `plugins.aardwolf.eqdb:item.get(ident, details=True)` | Return an item by serial or identifier as a new dict, or `None`. |
| `plugins.aardwolf.eqdb:item.save(item)` | Save an item mapping and its details. Returns `True` when saved, and `False` when the mapping has no valid `serial`, a detail has the wrong shape, or the database failed (the last two are logged). A wrong shape is caught before anything is written. |

`database.add` registers these under the plugin:

| API | Description |
| :--- | :--- |
| `plugins.aardwolf.eqdb:eqdb.select(sql, params)` | Run a select against the database. |
| `plugins.aardwolf.eqdb:eqdb.modify(sql, data)` | Run one modifying statement. |
| `plugins.aardwolf.eqdb:eqdb.modify.many(sql, data)` | Run a modifying statement for each item of `data`. |
| `plugins.aardwolf.eqdb:eqdb.row.get(row_id, table)` | Get one row of a table by its key. |

## Known gaps

- **No identifier writer.** No plugin ever wrote the `identifier` table: the old eq and itemid
  plugins only had a TODO ("do identifiers here"). The port keeps the table and the lookup by
  identifier in `item.get`, but adds no API to write one, so a lookup by identifier finds
  something only when a row was put there with `dbmodify`, or by an old database.

## From the old plugin

| Old | New |
| :--- | :--- |
| `sqldb.baseclass` and the `EqDb` subclass | `plugins.core.sqldb:database.add` with plain table data |
| API `getitem` and `saveitem`, taking an `Item` object | `item.get` and `item.save`, taking and returning a plain dict |
| `eqdb.select`, `eqdb.modify` and the other `eqdb.*` APIs | `plugins.aardwolf.eqdb:eqdb.select`, `.modify`, `.modify.many`, `.row.get` |
| events `statdb_backupstart` and `statdb_backupinternval` | the plugin's own `backupstart` and `backupinterval` setting events |
| backup interval setting in seconds | `backupinterval`, a time length such as `4h` |
| command `getitem`, printing `Item: {dict}` | `getitem`, printing one sorted `key: value` line for each field |
| command `test`, with a hard-coded serial | dropped |
| the `additemindexes` hook, which did nothing | dropped |
| the `trigger_dead` handler, which did nothing | dropped |
| `countitems`, which nothing called | dropped |
| `send.msg` logging of every query | dropped |
| `PRAGMA foreign_keys=On` and WAL mode | the core sqldb's settings |
| `itype` stored as the type name (`Weapon`) | the `OBJECTTYPES` number; the version 2 step converts old rows |

Bugs fixed in the port:

1. **`itype` was not converted to a number.** The old `itemu.dataparse` checked
   `name == 'type'`, but the field is called `itype`, so the conversion never ran and `itype`
   stayed the name the MUD sent, for example `Weapon`. The old `saveitemdetails` compared
   `item.itype` with `i.capitalize()`, so it did save the weapon, light, portal, furniture,
   container, drink and food rows. Only `spells` was never saved, because no object type is
   called "Spells". The port stores the number, and the version 2 step converts old rows.
2. **Backup setting changes were ignored.** The old plugin listened for `statdb_backupstart` and
   the misspelt `statdb_backupinternval`. Neither was raised, so a change to eqdb's own backup
   settings did not reschedule the timer. The plugin listens to its own settings.
3. **Crashes on missing `flags` or `keywords`.** `saveitem` ran `",".join(None)` for an item with
   no flags or keywords, and `getitem` ran `None.split(',')` on a row stored with `NULL`, which
   also broke every later save of that serial. An empty string came back as `['']` instead of `[]`.
4. **Wear locations were never looked up.** `getitem` ignored its `checkwearslot` argument, though
   the command help promised a wear location. The help now says serial or identifier. The old code
   also tested `if details:` twice.
5. **Stale mods were kept.** An empty `statmod`, `resistmod`, `skillmod`, `affectmod` or `enchant`
   was skipped, so the old rows stayed after an item lost its mods. An empty value now clears them.
6. **The caller's data was changed.** `savemultipledetails` added `serial` to the caller's
   `enchant` dicts. The store works on copies.
7. **SQL built with string formatting.** `getitembyserial` and `getdetail` built their SQL with
   `%`. Every value is now a bound parameter.
8. **No identifier writer.** The `identifier` table had no writer, so a lookup by identifier always
   failed. It is still a known gap, above.
