"""Tests for the shared setting validators."""

import pytest

from aardwolf._libs.validate import int_validator, time_format_error


def test_int_validator_accepts_range() -> None:
    check = int_validator(1, 5)
    assert check(1) is None
    assert check(5) is None


@pytest.mark.parametrize("value", [0, 6, True, "3", 2.5, None])
def test_int_validator_refuses(value: object) -> None:
    assert int_validator(1, 5)(value) is not None


def test_int_validator_without_maximum() -> None:
    check = int_validator(1)
    assert check(10**6) is None
    assert check(0) is not None


@pytest.mark.parametrize("value", ["%H:%M", "%a, %d %b %Y %H:%M:%S", "day %d"])
def test_time_format_accepts(value: str) -> None:
    assert time_format_error(value) is None


@pytest.mark.parametrize("value", ["", "   ", "no directive", 5, None, "%", "%Q"])
def test_time_format_refuses(value: object) -> None:
    assert time_format_error(value) is not None
