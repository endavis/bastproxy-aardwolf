"""Keep items of chosen types on Aardwolf when they reach the inventory."""

# these are required
PLUGIN_NAME = "Aardwolf Item autokeep"
PLUGIN_PURPOSE = "keep an item type automatically"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.settings",
    "plugins.core.triggers",
    "plugins.core.mudcmds",
    "plugins.aardwolf.eq",
]
