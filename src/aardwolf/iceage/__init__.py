"""Raise events when an Ice Age approaches and when Aardwolf is about to reboot."""

# these are required
PLUGIN_NAME = "Aardwolf Ice Age"
PLUGIN_PURPOSE = "raise events for Ice Ages and reboots"
PLUGIN_AUTHOR = "Bast"
PLUGIN_VERSION = 1

PLUGIN_REQUIRED = False
PLUGIN_DEPENDENCIES = [
    "plugins.core.events",
    "plugins.core.triggers",
]
