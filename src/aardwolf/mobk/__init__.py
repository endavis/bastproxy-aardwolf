"""Detect mob kills on Aardwolf and raise them as events."""

# these are required
PLUGIN_NAME = "Aardwolf Mobkill Events"
PLUGIN_PURPOSE = "raise an event for each mob kill of the character"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.triggers",
    "plugins.core.colors",
    "plugins.aardwolf.connect",
]
