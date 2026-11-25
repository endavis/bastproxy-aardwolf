"""Pure helpers and constants of the config plugin, with no bastproxy imports."""

from typing import Any

QUESTMASTERS = "questmasters"
DEFAULT_QUESTMASTERS = ("Commander Barcett", "A QuestoR", "Questor")

# the suffix of the event this plugin raises; the plugin builds the full name from its plugin id
SUFFIX_QUESTMASTERS_CHANGED = "questmasters_changed"

EVENTS: dict[str, dict[str, Any]] = {
    SUFFIX_QUESTMASTERS_CHANGED: {
        "description": ["raised when the list of questmaster names changes, with a copy"],
        "arg_descriptions": {"questmasters": "the list of questmaster names after the change"},
    },
}


def normalize_name(words: list[str] | str) -> str:
    """Join the words with single spaces and trim the ends."""
    text = words if isinstance(words, str) else " ".join(words)
    return " ".join(text.split())


def add_name(names: list[str], name: str) -> list[str] | None:
    """Return a new list with the name appended, or None when it is already there (exact match)."""
    if name in names:
        return None
    return [*names, name]


def remove_name(names: list[str], name: str) -> list[str] | None:
    """Return a new list without the name, or None when it is missing (exact match)."""
    if name not in names:
        return None
    return [item for item in names if item != name]
