---
title: The cp Plugin
description: Follow the campaigns of an Aardwolf character and raise the mobs left, the completion and the failure as events
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - cp
---

# The cp Plugin

The `cp` plugin follows the campaigns of the character from the MUD output. It keeps the state of the
campaign on disk, raises the mobs left whenever they are known or change, and raises one event when the
campaign is complete or cleared. The [statdb plugin](statdb.md) listens to `cp_comp` and `cp_failed`
and records the campaigns.

## Loading

The plugin id is `plugins.aardwolf.cp`:

```text
#bp.core.pluginm.load plugins.aardwolf.cp
```

It depends on the events, triggers, mudcmds and commands core plugins and on the
[connect plugin](connect.md) and on the [config plugin](config.md). The [mobk plugin](mobk.md) is optional: without it the mobs left are only
refreshed by a new `campaign check`.

## Behaviour

- **Triggers.** Their names carry a `cp_` prefix because trigger names are global: `cp_new`,
  `cp_none`, `cp_time`, `cp_mob`, `cp_scramble`, `cp_needtolevel`, `cp_cantake`, `cp_shnext`,
  `cp_mobdead`, `cp_complete`, `cp_clear`, `cp_reward` and `cp_compdone`, plus the `cp_info_*`
  triggers of the `campaign info` output. `cp_new` and `cp_mobdead` are always on. `cp_new`
  matches the new-campaign tell, but only from a questmaster, and only queues `campaign info`. The questmasters come from the
  [config plugin](config.md) (`plugins.aardwolf.config:questmasters.get`); add one with
  `#bp.aard.config.questmaster add <name>`. The trigger's regex is rebuilt when the list changes, so a
  player's tell or an emote of the same text never queues anything. With no
  questmasters the regex matches nothing, so no new campaign is recognised.
  The others sit in five groups, named `<plugin id>.<suffix>`: `cpcheck` (the output of
  `campaign check`, omitted from the client), `cpinfo` (the output of `campaign info`, omitted,
  the may-take lines too when the info was queued), `cpin` (while on a campaign), `cprew` (the rewards) and `cpdone`
  (the line under the rewards).
- **Campaign info.** Only the output of `campaign info` starts or replaces a campaign, so a faked
  tell costs one `campaign info` and nothing else. A `cpinfo` command type runs through the
  mudcmds queue like the check. It is queued on the new-campaign tell, on the CAMPAIGN-mob line
  (`cp_mobdead`) while cp is not on a campaign, and, together with a check, on the first active
  event and when the plugin loads with an active character.
    - On a campaign, when cp is not on one or the `Complete By` time differs from the stored
      `completeby`, cp starts a new state: `starttime` is now minus (7 days less the `Time Left`),
      which has minute precision and needs no timezone (now if the time left cannot be read);
      `level` is the `Level Taken` plus the remorts, tier and redos from GMCP; `mobs` and
      `mobsleft` are the targets; `cp_mobsorig` is raised and a check is queued for the mobs left.
      `Complete By` is in server time and is used only as the identity of the campaign.
    - The same campaign (on a campaign, same `Complete By`) changes nothing and queues nothing.
    - A target with a count of n is stored n times, because a mob has no count field, so each
      kill removes one entry.
    - Not on a campaign: the reply text of `campaign info` has not been captured and is assumed to
      match the check reply (`You are not currently on a campaign.`, then the may-take or
      must-level line). It sets `oncp` False and `cantake`. If the text differs, the first prompt
      after the not-on-a-campaign line finishes the command so the queue cannot stall.
    - A state saved before `completeby` existed has none, so the first info after an upgrade
      rebuilds the campaign, with a better start time.
- **Checking.** A `cpcheck` command type (`campaign check`) runs through the mudcmds queue. Before it
  is sent the mobs left are cleared and `cpcheck` is turned on; after it finishes `cpin` is turned on
  and `cpcheck` off. A check is queued after `campaign info` starts a campaign, together with an info on the
  first active event and when the plugin loads with an active character, on `cp refresh` and when a
  kill cannot be matched to a mob.
- **Hiding queued output.** The output of a `campaign check` or `campaign info` that the plugin
  queued is hidden from its first line through the next prompt: the target, time and info lines,
  the state line (`You will have to level...`, `You may take a campaign...`, `You cannot take
  another campaign for ...`), `You have completed N campaigns today.`, blank lines and the prompt.
  The window is the `hide_output` option of the core mudcmds command types `cpcheck` and
  `cpinfo`. It opens at the first line of the reply, which is any line an omitting trigger of the
  group matches (`hide_start` is built from those triggers), and closes at the first prompt after
  the plugin calls `command.finish`. The state triggers still fire on hidden lines, so `cantake`,
  need to level and `shtime` update. A `campaign check`, `cp check` or `campaign info` the player
  types is shown in full, because mudcmds hides only the output of a command it sent. If the
  command never finishes, the window ends at the cap (mudcmds counts the opening line, so the types
  pass `HIDE_MAX_LINES` + 1, which is 61) or at the command timeout, mudcmds logs a WARNING for the
  cap, and a disconnect ends it too. A finish on the prompt line itself, the info reply of a
  character that is not on a campaign with no limit line, closes the window at that prompt. Aardwolf
  sends no GA, so the prompt is recognised through the [promptfix plugin](promptfix.md); without
  it a finished window closes at once and the prompt is shown.
