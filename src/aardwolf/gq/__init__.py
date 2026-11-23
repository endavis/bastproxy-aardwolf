"""Follow Aardwolf global quests and raise their events."""

# these are required
PLUGIN_NAME = "Aardwolf GQ Events"
PLUGIN_PURPOSE = "follow the global quests of the character and raise them as events"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.triggers",
    "plugins.core.mudcmds",
    "plugins.core.watch",
    "plugins.core.settings",
    "plugins.aardwolf.connect",
]
