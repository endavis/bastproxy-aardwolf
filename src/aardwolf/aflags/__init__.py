"""Keep the character's Aardwolf affect flags up to date."""

# these are required
PLUGIN_NAME = "Aardwolf Affect Flags"
PLUGIN_PURPOSE = "keep up with affect flags"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.triggers",
    "plugins.core.mudcmds",
    "plugins.core.commands",
    "plugins.aardwolf.skills",
]
