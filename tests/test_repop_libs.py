"""Tests for the pure helpers of the repop plugin."""

import pytest

from aardwolf.repop.libs import (
    DEFAULT_FORMAT,
    format_message,
    repop_command,
    repop_zone,
)


def test_repop_zone() -> None:
    """The zone is returned stripped."""
    assert repop_zone({"zone": "aylor"}) == "aylor"
    assert repop_zone({"zone": "  aylor "}) == "aylor"


@pytest.mark.parametrize("data", [{}, {"zone": ""}, {"zone": "  "}, {"zone": 5}, None, "text", []])
def test_repop_zone_none(data: object) -> None:
    """A missing or unusable zone gives None."""
    assert repop_zone(data) is None


def test_format_default() -> None:
    """The default format is filled."""
    assert (
        format_message(DEFAULT_FORMAT, "aylor", "12:34:56")
        == "@r[@RRepop@r]@w aylor @R@@ @w12:34:56"
    )


def test_format_safe() -> None:
    """Unknown placeholders and a lone $ are left alone."""
    assert format_message("${foo} $ ${zone}", "z", "t") == "${foo} $ z"
    assert format_message("plain", "z", "t") == "plain"


def test_repop_command() -> None:
    """The channel is stripped, and a blank one gives None."""
    assert repop_command("gt", "msg") == "gt msg"
    assert repop_command(" gt ", "msg") == "gt msg"
    assert repop_command(" ", "msg") is None
    assert repop_command("", "msg") is None
