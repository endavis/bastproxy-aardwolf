"""Pure builders for the eq and inv tables: plain dicts in, lines with ``@`` colour codes out."""

from collections.abc import Mapping, Sequence
from typing import Any, NamedTuple

from aardwolf.libs.itemu import ITEMFLAGS, ITEMFLAGSCOLORS, WEARLOCS, WEARLOCSREV

OPTIONAL_SLOTS = frozenset({8, 9, 10, 11, 25, 28, 29, 30, 31, 32})
SECOND_SLOT = WEARLOCSREV["second"]
HIDDEN_BY_SECOND = frozenset({WEARLOCSREV["shield"], WEARLOCSREV["hold"]})
SCORE_DEFAULT = "Unkn"
RULE = "@B" + "-" * 80 + "@w"
VAULT_NOT_READ = (
    "The vault has not been refreshed.",
    'Please go to a bank and type "#bp.aardwolf.eq.refresh"',
)
_EMPTY_ITEM: dict[str, Any] = {
    "cname": "@r< empty >@w",
    "shortflags": "",
    "level": "",
    "serial": "",
}
_RED = frozenset({"wielded", "second"})
_WHITE = frozenset({"above", "light"})
_CYAN = frozenset({"portal", "sleeping"})


class DisplayOptions(NamedTuple):
    """What the eq and inv commands were asked to show."""

    noflags: bool = False
    score: bool = False
    serial: bool = False
    nogroup: bool = True


def flag_header() -> str:
    """The flag letters of the header, each in its colour."""
    cells = [
        f" @{ITEMFLAGSCOLORS[flag]}{flag}@w " if i == 0 else f"@{ITEMFLAGSCOLORS[flag]}{flag}@w "
        for i, flag in enumerate(ITEMFLAGS)
    ]
    return "(" + "".join(cells) + "@w) "


def flag_cells(shortflags: str) -> str:
    """The flag cells of an item row: its set flags in colour, blanks for the rest."""
    cells: list[str] = []
    for i, flag in enumerate(ITEMFLAGS):
        if flag in shortflags:
            cells.append(f"{' ' if i == 0 else ''}@{ITEMFLAGSCOLORS[flag]}{flag} ")
        else:
            cells.append("   " if i == 0 else "  ")
    return "(" + "".join(cells) + "@w) "


def _column_header(opts: DisplayOptions) -> str:
    """The header of the flag, level, serial, score and name columns."""
    parts = [] if opts.noflags else [flag_header()]
    parts.append(f"(@G{'Lvl':>3}@w) ")
    if opts.serial:
        parts.append(f"(@x136{'Serial':<12}@w) ")
    if opts.score:
        parts.append(f"(@C{'Score':<5}@w) ")
    parts.append("Item Name")
    return "".join(parts)


def _columns(
    item: Mapping[str, Any], opts: DisplayOptions, *, serial: str | None = None, blank_zero: bool
) -> str:
    """The flag, level, serial, score and name columns of one item."""
    level = item.get("level", "")
    if blank_zero:
        level = level or ""
    parts = [] if opts.noflags else [flag_cells(str(item.get("shortflags", "")))]
    parts.append(f"(@G{level:>3}@w) ")
    if opts.serial:
        parts.append(f"(@x136{serial if serial is not None else item.get('serial', ''):<12}@w) ")
    if opts.score:
        parts.append(f"(@C{item.get('score', SCORE_DEFAULT):>5}@w) ")
    parts.append(str(item.get("cname", "")))
    return "".join(parts)


def _location_colour(name: str) -> str:
    """The colour of a wear location."""
    if name in _RED:
        return "@R"
    if name in _WHITE:
        return "@W"
    if name in _CYAN:
        return "@C"
    return "@c"


def _worn_row(item: Mapping[str, Any], slot: int, opts: DisplayOptions) -> str:
    """One row of the worn table."""
    name = WEARLOCS[slot]
    location = f"@G[@w {_location_colour(name)}{name:<8}@w @G]@w "
    return location + _columns(item, opts, blank_zero=False)


def worn_lines(
    slots: Sequence[int | None], items: Mapping[int, Mapping[str, Any]], opts: DisplayOptions
) -> list[str]:
    """The worn table, one row per slot, hiding the empty slots that are not worth a row."""
    header = "@G[@w " + f"{'Location':<8}" + " @G]@w " + _column_header(opts) + "  "
    lines = ["You are using:", header, RULE]
    second_filled = len(slots) > SECOND_SLOT and slots[SECOND_SLOT] is not None
    for slot, serial in enumerate(slots):
        item = items.get(serial) if serial is not None else None
        if item is None:
            if slot in OPTIONAL_SLOTS or (slot in HIDDEN_BY_SECOND and second_filled):
                continue
            item = _EMPTY_ITEM
        lines.append(_worn_row(item, slot, opts))
    lines.append("")
    return lines


def container_lines(
    cid: str,
    serials: Sequence[int],
    items: Mapping[int, Mapping[str, Any]],
    opts: DisplayOptions,
) -> list[str]:
    """The table of one container, folding like items into one counted row unless nogroup."""
    header = ("" if opts.nogroup else f" {'#':>3}  ") + _column_header(opts)
    lines = [f"Items in {cid}:", header, RULE]
    rows = [items[serial] for serial in serials if serial in items]
    if not rows:
        lines.extend([f"You have nothing in {cid}", ""])
        return lines
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for item in rows:
        key = str(item.get("name", "")) + str(item.get("shortflags", "")) + str(item.get("level"))
        groups.setdefault(key if not opts.nogroup else f"{len(groups)}", []).append(item)
    for group in groups.values():
        count = len(group)
        prefix = "" if opts.nogroup else (f"({count:>3}) " if count > 1 else f" {'':>3}  ")
        serial = f"{'Many':<12}" if count > 1 else None
        lines.append(prefix + _columns(group[0], opts, serial=serial, blank_zero=True))
    lines.append("")
    return lines


def keyring_count_line(count: int) -> str:
    """The line that says how many items are on the keyring."""
    return f"@C({count:>2})@W ** Item(s) on Keyring **@w"


def vault_count_lines(counts: Mapping[str, int]) -> list[str]:
    """The lines that say how many items are in the vault, ints compared as ints."""
    lines = [f"@wYou have @Y{counts['items']}@w of @Y{counts['max']}@w items stored in your vault."]
    if counts["total"] > counts["items"]:
        lines.append(
            f"Including keep flagged items, you have @Y{counts['total']}@w items in your vault."
        )
    lines.append("")
    return lines


def inventory_extra_lines(keyring_count: int, vault_counts: Mapping[str, int] | None) -> list[str]:
    """What follows the inventory: the keyring count and, when the vault has items, its counts."""
    lines: list[str] = []
    if keyring_count > 0:
        lines.extend([keyring_count_line(keyring_count), ""])
    if vault_counts is not None and vault_counts["total"] > 0:
        lines.extend(vault_count_lines(vault_counts))
    return lines


__all__ = [
    "HIDDEN_BY_SECOND",
    "OPTIONAL_SLOTS",
    "RULE",
    "SCORE_DEFAULT",
    "SECOND_SLOT",
    "VAULT_NOT_READ",
    "DisplayOptions",
    "container_lines",
    "flag_cells",
    "flag_header",
    "inventory_extra_lines",
    "keyring_count_line",
    "vault_count_lines",
    "worn_lines",
]
