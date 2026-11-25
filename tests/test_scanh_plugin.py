"""Tests for the scan highlight plugin, with a stubbed API."""

import ast
import logging
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

import aardwolf
from aardwolf.scanh.libs import (
    CP_MOBS_API,
    CP_ONCP_API,
    EVENT_CP_COMP,
    EVENT_CP_FAILED,
    EVENT_GQ_CANCELLED,
    EVENT_GQ_COMPLETED,
    EVENT_GQ_DONE,
    EVENT_GQ_WON,
    EVENT_QUEST_COMP,
    EVENT_QUEST_FAILED,
    EVENT_QUEST_KILLED,
    EVENT_QUEST_RESET,
    SCAN_END_REGEX,
    SCAN_LINE_REGEX,
    SETTINGS,
)

if TYPE_CHECKING:
    from aardwolf.scanh.plugin._scanh import ScanhPlugin

PLUGIN_ID = "plugins.aardwolf.scanh"
GROUP = f"{PLUGIN_ID}.scan"
DEFAULTS = {name: default for name, default, _ in SETTINGS}


class FakeApi:
    """A stand-in for the bastproxy API that records what the plugin calls."""

    def __init__(self) -> None:
        self.settings = dict(DEFAULTS)
        self.record: dict[str, Any] = {}
        self.settings_added: list[tuple[Any, ...]] = []
        self.trigger_adds: list[tuple[str, str, dict[str, object]]] = []
        self.trigger_regs: dict[str, Callable[..., Any]] = {}
        self.toggles: list[tuple[str, bool]] = []
        self.cp_exists = False
        self.cp_mobs: list[dict[str, Any]] = []
        self.cp_oncp = True
        self.cp_calls = 0
        self.tag_toggles: list[tuple[str, bool]] = []

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.settings:setting.add": lambda *args: self.settings_added.append(args),
            "plugins.core.settings:setting.get": lambda pid, key: self.settings[key],
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
            "plugins.core.triggers:group.toggle.enable": lambda group, flag: self.toggles.append(
                (group, flag)
            ),
            "libs.api:api.exists": lambda api_name: (
                self.cp_exists and api_name in (CP_MOBS_API, CP_ONCP_API)
            ),
            "plugins.aardwolf.a102:tag.toggle": self._tag_toggle,
            CP_MOBS_API: self._cp_mobs,
            CP_ONCP_API: lambda: self.cp_oncp,
            "plugins.core.colors:colorcode.escape": lambda text: text.replace("@", "@@"),
            "plugins.core.colors:colorcode.to.ansicode": lambda text: text,
        }
        return table[name]

    def _tag_toggle(self, name: str, enable: bool) -> bool:
        self.tag_toggles.append((name, enable))
        return True

    def _cp_mobs(self) -> list[dict[str, Any]]:
        self.cp_calls += 1
        return self.cp_mobs

    def _trigger_add(self, name: str, regex: str, **kwargs: object) -> SimpleNamespace:
        self.trigger_adds.append((name, regex, kwargs))
        return SimpleNamespace(success=True, trigger=SimpleNamespace(trigger_id=name))

    def _trigger_register(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        self.trigger_regs[trigger_id] = func
        return True


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: "ScanhPlugin", fake: FakeApi) -> None:
        self.plugin = plugin
        self.fake = fake

    def event(self, callback: Callable[[], None], **record: object) -> None:
        """Deliver an event with a record to a callback."""
        self.fake.record = record
        callback()

    def scan_line(self, text: str, **attrs: object) -> SimpleNamespace:
        """Run the line trigger on a line and return the line object."""
        line = SimpleNamespace(line=text, noansi=text, mxp_mode=None)
        for key, value in attrs.items():
            setattr(line, key, value)
        self.fake.record = {"line": line}
        self.plugin._trigger_line()
        return line

    def set_cp(self, *names: str) -> None:
        """Set the campaign mobs through the mobsleft event."""
        mobs = [{"name": f"@R{n}", "nocolorname": n} for n in names]
        self.event(self.plugin._eventcb_cp_mobsleft, mobsleft=mobs)

    def set_gq(self, *names: str) -> None:
        """Set the gquest mobs through the mobsleft event."""
        self.event(self.plugin._eventcb_gq_mobsleft, mobsleft=[{"nocolorname": n} for n in names])

    def set_quest(self, name: str) -> None:
        """Set the quest mob through the start event."""
        self.event(self.plugin._eventcb_quest_start, mobname=name)


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build a ScanhPlugin with a fake API."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from aardwolf.scanh.plugin import _scanh

    fake = FakeApi()
    plugin = _scanh.ScanhPlugin.__new__(_scanh.ScanhPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    yield Env(plugin, fake)


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.scanh" in {p["plugin_id"] for p in result.plugins}


def test_after_load(env: Env) -> None:
    """after_load adds the settings and the triggers; the group triggers start disabled."""
    env.plugin._phook_initialize()
    assert len(env.fake.settings_added) == 6
    assert {a[1] for a in env.fake.settings_added} == set(DEFAULTS)
    assert all(a[0] == PLUGIN_ID and a[3] == "color" for a in env.fake.settings_added)
    adds = {name: (regex, kwargs) for name, regex, kwargs in env.fake.trigger_adds}
    assert set(adds) == {"scanh_start", "scanh_end", "scanh_line"}
    assert adds["scanh_start"][1] == {"omit": True}
    assert adds["scanh_end"] == (
        SCAN_END_REGEX,
        {"enabled": False, "group": GROUP, "omit": True},
    )
    assert adds["scanh_line"] == (SCAN_LINE_REGEX, {"enabled": False, "group": GROUP})
    assert set(env.fake.trigger_regs) == set(adds)


def test_tag_triggers_are_omitted(env: Env) -> None:
    """The {scan} and {/scan} triggers hide their lines; the scan lines stay visible."""
    env.plugin._phook_initialize()
    omit = {name: kwargs.get("omit", False) for name, _, kwargs in env.fake.trigger_adds}
    assert omit == {"scanh_start": True, "scanh_end": True, "scanh_line": False}


def test_after_load_requests_scan_tag_once(env: Env) -> None:
    """after_load asks for the SCAN tag; a restored flag (reload) does not ask again."""
    env.plugin._phook_initialize()
    assert env.fake.tag_toggles == [("SCAN", True)]
    assert env.plugin._scan_tag_on is True
    env.plugin._phook_initialize()
    assert env.fake.tag_toggles == [("SCAN", True)]


def test_reload_keeps_scan_tag_flag(env: Env) -> None:
    """The flag is saved across a reload."""
    assert env.plugin.attributes_to_save_on_reload == ["_scan_tag_on"]


def test_unload_releases_scan_tag(env: Env) -> None:
    """A real unload releases the tag once and clears the flag."""
    env.plugin._phook_initialize()
    env.plugin.is_reloading_f = False
    env.plugin._phook_uninitialize()
    env.plugin._phook_uninitialize()
    assert env.fake.tag_toggles == [("SCAN", True), ("SCAN", False)]
    assert env.plugin._scan_tag_on is False


def test_reload_releases_nothing(env: Env) -> None:
    """A reload leaves the tag on."""
    env.plugin._phook_initialize()
    env.plugin.is_reloading_f = True
    env.plugin._phook_uninitialize()
    assert env.fake.tag_toggles == [("SCAN", True)]
    assert env.plugin._scan_tag_on is True


def test_unload_without_request_releases_nothing(env: Env) -> None:
    """Without an earlier request an unload calls nothing."""
    env.plugin.is_reloading_f = False
    env.plugin._phook_uninitialize()
    assert env.fake.tag_toggles == []


def test_imports_no_other_plugin() -> None:
    """The plugin never imports another plugin."""
    root = Path(aardwolf.__file__).resolve().parent / "scanh"
    for path in root.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names = [node.module]
            for name in names:
                assert not name.startswith("aardwolf.") or name.startswith("aardwolf.scanh")
                assert not name.startswith("bastproxy.plugins.") or name in (
                    "bastproxy.plugins._baseplugin",
                    "bastproxy.plugins.core.events",
                )


def test_after_load_reads_cp(env: Env) -> None:
    """With the cp API, the targets start from the campaign mobs left."""
    env.fake.cp_exists = True
    env.fake.cp_mobs = [{"nocolorname": "A Rat"}]
    env.plugin._phook_initialize()
    assert env.plugin.targets == {"cp": ["a rat"]}
    assert env.scan_line("   - a rat").line == "@x0@z14   - a rat - (CP)@x"


def test_after_load_does_not_read_cp_mobs_when_not_on_a_campaign(env: Env) -> None:
    """A stale list of mobs is not read when cp says the campaign is over."""
    env.fake.cp_exists = True
    env.fake.cp_oncp = False
    env.fake.cp_mobs = [{"nocolorname": "A Rat"}]
    env.plugin._phook_initialize()
    assert "cp" not in env.plugin.targets
    assert env.fake.cp_calls == 0


def test_scan_start_clears_cp_when_the_campaign_is_over(env: Env) -> None:
    """A campaign that ended without an event stops being highlighted at the next scan."""
    env.fake.cp_exists = True
    env.plugin._phook_initialize()
    env.set_cp("a rat")
    env.set_gq("a gq mob")
    env.set_quest("A Quest Mob")
    env.fake.cp_oncp = False
    env.plugin._trigger_start()
    assert env.scan_line("  - a rat").line == "  - a rat"
    assert env.scan_line("  - a gq mob").line == "@x0@z9  - a gq mob - (GQ)@x"
    assert env.scan_line("  - a quest mob").line == "@x0@z13  - a quest mob - (Quest)@x"


def test_scan_start_keeps_cp_while_on_a_campaign(env: Env) -> None:
    """With the campaign on, the cp targets stay highlighted."""
    env.fake.cp_exists = True
    env.plugin._phook_initialize()
    env.set_cp("a rat")
    env.plugin._trigger_start()
    assert env.scan_line("  - a rat").line == "@x0@z14  - a rat - (CP)@x"


def test_scan_start_clears_cp_when_cp_is_not_loaded(env: Env) -> None:
    """Without the cp plugin there is no campaign to highlight."""
    env.plugin._phook_initialize()
    env.set_cp("a rat")
    env.plugin._trigger_start()
    assert "cp" not in env.plugin.targets


def test_new_campaign_after_a_clear_is_highlighted_again(env: Env) -> None:
    """A cp_mobsleft after a scan-start clear sets the targets again."""
    env.fake.cp_exists = True
    env.plugin._phook_initialize()
    env.set_cp("a rat")
    env.fake.cp_oncp = False
    env.plugin._trigger_start()
    assert "cp" not in env.plugin.targets
    env.fake.cp_oncp = True
    env.set_cp("a bat")
    env.plugin._trigger_start()
    assert env.scan_line("  - a bat").line == "@x0@z14  - a bat - (CP)@x"


def test_after_load_without_cp(env: Env) -> None:
    """Without the cp API, nothing is called and there are no targets."""
    env.plugin._phook_initialize()
    assert env.fake.cp_calls == 0
    assert env.plugin.targets == {}


def test_start_end_disconnect_toggle_group(env: Env) -> None:
    """The scan tags turn the group on and off; a disconnect turns it off."""
    env.plugin._phook_initialize()
    env.plugin._trigger_start()
    env.plugin._trigger_end()
    env.plugin._eventcb_disconnect()
    assert env.fake.toggles == [(GROUP, True), (GROUP, False), (GROUP, False)]


def test_toggle_without_group(env: Env) -> None:
    """Before after_load there is no group to toggle."""
    env.plugin._trigger_start()
    env.plugin._eventcb_disconnect()
    assert env.fake.toggles == []


def test_cp_line_rewritten(env: Env) -> None:
    """A cp target line gets the cp colours and tag; others stay."""
    env.set_cp("a big rat")
    assert env.scan_line("     - a big rat").line == "@x0@z14     - a big rat - (CP)@x"
    assert env.scan_line("     - a big cat").line == "     - a big cat"


def test_no_targets_unchanged(env: Env) -> None:
    """With no targets a line is left alone."""
    assert env.scan_line("     - a big rat").line == "     - a big rat"


def test_gq_and_quest_lines(env: Env) -> None:
    """GQ and quest targets get their own colours and tags."""
    env.set_gq("a gq mob")
    env.set_quest("A Quest Mob")
    assert env.scan_line("  - a gq mob").line == "@x0@z9  - a gq mob - (GQ)@x"
    assert env.scan_line("  - a quest mob").line == "@x0@z13  - a quest mob - (Quest)@x"


def test_at_sign_in_name_is_escaped(env: Env) -> None:
    """A literal @ in a mob name stays literal."""
    env.set_cp("a@b")
    assert env.scan_line("  - a@b").line == "@x0@z14  - a@@b - (CP)@x"


def test_user_colours_used(env: Env) -> None:
    """The colours come from the settings."""
    env.fake.settings["cptextcolor"] = "@x15"
    env.fake.settings["cpbackcolor"] = "@z1"
    env.set_cp("a rat")
    assert env.scan_line(" a rat").line == "@x15@z1 a rat - (CP)@x"


CLEARING = [
    ("cp", "_eventcb_cp_comp", EVENT_CP_COMP),
    ("cp", "_eventcb_cp_failed", EVENT_CP_FAILED),
    ("gq", "_eventcb_gq_done", EVENT_GQ_DONE),
    ("gq", "_eventcb_gq_won", EVENT_GQ_WON),
    ("gq", "_eventcb_gq_completed", EVENT_GQ_COMPLETED),
    ("gq", "_eventcb_gq_cancelled", EVENT_GQ_CANCELLED),
    ("quest", "_eventcb_quest_killed", EVENT_QUEST_KILLED),
    ("quest", "_eventcb_quest_comp", EVENT_QUEST_COMP),
    ("quest", "_eventcb_quest_failed", EVENT_QUEST_FAILED),
    ("quest", "_eventcb_quest_reset", EVENT_QUEST_RESET),
]


@pytest.mark.parametrize(("source", "method", "event_name"), CLEARING)
def test_clearing_event(env: Env, source: str, method: str, event_name: str) -> None:
    """A clearing event stops its source's highlight and leaves the others (bugs 3, 4)."""
    env.set_cp("mob one")
    env.set_gq("mob two")
    env.set_quest("mob three")
    lines = {"cp": "  - mob one", "gq": "  - mob two", "quest": "  - mob three"}
    getattr(env.plugin, method)()
    for key, text in lines.items():
        highlighted = env.scan_line(text).line != text
        assert highlighted is (key != source), (key, event_name)


def test_clearing_events_are_registered() -> None:
    """Each clearing callback is registered for its event name."""
    from aardwolf.scanh.plugin._scanh import ScanhPlugin

    for _, method, event_name in CLEARING:
        registrations = getattr(ScanhPlugin, method).event_registration
        assert [r["event_name"] for r in registrations] == [event_name], method


def test_mobsleft_replaces_cp_targets(env: Env) -> None:
    """A new cp_mobsleft replaces the old targets (bug 7)."""
    env.set_cp("mob one")
    env.set_cp("mob two")
    assert env.scan_line("  - mob one").line == "  - mob one"
    assert env.scan_line("  - mob two").line != "  - mob two"


def test_suffix_only_name_not_rewritten(env: Env) -> None:
    """Target rat does not highlight pirat (bug 1)."""
    env.set_cp("rat")
    assert env.scan_line("  - pirat").line == "  - pirat"
    assert env.scan_line("  - rat").line != "  - rat"


def test_two_tags(env: Env) -> None:
    """A line matching cp and quest gets both tags, with the cp colours (bug 2)."""
    env.set_quest("a rat")
    env.set_cp("a rat")
    assert env.scan_line("  - a rat").line == "@x0@z14  - a rat - (CP) (Quest)@x"


def test_debug_goes_to_logger(env: Env, monkeypatch: pytest.MonkeyPatch) -> None:
    """Debug output is logged, never sent to the client (bug 6)."""
    from aardwolf.scanh.plugin import _scanh

    assert not hasattr(_scanh, "SendDataDirectlyToClient")
    log = MagicMock()
    monkeypatch.setattr(_scanh, "log_to", log)
    env.plugin._phook_initialize()
    env.plugin._trigger_start()
    assert log.call_args_list[-1].args == ([PLUGIN_ID], logging.DEBUG, "found {scan}")


def test_mxp_and_non_str_lines_untouched(env: Env) -> None:
    """A line with mxp mode set, or whose text is not a str, is left alone."""
    env.set_cp("a rat")
    assert env.scan_line("  - a rat", mxp_mode="open").line == "  - a rat"
    assert env.scan_line("  - a rat", line=b"  - a rat").line == b"  - a rat"
