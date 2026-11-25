"""Tests for the pure constants of the idle plugin."""

import re

import pytest

import aardwolf.idle.libs
from aardwolf.idle.libs import (
    ANTI_IDLE_CMD,
    GLAZE_REGEX,
    SETTING_COMMAND,
    SETTING_REGEX,
    TRIGGER_GLAZE,
    regex_error,
)


def test_constants() -> None:
    """The constants carry the documented values."""
    assert ANTI_IDLE_CMD == "look"
    assert TRIGGER_GLAZE == "glaze"


def test_glaze_regex_matches() -> None:
    """The glaze line matches."""
    assert re.match(GLAZE_REGEX, "Your eyes glaze over.")


@pytest.mark.parametrize(
    "line",
    [
        "Your eyes glaze overX",
        "Your eyes glaze over",
        "Your eyes glaze over. more",
        "Bob says 'Your eyes glaze over.'",
        "",
    ],
)
def test_glaze_regex_rejects(line: str) -> None:
    """Near misses do not match."""
    assert not re.match(GLAZE_REGEX, line)


def test_setting_names() -> None:
    """The setting names carry the documented values."""
    assert SETTING_COMMAND == "command"
    assert SETTING_REGEX == "regex"


def test_plugin_id_not_exported() -> None:
    """The libs no longer carry the plugin id."""
    assert not hasattr(aardwolf.idle.libs, "PLUGIN_ID")


def test_regex_error_accepts_default() -> None:
    """The default glaze regex is valid."""
    assert regex_error(GLAZE_REGEX) is None


def test_regex_error_rejects_bad_regex() -> None:
    """An uncompilable regex is refused with a reason."""
    error = regex_error("(")
    assert error is not None
    assert "invalid regex" in error


@pytest.mark.parametrize("value", ["", "   ", None, 5])
def test_regex_error_rejects_empty(value: object) -> None:
    """An empty, blank or non-string value is refused."""
    assert regex_error(value) is not None
