"""Keep the Aardwolf character's identified items in a database."""

# these are required
PLUGIN_NAME = "Aardwolf eqDB"
PLUGIN_PURPOSE = "keep the character's identified items in a database"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.sqldb",
    "plugins.core.events",
    "plugins.core.timers",
]
