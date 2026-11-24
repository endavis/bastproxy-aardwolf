"""Tests for the pure helpers of the Aardwolf ct plugin."""

import re
from typing import Any

import pytest

from aardwolf.ct.libs import (
    EMPTYLINE_ID,
    EVENT_MOBK_KILL,
    LINE_LENGTH,
    SETTINGS,
    TableHelpers,
    average,
    damage_label,
    format_kill,
    pad_label,
    percent,
    title_text,
)

STAT = "@W"
INFO = "@x033"
DIV = INFO + "-" * LINE_LENGTH
CODE = re.compile(r"@(?:@|x\d{3}|[A-Za-z])")


def _escape(text: str) -> str:
    """Escape the @ of a text, like colorcode.escape."""
    return text.replace("@", "@@")


def _visible(text: str) -> str:
    """Return the text as shown: color codes removed and @@ one column."""
    return CODE.sub(lambda m: "@" if m.group(0) == "@@" else "", text)


def _center(text: str, filler: str, length: int) -> str:
    """Center a text with two spaces around it, counting only the visible columns."""
    free = length - (len(_visible(text)) + 4)
    left = free // 2
    return f"{filler * left}  {text}  {filler * (left + max(0, free - left * 2))}"


def _duration(start: float, end: float, num: str, unit: str) -> str:
    """Return the seconds between two times, like timedelta.to.string."""
    return f"{num}{int(abs(end - start)):02d}{unit}s"


HELPERS = TableHelpers(center=_center, duration=_duration, escape=_escape)


def kill(**extra: object) -> dict[str, Any]:
    """Return the example kill of the old plugin's docstring."""
    base: dict[str, Any] = {
        "name": "the dwarven barkeeper",
        "totalxp": 72,
        "starttime": 100.0,
        "finishtime": 106.0,
        "damage": {
            "pierce": {"hits": 2, "misses": 0, "damage": 665},
            "backstab": {"hits": 2, "misses": 1, "damage": 982},
            "cleave": {"hits": 3, "misses": 2, "damage": 976},
        },
    }
    base.update(extra)
    return base


def test_constants() -> None:
    """The names match the mobk event and the empty line trigger."""
    assert EVENT_MOBK_KILL == "ev_plugins.aardwolf.mobk_kill"
    assert EMPTYLINE_ID == "t_plugins.core.triggers_emptyline"
    assert set(SETTINGS) == {"statcolor", "infocolor"}


def test_docstring_example_line_by_line() -> None:
    """The table of the old plugin's docstring comes out line by line."""
    lines = format_kill(kill(), STAT, INFO, HELPERS).split("\n")
    assert lines == [
        DIV,
        INFO
        + "-" * 17
        + "  @Wthe dwarven barkeeper@x033 : @W06@x033s@x033 - @W72@x033xp  "
        + "-" * 17,
        DIV,
        "@x033Dam Type             @x033: @x033   Hits      Damage   (  0%)   Misses    Average  ",
        DIV,
        "@Wbackstab             @x033: @W    2         982     ( 37%)     1         491    ",
        "@Wcleave               @x033: @W    3         976     ( 37%)     2         325    ",
        "@Wpierce               @x033: @W    2         665     ( 25%)     0         332    ",
        DIV,
        "@WTotal                @x033: @W    7         2623    (100%)     3         374    ",
        DIV,
    ]


def test_rows_are_sorted_by_damage_type() -> None:
    """The rows follow the damage type, whatever the order of the payload."""
    lines = format_kill(kill(), STAT, INFO, HELPERS).split("\n")
    rows = [line[2:10].strip() for line in lines[5:8]]
    assert rows == ["backstab", "cleave", "pierce"]


def test_backstab_in_combat_label() -> None:
    """A backstab with an incombat key says so; another type does not."""
    assert damage_label("backstab", {"incombat": 1}) == "backstab (in)"
    assert damage_label("backstab", {}) == "backstab"
    assert damage_label("cleave", {"incombat": 1}) == "cleave"
    data = kill()
    data["damage"]["backstab"]["incombat"] = 1
    assert "backstab (in)" in format_kill(data, STAT, INFO, HELPERS)


def test_zero_total_damage_gives_zero_percent() -> None:
    """With no damage the share is 0 and nothing is raised."""
    data = kill(damage={"slash": {"hits": 0, "misses": 3, "damage": 0}})
    lines = format_kill(data, STAT, INFO, HELPERS).split("\n")
    assert "(  0%)" in lines[5]
    assert "(100%)" in lines[-2]
    assert percent(0, 0) == 0.0


def test_zero_hits_average_is_zero() -> None:
    """A type without hits has an average of 0, and the total divides by 1."""
    assert average(0, 0) == 0
    data = kill(damage={"slash": {"hits": 0, "misses": 2, "damage": 0}})
    assert format_kill(data, STAT, INFO, HELPERS).split("\n")[-2].rstrip().endswith(" 0")


def test_averages_are_floored() -> None:
    """The averages are whole numbers, as in Python 2."""
    assert average(982, 2) == 491
    assert average(976, 3) == 325
    assert average(665, 2) == 332
    assert average(2623, 7) == 374
    assert isinstance(average(7, 2), int)


def test_percent() -> None:
    """The share is a fraction of the total."""
    assert percent(25, 100) == 0.25


def test_empty_damage() -> None:
    """A kill without damage still has its frame and a total row of zeros."""
    lines = format_kill(kill(damage={}), STAT, INFO, HELPERS).split("\n")
    assert len(lines) == 8
    assert lines[6].startswith("@WTotal")
    assert "(100%)" in lines[6]


def test_time_only_with_both_times() -> None:
    """The time is shown only when the fight has a start and a finish."""
    assert "06" in title_text(kill(), STAT, INFO, HELPERS)
    for extra in ({"starttime": None}, {"finishtime": None}, {"starttime": 0}):
        text = title_text(kill(**extra), STAT, INFO, HELPERS)
        assert text == "@Wthe dwarven barkeeper@x033 : @x033 - @W72@x033xp"


def test_name_is_escaped() -> None:
    """A mob name with an @ is escaped in the title."""
    assert "@@Wolf" in title_text(kill(name="@Wolf"), STAT, INFO, HELPERS)


def test_label_escaping_keeps_the_column_width() -> None:
    """An @ in a label is escaped, and the padding counts the raw label."""
    assert pad_label("a@b", _escape) == "a@@b" + " " * 17
    assert _visible(pad_label("a@b", _escape)) == "a@b" + " " * 17
    data = kill(damage={"@x": {"hits": 1, "misses": 0, "damage": 5}})
    row = format_kill(data, STAT, INFO, HELPERS).split("\n")[5]
    assert row.startswith("@W@@x" + " " * 18 + " @x033: ")


def test_long_label_gets_no_negative_padding() -> None:
    """A label over 20 columns is not cut and not padded."""
    label = "x" * 25
    assert pad_label(label, _escape) == label


def test_colors_from_settings_are_used() -> None:
    """The stat and info colors given are the ones in the table."""
    text = format_kill(kill(), "@R", "@G", HELPERS)
    assert text.startswith("@G" + "-" * LINE_LENGTH)
    assert "@Rbackstab" in text
    assert "@W" not in text
    assert "@x033" not in text


@pytest.mark.parametrize("total", [1, 5, 99])
def test_total_row_is_always_100_percent(total: int) -> None:
    """The total row is 100% whatever the damage."""
    data = kill(damage={"hit": {"hits": 1, "misses": 0, "damage": total}})
    assert "(100%)" in format_kill(data, STAT, INFO, HELPERS).split("\n")[-2]
