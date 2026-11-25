"""Tests for the shared setting validators."""

import time

import pytest

from aardwolf._libs.validate import TIME_DIRECTIVES, int_validator, time_format_error
from aardwolf.afk.libs import TIME_FORMAT as AFK_TIME_FORMAT
from aardwolf.daily.libs import TIME_FORMAT as DAILY_TIME_FORMAT
from aardwolf.statdb.libs import TIME_FORMAT as STATDB_TIME_FORMAT


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


@pytest.mark.parametrize("value", [DAILY_TIME_FORMAT, AFK_TIME_FORMAT, STATDB_TIME_FORMAT])
def test_time_format_accepts_every_default(value: str) -> None:
    assert time_format_error(value) is None


@pytest.mark.parametrize(
    "value", ["%Q", "%K", "%v", "%H %Q", "%Q %H", "%H:%", "%-d", "%#d", "%e", "%Ez"]
)
def test_time_format_refuses_unknown_directives(value: str) -> None:
    assert time_format_error(value) is not None


def test_time_format_names_the_unknown_directive() -> None:
    assert "%Q" in (time_format_error("%H %Q") or "")


def test_time_format_refuses_literal_percent_alone() -> None:
    assert time_format_error("%%") == "the time format has no usable strftime directive"


def test_time_format_accepts_escaped_percent_with_directive() -> None:
    assert time_format_error("%H%%") is None
    assert time_format_error("100%% at %H") is None


def test_time_format_refuses_escaped_percent_before_letter() -> None:
    # %%H is a literal "%H", not a directive
    assert time_format_error("%%H") is not None


@pytest.mark.parametrize("letter", sorted(TIME_DIRECTIVES))
def test_time_format_accepts_each_allowed_directive(letter: str) -> None:
    assert time_format_error(f"%{letter}") is None


def test_time_format_refuses_unknown_when_libc_drops_the_percent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """BSD libc turns %Q into Q; the check must not rely on the C library."""

    def bsd_strftime(fmt: str, _when: time.struct_time | None = None) -> str:
        return fmt.replace("%Q", "Q")

    monkeypatch.setattr(time, "strftime", bsd_strftime)
    assert time_format_error("%Q") is not None
