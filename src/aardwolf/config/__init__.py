"""Settings shared by the Aardwolf plugins, starting with the questmaster list."""

# these are required
PLUGIN_NAME = "Aardwolf Config"
PLUGIN_PURPOSE = "keep the settings that several Aardwolf plugins share"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.utils",
]
