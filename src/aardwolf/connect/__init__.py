"""Set up Aardwolf GMCP and detect when the character is first active."""

# these are required
PLUGIN_NAME = "Aardwolf Connect"
PLUGIN_PURPOSE = "set up Aardwolf GMCP and detect when the character is first active"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.triggers",
    "plugins.core.proxy",
    "plugins.core.clients",
    "plugins.core.web",
]
