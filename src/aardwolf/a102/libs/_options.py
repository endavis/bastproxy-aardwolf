"""The option table and the counting rules of Aardwolf telnet option 102.

Nothing here imports bastproxy, so it can be tested on its own.
"""

A102_OPTION = 102
ON = 1
OFF = 2

OPTIONS: dict[str, int] = {
    "STATMON": 1,
    "BIGMAPTAGS": 2,
    "HELPTAGS": 3,
    "MAPTAGS": 4,
    "CHANNELTAGS": 5,
    "TELLTAGS": 6,
    "SPELLUPTAGS": 7,
    "SKILLGAINTAGS": 8,
    "SAYTAGS": 9,
    "SCORETAGS": 11,
    "ROOMNAME": 12,
    "EXITS": 14,
    "EDITORTAGS": 15,
    "EQTAGS": 16,
    "INVTAGS": 17,
    "ROOMDESCTAGS": 18,
    "ROOMNAMETAGS": 19,
    "INVMONTAGS": 20,
    "REPOPTAGS": 21,
    "QUIETTAGS": 50,
    "AUTOTICK": 51,
    "PROMPT": 52,
    "PAGING": 53,
    "AUTOMAP": 54,
    "SHORTMAP": 55,
}

OPTION_NAMES: dict[int, str] = {number: name for name, number in OPTIONS.items()}


def option_number(name: object) -> int | None:
    """Return the number of option ``name`` (case-insensitive), or None when unknown."""
    if not isinstance(name, str):
        return None
    return OPTIONS.get(name.strip().upper())


def apply_toggle(counts: dict[int, int], number: int, enable: bool) -> int | None:
    """Count one on or off request for ``number`` in ``counts``.

    Returns ``ON`` when the count went from 0 to 1, ``OFF`` when it went back to 0 and
    None when the MUD needs no message. An off at 0 changes nothing and adds no entry.
    """
    current = counts.get(number, 0)
    if enable:
        counts[number] = current + 1
        return ON if current == 0 else None
    if current == 0:
        return None
    counts[number] = current - 1
    return OFF if current == 1 else None


def state_payloads(counts: dict[int, int]) -> list[bytes]:
    """Return one payload per counted option, sorted by option number."""
    return [bytes([number, ON if count > 0 else OFF]) for number, count in sorted(counts.items())]


def off_payloads(counts: dict[int, int]) -> list[bytes]:
    """Return an "off" payload for every option with a count above 0, sorted by option number."""
    return [bytes([number, OFF]) for number, count in sorted(counts.items()) if count > 0]


def parse_pair(data: bytes) -> tuple[int, int] | None:
    """Return ``(option, flag)`` for a two-byte payload, else None.

    The MUD uses flags beyond 1 and 2 (option 100 reports the character state with 3).
    """
    if len(data) != 2:
        return None
    return data[0], data[1]


def parse_toggle(data: bytes) -> tuple[int, bool] | None:
    """Return ``(option, enable)`` for a client's toggle, else None.

    A toggle is two bytes: a known option number and a flag of ``ON`` or ``OFF``.
    """
    pair = parse_pair(data)
    if pair is None:
        return None
    number, flag = pair
    if number not in OPTION_NAMES or flag not in (ON, OFF):
        return None
    return number, flag == ON
