"""Keep an idle character from being disconnected from Aardwolf."""

# these are required
PLUGIN_NAME = "Aardwolf Idle"
PLUGIN_PURPOSE = "anti idle"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.settings",
    "plugins.core.triggers",
]
