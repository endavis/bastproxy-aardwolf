"""Pure validators for plugin settings, usable as a setting ``validator``."""

import time
from collections.abc import Callable


def int_validator(minimum: int, maximum: int | None = None) -> Callable[[object], str | None]:
    """Return a setting validator that accepts an int in a range.

    Args:
        minimum: the lowest accepted value.
        maximum: the highest accepted value, or None for no upper bound.

    Returns:
        A function giving the reason a value is refused, or None when it is accepted.
    """

    def check(value: object) -> str | None:
        if isinstance(value, bool) or not isinstance(value, int):
            return "the value must be a whole number"
        if value < minimum:
            return f"the value must be at least {minimum}"
        if maximum is not None and value > maximum:
            return f"the value must be at most {maximum}"
        return None

    return check


def time_format_error(value: object) -> str | None:
    """Return why a value is not a usable strftime pattern, or None when it is usable."""
    if not isinstance(value, str) or not value.strip():
        return "the time format may not be empty"
    if "%" not in value:
        return "the time format must contain a strftime directive such as %H"
    try:
        formatted = time.strftime(value, time.localtime(0))
    except ValueError as err:
        return f"invalid time format: {err}"
    if formatted == value:
        # an unknown directive is passed through unchanged by some C libraries
        return "the time format has no usable strftime directive"
    return None
