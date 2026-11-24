"""Identify items on Aardwolf with invdetails and identify, and show them."""

# these are required
PLUGIN_NAME = "Aardwolf Item Identification"
PLUGIN_PURPOSE = "read invdetails and identify for an item, keep the result and show it"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.triggers",
    "plugins.core.mudcmds",
    "plugins.core.commands",
    "plugins.core.colors",
    "plugins.aardwolf.eq",
]
