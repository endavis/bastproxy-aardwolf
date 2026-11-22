"""Detect levels, powerups, superhero, remort and tier on Aardwolf and raise them as events."""

# these are required
PLUGIN_NAME = "Aardwolf Level Events"
PLUGIN_PURPOSE = "raise events for the levels and powerups of the character"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.triggers",
    "plugins.core.watch",
    "plugins.core.settings",
    "plugins.aardwolf.connect",
]
