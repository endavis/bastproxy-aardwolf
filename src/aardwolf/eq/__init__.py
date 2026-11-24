"""Keep track of the items the Aardwolf character wears and carries."""

# these are required
PLUGIN_NAME = "Aardwolf Eq"
PLUGIN_PURPOSE = "keep track of the items the character wears, carries, keeps and stores"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.triggers",
    "plugins.core.mudcmds",
    "plugins.core.commands",
    "plugins.core.colors",
    "plugins.aardwolf.connect",
    "plugins.aardwolf.a102",
]
