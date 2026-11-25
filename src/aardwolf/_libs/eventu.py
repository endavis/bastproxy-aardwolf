"""Pure helpers that build a plugin's own event names from its plugin id.

A plugin's ``libs`` keep only the suffix of each event it raises, with the description and the
argument descriptions. The plugin builds the full name from ``self.plugin_id``, so the id is
written nowhere but the plugin loader. This module imports nothing from bastproxy.
"""

from typing import Any


def own_event(plugin_id: str, suffix: str) -> str:
    """Return the full name of an event a plugin raises, for example ``ev_<plugin id>_<suffix>``."""
    return f"ev_{plugin_id}_{suffix}"


def own_events(plugin_id: str, events: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Return ``events`` re-keyed from suffixes to full names, in the same order."""
    return {own_event(plugin_id, suffix): info for suffix, info in events.items()}
