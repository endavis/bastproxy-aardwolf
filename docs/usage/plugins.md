---
title: Plugins
description: The Aardwolf plugins this package adds to bastproxy
audience:
  - users
tags:
  - usage
  - plugins
---

# Plugins

`bastproxy-aardwolf` registers itself with bastproxy through the `bastproxy.plugins` entry
point, so its plugins get the ids `plugins.aardwolf.<name>`.

## connect

Plugin id: `plugins.aardwolf.connect`.

Load it from a client connected to the proxy:

```text
#bp.core.pluginm.load plugins.aardwolf.connect
```

It does three things:

- Asks the mud for the GMCP modules `Char 1`, `Room 1`, `Comm 1`, `Group 1` and `Core 1`.
  After the first GMCP message it sends `rawcolor on` and `group on`.
- Presses return at each `[ Press Return to continue ]` prompt until the character is first
  active.
- Detects when the character is first active: the character, room and quest GMCP data have
  arrived and `char.status.state` is 3. It then sends `look` and `map` and sets the
  character active, which raises the bastproxy event `ev_libs.api_character_active`. A
  disconnect resets this, so the next login detects it again.

The API `plugins.aardwolf.connect:character.is.first.active` returns True once the character
has been first active.
