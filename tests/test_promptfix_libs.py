"""Tests for the pure helpers of the prompt fixer plugin."""

import re

import pytest
from hypothesis import given
from hypothesis import strategies as st

from aardwolf.promptfix.libs import (
    MAX_VISIBLE,
    PROMPT_MARK_PRIORITY,
    PROMPT_SET_REGEX,
    PatternStatus,
    PromptStatus,
    build_prompt_pattern,
    ends_in_newline,
    fix_prompt,
    fixed_message,
    is_prompt_text,
    strip_colour_codes,
    strip_trailing,
    too_long_message,
    visible_length,
)


@pytest.mark.parametrize(
    ("prompt", "expected"),
    [
        ("[%h/%Hhp] > ", "[%h/%Hhp] >%c"),
        ("@R[%h]@w", "@R[%h]%c"),
        ("50%%c", "50%%c%c"),
        ("x@@", "x@@%c"),
    ],
)
def test_fix_needed(prompt: str, expected: str) -> None:
    """A prompt without a final %c gets one, after its trailing codes and spaces are dropped."""
    assert fix_prompt(prompt) == (PromptStatus.FIXED, expected)


@pytest.mark.parametrize("prompt", ["x%c", "x%c@w", "x%c  ", "x%c @R@x123 ", "x%%%c", "@R[%h]%c@w"])
def test_already_ok(prompt: str) -> None:
    """A prompt that ends in %c, with only codes or spaces after it, is left alone."""
    assert fix_prompt(prompt) == (PromptStatus.OK, prompt)


def test_length_limit() -> None:
    """The 80 limit counts the added %c and not the colour codes."""
    assert fix_prompt("a" * 78).status == PromptStatus.FIXED
    assert fix_prompt("a" * 79) == (PromptStatus.TOO_LONG, "a" * 79)
    assert fix_prompt("a" * 80).status == PromptStatus.TOO_LONG
    coloured = "@R" + "a" * 78 + "@w"
    assert fix_prompt(coloured).status == PromptStatus.FIXED
    assert MAX_VISIBLE == 80


@pytest.mark.parametrize("prompt", ["", "   ", "@w  ", "@R@x123"])
def test_empty(prompt: str) -> None:
    """A prompt with nothing visible is not fixed."""
    assert fix_prompt(prompt) == (PromptStatus.EMPTY, prompt)


@pytest.mark.parametrize(
    ("prompt", "expected"),
    [
        ("abc @R ", "abc"),
        ("abc@@", "abc@@"),
        ("abc@@ @w", "abc@@"),
        ("abc@", "abc@"),
        ("abc @x123@Z12 ", "abc"),
        ("", ""),
    ],
)
def test_strip_trailing(prompt: str, expected: str) -> None:
    """Trailing colour codes and spaces go; a trailing escaped @ stays."""
    assert strip_trailing(prompt) == expected


def test_strip_colour_codes_and_length() -> None:
    """Colour codes are removed, @@ is one @, and %x counts as its raw characters."""
    assert strip_colour_codes("@R[%h]@x123 @@") == "[%h] @"
    assert visible_length("@R[%h]@w") == 4
    assert visible_length("a@@b") == 3
    assert visible_length("%h%c") == 4


@pytest.mark.parametrize(
    ("prompt", "expected"),
    [
        ("x%c", True),
        ("%c", True),
        ("x%%c", False),
        ("x%%%c", True),
        ("x%", False),
        ("xc", False),
        ("", False),
    ],
)
def test_ends_in_newline(prompt: str, expected: bool) -> None:
    """An odd run of % before a final c is an unescaped %c."""
    assert ends_in_newline(prompt) is expected


@pytest.mark.parametrize(
    ("line", "matches"),
    [
        ("Prompt set to: [%h]", True),
        ("Battle prompt set to [%h]", True),
        ("[10/10hp] > Prompt set to: [%h]", True),
        ("prompt set to [%h]", False),
        ("Prompt is not set", False),
    ],
)
def test_prompt_set_regex(line: str, matches: bool) -> None:
    """The trigger regex finds the mud's confirmation, even stuck to a prompt."""
    assert bool(re.search(PROMPT_SET_REGEX, line)) is matches


def test_messages_name_the_prompt() -> None:
    """The messages name the prompt and never carry its text."""
    assert "battle prompt" in fixed_message("battle prompt")
    assert "80" in too_long_message("prompt")


