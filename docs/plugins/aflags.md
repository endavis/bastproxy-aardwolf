---
title: The aflags Plugin
description: Keep the Aardwolf character's affect flags from the aflags command
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - aflags
---

# The aflags Plugin

The `aflags` plugin keeps the set of the character's affect flags, such as `sanctuary` or `fly`,
read from the MUD command `aflags`. It reads the flags again when the [skills plugin](skills.md)
reports that an affect changed, and it raises an event with the flags added and removed. It is
ported from the `aflags` plugin of the old bastproxy.

## Loading

The plugin id is `plugins.aardwolf.aflags`:

```text
#bp.core.pluginm.load plugins.aardwolf.aflags
```

It depends on the events, triggers, mudcmds and commands core plugins and on the skills plugin. It
never imports another plugin: it keeps its own copies of the skills event names. It is not
required, so it does not load until asked.

## Behaviour

- **Reading.** `aflags` goes through the mudcmds queue as the type `aflags`. The plugin looks at
  every line of the output through the built-in all-lines trigger, as the cp plugin does, and
  drops that callback when the read ends, times out or the link drops. The core triggers plugin
  sends no blank line through a user trigger, so a group regex cannot see the blank line that
  ends the output.
  - Lines before the header are ignored, a prompt of the previous command among them.
  - The header `Affect Flags: ...` starts the read, and its flags are comma separated.
  - Each non-blank line after it adds flags, lowercased and stripped.
  - A line that starts with `{` is an Aardwolf tag and is skipped.
  - A blank line or a prompt ends the read.
- **State.** The flags are a set in memory. Each complete read replaces it, so a flag that wore off
  is gone. A disconnect clears it, drops a read in progress and forgets the changes noted.
- **When it reads.** When the character becomes active, and on the skills events `skills_affon`,
  `skills_affoff`, `skills_affected_update` and `skills_uptodate`. A refresh asked for during a
  read would be dropped by mudcmds, so the plugin remembers it and queues one more `aflags` when
  the read ends. Recoveries are not listened to: a recovery is a cooldown, not an affect flag.
- **Timeout.** When the output never ends, the mudcmds timeout frees the queue, the read is dropped
  and the flags stay as they were.
- **Hiding.** A queued `aflags` is hidden from the client: the hide window opens at the header and
  closes at the prompt after the command finishes, so the blank line and the prompt are hidden
  too. An `aflags` you type yourself is shown and not parsed.
- **Learning which affect sets which flag.** When exactly one affect changed (`skills_affon` or
  `skills_affoff`) between two reads and the flags differ, the plugin remembers the flags under
  the affect's sn. It is in memory only and written as a debug log; nothing reads it yet.

## MUD output

A live character with one affect answered `aflags` with the header, two blank lines and the prompt:

```text
Affect Flags: detecthidden


<prompt>
```

The example below, with several flags and a continuation line, is inferred from the old plugin's
regex and has not been seen live:

```text
Affect Flags: Sanctuary, Haste
              Fly, Detect Magic

<100/100hp 50/50mn 90/90mv>
```

The header is matched by `^Affect Flags: (?P<flags>.*)$`. The reader ends on a blank line or the
prompt. Whether the MUD wraps a long flag list onto more lines is not confirmed.

## Events

| Event | Arguments |
| :--- | :--- |
| `ev_plugins.aardwolf.aflags_diff` | `added` (sorted list), `removed` (sorted list), `sn` (the sn of the one affect that changed, or `None`) |

It is raised only when a read found a difference.

## APIs

| API | Returns |
| :--- | :--- |
| `plugins.aardwolf.aflags:flag.check` | True when the character has the flag; the case of the argument does not matter |

## Commands

```text
#bp.aardwolf.aflags.refresh
#bp.aardwolf.aflags.check sanctuary
#bp.aardwolf.aflags.list
```

## From the old plugin

| Old | New |
| :--- | :--- |
| `aard_skill_affon`, `aard_skill_affoff` | `skills_affon`, `skills_affoff` |
| `aard_skill_recon`, `aard_skill_recoff` | dropped |
| `skills_affected_update`, `skills_uptodate` | the same, as skills events |
| `afterfirstactive` | the `character_active` hook |
| `cmdq` | mudcmds |
| `affect_diff` event | `ev_plugins.aardwolf.aflags_diff` |
| `api('aflags.check')` | `plugins.aardwolf.aflags:flag.check` |
| `AUTOLOAD = False` | `PLUGIN_REQUIRED = False` |

## Changes from the old plugin

The old plugin had these bugs:

1. The module and class docstrings were copied from the scanh plugin. They are replaced.
2. `addflag` only added and `removeflag` was never called, so a flag that wore off stayed active
   until a reload. Each read now replaces the set.
3. `removeflag` set the flag to `False`, but `checkflag` tested `in`. It is dropped.
4. `aflagsafter` took the `Before` snapshot again before the diff, so `added` and `removed` were
   always empty and `flagstable` never filled. The plugin now compares before and after.
5. `flagsdiff` stored `removed` under the same key as `added`. The union is stored.
6. The "multiple affects" branch of `flagschanged` is replaced by the set of sns noted.
7. `aflagsbefore` toggled the group `cmd_<cmd>` while the trigger was in `cmd_<cid>`. It worked by
   accident; the point is moot.
8. `cmdq.cmdstart` was called from the first-line trigger. `command.start` now runs in the type's
   `beforef`.
9. Mutable state lived on two helper classes with back references (`_dump_shallow_attrs`). It is a
   set plus pure helper classes.
10. A refresh on `recon` or `recoff` is dropped. A refresh during a read was lost; it is now queued
    after the read.
11. `cmd_check` had a typo in its message. The debug chatter through `send.msg` is a debug log.

Other changes:

- **The event.** `affect_diff` was always empty (bug 4) and was raised on every read. The new event
  is raised only when something changed, and carries sorted lists and the sn.
- **Hiding.** The old plugin omitted only the header and the flag lines, so the blank line and the
  prompt showed. The new hide window runs from the header to the prompt, and it is bounded by
  `hide_max`.

## Known gaps

- A `{...}` tag line inside the hide window is hidden with it. aflags reads no tags of its own;
  `{affon}` and `{affoff}` belong to the skills plugin.
- The learned flags of an affect are not used or saved.
- When a read times out, the flags are not refreshed again until the next change.
- The wrapping of a long flag list, and the output with no flags set, are unconfirmed (see MUD
  output).
