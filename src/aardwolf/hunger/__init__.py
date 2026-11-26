"""Drink from a container when Aardwolf says the character is hungry or thirsty."""

# these are required
PLUGIN_NAME = "Aardwolf Hunger"
PLUGIN_PURPOSE = "drink when the character is hungry or thirsty"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.settings",
    "plugins.core.triggers",
    "plugins.core.commands",
    "plugins.core.timers",
    "plugins.aardwolf.eq",
    "plugins.aardwolf.move",
]
