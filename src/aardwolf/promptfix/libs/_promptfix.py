"""Pure helpers and constants of the prompt fixer plugin, with no bastproxy imports."""

import re
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


class PromptStatus(StrEnum):
    """What fix_prompt decided about a prompt."""

    OK = "ok"
    FIXED = "fixed"
    TOO_LONG = "too_long"
    EMPTY = "empty"


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
