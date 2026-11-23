"""Record Aardwolf character stats, quests, campaigns, global quests, levels and mob kills."""

# these are required
PLUGIN_NAME = "Aardwolf StatDB"
PLUGIN_PURPOSE = "record Aardwolf stats, quests, campaigns, levels and mob kills in a database"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.sqldb",
    "plugins.core.events",
    "plugins.core.triggers",
    "plugins.core.timers",
    "plugins.core.proxy",
    "plugins.core.utils",
]
