"""Tests for the Aardwolf whois plugin, with a stubbed API that drives its triggers."""

import logging
import re
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from event_keys import assert_raised_described
from mudcmds_support import CoreHide
from statdb_support import make_db

import aardwolf
from aardwolf.whois.libs import END_REGEX, HIDE_MAX_LINES

if TYPE_CHECKING:
    from aardwolf.whois.plugin._whois import WhoisPlugin

PLUGIN_ID = "plugins.aardwolf.whois"
DASHES = "-" * 74
HEADER = "[ 201 Hero ]  Bast the Tester (Male Human)"
SINGLE = [
    DASHES,
    HEADER,
    "Quests Complete   : [ 12 ]   Campaigns Fld   : [ 3 ]",
    "Monsters Killed   : [ 456 ]",
    "Powerups Taken   : [ 5 ]   Powerups   : [ 3 ] [ 2 ]",
    DASHES,
]
MULTI = [
    DASHES,
    HEADER,
    "[Multiclass Player: Mage/Thief/Ranger ]",
    "Monsters Killed   : [ 456 ]",
    DASHES,
]
PROMPT = "[201/201hp 176/176mn 630/630mv 13qt 773tnl] >*[NOEXP]*"
REAL_REPLY = [
    DASHES,
    "[  4 T0   Half Thi] Cyrinik [C] (Male Ninja)",
    "",
    "Quests Complete   : [ 12 ]   Campaigns Fld   : [ 3 ]",
    "Monsters Killed   : [ 456 ]   Hours Online   : [ 7 ]",
    "",
    "Powerups Taken   : [ 5 ]   Powerups   : [ 3 ] [ 2 ]",
    DASHES,
    "To see warfare stats, use 'warinfo <player>'",
    "",
    PROMPT,
]
GMCP: dict[str, Any] = {
    "char.base.name": "Bast",
    "char.status.level": 50,
    "char.base.tier": 2,
    "char.base.redos": 1,
    "char.base.race": "Human",
    "char.base.subclass": "Sorcerer",
    "char.base.remorts": 1,
    "char.base.class": "Mage",
}


