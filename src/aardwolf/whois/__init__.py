"""Parse the output of the Aardwolf whois command and raise it as an event."""

# these are required
PLUGIN_NAME = "Aardwolf Whois"
PLUGIN_PURPOSE = "gather the whois data of the character"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.triggers",
    "plugins.core.watch",
    "plugins.core.mudcmds",
]