REAL = "@R[@W%h@R/@W%H@Rhp %m/%Mmn %v/%Vmv %qqt %Xtnl@R] >%c"
REAL_LINE = "[201/201hp 176/176mn 630/630mv 0qt 773tnl] >"


def pattern(template: str) -> re.Pattern[str]:
    """Return the regex of a template that must be OK."""
    result = build_prompt_pattern(template)
    assert result.status == PatternStatus.OK
    assert result.regex is not None
    return result.regex


@pytest.mark.parametrize(
    "text",
    [
        REAL_LINE,
        REAL_LINE + "*[NOEXP]*",
        REAL_LINE + "*[NOEXP]* *[AFK]*",
    ],
)
def test_real_prompt_matches(text: str) -> None:
    """The real-style prompt matches with and without Aardwolf's flags."""
    assert is_prompt_text(text, [pattern(REAL)])


@pytest.mark.parametrize(
    "text",
    [
        REAL_LINE + " hello",
        "[201/201mn 176/176mn 630/630mv 0qt 773tnl] >",
        "[201/201hp 176/176mn 630/630mv 0qt 773tnl >",
        "To see warfare stats, use 'warinfo <player>'",
        "",
        "Prompt set to: " + REAL_LINE,
    ],
)
def test_real_prompt_rejects(text: str) -> None:
    """Other text, even if it ends like a prompt, is not a prompt."""
    assert not is_prompt_text(text, [pattern(REAL)])


def test_battle_prompt() -> None:
    """A battle prompt with literal text matches its output."""
    assert is_prompt_text("[100] Enemy: 50%", [pattern("[%h] Enemy: %e%c")])


@pytest.mark.parametrize("template", ["%h%m%c", "%h>%c", "%c", ""])
def test_too_loose(template: str) -> None:
    """A template with too little fixed text gets no pattern."""
    result = build_prompt_pattern(template)
    assert result.status in (PatternStatus.TOO_LOOSE, PatternStatus.NO_NEWLINE)
    assert result.regex is None
    if template.endswith("%c"):
        assert result.status == PatternStatus.TOO_LOOSE


@pytest.mark.parametrize("template", ["[%h] >", "x%%c", "[%h] > @w"])
def test_no_newline(template: str) -> None:
    """A template that does not end in an unescaped %c gets no pattern."""
    result = build_prompt_pattern(template)
    assert result.status == PatternStatus.NO_NEWLINE
    assert result.regex is None


def test_trailing_space_and_colour_after_newline() -> None:
    """Trailing colour and space after %c, and a space before it, are tolerated."""
    regex = pattern("[%h] > %c@w ")
    assert is_prompt_text("[5] >", [regex])
    assert is_prompt_text("[5] > ", [regex])


def test_percent_is_literal() -> None:
    """A %% in the template is a literal percent sign."""
    regex = pattern("[%h%%]%c")
    assert is_prompt_text("[50%]", [regex])
    assert not is_prompt_text("[50]", [regex])


def test_multi_line_template_marks_only_the_last_line() -> None:
    """Only the line the prompt ends on is recognised."""
    regex = pattern("Line one here%c[%h] >%c")
    assert is_prompt_text("[5] >", [regex])
    assert not is_prompt_text("Line one here", [regex])


def test_is_prompt_text_without_patterns() -> None:
    """No patterns never match."""
    assert not is_prompt_text(REAL_LINE, [])


def test_mark_priority_is_before_the_core_waiters() -> None:
    """The core waiters run at 40 and the triggers at 50."""
    assert PROMPT_MARK_PRIORITY < 40


_PIECE = st.one_of(
    st.just("%h"),
    st.just("%%"),
    st.text(alphabet="ab[]>: -", min_size=1, max_size=6),
)


@pytest.mark.property
@given(st.lists(_PIECE, max_size=8))
def test_a_line_rendered_from_a_template_matches_its_pattern(pieces: list[str]) -> None:
    """Invariant: when a template gets a pattern, the line it renders to is a prompt."""
    result = build_prompt_pattern("".join(pieces) + "%c")
    assert (result.regex is None) == (result.status != PatternStatus.OK)
    if result.regex is None:
        return
    line = "".join("12" if p == "%h" else "%" if p == "%%" else p for p in pieces)
    assert is_prompt_text(line, [result.regex])
