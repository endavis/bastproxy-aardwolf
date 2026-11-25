"""A plugin's libs never write the plugin's own id (#138).

The plugin builds its own event names from ``self.plugin_id``, so a copy of the id in a libs
module would go stale when the plugin is renamed or moved. Only the plugin's own id is checked:
the literal name of another plugin's event or API is how a plugin listens to it.
"""

import ast
import re
from pathlib import Path

import pytest

import aardwolf

ROOT = Path(aardwolf.__file__).resolve().parent
PLUGINS = sorted(path.parent.name for path in ROOT.glob("*/libs") if path.is_dir())


def own_id_findings(source: str, name: str) -> list[str]:
    """Return what in ``source`` names the plugin ``name``'s own id.

    A finding is a ``PLUGIN_ID`` name, import alias or ``__all__`` string, or a string constant
    that holds ``plugins.aardwolf.<name>`` not followed by more of a longer name.
    """
    own = re.compile(r"plugins\.aardwolf\." + re.escape(name) + r"(?![a-z0-9])")
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Name) and node.id == "PLUGIN_ID":
            found.append(f"line {node.lineno}: the name PLUGIN_ID")
        elif isinstance(node, ast.alias) and "PLUGIN_ID" in (node.name, node.asname):
            found.append(f"line {node.lineno}: an import of PLUGIN_ID")
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and (node.value == "PLUGIN_ID" or own.search(node.value))
        ):
            found.append(f"line {node.lineno}: the string {node.value!r}")
    return found


def test_the_scan_covers_the_plugins() -> None:
    """The glob is not empty, and it holds plugins with a plain, a deleted and a moved id."""
    assert {"daily", "su", "mapper", "idle", "eq"} <= set(PLUGINS)


@pytest.mark.parametrize("name", PLUGINS)
def test_libs_do_not_write_their_own_plugin_id(name: str) -> None:
    findings: list[str] = []
    for path in sorted((ROOT / name / "libs").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        findings.extend(f"{path.name} {item}" for item in own_id_findings(source, name))
    assert findings == []


@pytest.mark.parametrize(
    "source",
    [
        'PLUGIN_ID = "plugins.aardwolf.eq"\n',
        "from ._eq import PLUGIN_ID\n",
        "from ._eq import X as PLUGIN_ID\n",
        '__all__ = ["PLUGIN_ID"]\n',
        'EVENT = "ev_plugins.aardwolf.eq_worn"\n',
        'EVENT = f"ev_plugins.aardwolf.eq_{suffix}"\n',
        'API = "plugins.aardwolf.eq:item.find"\n',
        "x = PLUGIN_ID\n",
    ],
)
def test_own_id_findings_flags_the_own_id(source: str) -> None:
    assert own_id_findings(source, "eq")


@pytest.mark.parametrize(
    "source",
    [
        'EVENT = "ev_plugins.aardwolf.eqdb:item.save"\n',
        'EVENT = "ev_plugins.aardwolf.skills_affon"\n',
        'API = "plugins.aardwolf.eqdb:item.save"\n',
        'EVENT = "ev_libs.net.mud_muddisconnect"\n',
        'NAME = "eq"\n',
    ],
)
def test_own_id_findings_leaves_other_names_alone(source: str) -> None:
    assert own_id_findings(source, "eq") == []
