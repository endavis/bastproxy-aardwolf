---
title: Adding a Plugin
description: Where a new or migrated Aardwolf plugin's code, tests and documentation go
audience:
  - contributors
tags:
  - plugin
  - development
---

# Adding a Plugin

Each Aardwolf plugin is a package under `src/aardwolf/<name>/`, discovered by bastproxy through
this project's `bastproxy.plugins` entry point and loaded as `plugins.aardwolf.<name>`. Follow the
existing plugins, `connect` and `a102`, for layout.

## Checklist

- **Code:** `src/aardwolf/<name>/` with its `plugin/` package. A plugin reaches another plugin
  only through bastproxy's API, never by importing it. Shared helpers that are not plugins go in
  `src/aardwolf/libs/`.
- **Tests:** add tests under `tests/`. A test file that imports `aardwolf` must be listed in
  `pytest_add_cli_args_test_selection` under `[tool.mutmut]` in `pyproject.toml`, or the mutmut
  configuration test fails.
- **Docs:**
  - add a page `docs/plugins/<name>.md`, laid out like the existing ones: loading, behaviour,
    APIs, events and, for a migrated plugin, a "From the old plugin" table mapping the old APIs and
    events to the new ones;
  - add a row for it to the table in [Plugins](../plugins/index.md);
  - add it to the Plugins section of the `mkdocs.yml` nav.
- **First active:** a plugin that must act once the character is logged in uses bastproxy's
  `@RegisterPluginHook("character_active")` hook rather than its own event handling. See
  [connect](../plugins/connect.md). The hook needs a bastproxy that includes endavis/bastproxy#589,
  so the first plugin that uses it also upgrades the locked bastproxy
  (`uv lock --upgrade-package bastproxy`) in its own PR.
