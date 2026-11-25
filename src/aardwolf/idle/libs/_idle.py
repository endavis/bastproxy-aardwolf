"""Pure constants and helpers of the idle plugin, with no bastproxy imports."""

import re

TRIGGER_GLAZE = "glaze"
SETTING_COMMAND = "command"
SETTING_REGEX = "regex"
# the defaults of the regex and command settings
GLAZE_REGEX = r"^Your eyes glaze over\.$"
ANTI_IDLE_CMD = "look"


def regex_error(value: object) -> str | None:
    """Return why a value is not a usable glaze regex, or None when it is usable."""
    if not isinstance(value, str) or not value.strip():
        return "the regex may not be empty"
    try:
        re.compile(value)
    except re.error as err:
        return f"invalid regex: {err}"
    return None
