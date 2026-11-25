"""Names and commands of the MUD's ``tags`` command.

Nothing here imports bastproxy, so it can be tested on its own.
"""

import re

_TAG_NAME = re.compile(r"^[A-Za-z]+$")


def tag_name(name: object) -> str | None:
    """Return the upper-cased tag ``name``, or None when it is not one alphabetic word."""
    if not isinstance(name, str):
        return None
    stripped = name.strip()
    if not _TAG_NAME.match(stripped):
        return None
    return stripped.upper()


def tag_command(name: str, enable: bool) -> str:
    """Return the MUD command that turns tag ``name`` on or off."""
    return f"tags {name.lower()} {'on' if enable else 'off'}"
