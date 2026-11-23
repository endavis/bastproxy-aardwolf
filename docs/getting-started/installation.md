---
title: Installation Guide
description: How to install and set up your project
audience:
  - users
  - contributors
tags:
  - getting-started
  - setup
---

# Installation Guide

> **Setting up from the template?** See the [New Project Setup](../template/new-project.md) guide instead.

## Requirements

- Python 3.12 or higher
- pip or uv

## Install from PyPI

### Using pip

```bash
pip install bastproxy-aardwolf
```

### Using uv (recommended)

```bash
uv pip install bastproxy-aardwolf
```

## Install from Source

### Clone the Repository

```bash
git clone https://github.com/endavis/bastproxy-aardwolf.git
cd bastproxy-aardwolf
```

### Install in Development Mode

```bash
# Creates .venv and installs the project, editable, with every extra from uv.lock
uv sync --all-extras --dev
```

The development tools, `doit` included, live in the `dev` and `security` extras, and a plain
`uv sync` uninstalls them. Every sync after this first one is `doit install_dev`, which runs the
same command.

## Running as a bastproxy Plugin Source

This package is a bastproxy plugin source. It registers itself in the `bastproxy.plugins`
entry-point group (`aardwolf = "aardwolf"` in `pyproject.toml`), so bastproxy loads its plugins
with IDs of the form `plugins.aardwolf.*`.

bastproxy will not start unless `BASTPROXY_HOME` points at an existing, writable directory, where
it keeps settings, data and logs. The tracked `.envrc` defaults it to `~/bastproxy`; override it
in `.envrc.local`. Without direnv, export it in the shell before running bastproxy.

```bash
# Start bastproxy from this repo, with this package installed and discovered
uv run bastproxy
```

bastproxy is not on PyPI yet, so the dependency is a direct git reference to its `main` branch
(`bastproxy @ git+https://github.com/endavis/bastproxy@main`, with hatch's
`allow-direct-references` enabled), which keeps the built wheel installable. `uv.lock` pins the
commit. To pick up newer bastproxy commits:

```bash
uv lock --upgrade-package bastproxy
```

When bastproxy is published on PyPI, the git reference is replaced by a version floor. Until then
PyPI does not accept an upload of this package, because PyPI rejects direct references.

To run against a local bastproxy checkout without touching `.venv` or `uv.lock`, layer it over
the environment for one run:

```bash
uv run --with-editable ../bastproxy bastproxy
```

[Working against a local bastproxy checkout](../usage/basics.md#working-against-a-local-bastproxy-checkout)
covers when the pin still needs moving. To install the checkout into `.venv` instead:

```bash
uv pip install -e ../bastproxy
```

The next `uv sync` or `doit install_dev` undoes this and restores the locked commit.

A symlink at `$BASTPROXY_HOME/plugins/aardwolf` overrides the installed copy, and bastproxy logs
a warning while it exists. Remove it; the entry point replaces it.

## Optional Dependencies

The development setup above installs both extras:

- `dev` - the test, lint, type-check, docs and release tools, `doit` among them
- `security` - `pip-audit`, `bandit` and the other security tools

## Verify Installation

Check that the package is installed correctly:

```python
import aardwolf
print(aardwolf.__version__)
```

Or from the command line (if CLI is available):

```bash
package-cli --version
```

## Upgrading

### From PyPI

```bash
pip install --upgrade bastproxy-aardwolf
```

### From Source

```bash
cd bastproxy-aardwolf
git pull
doit install_dev
```

## Uninstallation

```bash
pip uninstall bastproxy-aardwolf
```

## Troubleshooting

### Python Version Issues

Ensure you're using Python 3.12 or higher:

```bash
python --version
```

If you have multiple Python versions:

```bash
python3.12 -m pip install bastproxy-aardwolf
```

### Virtual Environment Issues

If you encounter issues, try creating a fresh virtual environment:

```bash
rm -rf .venv
uv venv
source .venv/bin/activate
uv pip install bastproxy-aardwolf
```

### Permission Errors

If you get permission errors, use a virtual environment instead of installing globally:

```bash
uv venv
source .venv/bin/activate
uv pip install bastproxy-aardwolf
```

## Next Steps

- Read the [Usage Guide](../usage/basics.md) to learn how to use the package
- Check the [API Reference](../reference/api.md) for detailed documentation
- See [Examples](../examples/README.md) for usage examples
