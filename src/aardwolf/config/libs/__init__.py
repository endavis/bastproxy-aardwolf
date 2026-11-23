"""Pure helpers for the config plugin."""

from ._config import (
    DEFAULT_QUESTMASTERS,
    EVENT_QUESTMASTERS_CHANGED,
    EVENT_QUESTMASTERS_MODIFIED,
    EVENTS,
    PLUGIN_ID,
    QUESTMASTERS,
    add_name,
    normalize_name,
    remove_name,
)

__all__ = [
    "DEFAULT_QUESTMASTERS",
    "EVENTS",
    "EVENT_QUESTMASTERS_CHANGED",
    "EVENT_QUESTMASTERS_MODIFIED",
    "PLUGIN_ID",
    "QUESTMASTERS",
    "add_name",
    "normalize_name",
    "remove_name",
]
