"""Tests for the pure helpers of the prompt fixer plugin."""

import re

import pytest

from aardwolf.promptfix.libs import (
    MAX_VISIBLE,
    PROMPT_SET_REGEX,
    PromptStatus,
    ends_in_newline,
    fix_prompt,
    fixed_message,
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