class FakeApi:
    """A stand-in for the bastproxy API that records the calls and drives the triggers."""

    def __init__(self) -> None:
        self.gmcp: dict[str, Any] = dict(GMCP)
        self.events_added: list[tuple[str, str]] = []
        self.registered: dict[str, Callable[..., Any]] = {}
        self.watches: list[tuple[str, str]] = []
        self.types: dict[str, dict[str, Any]] = {}
        self.finished: list[str] = []
        self.raised: list[tuple[str, dict[str, Any]]] = []
        self.triggers: dict[str, dict[str, Any]] = {}
        self.callbacks: dict[str, Callable[..., Any]] = {}
        # the real core hide window; the whois queue is the tests' own
        self.core = CoreHide(lambda: self.record)
        self.shown: list[str] = []
        self.hidden: list[str] = []
        self.group_toggles: list[tuple[str, bool]] = []
        self.trigger_toggles: list[tuple[str, bool]] = []
        self.add_ok = True
        self.record: dict[str, Any] = {}
        self.active = False
        self.queued: list[str] = []

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name."""
        table: dict[str, Callable[..., Any]] = {
            "plugins.core.events:event.add": self._event_add,
            "plugins.core.events:event.register": self._event_register,
            "plugins.core.events:event.raise": self._event_raise,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.watch:watch.add": lambda wname, regex: self.watches.append(
                (wname, regex)
            ),
            "plugins.core.mudcmds:type.add": self._type_add,
            "plugins.core.mudcmds:command.finish": self._command_finish,
            "plugins.core.mudcmds:command.queue": self.queued.append,
            "libs.api:character.is.active": lambda: self.active,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
            "plugins.core.triggers:trigger.toggle.enable": self._trigger_toggle,
            "plugins.core.triggers:group.toggle.enable": self._group_toggle,
            "libs.net.protocols:gmcp.value.get": self.gmcp.get,
        }
        return table[name]

    def _event_add(self, name: str, created_by: str, **kwargs: object) -> None:
        self.events_added.append((name, created_by))

    def _event_register(self, name: str, func: Callable[..., Any]) -> None:
        self.registered[name] = func

    def _event_raise(self, name: str, event_args: dict[str, Any] | None = None) -> None:
        self.raised.append((name, event_args or {}))

    def _type_add(self, cmdtype: str, cmd: str, regex: str, **kwargs: object) -> None:
        self.types[cmdtype] = {"cmd": cmd, "regex": regex, **kwargs}
        self.core.add_type(cmdtype, cmd, regex, **kwargs)

    def _command_finish(self, cmdtype: str) -> None:
        """Record the finish; the core closes the hide window of the command it sent."""
        self.finished.append(cmdtype)
        self.core.finished(cmdtype)

    def _trigger_add(self, name: str, regex: str, **kwargs: object) -> SimpleNamespace:
        self.triggers[name] = {
            "regex": regex,
            "enabled": kwargs.get("enabled", True),
            "group": kwargs.get("group"),
        }
        return SimpleNamespace(success=self.add_ok, trigger=SimpleNamespace(trigger_id=name))

    def _trigger_register(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        self.callbacks[trigger_id] = func
        return True

    def _trigger_toggle(self, name: str, flag: bool) -> bool:
        assert name in self.triggers, f"unknown trigger {name}"
        self.trigger_toggles.append((name, flag))
        self.triggers[name]["enabled"] = flag
        return True

    def _group_toggle(self, group: str, flag: bool) -> bool:
        assert any(t["group"] == group for t in self.triggers.values()), f"unknown group {group}"
        self.group_toggles.append((group, flag))
        for trigger in self.triggers.values():
            if trigger["group"] == group:
                trigger["enabled"] = flag
        return True

    def feed(
        self,
        lines: list[str],
        prompt: bool = False,
        is_prompt: Callable[[str], bool] | None = None,
    ) -> None:
        """Run each line through the triggers, as the triggers plugin does.

        The core hide window sees each line first. prompt marks the last line as a prompt;
        is_prompt decides per line instead.
        """
        for index, text in enumerate(lines):
            marked = is_prompt(text) if is_prompt else prompt and index == len(lines) - 1
            line = SimpleNamespace(noansi=text, is_prompt=marked, send=True, internal=False)
            self.record = {"matches": {}, "line": line}
            self.core.line()
            for name, trigger in list(self.triggers.items()):
                if not trigger["enabled"]:
                    continue
                match = re.match(trigger["regex"], text)
                if match and name in self.callbacks:
                    self.record = {"matches": match.groupdict(), "line": line}
                    self.callbacks[name]()
            (self.shown if line.send else self.hidden).append(text)

    def enabled(self) -> set[str]:
        """The names of the enabled triggers."""
        return {name for name, trigger in self.triggers.items() if trigger["enabled"]}


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: "WhoisPlugin", fake: FakeApi, home: Path) -> None:
        self.plugin = plugin
        self.fake = fake
        self.home = home

    def typed_whois(self) -> None:
        """A client types whois: the watch event fires."""
        self.fake.registered["watch_whois"]()

    def queued_whois(self) -> None:
        """A queued whois: mudcmds calls the type's beforef, then arms the hide window and sends."""
        self.fake.types["whois"]["beforef"]()
        self.fake.core.sent("whois", "whois")

    def disconnect(self) -> None:
        """The MUD link closes: the plugin and the core hide window see it."""
        self.plugin._eventcb_disconnect()
        self.fake.core.disconnect()


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build a WhoisPlugin with a fake API and load it."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from aardwolf.whois.plugin import _whois

    fake = FakeApi()
    plugin = _whois.WhoisPlugin.__new__(_whois.WhoisPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.plugin_info = SimpleNamespace(data_directory=tmp_path)  # type: ignore[assignment]
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    plugin._phook_initialize()
    yield Env(plugin, fake, tmp_path)


def test_character_first_active_queues_a_whois(env: Env) -> None:
    """Each first active queues a whois, with nothing else loaded."""
    env.fake.record = {"is_character_active": True}
    env.plugin._eventcb_character_active()
    assert env.fake.queued == ["whois"]
    env.plugin._eventcb_character_active()
    assert env.fake.queued == ["whois", "whois"]


def test_character_not_active_queues_nothing(env: Env) -> None:
    """An inactive record, or no record, queues no whois."""
    env.fake.record = {"is_character_active": False}
    env.plugin._eventcb_character_active()
    env.fake.record = {}
    env.plugin._eventcb_character_active()
    assert env.fake.queued == []


def test_load_while_active_queues_a_whois(env: Env) -> None:
    """Loading the plugin while the character is already active queues a whois."""
    assert env.fake.queued == []
    env.fake.active = True
    env.plugin._phook_initialize()
    assert env.fake.queued == ["whois"]


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.whois" in {p["plugin_id"] for p in result.plugins}


def test_after_load(env: Env) -> None:
    """after_load adds the event, the watch, the command type and seven disabled triggers."""
    fake = env.fake
    assert fake.events_added == [("ev_plugins.aardwolf.whois_received", PLUGIN_ID)]
    assert fake.watches == [("whois", r"^(whoi|whois)$")]
    assert "watch_whois" in fake.registered
    assert fake.types["whois"]["cmd"] == "whois"
    assert fake.types["whois"]["regex"] == r"^(whoi|whois)$"
    assert fake.types["whois"]["beforef"] == env.plugin._start_whois
    assert set(fake.triggers) == {
        "whoisheader",
        "whoisclasses",
        "whois1",
        "whois2",
        "whois3",
        "whoispowerup",
        "whoisend",
    }
    assert not fake.enabled()
    assert {n for n, t in fake.triggers.items() if t["group"] == PLUGIN_ID} == set(
        fake.triggers
    ) - {"whoisend"}
    assert set(fake.callbacks) == set(fake.triggers)


def test_failed_trigger_add_is_logged_and_not_toggled(env: Env) -> None:
    """When no trigger could be added, no toggle is attempted for the unknown group."""
    env.fake.add_ok = False
    env.fake.triggers.clear()
    env.fake.callbacks.clear()
    env.plugin._group_ready = env.plugin._end_ready = False
    env.plugin._phook_initialize()
    assert env.fake.callbacks == {}
    env.plugin._start_whois()
    env.plugin._eventcb_disconnect()
    assert env.fake.group_toggles == []
    assert env.fake.trigger_toggles == []


def test_single_class_typed_whois(env: Env) -> None:
    """A typed whois: the watch starts it, the fixture is parsed and the event raised once."""
    env.typed_whois()
    assert env.fake.enabled() == {
        "whoisheader",
        "whoisclasses",
        "whois1",
        "whois2",
        "whois3",
        "whoispowerup",
    }
    env.fake.feed(SINGLE)
    assert len(env.fake.raised) == 1
    name, payload = env.fake.raised[0]
    assert name == "ev_plugins.aardwolf.whois_received"
    assert payload["classes"] == [{"remort": 1, "class": "mag"}]
    assert payload["stats"]["questscomplete"] == "12"
    assert payload["stats"]["campaignsfld"] == "3"
    assert payload["stats"]["monsterskilled"] == "456"
    assert payload["powerupsall"] == "3"
    assert payload["powerupsmort"] == "2"
    assert payload["sex"] == "male"
    assert payload["race"] == "human"
    assert payload["name"] == "Bast"
    assert payload["totallevels"] == (2 + 1) * 1407 + 50
    assert env.fake.finished == ["whois"]


def test_queued_whois_calls_finish(env: Env) -> None:
    """A queued whois: beforef starts it, and the end line finishes the command."""
    env.queued_whois()
    env.fake.feed(SINGLE)
    assert len(env.fake.raised) == 1
    assert env.fake.finished == ["whois"]


def test_multiclass(env: Env) -> None:
    """The multiclass line sets the classes, overrides the remorts and feeds the total level."""
    env.fake.gmcp["char.base.remorts"] = 3
    env.typed_whois()
    env.fake.feed(MULTI)
    payload = env.fake.raised[0][1]
    assert payload["classes"] == [
        {"remort": 1, "class": "mag"},
        {"remort": 2, "class": "thi"},
        {"remort": 3, "class": "ran"},
    ]
    assert payload["remorts"] == 3
    assert payload["totallevels"] == 3 * 1407 + 2 * 201 + 50
    assert payload["stats"]["monsterskilled"] == "456"


def test_multiclass_line_overrides_gmcp_remorts(env: Env) -> None:
    """The class count replaces the GMCP remorts."""
    env.fake.gmcp["char.base.remorts"] = 2
    env.typed_whois()
    env.fake.feed(MULTI)
    assert env.fake.raised[0][1]["remorts"] == 3


def test_triggers_follow_the_whois_lifecycle(env: Env) -> None:
    """Triggers are off before the whois, on during it and off after the end line."""
    env.fake.feed(SINGLE)
    assert env.fake.raised == []
    env.typed_whois()
    env.fake.feed(SINGLE)
    assert len(env.fake.raised) == 1
    assert not env.fake.enabled()
    env.fake.feed(SINGLE)
    assert len(env.fake.raised) == 1


def test_dashed_line_before_the_header_does_not_end_the_whois(env: Env) -> None:
    """The end trigger is only on from the header."""
    env.typed_whois()
    env.fake.feed([DASHES])
    assert env.fake.raised == []
    assert "whoisend" not in env.fake.enabled()
    env.fake.feed([HEADER])
    assert "whoisend" in env.fake.enabled()


def test_payload_is_a_plain_copy(env: Env) -> None:
    """The raised payload is a plain dict that does not change the saved state."""
    env.typed_whois()
    env.fake.feed(SINGLE)
    payload = env.fake.raised[0][1]
    assert type(payload) is dict
    payload["name"] = "changed"
    assert env.plugin.whois["name"] == "Bast"


def test_disconnect_turns_the_triggers_off(env: Env) -> None:
    """A disconnect in the middle of a whois turns the group and whoisend off."""
    env.typed_whois()
    env.fake.feed(SINGLE[:2])
    assert "whoisend" in env.fake.enabled()
    env.plugin._eventcb_disconnect()
    assert not env.fake.enabled()


def test_start_clears_the_old_state(env: Env) -> None:
    """A new whois starts from an empty state."""
    env.plugin.whois["old"] = "x"
    env.typed_whois()
    assert "old" not in env.plugin.whois


def test_missing_gmcp_does_not_raise(env: Env) -> None:
    """A whois with no GMCP values still ends and raises."""
    env.fake.gmcp.clear()
    env.typed_whois()
    env.fake.feed(SINGLE)
    payload = env.fake.raised[0][1]
    assert payload["name"] == ""
    assert payload["classes"] == []


def test_state_is_persisted(env: Env) -> None:
    """After a whois a new dict on the same file has the state, and the save hook syncs."""
    from bastproxy.libs.persistentdict import PersistentDict

    env.typed_whois()
    env.fake.feed(SINGLE)
    again = PersistentDict(PLUGIN_ID, env.home / "whois.txt", "c")
    assert again["name"] == "Bast"
    assert again["monsterskilled"] == "456"
    env.plugin.whois["extra"] = 1
    env.plugin._phook_save()
    assert PersistentDict(PLUGIN_ID, env.home / "whois.txt", "c")["extra"] == 1


def test_payload_is_saved_by_statdb(env: Env, tmp_path: Path) -> None:
    """The raised payload feeds statdb's save_whois."""
    from aardwolf.statdb.libs import StatStore

    env.fake.gmcp["char.base.remorts"] = 3
    env.typed_whois()
    env.fake.feed(MULTI)
    database = make_db(tmp_path / "db")
    try:
        store = StatStore(database)
        store.save_whois(env.fake.raised[0][1])
        row = database.select("SELECT * FROM stats WHERE milestone = 'current'")[0]
        assert row["name"] == "Bast"
        assert row["totallevels"] == 3 * 1407 + 2 * 201 + 50
        assert row["monsterskilled"] == 456
        assert store.get_classes() == ["mage", "thief", "ranger"]
    finally:
        database.close()


def test_raised_keys_are_all_described(env: Env) -> None:
    """The payload has only described top-level keys, and the stat lines are under stats (#43)."""
    from aardwolf.whois.plugin._whois import EVENT_ARGS, EVENT_WHOIS

    env.typed_whois()
    env.fake.feed(SINGLE)
    event = {EVENT_WHOIS: {"arg_descriptions": EVENT_ARGS}}
    assert_raised_described(env.fake.raised, event)
    payload = env.fake.raised[0][1]
    assert payload["stats"]["questscomplete"] == "12"
    assert payload["stats"]["monsterskilled"] == "456"
    assert "questscomplete" not in payload
    assert payload["powerupsall"] == "3"


def test_queued_whois_is_hidden_to_the_prompt(env: Env) -> None:
    """Every line of a queued whois is hidden, blanks and the prompt included."""
    env.queued_whois()
    env.fake.feed(REAL_REPLY, prompt=True)
    assert env.fake.hidden == REAL_REPLY
    assert env.fake.shown == []
    assert not env.fake.core.is_open()
    assert env.fake.finished == ["whois"]
    env.fake.feed(["Next line"])
    assert env.fake.shown == ["Next line"]


def test_typed_whois_is_shown(env: Env) -> None:
    """A typed whois is shown in full and never arms a hide window."""
    env.typed_whois()
    env.fake.feed(REAL_REPLY, prompt=True)
    assert env.fake.shown == REAL_REPLY
    assert env.fake.hidden == []
    assert not env.fake.core.is_armed()
    assert not env.fake.core.is_open()


def test_hidden_and_typed_whois_parse_the_same(env: Env) -> None:
    """Hiding does not change the saved state or the event payload."""
    env.queued_whois()
    env.fake.feed(REAL_REPLY, prompt=True)
    queued_state = dict(env.plugin.whois)
    env.typed_whois()
    env.fake.feed(REAL_REPLY, prompt=True)
    assert queued_state["name"] == "Bast"
    assert dict(env.plugin.whois) == queued_state
    assert len(env.fake.raised) == 2
    assert env.fake.raised[0] == env.fake.raised[1]
    assert env.fake.finished == ["whois", "whois"]


def test_lines_before_the_first_dashes_are_shown(env: Env) -> None:
    """Lines between the queued send and the reply are not hidden."""
    env.queued_whois()
    env.fake.feed(["You say 'hi'"])
    env.fake.feed(["[1/1hp] >"], prompt=True)
    assert env.fake.shown == ["You say 'hi'", "[1/1hp] >"]
    assert not env.fake.core.is_open()
    assert env.fake.core.is_armed()
    env.fake.feed(REAL_REPLY, prompt=True)
    assert env.fake.hidden == REAL_REPLY


def test_closing_dashes_do_not_restart_the_window(env: Env) -> None:
    """The window opens at the first dashes; the closing dashes keep the same open window."""
    env.queued_whois()
    env.fake.feed(REAL_REPLY[:7])
    window = env.fake.core.core._hide_open
    assert window is not None
    env.fake.feed(REAL_REPLY[7:8])
    assert env.fake.core.core._hide_open is window
    assert not env.fake.core.is_armed()


def test_window_ends_at_the_line_cap(env: Env, caplog: pytest.LogCaptureFixture) -> None:
    """Without a prompt, the dashes and HIDE_MAX_LINES lines are hidden and the next is shown."""
    env.queued_whois()
    others = [f"line {i}" for i in range(HIDE_MAX_LINES + 1)]
    with caplog.at_level(logging.WARNING):
        env.fake.feed([DASHES, *others])
    assert env.fake.hidden == [DASHES, *others[:HIDE_MAX_LINES]]
    assert env.fake.shown == [others[-1]]
    assert not env.fake.core.is_open()
    caps = [r for r in caplog.records if "reached its cap" in r.getMessage()]
    assert len(caps) == 1
    assert caps[0].levelno == logging.WARNING


def test_disconnect_mid_window_closes_it(env: Env) -> None:
    """A disconnect closes the window."""
    env.queued_whois()
    env.fake.feed(REAL_REPLY[:3])
    assert env.fake.core.is_open()
    env.disconnect()
    assert not env.fake.core.is_open()
    env.fake.feed(["Hello"])
    assert env.fake.shown == ["Hello"]


def test_disconnect_before_the_dashes_clears_the_flag(env: Env) -> None:
    """A later typed whois is shown after a disconnect that followed a queued send."""
    env.queued_whois()
    assert env.fake.core.is_armed()
    env.disconnect()
    assert not env.fake.core.is_armed()
    env.typed_whois()
    env.fake.feed(REAL_REPLY, prompt=True)
    assert env.fake.shown == REAL_REPLY


def test_typed_whois_after_a_queued_one_timed_out_is_shown(env: Env) -> None:
    """After the unanswered queued whois times out, its window is gone and a typed one shows."""
    env.queued_whois()
    env.fake.core.timed_out("whois")
    assert not env.fake.core.is_armed()
    env.typed_whois()
    env.fake.feed(REAL_REPLY, prompt=True)
    assert env.fake.shown == REAL_REPLY
    assert env.fake.hidden == []


def test_typed_whois_reply_before_the_queued_one_times_out_is_hidden(env: Env) -> None:
    """Behaviour change: the armed window opens on the first dashes, whoever sent the whois."""
    env.queued_whois()
    env.typed_whois()
    env.fake.feed(REAL_REPLY, prompt=True)
    assert env.fake.hidden == REAL_REPLY
    assert env.fake.shown == []
    assert env.fake.finished == ["whois"]
    assert not env.fake.core.is_open()


def test_whois_type_hides_its_output_through_mudcmds(env: Env) -> None:
    """The type opens on the first 74-dash line, has no end regex and caps at the cap plus one."""
    kwargs = env.fake.types["whois"]
    assert kwargs["hide_output"] is True
    assert kwargs["hide_start"] == END_REGEX
    assert "hide_end" not in kwargs
    assert kwargs["hide_max"] == HIDE_MAX_LINES + 1
    assert env.fake.core.core.cmds["whois"].hide_output is True


def test_marked_prompt_from_promptfix_closes_the_window(
    env: Env, caplog: pytest.LogCaptureFixture
) -> None:
    """The window closes at a prompt recognised from the template, with no cap warning."""
    from aardwolf.promptfix.libs import build_prompt_pattern, is_prompt_text

    template = "@R[@W%h@R/@W%H@Rhp %m/%Mmn %v/%Vmv %qqt %Xtnl@R] >%c"
    regex = build_prompt_pattern(template).regex
    assert regex is not None
    env.queued_whois()
    with caplog.at_level(logging.WARNING):
        env.fake.feed(REAL_REPLY, is_prompt=lambda text: is_prompt_text(text, [regex]))
        env.fake.feed(["Next line"])
    assert env.fake.hidden == REAL_REPLY
    assert env.fake.shown == ["Next line"]
    assert not env.fake.core.is_open()
    assert not [r for r in caplog.records if "reached its cap" in r.getMessage()]
