---
title: Usage Guide
description: Run bastproxy with the Aardwolf plugins and load them from a client
audience:
  - users
tags:
  - usage
  - getting-started
---

# Usage Guide

`bastproxy-aardwolf` adds Aardwolf plugins to [bastproxy](https://github.com/endavis/bastproxy), a
MUD proxy. It has no program of its own: you run bastproxy with this package installed, connect a
MUD client to the proxy, and load the plugins you want.

## Running bastproxy with the plugins

Install the project as described in [Installation](../getting-started/installation.md). Then, from
this repository:

```bash
uv run bastproxy
```

bastproxy will not start unless `BASTPROXY_HOME` points at an existing, writable directory, where
it keeps its settings, data and logs. The tracked `.envrc` defaults it to `~/bastproxy`; without
direnv, export it in the shell first.

A `BASTPROXY_HOME` holds one character: plugins such as the
[statdb plugin](../plugins/statdb.md) keep one character's data there. Use a separate
`BASTPROXY_HOME` for each character you play.

Connect your MUD client to the proxy's port. bastproxy's own documentation covers the proxy
settings, passwords and connecting to the MUD.

## Loading plugins

bastproxy finds this package's plugins through its `bastproxy.plugins` entry point and names them
`plugins.aardwolf.<name>`. Load one from a client connected to the proxy:

```text
#bp.core.pluginm.load plugins.aardwolf.connect
```

To load several at once, name them all, or load the whole package:

```text
#bp.core.pluginm.load aardwolf.connect aardwolf.whois aardwolf.statdb
#bp.core.pluginm.load aardwolf
```

`aardwolf` loads every Aardwolf plugin that is not loaded yet, with its dependencies.

A loaded plugin is loaded again whenever bastproxy starts. `#bp.core.pluginm.list` lists every
discovered plugin. [Plugins](../plugins/index.md) describes each one.

## Working against a local bastproxy checkout

`uv.lock` pins a bastproxy commit. To run the plugins against a local bastproxy checkout instead,
for example while bastproxy is changing often or to try a change before it is merged, layer it
over this project's environment for one run:

```bash
uv run --with-editable ../bastproxy bastproxy
```

This runs whatever is checked out in `../bastproxy` and leaves `.venv` and `uv.lock` untouched, so
there is nothing to bump or commit to pick up a core change.

CI and `doit check` still use the pinned commit. When a plugin change needs a newer bastproxy API,
move the pin forward in that change's PR:

```bash
uv lock --upgrade-package bastproxy
```

## Next Steps

- [Plugins](../plugins/index.md): what each plugin does, and its APIs and events.
- [Adding a Plugin](../development/adding-a-plugin.md): where a new or migrated plugin's code,
  tests and docs go.
- [Doit Tasks Reference](../development/doit-tasks-reference.md): the development tasks (tests,
  linting, docs, issues and PRs).
- [CONTRIBUTING.md](https://github.com/endavis/bastproxy-aardwolf/blob/main/.github/CONTRIBUTING.md):
  the contribution workflow.
