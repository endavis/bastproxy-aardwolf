---
title: The idle Plugin
description: Keep an idle Aardwolf character from being disconnected
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - idle
---

# The idle Plugin

The `idle` plugin sends `look` when Aardwolf warns that the character is idle, so the mud does not
disconnect it. It is ported from the `idle` plugin of the old bastproxy.

## Loading

The plugin id is `plugins.aardwolf.idle`:

```text
#bp.core.pluginm.load plugins.aardwolf.idle
```

It depends on the triggers core plugin and imports no other plugin. It is not required, so it does
not load until asked.

## Behaviour

- One trigger, `glaze`, is always enabled. It has no group and no rate limit.
- When the trigger fires, the plugin sends `look` straight to the mud.

## MUD output

The trigger matches this line (`GLAZE_REGEX` in `src/aardwolf/idle/libs/_idle.py`):

```text
Your eyes glaze over.
```

The output of the `look` stays visible to the client.

## Settings, commands and events

The plugin has no settings, commands or APIs, and raises no events. The trigger raises the core
trigger event `event_t_plugins.aardwolf.idle_glaze`.

## Old to new

| Old | New |
| :--- | :--- |
| the old `idle` plugin module | `src/aardwolf/idle/` |
| `AUTOLOAD = False` | `PLUGIN_REQUIRED = False` |
| trigger `glaze` | trigger `glaze` |
| event `trigger_glaze` | event `event_t_plugins.aardwolf.idle_glaze` |
| `send.execute('look')` | a plain send to the mud |

## Changes from the old plugin

1. The regex had an unescaped `.`, so `Your eyes glaze overX` matched. It is now
   `^Your eyes glaze over\.$`.
2. The trigger event `trigger_glaze` is now `event_t_plugins.aardwolf.idle_glaze`.
3. `send.execute('look')` went through proxy command processing, so a proxy alias named `look`
   would expand. The new send goes straight to the mud.
4. The docstrings were copied from an example plugin ("a plugin to show how to use triggers").
5. The `look` output stays visible, as before.

## Known gaps

- The `look` output is not hidden. A hide window opens on the first line matching its start
  regex, and `^look$` never matches a room description. Hiding would need a catch-all start that
  also hides tells and combat lines arriving after the send.
