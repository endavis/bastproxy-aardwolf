"""Pure helpers and constants of the prompt fixer plugin, with no bastproxy imports."""

import re
from collections.abc import Iterable
from enum import StrEnum
from typing import NamedTuple

PLUGIN_ID = "plugins.aardwolf.promptfix"
SETTING_AUTOFIX = "autofix"
MAX_VISIBLE = 80
GMCP_REQUEST = "request prompt"

EVENT_PROMPTS = "ev_libs.net.mud_gmcp_char.prompts"
EVENT_DISCONNECT = "ev_libs.net.mud_muddisconnect"
# the event the core settings plugin raises when the setting changes or loads
EVENT_AUTOFIX_MODIFIED = "ev_plugins.aardwolf.promptfix_var_autofix_modified"

EVENT_LINE_MODIFY = "ev_to_client_data_modify"
# runs before the core line waiters (priority 40) and triggers (priority 50) read is_prompt
PROMPT_MARK_PRIORITY = 30
# fewest non-blank fixed characters a prompt line needs to be recognised safely
MIN_PROMPT_LITERAL = 3

PROMPT_SET_TRIGGER = "promptfix_set"
# not anchored: the line can arrive stuck to the end of a prompt
PROMPT_SET_REGEX = r"(?:Battle p|P)rompt set to:? "

# (GMCP key, mud command, label shown to the user)
PROMPT_KINDS: tuple[tuple[str, str, str], ...] = (
    ("main", "prompt", "prompt"),
    ("battle", "bprompt", "battle prompt"),
)

_TOKEN = re.compile(r"@@|@[xXzZ]\d{1,3}|@[A-Za-z]|[^@]+|@")
_COLOUR = re.compile(r"@[xXzZ]\d{1,3}|@[A-Za-z]")
_PROMPT_TOKEN = re.compile(r"%%|%.|[^%]+|%", re.S)
# Aardwolf appends flags such as *[NOEXP]* to a prompt line
_FLAG_SUFFIX = r"(?:\s*\*\[[A-Z]+\]\*)*\s*"


class PromptStatus(StrEnum):
    """What fix_prompt decided about a prompt."""

    OK = "ok"
    FIXED = "fixed"
    TOO_LONG = "too_long"
    EMPTY = "empty"


class PatternStatus(StrEnum):
    """What build_prompt_pattern decided about a prompt template."""

    OK = "ok"
    NO_NEWLINE = "no_newline"
    TOO_LOOSE = "too_loose"


class PromptPattern(NamedTuple):
    """The status of a template and its regex (None unless OK)."""

    status: PatternStatus
    regex: re.Pattern[str] | None


class PromptFix(NamedTuple):
    """The status of a prompt and the prompt to use (the new one only when FIXED)."""

    status: PromptStatus
    prompt: str


def strip_colour_codes(prompt: str) -> str:
    """Return the prompt without its colour codes; an escaped ``@@`` becomes one ``@``."""
    parts: list[str] = []
    for token in _TOKEN.findall(prompt):
        if token == "@@":  # nosec B105  # colour-code token, not a password
            parts.append("@")
        elif not _COLOUR.fullmatch(token):
            parts.append(token)
    return "".join(parts)


def visible_length(prompt: str) -> int:
    """Return the length of the prompt as shown: colour codes do not count, ``%x`` counts two."""
    return len(strip_colour_codes(prompt))


def strip_trailing(prompt: str) -> str:
    """Drop trailing colour codes and whitespace; a trailing escaped ``@@`` is kept."""
    tokens = _TOKEN.findall(prompt)
    while tokens:
        last = tokens[-1]
        if _COLOUR.fullmatch(last):
            tokens.pop()
            continue
        if last in ("@@", "@"):
            break
        stripped = last.rstrip()
        if stripped:
            tokens[-1] = stripped
            break
        tokens.pop()
    return "".join(tokens)


def ends_in_newline(prompt: str) -> bool:
    """Return True when the prompt ends in an unescaped ``%c``."""
    if not prompt.endswith("c"):
        return False
    body = prompt[:-1]
    percents = len(body) - len(body.rstrip("%"))
    return percents % 2 == 1


def fix_prompt(prompt: str) -> PromptFix:
    """Decide what to do with a prompt so that it ends in ``%c``.

    Trailing colour codes and spaces after an existing ``%c`` leave the prompt alone.
    """
    stripped = strip_trailing(prompt)
    if ends_in_newline(stripped):
        return PromptFix(PromptStatus.OK, prompt)
    if not stripped.strip():
        return PromptFix(PromptStatus.EMPTY, prompt)
    new = stripped + "%c"
    if visible_length(new) > MAX_VISIBLE:
        return PromptFix(PromptStatus.TOO_LONG, prompt)
    return PromptFix(PromptStatus.FIXED, new)


def fixed_message(label: str) -> str:
    """Return what to tell the client after a prompt was changed."""
    return f"Prompt fixer: your {label} did not end in %c, so it was changed to end in %c."


def too_long_message(label: str) -> str:
    """Return what to tell the client when the fixed prompt would be too long."""
    return (
        f"Prompt fixer: your {label} does not end in %c, but adding it would make it longer "
        f"than {MAX_VISIBLE} visible characters. Shorten it and end it in %c by hand."
    )


def build_prompt_pattern(template: str) -> PromptPattern:
    """Build an anchored regex for the line a prompt template ends on.

    A template that does not end in ``%c`` has no pattern (its prompt sticks to the next line),
    and neither does one with too little fixed text to tell a prompt from other output.
    """
    stripped = strip_trailing(template)
    if not ends_in_newline(stripped):
        return PromptPattern(PatternStatus.NO_NEWLINE, None)
    # drop the final %c, then keep the last line of a multi-line prompt
    tokens = _PROMPT_TOKEN.findall(strip_colour_codes(stripped))[:-1]
    segment: list[str] = []
    for token in tokens:
        if token == "%c":  # nosec B105  # newline token, not a password
            segment = []
        else:
            segment.append(token)
    pieces: list[tuple[bool, str]] = []  # (is_wildcard, text)
    for token in segment:
        if token == "%%":  # nosec B105  # escaped percent token, not a password
            pieces.append((False, "%"))
        elif token.startswith("%") and len(token) == 2:
            pieces.append((True, ""))
        else:
            pieces.append((False, token))
    while pieces and not pieces[-1][0]:
        text = pieces[-1][1].rstrip()
        if text:
            pieces[-1] = (False, text)
            break
        pieces.pop()
    literal = sum(len("".join(text.split())) for wild, text in pieces if not wild)
    if literal < MIN_PROMPT_LITERAL:
        return PromptPattern(PatternStatus.TOO_LOOSE, None)
    body = "".join(".*?" if wild else re.escape(text) for wild, text in pieces)
    return PromptPattern(PatternStatus.OK, re.compile(rf"\A{body}{_FLAG_SUFFIX}\Z"))


def is_prompt_text(text: str, patterns: Iterable[re.Pattern[str]]) -> bool:
    """Return True when the line of text matches any prompt pattern."""
    return any(pattern.search(text) for pattern in patterns)
