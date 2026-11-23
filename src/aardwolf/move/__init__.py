"""Raise an event when the character moves to another room."""

# these are required
PLUGIN_NAME = "Aardwolf Movement"
PLUGIN_PURPOSE = "raise an event when the character moves to another room"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.aardwolf.connect",
]
