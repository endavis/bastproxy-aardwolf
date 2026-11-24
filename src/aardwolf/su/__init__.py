"""Recast the spellups of the character on itself when they wear off."""

# these are required
PLUGIN_NAME = "Aardwolf Spellup"
PLUGIN_PURPOSE = "cast the spellups of the character on itself when they wear off"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.settings",
    "plugins.core.commands",
    "plugins.core.timers",
    "plugins.aardwolf.connect",
    "plugins.aardwolf.skills",
    "plugins.aardwolf.move",
]
