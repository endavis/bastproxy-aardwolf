"""Highlight the campaign, global quest and quest mobs in the scan output."""

# these are required
PLUGIN_NAME = "Scan Highlight"
PLUGIN_PURPOSE = "highlight cp, gq and quest mobs in scan"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.triggers",
    "plugins.core.settings",
    "plugins.core.colors",
    "plugins.aardwolf.a102",
]
