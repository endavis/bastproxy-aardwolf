---
title: The repop Plugin
description: Send a message to a channel when an Aardwolf area repops
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - repop
---

# The repop Plugin

When an area repops, Aardwolf sends the GMCP message `comm.repop` with the zone. The `repop` plugin
sends a message about it to a channel, by default the group channel `gt`. It is ported from the
`repop` plugin of the old bastproxy.

## Loading

The plugin id is `plugins.aardwolf.repop`:

```text
#bp.core.pluginm.load plugins.aardwolf.repop
```

It loads with `aardwolf` too. It depends on the events and settings core plugins and on the
[connect plugin](connect.md), which turns on the GMCP `Comm` module.

## Behaviour

On each `comm.repop` message the plugin fills the `format` setting with the zone and the local time
(`HH:MM:SS`) and sends `<channel> <message>` straight to the MUD. A message without a zone sends
nothing, and a debug line is logged. A blank `channel` sends nothing.

## Settings

- `channel`: the channel to send the message to. Default `gt`.
- `format`: the message. `${zone}` and `${time}` are replaced; use `@@` for a literal `@`. Default
  `@r[@RRepop@r]@w ${zone} @R@@ @w${time}`.

```text
#bp.aardwolf.repop.set channel ft
```

## Changes from the old plugin

- **Missing zone.** A `comm.repop` without a `zone`, or with data that is not a dict, used to raise
  `KeyError` or `TypeError`. The message is now skipped.
- **Empty channel.** An empty `channel` used to send `" <message>"` to the MUD. Now nothing is sent.
- **How the line is sent.** The line used to go through proxy command processing. It now goes
  straight to the MUD, so a `#bp` command or proxy alias as the channel no longer expands. MUD-side
  aliases still work.
- **How `format` is shown.** `format` is added with `nocolor`, so the set command and the settings
  list show the raw `@` codes instead of rendering them. This fixes the old display, where the codes
  could not be read back.

## Events

The plugin raises no events. It listens to `ev_libs.net.mud_gmcp_comm.repop`.
