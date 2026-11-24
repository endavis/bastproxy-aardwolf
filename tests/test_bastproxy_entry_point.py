"""bastproxy discovers this package as a plugin source through its entry point."""

from importlib.metadata import entry_points
from pathlib import Path

import pytest

import aardwolf


def test_entry_point_is_registered() -> None:
    """The package registers itself in the ``bastproxy.plugins`` group."""
    found = {ep.name: ep.value for ep in entry_points(group="bastproxy.plugins")}
    assert found.get("aardwolf") == "aardwolf"


def test_bastproxy_loader_finds_the_package(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The loader turns the entry point into a search path with the right IDs."""
    # Importing bastproxy raises unless BASTPROXY_HOME is an existing directory.
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.loader import installed_plugin_search_paths

    paths = installed_plugin_search_paths()
    entry = next(p for p in paths if p["id_prefix"] == "plugins.aardwolf.")

    assert Path(str(entry["path"])).resolve() == Path(aardwolf.__file__).resolve().parent
    assert entry["import_prefix"] == "aardwolf."
    assert entry["source"] == "installed"


def test_libs_package_is_not_a_plugin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``aardwolf._libs`` is a plain package: the loader must not treat it as a plugin."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    root = Path(aardwolf.__file__).resolve().parent
    result = find_packages_and_plugins(root, "aardwolf.")

    assert "aardwolf._libs" in {p["package_id"] for p in result.packages}
    assert not any(
        p["package_import_location"].startswith("aardwolf._libs") for p in result.plugins
    )
