"""Tests for the pure constants of the idle plugin."""

import re

import pytest

from aardwolf.idle.libs import ANTI_IDLE_CMD, GLAZE_REGEX, PLUGIN_ID, TRIGGER_GLAZE


def test_constants() -> None:
    """The constants carry the documented values."""
    assert ANTI_IDLE_CMD == "look"
    assert TRIGGER_GLAZE == "glaze"
    assert PLUGIN_ID == "plugins.aardwolf.idle"


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
