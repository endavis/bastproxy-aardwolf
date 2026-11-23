"""Pure helpers and constants of the repop plugin, with no bastproxy imports."""

from string import Template

PLUGIN_ID = "plugins.aardwolf.repop"
EVENT_GMCP_REPOP = "ev_libs.net.mud_gmcp_comm.repop"
SETTING_CHANNEL = "channel"
DEFAULT_CHANNEL = "gt"
SETTING_FORMAT = "format"
DEFAULT_FORMAT = "@r[@RRepop@r]@w ${zone} @R@@ @w${time}"


def repop_zone(data: object) -> str | None:
    """Return the stripped zone of a comm.repop message, or None when there is none."""
    if not isinstance(data, dict):
        return None
    zone = data.get("zone")
    if not isinstance(zone, str):
        return None
    return zone.strip() or None


def format_message(fmt: str, zone: str, when: str) -> str:
    """Fill the ${zone} and ${time} placeholders of a format."""
    return Template(fmt).safe_substitute(zone=zone, time=when)


def repop_command(channel: str, message: str) -> str | None:
    """Return the line to send to the mud, or None when the channel is blank."""
    channel = channel.strip()
    if not channel:
        return None
    return f"{channel} {message}"
