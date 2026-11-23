"""Keep the skills, spells and recoveries of the character up to date from slist."""

# these are required
PLUGIN_NAME = "Aardwolf Skills"
PLUGIN_PURPOSE = "keep the character's skills, spells and recoveries up to date from slist"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.triggers",
    "plugins.core.mudcmds",
    "plugins.core.commands",
    "plugins.aardwolf.connect",
    "plugins.aardwolf.a102",
]
