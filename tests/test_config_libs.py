"""Tests for the pure helpers of the config plugin."""

from aardwolf.config.libs import add_name, normalize_name, remove_name


def test_default_questmasters_are_the_three_names() -> None:
    """The default list is Commander Barcett, A QuestoR and Questor, in that order."""
    from aardwolf.config.libs import DEFAULT_QUESTMASTERS

    assert DEFAULT_QUESTMASTERS == ("Commander Barcett", "A QuestoR", "Questor")


def test_normalize_joins_words() -> None:
    """Words are joined with a single space."""
    assert normalize_name(["A", "QuestoR"]) == "A QuestoR"


def test_normalize_collapses_and_trims() -> None:
    """Repeated spaces collapse and the ends are trimmed."""
    assert normalize_name(["  A", "", "  QuestoR "]) == "A QuestoR"
    assert normalize_name("  Commander   Barcett ") == "Commander Barcett"


def test_normalize_empty() -> None:
    """An empty list gives an empty name."""
    assert normalize_name([]) == ""


def test_add_appends_to_a_new_list() -> None:
    """The input list is unchanged."""
    names = ["A"]
    assert add_name(names, "B") == ["A", "B"]
    assert names == ["A"]


def test_add_duplicate_is_none() -> None:
    """An exact duplicate is not added."""
    assert add_name(["A QuestoR"], "A QuestoR") is None


def test_add_case_variant_is_distinct() -> None:
    """A different case is a different name."""
    assert add_name(["A QuestoR"], "A Questor") == ["A QuestoR", "A Questor"]


def test_remove_exact_match() -> None:
    """The name goes and the input is unchanged."""
    names = ["A", "B"]
    assert remove_name(names, "A") == ["B"]
    assert names == ["A", "B"]


def test_remove_missing_is_none() -> None:
    """A missing name, or a case miss, gives None."""
    assert remove_name(["A QuestoR"], "Nobody") is None
    assert remove_name(["A QuestoR"], "a questor") is None
