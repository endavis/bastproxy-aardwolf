"""Show which Aarchaeology items and pamphlets are still needed on Aardwolf."""

# these are required
PLUGIN_NAME = "Aardwolf Aarch"
PLUGIN_PURPOSE = "see what aarch items are needed"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.commands",
    "plugins.aardwolf.eq",
]
