"""Show a report of Aardwolf stats and a message when a quest, campaign, gquest or level ends."""

# these are required
PLUGIN_NAME = "Aardwolf StatMonitor"
PLUGIN_PURPOSE = "report the stats of recent events and show a message when one completes"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.settings",
    "plugins.core.triggers",
    "plugins.core.timers",
    "plugins.core.commands",
    "plugins.core.utils",
    "plugins.core.proxy",
    "plugins.aardwolf.statdb",
]
