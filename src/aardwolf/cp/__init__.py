"""Follow Aardwolf campaigns and raise their events."""

# these are required
PLUGIN_NAME = "Aardwolf CP Events"
PLUGIN_PURPOSE = "follow the campaigns of the character and raise them as events"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.triggers",
    "plugins.core.mudcmds",
    "plugins.core.commands",
    "plugins.core.utils",
    "plugins.core.web",
    "plugins.aardwolf.connect",
    "plugins.aardwolf.config",
]
