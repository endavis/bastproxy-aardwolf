---
title: The iceage Plugin
description: Raise events when an Aardwolf Ice Age approaches or the MUD is about to reboot
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - iceage
---

# The iceage Plugin

Aardwolf announces an Ice Age and a reboot with countdown lines. The `iceage` plugin raises an event
for each of those lines, with the minutes left. It is ported from the `iceage` plugin of the old
bastproxy.

## Loading

The plugin id is `plugins.aardwolf.iceage`:

```text
#bp.core.pluginm.load plugins.aardwolf.iceage
```

It loads with `aardwolf` too. It depends on the events and triggers core plugins only. It has no
settings.

## Behaviour

Two triggers are always on:

- `iceage` matches `INFO: An Ice Age Approaches - 5 minutes - See 'help iceage'.` (also `1 minute`).
- `reboot` matches `INFO: Aardwolf will Reboot in 3 minutes.` and the form with a reason, such as
  `INFO: Aardwolf will reboot for a code update in 10 minutes.` The reason is not captured.

Each matching line raises one event with the minutes as an int, and logs a debug line such as
`Ice Age imminent: 5 minutes`. A match without a valid minutes value raises nothing.

## Events

- `ev_plugins.aardwolf.iceage_iceage`: an Ice Age countdown line. Argument `minutes`.
- `ev_plugins.aardwolf.iceage_reboot`: a reboot countdown line. Argument `minutes`.

## Commands

The plugin has no commands.

## Changes from the old plugin

1. **Event names.** `aard_iceage` and `aard_reboot` are now `ev_plugins.aardwolf.iceage_iceage` and
   `ev_plugins.aardwolf.iceage_reboot`. Nothing in this repository listened to the old names.
2. **Minutes in the events.** Both events were raised with `{}` and dropped the captured minutes.
   They now carry `minutes` (int).
3. **Reboot regex group.** The minutes were group 2 because `(.* )?` was group 1, so code reading the
   first group got the reason text or None. The port uses a named group `(?P<minutes>\d+)`.
4. **Empty number.** `\d*` matched an empty number, which is a `ValueError` with an int argtype in
   the core. The port uses `\d+`.
5. **Declared events.** The events were undeclared. They are now added with descriptions.
6. **Echoes.** The `send.msg` echoes are debug log lines that include the minutes.
7. **Docstring.** The class docstring said "quest events"; it no longer does.
8. **Loading.** `AUTOLOAD = False` is now `PLUGIN_REQUIRED = False`.

## Known gaps

- The countdown lines are matched on any channel prefix, so a player can spoof one by typing it on a
  channel.
- The sample lines come from the old regexes and were not checked against live Aardwolf.
