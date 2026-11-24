"""Raise an event when the Aardwolf daily blessing is available."""

# these are required
PLUGIN_NAME = "Aardwolf Daily blessing"
PLUGIN_PURPOSE = "raise an event when the daily blessing is available"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.triggers",
    "plugins.core.timers",
    "plugins.core.commands",
    "plugins.aardwolf.connect",
]
