"""Turn the GMCP quest messages of Aardwolf into quest events."""

# these are required
PLUGIN_NAME = "Aardwolf Quest Events"
PLUGIN_PURPOSE = "raise events for the quests of the character"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.web",
    "plugins.aardwolf.connect",
]
