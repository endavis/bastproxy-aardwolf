---
title: The config Plugin
description: Keep the settings that several Aardwolf plugins share, starting with the list of questmasters
audience:
  - users
  - contributors
tags:
  - aardwolf
  - plugin
  - config
---

# The config Plugin

The `config` plugin holds settings that more than one Aardwolf plugin needs. Its first setting is the
list of questmaster names, which the [cp plugin](cp.md) uses to recognise the lines a questmaster
sends.

## Loading

The plugin id is `plugins.aardwolf.config`:

```text
#bp.core.pluginm.load plugins.aardwolf.config
```

It loads with `aardwolf` too. It depends on the events and utils core plugins.

## Behaviour

- **The setting.** `questmasters` is a list setting. The default is `Commander Barcett` and
  `A QuestoR`. The setting is read-only, so the settings command cannot set it with a string; the
  `questmaster` command is the way to change it.
- **Saved.** The settings plugin saves the list, so it survives a restart of bastproxy.
- **Exact names.** Matching is case-sensitive for add and remove, because each name becomes a
  case-sensitive trigger text in the cp plugin. `A Questor` and `A QuestoR` are two entries. A name
  stored with the wrong case is removed with its exact text.

## Commands

The prefix is `#bp.aard.config`.

| Command | Description |
| :--- | :--- |
| `questmaster` | List the questmasters. |
| `questmaster add <name>` | Add a name. The name may have spaces and needs no quotes. |
| `questmaster remove <name>` | Remove a name. |

An add of a name that is in the list, and a remove of a name that is not, change nothing and say so.
An add or remove with no name fails.

## APIs

| API | Description |
| :--- | :--- |
| `plugins.aardwolf.config:questmasters.get` | Return a copy of the questmaster names. |

## Events

| Event | Arguments | Description |
| :--- | :--- | :--- |
| `ev_plugins.aardwolf.config_questmasters_changed` | `questmasters` | Raised when the list changes, with the list after the change. It is not raised when the plugin loads. |
