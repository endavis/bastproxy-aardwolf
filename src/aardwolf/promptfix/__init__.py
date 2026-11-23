"""Make the Aardwolf prompt and battle prompt end in %c."""

# these are required
PLUGIN_NAME = "Aardwolf Prompt Fixer"
PLUGIN_PURPOSE = "make the Aardwolf prompt and battle prompt end in %c"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.triggers",
    "plugins.core.settings",
    "plugins.core.proxy",
    "plugins.aardwolf.connect",
]
