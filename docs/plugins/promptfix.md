---
title: The promptfix Plugin
description: Make the Aardwolf prompt and battle prompt end in %c so the next line never sticks to them, and mark prompt lines as prompts
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - promptfix
---

# The promptfix Plugin

When an Aardwolf prompt does not end in `%c`, the next line from the MUD can arrive stuck to the end
of the prompt, and a trigger anchored to the start of the line misses it. The `promptfix` plugin
changes the prompt and the battle prompt so that each ends in `%c`. It is ported from the
`aard_prompt_fixer.xml` plugin of the Aardwolf MUSHclient package.

## Loading

The plugin id is `plugins.aardwolf.promptfix`:

```text
#bp.core.pluginm.load plugins.aardwolf.promptfix
```

It loads with `aardwolf` too. It depends on the events, triggers, settings and proxy core plugins and
on the [connect plugin](connect.md).

## Behaviour

- **When it runs.** Once when the character is first active, and again each time the MUD says
  `Prompt set to ...` or `Battle prompt set to ...`.
- **What it does.** It sends the GMCP packet `request prompt` and reads the `char.prompts` reply,
  which holds `main` and `battle`. A request that is waiting blocks a second one, so the two sources
  never send twice.
- **The fix.** A prompt that does not end in an unescaped `%c` has its trailing colour codes and
  spaces removed and `%c` added, and is sent to the MUD with `prompt <new>` or `bprompt <new>`. An
  escaped `%%c` does not count as a `%c`. The client is told each time a prompt is changed; the
  message never shows the prompt text.
- **Left alone.** A prompt that already ends in `%c` is not changed, even with colour codes or spaces
  after the `%c`. A prompt with nothing visible is not changed either.
- **Too long.** When the fixed prompt would be over 80 visible characters (colour codes do not count,
  the added `%c` does), nothing is sent and the client is told to shorten the prompt by hand.

- **Marking prompts.** Aardwolf sends no IAC GA or EOR, so no line would be flagged as a prompt.
  From each `char.prompts` template the plugin builds an anchored pattern for the last line of the
  prompt (colour codes dropped, each `%x` code a wildcard, `%%` a literal `%`), and sets `is_prompt`
  on a MUD line that matches it. Aardwolf's trailing `*[FLAG]*` markers, such as `*[NOEXP]*`, are
  tolerated. A template that does not end in a `%c`, or has fewer than 3 fixed characters on its last
  line, gets no pattern and one warning (never with the template text). Only MUD lines are marked;
  internal and client lines never are. The patterns are built from any `char.prompts`, even with
  `autofix` off, though the plugin requests prompts only while `autofix` is on. A disconnect clears
  them.
- **What marking does.** Marked prompts reach triggers, `on_prompt` triggers and line waiters as real
  prompts, which is how the [cp plugin](cp.md) ends its hide window. Clients get IAC GA or EOR after a
  marked line, as they do from a MUD that sends one.

## Settings

`autofix` is on by default. Turn it off, because the plugin changes a game setting:

```text
#bp.aardwolf.promptfix.set autofix off
```

`#bp.aardwolf.promptfix.set autofix on` turns it on again; when the character is active the plugin
reads the prompts at once. With `autofix` off the plugin sends no request and changes nothing.

## Events

The plugin raises no events. It listens to `ev_libs.net.mud_gmcp_char.prompts`, the disconnect event
and the change of the `autofix` setting, and to `ev_to_client_data_modify` at priority 30, before
the core waiters (40) and triggers (50) read `is_prompt`.
