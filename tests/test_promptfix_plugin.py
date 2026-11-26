"""Tests for the Aardwolf prompt fixer plugin, with a stubbed API."""

import inspect
import logging
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

import aardwolf
from aardwolf.promptfix.libs import PROMPT_MARK_PRIORITY, PROMPT_SET_REGEX

if TYPE_CHECKING:
    from bastproxy.libs.records import NetworkData

    from aardwolf.promptfix.plugin._promptfix import PromptFixPlugin

PLUGIN_ID = "plugins.aardwolf.promptfix"
MAIN = "[%h/%Hhp] > "
BATTLE = "[%h] @R%e"


class FakeApi:
    """A stand-in for the bastproxy API that records what the plugin calls."""

    def __init__(self) -> None:
        self.autofix = True
        self.mud_connected = True
        self.character_active = True
        self.gmcp_send_ok = True
        self.sent_gmcp: list[str] = []
        self.record: dict[str, Any] = {}
        self.settings_added: list[tuple[Any, ...]] = []
        self.trigger_adds: list[tuple[str, str]] = []
        self.trigger_regs: list[tuple[str, Callable[..., Any]]] = []

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "libs.net.protocols:gmcp.send": self._gmcp_send,
            "plugins.core.proxy:mud.is.connected": lambda: self.mud_connected,
            "libs.api:character.is.active": lambda: self.character_active,
            "plugins.core.settings:setting.add": lambda *args: self.settings_added.append(args),
            "plugins.core.settings:setting.get": lambda pid, name: self.autofix,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
        }
        return table[name]

    def _gmcp_send(self, package: str) -> bool:
        if self.gmcp_send_ok:
            self.sent_gmcp.append(package)
        return self.gmcp_send_ok

    def _trigger_add(self, name: str, regex: str) -> SimpleNamespace:
        self.trigger_adds.append((name, regex))
        return SimpleNamespace(success=True, trigger=SimpleNamespace(trigger_id="tid"))

    def _trigger_register(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        self.trigger_regs.append((trigger_id, func))
        return True


class Env:
    """The plugin under test with its fake API and what it sent."""

    def __init__(
        self,
        module: ModuleType,
        plugin: "PromptFixPlugin",
        fake: FakeApi,
        mud: list[str],
        client: list[str],
    ) -> None:
        self.module = module
        self.plugin = plugin
        self.fake = fake
        self.mud = mud
        self.client = client

    def prompts(self, **data: object) -> None:
        """Deliver a char.prompts event with the given data."""
        self.fake.record = {"package": "char.prompts", "data": data}
        self.plugin._eventcb_prompts()


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build a PromptFixPlugin with a fake API."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from aardwolf.promptfix.plugin import _promptfix

    mud: list[str] = []
    client: list[str] = []

    def make_sender(sink: list[str]) -> type:
        class FakeSend:
            def __init__(self, message: "NetworkData") -> None:
                self.message = message

            def __call__(self) -> None:
                sink.extend(str(item.line) for item in self.message)

        return FakeSend

    monkeypatch.setattr(_promptfix, "SendDataDirectlyToMud", make_sender(mud))
    monkeypatch.setattr(_promptfix, "SendDataDirectlyToClient", make_sender(client))
    fake = FakeApi()
    plugin = _promptfix.PromptFixPlugin.__new__(_promptfix.PromptFixPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    yield Env(_promptfix, plugin, fake, mud, client)


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.promptfix" in {p["plugin_id"] for p in result.plugins}


def test_after_load(env: Env) -> None:
    """after_load adds the setting and the trigger, and sends nothing."""
    env.plugin._phook_initialize()
    assert env.fake.settings_added[0][:3] == (PLUGIN_ID, "autofix", True)
    assert env.fake.trigger_adds == [("promptfix_set", PROMPT_SET_REGEX)]
    assert env.fake.trigger_regs == [("tid", env.plugin._trigger_prompt_set)]
    assert env.fake.sent_gmcp == []


def test_registered_events_of_its_own_setting(env: Env) -> None:
    """The setting event is named from the plugin id; no other event carries the plugin's id."""
    names: set[str] = set()
    for _, method in inspect.getmembers(env.plugin, inspect.ismethod):
        for item in getattr(method, "event_registration", []):
            names.add(item["event_name"].format(**env.plugin.__dict__))
    own = {name for name in names if name.startswith(f"ev_{PLUGIN_ID}_")}
    assert own == {f"ev_{PLUGIN_ID}_var_autofix_modified"}


def test_character_active_requests_once(env: Env) -> None:
    """First active sends one request; a second while one waits sends none."""
    env.plugin._phook_character_active()
    env.plugin._phook_character_active()
    assert env.fake.sent_gmcp == ["request prompt"]
    assert env.plugin._requesting


def test_trigger_requests(env: Env) -> None:
    """The prompt set trigger requests the prompts."""
    assert re.search(PROMPT_SET_REGEX, "Prompt set to: x")
    env.plugin._trigger_prompt_set()
    assert env.fake.sent_gmcp == ["request prompt"]


def test_failed_send_leaves_requesting_false(env: Env) -> None:
    """A request that was not sent does not block the next one."""
    env.fake.gmcp_send_ok = False
    env.plugin._trigger_prompt_set()
    assert not env.plugin._requesting
    env.fake.gmcp_send_ok = True
    env.plugin._trigger_prompt_set()
    assert env.fake.sent_gmcp == ["request prompt"]


def test_both_prompts_fixed(env: Env) -> None:
    """Both prompts without %c are sent to the mud fixed, and the client is told."""
    env.plugin._requesting = True
    env.prompts(main=MAIN, battle=BATTLE)
    assert env.mud == ["prompt [%h/%Hhp] >%c", "bprompt [%h] @R%e%c"]
    assert len(env.client) == 2
    assert "battle prompt" in env.client[1]
    assert all("%h" not in line for line in env.client)
    assert not env.plugin._requesting


def test_prompts_already_fine(env: Env) -> None:
    """Prompts that end in %c send nothing."""
    env.prompts(main="x%c", battle="y%c@w ")
    assert env.mud == []
    assert env.client == []


def test_too_long_main_still_fixes_battle(env: Env) -> None:
    """A too long prompt is not sent and the client is told; the other is still fixed."""
    env.prompts(main="a" * 79, battle="b")
    assert env.mud == ["bprompt b%c"]
    assert len(env.client) == 2
    assert "80" in env.client[0]
    assert "prompt" in env.client[0]


def test_bad_data_skipped(env: Env) -> None:
    """Data that is not a dict, and a prompt that is not a string, are skipped."""
    env.fake.record = {"data": "nope"}
    env.plugin._eventcb_prompts()
    env.prompts(main=5, battle="b")
    assert env.mud == ["bprompt b%c"]


def test_autofix_off(env: Env) -> None:
    """With the fixer off nothing is requested or sent, and the waiting flag clears."""
    env.fake.autofix = False
    env.plugin._phook_character_active()
    env.plugin._trigger_prompt_set()
    assert env.fake.sent_gmcp == []
    env.plugin._requesting = True
    env.prompts(main=MAIN, battle=BATTLE)
    assert env.mud == []
    assert env.client == []
    assert not env.plugin._requesting


def test_autofix_modified(env: Env) -> None:
    """Turning the fixer on requests only when connected and active, never on load."""
    env.fake.record = {"oldvalue": "__init__", "newvalue": True}
    env.plugin._eventcb_autofix_modified()
    assert env.fake.sent_gmcp == []
    env.fake.record = {"oldvalue": False, "newvalue": False}
    env.plugin._eventcb_autofix_modified()
    assert env.fake.sent_gmcp == []
    env.fake.record = {"oldvalue": False, "newvalue": True}
    env.fake.character_active = False
    env.plugin._eventcb_autofix_modified()
    assert env.fake.sent_gmcp == []
    env.fake.character_active = True
    env.plugin._eventcb_autofix_modified()
    assert env.fake.sent_gmcp == ["request prompt"]


def test_disconnect_clears_requesting(env: Env) -> None:
    """A mud disconnect clears the waiting request."""
    env.plugin._requesting = True
    env.plugin._eventcb_disconnect()
    assert not env.plugin._requesting


TEMPLATE_MAIN = "[%h/%Hhp] >%c"
TEMPLATE_BATTLE = "[%h] Enemy: %e%c"
LOOSE = "%h%m%c"


def line(text: str, *, frommud: bool = True, internal: bool = False) -> SimpleNamespace:
    """Return a stand-in line."""
    return SimpleNamespace(noansi=text, frommud=frommud, internal=internal, is_prompt=False)


def mark(env: Env, text: str, **kwargs: bool) -> bool:
    """Run the mark callback on a line and return its is_prompt."""
    obj = line(text, **kwargs)
    env.fake.record = {"line": obj}
    env.plugin._eventcb_mark_prompt()
    return bool(obj.is_prompt)


def test_patterns_mark_matching_mud_lines(env: Env) -> None:
    """Both templates build patterns; a matching line is marked and others are not."""
    env.prompts(main=TEMPLATE_MAIN, battle=TEMPLATE_BATTLE)
    assert set(env.plugin._prompt_patterns) == {"main", "battle"}
    assert mark(env, "[5/10hp] >")
    assert mark(env, "[5] Enemy: 50%")
    assert not mark(env, "Some other line")


def test_battle_line_with_a_spaced_value_is_marked(env: Env) -> None:
    """A battle template whose value holds spaces still marks its line (#178)."""
    env.prompts(main=TEMPLATE_MAIN, battle="[Combat: %hhp %b ]>%c")
    assert mark(env, "[Combat: 5hp Enemy: 100% ]>")
    assert mark(env, "[5/10hp] >")
    assert not mark(env, "Some other line")


def test_internal_and_client_lines_are_never_marked(env: Env) -> None:
    """Only lines from the mud are marked."""
    env.prompts(main=TEMPLATE_MAIN)
    assert not mark(env, "[5/10hp] >", frommud=False, internal=True)
    assert not mark(env, "[5/10hp] >", frommud=False)


def test_missing_line_or_text_is_skipped(env: Env) -> None:
    """A record without a line, or a line without text, is left alone."""
    env.prompts(main=TEMPLATE_MAIN)
    env.fake.record = {}
    env.plugin._eventcb_mark_prompt()
    obj = SimpleNamespace(noansi=None, frommud=True, is_prompt=False)
    env.fake.record = {"line": obj}
    env.plugin._eventcb_mark_prompt()
    assert obj.is_prompt is False


def test_new_template_replaces_the_old_pattern(env: Env) -> None:
    """A new char.prompts drops the old pattern."""
    env.prompts(main=TEMPLATE_MAIN)
    env.prompts(main="<%h> prompt%c")
    assert not mark(env, "[5/10hp] >")
    assert mark(env, "<5> prompt")


def test_template_without_newline_clears_the_pattern(env: Env) -> None:
    """A template without %c clears its key; the fix is sent and nothing is marked."""
    env.prompts(main=TEMPLATE_MAIN)
    env.prompts(main="[%h/%Hhp] >")
    assert env.mud == ["prompt [%h/%Hhp] >%c"]
    assert "main" not in env.plugin._prompt_patterns
    assert not mark(env, "[5/10hp] >")
    env.prompts(main="[%h/%Hhp] >%c")
    assert mark(env, "[5/10hp] >")


def test_key_missing_from_the_data_keeps_its_pattern(env: Env) -> None:
    """A char.prompts without a key does not clear that key's pattern."""
    env.prompts(main=TEMPLATE_MAIN, battle=TEMPLATE_BATTLE)
    env.prompts(battle=TEMPLATE_BATTLE)
    assert mark(env, "[5/10hp] >")


def test_loose_template_warns_once_and_marks_nothing(
    env: Env, caplog: pytest.LogCaptureFixture
) -> None:
    """A code-only template logs one warning for the same template, without its text."""
    with caplog.at_level(logging.WARNING):
        env.prompts(main=LOOSE)
        env.prompts(main=LOOSE)
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert LOOSE not in warnings[0].getMessage()
    assert not env.plugin._prompt_patterns
    assert not mark(env, "12 34")


def test_autofix_off_still_builds_patterns(env: Env) -> None:
    """With autofix off patterns are built and nothing is sent."""
    env.fake.autofix = False
    env.prompts(main=TEMPLATE_MAIN, battle="x")
    assert env.mud == []
    assert env.client == []
    assert mark(env, "[5/10hp] >")


def test_disconnect_clears_the_patterns(env: Env) -> None:
    """The next login may be another character."""
    env.prompts(main=TEMPLATE_MAIN)
    env.plugin._eventcb_disconnect()
    assert not mark(env, "[5/10hp] >")


def test_mark_callback_is_registered_before_the_core_waiters() -> None:
    """The callback registers on the line modify event at PROMPT_MARK_PRIORITY."""
    from aardwolf.promptfix.plugin._promptfix import PromptFixPlugin

    registrations = PromptFixPlugin._eventcb_mark_prompt.event_registration
    assert registrations == [
        {"event_name": "ev_to_client_data_modify", "priority": PROMPT_MARK_PRIORITY}
    ]
    assert PROMPT_MARK_PRIORITY < 40
