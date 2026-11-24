"""Feed the core client mapper with the rooms, areas and walking rules of Aardwolf."""

# these are required
PLUGIN_NAME = "Aardwolf Mapper"
PLUGIN_PURPOSE = "feed the core mapper with Aardwolf rooms, areas, room flags and walking rules"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.triggers",
    "plugins.core.colors",
    "plugins.aardwolf.move",
    "plugins.client.mapper",
]
