---
title: The scanh Plugin
description: Highlight the campaign, global quest and quest mobs in the Aardwolf scan output
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - scanh
---

# The scanh Plugin

The `scanh` plugin rewrites the lines of the `scan` output that end with a campaign, global quest or
quest mob, so the targets stand out. It is ported from the `scanh` plugin of the old bastproxy.

## Loading

The plugin id is `plugins.aardwolf.scanh`:

```text
#bp.core.pluginm.load plugins.aardwolf.scanh
```

It loads with `aardwolf` too. It depends on the events, triggers, settings and colors core plugins and on
[a102](a102.md), which turns the MUD's `SCAN` tag on. It needs none of the [cp](cp.md), [gq](gq.md) or [quest](quest.md) plugins: it learns the
targets from their events, so it works with any subset of them loaded.

## Behaviour

- **Scan tag.** After load the plugin asks a102 for the `SCAN` tag (`tags scan on`, sent once the
  character is active), so Aardwolf sends the `{scan}` and `{/scan}` lines. A real unload releases
  it, which turns it off, so a user who had it on before loses it; a reload leaves it on.
- **Scan lines.** The trigger `scanh_start` matches `{scan}` and turns on the trigger group
  `plugins.aardwolf.scanh.scan`. Its triggers match each line that starts with a space and the
  closing `{/scan}`, which turns the group off. Outside a scan the group is off and costs nothing.
- **Matching.** A line is lower-cased and stripped, and must end with the name of a target. The
  character before the name must be the start of the text or not a letter, so the target `rat` does
  not highlight `pirat`. An empty name never matches.
- **Output.** The line becomes `<text><back><line> - (CP) (Quest)@x`: the plain text of the line in
  the colours of the first source that matched, then one tag for each source that matched, in the
  order CP, GQ, Quest. A literal `@` in a mob name stays literal.
- **Left alone.** A line with MXP mode set. The `{scan}` and `{/scan}` lines are omitted: the
  triggers hide them from the client.
- **Debug output.** It goes to the plugin's log at DEBUG, never to the client.

## Targets

The targets are kept in memory and start empty after a restart.

| Event | Effect |
| :--- | :--- |
| `ev_plugins.aardwolf.cp_mobsleft` | Replaces the cp targets with the `mobsleft` mobs. |
| `ev_plugins.aardwolf.gq_mobsleft` | Replaces the gq targets with the `mobsleft` mobs. |
| `ev_plugins.aardwolf.quest_start` | Sets the quest target to `mobname`. |
| `ev_plugins.aardwolf.cp_comp`, `cp_failed` | Clear the cp targets. |
| `ev_plugins.aardwolf.gq_done`, `gq_won`, `gq_completed`, `gq_cancelled` | Clear the gq targets. |
| `ev_plugins.aardwolf.quest_killed`, `quest_comp`, `quest_failed`, `quest_reset` | Clear the quest target. |
| `ev_libs.net.mud_muddisconnect` | Turns the scan group off. |

Names come from `nocolorname`, or `name` when there is none. When the cp plugin is loaded before
scanh, the plugin reads the campaign mobs left from the `plugins.aardwolf.cp:mobs.left.get` API at
load. When cp loads later the targets stay empty until the next `cp_mobsleft`, which cp raises on
every check and kill.

## Settings

Six colour settings, changed with `#bp.aardwolf.scanh.set <name> <value>`:

| Setting | Default |
| :--- | :--- |
| `cptextcolor` | `@x0` |
| `cpbackcolor` | `@z14` |
| `gqtextcolor` | `@x0` |
| `gqbackcolor` | `@z9` |
| `questtextcolor` | `@x0` |
| `questbackcolor` | `@z13` |

## Events

The plugin raises no events. It listens to the events in the table above.

## Changes from the old plugin

- **Scan tag.** The plugin turns the `SCAN` tag on itself and hides the tag lines.
- **Name match.** The old plugin compared the tail of the line by length, so `rat` matched `pirat`.
  The character before the name must now not be a letter.
- **More than one tag.** The old plugin replaced the line for each source, so only the last tag
  showed. All the tags show now, with the colours of the first source.
- **gq completed and won.** The old plugin set the targets again on `gq_completed` and `gq_won`
  instead of clearing them. They clear now, and `gq_cancelled` clears too.
- **Quest killed and reset.** The old plugin kept the quest mob after `quest_killed` and
  `quest_reset`. They clear it now.
- **Help text.** The text colour settings said "background color". They say "text color".
- **Debug output.** The old plugin sent its debug messages to the client. They go to the log.
- **cp mobs.** The old plugin called the cp plugin for the mobs on each line. The plugin keeps them
  from `cp_mobsleft` and reads the cp API only once at load.
- **Scan group.** The old plugin registered a handler for every line of output during a scan. A
  disabled trigger group is turned on for the scan instead, and a disconnect turns it off.
