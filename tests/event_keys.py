"""A helper for the tests that check an event is raised only with keys it describes (#43)."""

from collections.abc import Iterable, Mapping
from typing import Any


def undeclared_keys(
    raised: Iterable[tuple[str, Mapping[str, Any] | None]],
    declared: Mapping[str, Iterable[str]],
) -> dict[str, set[str]]:
    """Return, per event, the top-level payload keys that its arg_descriptions do not describe.

    The core events plugin compares the same way: the top-level keys of the payload against the
    keys of arg_descriptions. An event that is not in ``declared`` has no descriptions at all.
    """
    found: dict[str, set[str]] = {}
    for name, payload in raised:
        extra = set(payload or {}) - set(declared.get(name, ()))
        if extra:
            found.setdefault(name, set()).update(extra)
    return found


def assert_raised_described(
    raised: Iterable[tuple[str, Mapping[str, Any] | None]],
    events: Mapping[str, Mapping[str, Any]],
) -> None:
    """Assert every raised payload has only keys its event's arg_descriptions describe.

    ``events`` maps an event name to its declaration, as the plugins' ``EVENTS`` dicts do.
    """
    declared = {name: info["arg_descriptions"] for name, info in events.items()}
    found = undeclared_keys(raised, declared)
    assert found == {}, f"keys raised but not in arg_descriptions: {found}"
