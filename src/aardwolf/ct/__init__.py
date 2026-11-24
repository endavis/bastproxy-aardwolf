"""Show a table of the damage done after each mob kill on Aardwolf."""

# these are required
PLUGIN_NAME = "Aardwolf CombatTracker"
PLUGIN_PURPOSE = "show combat stats after a mob kill"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.settings",
    "plugins.core.triggers",
    "plugins.core.colors",
    "plugins.core.utils",
    "plugins.aardwolf.mobk",
]