- **Mobs.** Each `cp_mob` line adds a mob with `name`, `nocolorname`, `location` and `mobdead`. The
  mobs left are saved in the state under `mobsleft`, so they survive a restart. The first check of a
  campaign copies them to `mobs` and raises `cp_mobsorig`; every check raises `cp_mobsleft`. When
  `campaign info` started the campaign, `mobs` is already set from it and the check does not raise
  `cp_mobsorig` again.
- **Kills.** `cp_mobdead` sets a flag. The next `mobk_kill` event, when the flag is set, removes the
  first mob with that name from the mobs left and raises `cp_mobsleft`. A name that is not in the list
  queues a check instead.
- **Completion.** `cp_complete` turns on the rewards group, and each `cp_reward` line sets `qp`,
  `trains`, `gold`, `tp` or `pracs`. A reward of an unknown type is logged at debug level and ignored.
  After the dashed line, the plugin watches every line: the bonus line sets `bonusqp` and finishes,
  the `You have completed N campaigns today.` line finishes, and so does the first prompt. Finishing
  turns off the rewards groups and raises `cp_comp`.
- **Cleared.** `cp_clear` sets `failed` to 1, raises `cp_failed`, and leaves the campaign.
- **Disconnect.** All the groups are turned off. A campaign that waits for its last line is raised
  first, so `cp_comp` is not lost.
- **Level.** The `level` of the state is the total level from
  `aardwolf._libs.aardu.actual_level_from_gmcp`, read when the campaign starts.

## Events

| Event | When | Payload keys |
| :--- | :--- | :--- |
| `ev_plugins.aardwolf.cp_mobsorig` | the mobs of a campaign are known for the first time | `mobsleft` |
| `ev_plugins.aardwolf.cp_mobsleft` | the mobs left are known or changed | `mobsleft` |
| `ev_plugins.aardwolf.cp_comp` | a campaign is complete and its rewards are known | `oncp`, `cantake`, `shtime`, `mobs`, `mobsleft`, `trains`, `pracs`, `gold`, `tp`, `qp`, `bonusqp`, `failed`, `starttime`, `finishtime`, `level`, `completeby` |
| `ev_plugins.aardwolf.cp_failed` | a campaign is cleared | the same keys as `cp_comp` |

Each payload is a deep copy; changing it does not change the state. statdb stores the columns of its
`campaigns` table and the mobs, and ignores the keys it has no column for.

## APIs

| API | Returns |
| :--- | :--- |
| `plugins.aardwolf.cp:oncp` | True when the character is on a campaign |
| `plugins.aardwolf.cp:mobs.left.get` | a copy of the mobs left |

## Commands

| Command | Does |
| :--- | :--- |
| `show` | lists the mobs left, dead ones in red, or says the character is not on a campaign |
| `refresh` | queues a `campaign check` when on a campaign |

## Changes from the old plugin

- **New campaign tell.** It no longer resets the state; it queues `campaign info`, and only that
  output starts a campaign.
- **First mob.** The old plugin tested the index of the killed mob for truth, so the mob at index 0
  was never removed. `remove_mob` tests it with `is not None`.
- **Level.** The old plugin passed only `char.status.level` to its level helper. The level is now
  `actual_level_from_gmcp`, which also reads the remorts, the tier and the redos.
- **No bonus line.** The old plugin waited for the bonus line or the count line, and lost the
  campaign when neither came. A prompt now finishes it too.
- **Unknown reward type.** It is ignored instead of raising `KeyError`.
- **Echoes.** The `send.msg` echoes are gone; the plugin logs at debug level.
- **Kill callback.** The plugin registers once for `mobk_kill` and uses a flag, instead of
  registering and unregistering a callback on every kill.
- **Watch.** The `cp_check` watch is not ported. Its handler was commented out in the old plugin, and
  enabling the omitting `cpcheck` group on a typed `cp check` would hide the output.
- **Hidden output.** The old plugin omitted the check lines but left the state line, the blank
  line and the prompt of a queued command visible; they are hidden now.
- **Events.** `aard_cp_*` events are now `ev_plugins.aardwolf.cp_*`.
