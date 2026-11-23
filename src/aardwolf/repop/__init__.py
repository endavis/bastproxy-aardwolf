"""Send a message to a channel when an area repops."""

# these are required
PLUGIN_NAME = "Aardwolf Repop"
PLUGIN_PURPOSE = "send repop messages to a channel"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.settings",
    "plugins.aardwolf.connect",
]
