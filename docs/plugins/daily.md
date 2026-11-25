---
title: The daily Plugin
description: Raise an event when the Aardwolf daily blessing is available
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - daily
---

# The daily Plugin

The `daily` plugin follows the Aardwolf daily blessing. It raises an event when the blessing can be
received and shows when the next one is. It is ported from the `daily` plugin of the old bastproxy.

## Loading

The plugin id is `plugins.aardwolf.daily`:

```text
#bp.core.pluginm.load plugins.aardwolf.daily
```

It depends on the events, triggers, timers and commands core plugins and on `plugins.aardwolf.connect`
(for the character-active event), and imports no other plugin. It is not required, so it does not
load until asked.

## Behaviour

- A "You can receive a new daily blessing in ..." line sets the next daily time and arms a
  one-time timer. When the timer fires the available event is raised.
- "You are ready to receive a new daily blessing." raises the available event at once.
- "You bow your head to Ayla and receive your daily blessing." arms the timer for 23 hours (the
  constant of the old plugin, not verified against the mud).
- A wait of 0 seconds raises the available event at once, because the timers core refuses a
  timer under 1 second.
- When the character is first active (or already active when the plugin loads), GMCP
  `char.status.state` is 3, nothing is known and the daily is not available, the plugin sends
  `daily`. That send is not hidden: its reply may carry the blessing line other plugins match.

## MUD output

The triggers match these lines (`src/aardwolf/daily/libs/_daily.py`). The wait is any list of hours,
minutes and seconds, each optional:

```text
You can receive a new daily blessing in 1 hour, 2 minutes and 3 seconds.
You can receive a new daily blessing in 5 minutes and 7 seconds.
You can receive a new daily blessing in 45 seconds.
You are ready to receive a new daily blessing.
You bow your head to Ayla and receive your daily blessing.
```

On a live character that had taken a blessing the day before, `daily` answered:

```text
You received your last daily blessing at 23 Nov 2026 08:06:26.
You can receive a new daily blessing in 56 minutes and 47 seconds.
```

The wait line matched and `next` showed the time it gives. The first line is not read. The ready and
took lines have not been seen live yet; they come from the old plugin.

## Settings, commands and events

The plugin has one setting, one command and one event.

| Setting | Default | Meaning |
| :--- | :--- | :--- |
| `timeformat` | `%a, %d %b %Y %H:%M:%S` | The `strftime` pattern of the time `next` shows. It must contain a valid directive; it is read each time, so a change needs no reload. |

| Command | Does |
| :--- | :--- |
| `next` | shows when the next daily is, that it is ready, or asks you to type `daily` |

| Event | Raised |
| :--- | :--- |
| `ev_plugins.aardwolf.daily_available` | each time the daily can be received; no arguments |

## Old to new

| Old | New |
| :--- | :--- |
| the old `daily` plugin module | `src/aardwolf/daily/` |
| `AUTOLOAD = False` | `PLUGIN_REQUIRED = False` |
| triggers `daily1`, `daily2`, `daily3` | one trigger `dailywait` and a parser |
| triggers `dailynow`, `tookdaily` | triggers `dailynow`, `tookdaily` |
| event `aard_daily_available` | event `ev_plugins.aardwolf.daily_available`, declared |
| `GMCP.getv('char.status.state')` | `libs.net.protocols:gmcp.value.get` |

## Changes from the old plugin

1. The module docstring was copied from the iceage plugin, the class said "quest events" and a
   docstring had the typo "nex".
2. The final `.` before `$` was unescaped in all five regexes.
3. `[\d]*` matched an empty string, so `int('')` raised, and `[s]*` accepted "hourss".
4. The wait regexes were locked to three shapes, so any other shape left a stale timer. One
   trigger and `parse_wait` now read any mix of hours, minutes and seconds.
5. The next time was never cleared once the daily was available, so `next` showed a past time and
   the check never sent `daily` again.
6. `next` had no output for a ready daily.
7. A 0-second wait reached `timers.add` with 0, which core rejects, so the event never fired.
8. `timers.remove` was called without checking that the timer exists, which logs an error.
9. The check at load did not look at whether the character is active.
10. The event `aard_daily_available` was not declared.
11. The `send.msg` echo is now a debug log line.
12. `AUTOLOAD = False` is now `PLUGIN_REQUIRED = False`.

## Known gaps

- The next time is kept in memory, so it is lost when the proxy restarts. The plugin sends
  `daily` again when the character is next active.
- The `daily` reply is shown, not hidden. A follow-up can hide it after a live check of the reply.
- The 23 hour wait after receiving a blessing is the old plugin's value. The live reply above fits
  it if the MUD reports the last blessing in US Eastern time: 08:06:26 Eastern on 23 Nov plus 23
  hours is the 12:06:26 UTC on 24 Nov that the wait line gave.
