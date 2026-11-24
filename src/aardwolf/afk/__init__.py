"""Set a title and keep the tells while no client that can play is connected to Aardwolf."""

# these are required
PLUGIN_NAME = "Aardwolf AFK"
PLUGIN_PURPOSE = "do actions when no client is playing"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.settings",
    "plugins.core.triggers",
    "plugins.core.watch",
    "plugins.core.mudcmds",
    "plugins.core.commands",
    "plugins.core.clients",
    "plugins.aardwolf.connect",
]
