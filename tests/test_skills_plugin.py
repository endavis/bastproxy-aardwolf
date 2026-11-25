"""Tests for the Aardwolf skills plugin, with a stubbed API that drives its triggers."""

import re
from collections.abc import Callable, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from event_keys import assert_raised_described
from mudcmds_support import CoreHide

import aardwolf
from aardwolf.skills.libs import (
    A102_OPTIONS,
    ARGS_FULL,
    ARGS_SPELLUP,
    CMDTYPE,
    CMDTYPE_SPELLUP,
    HIDE_END_FULL,
    HIDE_END_SPELLUP,
    HIDE_MAX_LINES,
    HIDE_START_FULL,
    HIDE_START_SPELLUP,
    TRIGGERS,
)
from aardwolf.skills.libs import EVENTS as SUFFIX_EVENTS

if TYPE_CHECKING:
    from bastproxy.libs.records import NetworkData

    from aardwolf.skills.plugin._skills import SkillsPlugin

PLUGIN_ID = "plugins.aardwolf.skills"
EVENT_AFFECTED_UPDATE = f"ev_{PLUGIN_ID}_affected_update"
EVENT_AFFOFF = f"ev_{PLUGIN_ID}_affoff"
EVENT_AFFON = f"ev_{PLUGIN_ID}_affon"
EVENT_FAIL = f"ev_{PLUGIN_ID}_fail"
EVENT_GAIN = f"ev_{PLUGIN_ID}_gain"
EVENT_RECOFF = f"ev_{PLUGIN_ID}_recoff"
EVENT_RECON = f"ev_{PLUGIN_ID}_recon"
EVENT_UPTODATE = f"ev_{PLUGIN_ID}_uptodate"
EVENTS = {f"ev_{PLUGIN_ID}_{suffix}": info for suffix, info in SUFFIX_EVENTS.items()}
NOW = 1000.0
GROUPS = ("slist", "slist_spells", "slist_recoveries")
FULL_Q = f"slist {ARGS_FULL}"
SPELLUP_Q = f"slist {ARGS_SPELLUP}"

SPELLS = (
    "14,armor,2,0,85,-1,1",
    "15,fireball,1,0,90,4,1",
    "20,bash door,0,0,5,-1,2",
)
RECOVERIES = ("4,leadership,0",)


def full_block() -> list[str]:
    """Return the lines of ``slist noprompt``."""
    return [
        "{spellheaders noprompt}",
        *SPELLS,
        "{/spellheaders}",
        "{recoveries noprompt}",
        *RECOVERIES,
        "{/recoveries}",
    ]


def spellup_block(*sns: str) -> list[str]:
    """Return the lines of ``slist spellup noprompt`` for the given spell lines."""
    return ["{spellheaders spellup noprompt}", *sns, "{/spellheaders}"]


class FakeApi:
    """A stand-in for the bastproxy API that records the calls and drives the triggers."""

    def __init__(self) -> None:
        self.events_added: dict[str, dict[str, Any]] = {}
        self.raised: list[tuple[str, dict[str, Any]]] = []
        self.triggers: dict[str, str] = {}
        self.kwargs: dict[str, dict[str, Any]] = {}
        self.trigger_cbs: dict[str, list[Callable[..., Any]]] = {}
        self.enabled: dict[str, bool] = {}
        self.toggles: list[tuple[str, bool]] = []
        self.a102: list[tuple[str, bool]] = []
        self.add_ok = True
        self.record: dict[str, Any] = {}
        self.args: dict[str, Any] = {}
        self.shown: list[str] = []
        self.hidden: list[str] = []
        self.types: dict[str, dict[str, Any]] = {}
        self.queued: list[str] = []
        self.pending: list[tuple[str, str]] = []
        self.cmds: dict[str, str] = {}
        # the real core hide window; the queue below is the fake's own
        self.core = CoreHide(lambda: self.record)
        self.started: list[str] = []
        self.finished: list[str] = []
        self.current: str | None = None
        self.table: dict[str, Callable[..., Any]] = {
            "plugins.core.events:event.add": self._event_add,
            "plugins.core.events:event.raise": self._event_raise,
            "plugins.core.events:event.current.record.get": lambda: self.record,
            "plugins.core.triggers:trigger.add": self._trigger_add,
            "plugins.core.triggers:trigger.register": self._trigger_register,
            "plugins.core.triggers:trigger.unregister": self._trigger_unregister,
            "plugins.core.triggers:group.toggle.enable": self._group_toggle,
            "plugins.core.mudcmds:type.add": self._type_add,
            "plugins.core.mudcmds:command.queue": self._command_queue,
            "plugins.core.mudcmds:command.start": self.started.append,
            "plugins.core.mudcmds:command.finish": self._command_finish,
            "plugins.aardwolf.a102:option.toggle": lambda name, flag: self.a102.append(
                (name, flag)
            ),
            "plugins.core.utils:timedelta.to.string": lambda start, end: f"{end - start:.0f}s",
            "plugins.core.commands:command.current.args.get": lambda: self.args,
        }

    def __call__(self, name: str) -> Callable[..., Any]:
        """Return the fake for an API name; an unknown name is a KeyError."""
        return self.table[name]

    def _event_add(self, name: str, created_by: str, **kwargs: object) -> None:
        self.events_added[name] = kwargs

    def _event_raise(self, name: str, event_args: dict[str, Any] | None = None) -> None:
        self.raised.append((name, event_args or {}))

    def _trigger_add(self, name: str, regex: str, **kwargs: object) -> SimpleNamespace:
        self.triggers[name] = regex
        self.kwargs[name] = dict(kwargs)
        self.enabled[name] = bool(kwargs.get("enabled", True))
        self.trigger_cbs.setdefault(name, [])
        return SimpleNamespace(success=self.add_ok, trigger=SimpleNamespace(trigger_id=name))

    def _trigger_register(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        assert trigger_id in self.trigger_cbs
        self.trigger_cbs.setdefault(trigger_id, []).append(func)
        return True

    def _trigger_unregister(self, trigger_id: str, func: Callable[..., Any]) -> bool:
        self.trigger_cbs[trigger_id].remove(func)
        return True

    def _group_toggle(self, group: str, flag: bool) -> None:
        self.toggles.append((group, flag))
        for name, kwargs in self.kwargs.items():
            if kwargs.get("group") == group:
                self.enabled[name] = flag

    def _type_add(self, cmdtype: str, cmd: str, regex: str, **kwargs: object) -> None:
        self.types[cmdtype] = dict(kwargs)
        self.cmds[cmdtype] = cmd
        self.core.add_type(cmdtype, cmd, regex, **kwargs)

    def _command_queue(self, cmdtype: str, arguments: str = "") -> None:
        """Queue a command like mudcmds: one already pending or running is not queued twice."""
        cmd = f"{self.cmds[cmdtype]} {arguments}".strip()
        if cmd in [queued for _, queued in self.pending] or cmd == self.current:
            return
        self.queued.append(cmd)
        if self.current is None:
            self.begin(cmdtype, cmd)
        else:
            self.pending.append((cmdtype, cmd))

    def begin(self, cmdtype: str, cmd: str) -> None:
        """Send a command: its beforef runs, then core arms the hide window."""
        self.current = cmd
        self.types[cmdtype]["beforef"]()
        self.core.sent(cmdtype, cmd)

    def _command_finish(self, cmdtype: str) -> None:
        """Finish the command, run its after function and send the next one."""
        self.finished.append(cmdtype)
        if self.current is not None:
            self.current = None
            self.types[cmdtype]["afterf"]()
            self.core.finished(cmdtype)
            if self.pending and self.current is None:
                self.begin(*self.pending.pop(0))

    def disconnect(self) -> None:
        """The MUD link closed: the core drops its hide windows."""
        self.core.disconnect()

    def group_on(self, suffix: str) -> bool:
        """Return True when every trigger of the group is on."""
        group = f"{PLUGIN_ID}.{suffix}"
        names = [n for n, k in self.kwargs.items() if k.get("group") == group]
        assert names
        return all(self.enabled[n] for n in names)

    def feed(self, *lines: str, prompt: bool = False) -> None:
        """Run each line through the before-all callbacks and the enabled triggers."""
        for line in lines:
            line_obj = SimpleNamespace(noansi=line, is_prompt=prompt, send=True, internal=False)
            self.record = {"matches": {}, "line": line_obj}
            self.core.line()
            for name, regex in list(self.triggers.items()):
                match = re.match(regex, line)
                if not match or not self.enabled[name]:
                    continue
                groups = match.groupdict()
                for arg, argtype in (self.kwargs[name].get("argtypes") or {}).items():
                    groups[arg] = argtype(groups[arg])
                if self.kwargs[name].get("omit"):
                    line_obj.send = False
                self.record = {"matches": groups, "line": line_obj}
                for func in list(self.trigger_cbs[name]):
                    func()
            (self.shown if line_obj.send else self.hidden).append(line)

    def events(self, name: str) -> list[dict[str, Any]]:
        """The payloads raised for an event."""
        return [payload for event, payload in self.raised if event == name]


class Env:
    """The plugin under test with its fake API."""

    def __init__(self, plugin: "SkillsPlugin", fake: FakeApi, sent: list[str]) -> None:
        self.plugin = plugin
        self.fake = fake
        self.sent = sent

    def disconnect(self) -> None:
        """The MUD link closes: the plugin and the core hide window see it."""
        self.plugin._eventcb_disconnect()
        self.fake.disconnect()

    def load_all(self) -> None:
        """Run the queued full and spellup slists, as the MUD answers them."""
        self.plugin._refresh()
        self.fake.feed(*full_block())
        self.fake.feed(*spellup_block(SPELLS[0]))


def build(fake: FakeApi) -> "SkillsPlugin":
    """Build and load a plugin."""
    from aardwolf.skills.plugin import _skills

    plugin = _skills.SkillsPlugin.__new__(_skills.SkillsPlugin)
    plugin.plugin_id = PLUGIN_ID
    plugin.api = MagicMock(side_effect=fake)
    plugin._phook_init_plugin()
    plugin._phook_initialize()
    return plugin


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Env]:
    """Build a SkillsPlugin with a fake API and load it."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from aardwolf.skills.plugin import _skills

    sent: list[str] = []

    class FakeSend:
        def __init__(self, message: "NetworkData") -> None:
            self.message = message

        def __call__(self) -> None:
            sent.extend(str(item.line) for item in self.message)

    monkeypatch.setattr(_skills, "SendDataDirectlyToMud", FakeSend)
    monkeypatch.setattr(_skills.SkillsPlugin, "_now", staticmethod(lambda: NOW))
    fake = FakeApi()
    result = Env(build(fake), fake, sent)
    yield result
    assert_raised_described(fake.raised, EVENTS)


def test_plugin_is_discovered(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The loader's discovery finds the plugin without errors."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    from bastproxy.libs.plugins.imputils import find_packages_and_plugins

    result = find_packages_and_plugins(Path(aardwolf.__file__).resolve().parent, "aardwolf.")
    assert not result.errors
    assert "aardwolf.skills" in {p["plugin_id"] for p in result.plugins}


def test_dependencies() -> None:
    """The plugin needs a102 and mudcmds, and not the level plugin."""
    from aardwolf import skills

    assert "plugins.aardwolf.a102" in skills.PLUGIN_DEPENDENCIES
    assert "plugins.core.mudcmds" in skills.PLUGIN_DEPENDENCIES
    assert "plugins.aardwolf.level" not in skills.PLUGIN_DEPENDENCIES


def test_after_load_adds_events_type_triggers_and_tags(env: Env) -> None:
    """The 8 events, the slist type, the triggers and the tag toggles are added."""
    assert set(env.fake.events_added) == set(EVENTS)
    assert len(env.fake.events_added) == 8
    assert set(env.fake.types) == {CMDTYPE, CMDTYPE_SPELLUP}
    assert set(env.fake.triggers) == {spec.name for spec in TRIGGERS}
    omitted = {n for n, k in env.fake.kwargs.items() if k.get("omit")}
    assert omitted == {s.name for s in TRIGGERS if s.omit}
    assert "skills_affon" not in omitted
    assert env.fake.kwargs["skills_start"]["group"] == f"{PLUGIN_ID}.slist"
    assert env.fake.kwargs["skills_spell_line"]["group"] == f"{PLUGIN_ID}.slist_spells"
    assert env.fake.kwargs["skills_recov_line"]["group"] == f"{PLUGIN_ID}.slist_recoveries"
    assert env.fake.enabled["skills_affon"]
    assert not env.fake.enabled["skills_start"]
    assert env.fake.a102 == [(name, True) for name in A102_OPTIONS]


def test_character_active_with_an_empty_table_queues_both_slists(env: Env) -> None:
    """The first active reads the full slist, then the spellups."""
    env.plugin._phook_character_active()
    assert env.fake.queued == [FULL_Q, SPELLUP_Q]


def test_character_active_with_a_known_table_queues_nothing(env: Env) -> None:
    """A full, up-to-date table is not read again."""
    env.load_all()
    env.fake.queued.clear()
    env.plugin._phook_character_active()
    assert env.fake.queued == []


def test_full_slist_fills_the_table_and_hides_every_line(env: Env) -> None:
    """A full block fills skills and recoveries, hides all of it, and shows the next prompt."""
    env.plugin._refresh()
    assert env.fake.started == [CMDTYPE]
    assert env.fake.group_on("slist")
    env.fake.pending.clear()
    env.fake.feed(*full_block())
    env.fake.feed("<100hp>", prompt=True)
    assert env.fake.shown == ["<100hp>"]
    assert env.fake.hidden == full_block()
    assert "{/spellheaders}" in env.fake.hidden
    assert env.plugin.table.count() == 3
    assert env.plugin.table.recoveries[4]["name"] == "leadership"
    assert env.fake.events(EVENT_AFFECTED_UPDATE) == [{}]
    for suffix in GROUPS:
        assert not env.fake.enabled[
            next(n for n, k in env.fake.kwargs.items() if k.get("group") == f"{PLUGIN_ID}.{suffix}")
        ]
    assert env.fake.finished[0] == CMDTYPE
    assert not env.fake.core.is_open()


def test_spellup_block_flags_spellups_and_raises_uptodate_once(env: Env) -> None:
    """The spellup slist flags the spellups; the first one raises uptodate, the next does not."""
    env.load_all()
    assert env.fake.events(EVENT_UPTODATE) == [{}]
    assert env.plugin._api_is_up_to_date()
    assert [s["sn"] for s in env.plugin._api_spellups_get()] == [14]
    env.plugin._refresh()
    env.fake.feed(*full_block())
    env.fake.feed(*spellup_block(SPELLS[0]))
    assert len(env.fake.events(EVENT_UPTODATE)) == 2  # the full slist reset it, so once more
    env.fake.queued.clear()
    env.plugin._refresh()
    env.fake.feed(*spellup_block(SPELLS[0]))  # a lone spellup block, already up to date
    assert len(env.fake.events(EVENT_UPTODATE)) == 2


def test_affected_block_resets_and_sets_durations(env: Env) -> None:
    """An affected slist zeroes the durations and sets the current ones."""
    env.load_all()
    env.plugin.table.set_duration(15, 99, NOW)
    env.plugin.table.set_recovery_duration(4, 99, NOW)
    env.fake.raised.clear()
    env.fake.begin(CMDTYPE, f"{CMDTYPE} affected noprompt")
    env.fake.feed(
        "{spellheaders affected noprompt}",
        "14,armor,2,600,85,-1,1",
        "{/spellheaders}",
        "{recoveries affected noprompt}",
        "4,leadership,45",
        "{/recoveries}",
    )
    table = env.plugin.table
    assert table.skills[14]["duration"] == NOW + 600
    assert table.skills[15]["duration"] == 0
    assert table.recoveries[4]["duration"] == NOW + 45
    assert env.fake.events(EVENT_AFFECTED_UPDATE) == [{}]
    assert env.fake.events(EVENT_UPTODATE) == []
    assert env.fake.hidden[-6:] == [
        "{spellheaders affected noprompt}",
        "14,armor,2,600,85,-1,1",
        "{/spellheaders}",
        "{recoveries affected noprompt}",
        "4,leadership,45",
        "{/recoveries}",
    ]


def test_learned_block_updates_percents(env: Env) -> None:
    """A learned slist sets the percents and ends at the spell headers."""
    env.load_all()
    env.fake.begin(CMDTYPE, f"{CMDTYPE} learned noprompt")
    env.fake.feed("{spellheaders learned noprompt}", "14,armor,2,0,99,-1,1", "{/spellheaders}")
    assert env.plugin.table.skills[14]["percent"] == 99
    assert len(env.fake.finished) == 3  # full, spellup, learned
    assert not env.fake.core.is_open()


def test_typed_slist_is_shown(env: Env) -> None:
    """An slist the player types is not queued, so its groups are off and it is shown."""
    env.fake.feed(*full_block())
    assert env.fake.hidden == []
    assert env.fake.shown == full_block()
    assert env.plugin.table.count() == 0


def test_hide_window_stops_at_the_cap(env: Env) -> None:
    """With no end tag, the window shows lines again after HIDE_MAX_LINES."""
    env.plugin._refresh()
    env.fake.feed("{spellheaders noprompt}")
    junk = [f"line {i}" for i in range(HIDE_MAX_LINES + 2)]
    env.fake.feed(*junk)
    assert env.fake.hidden == ["{spellheaders noprompt}", *junk[:HIDE_MAX_LINES]]
    assert env.fake.shown == junk[HIDE_MAX_LINES:]
    assert not env.fake.core.is_open()


def test_affon_and_affoff(env: Env) -> None:
    """The affect tags set the duration and raise events."""
    env.load_all()
    env.fake.feed("{affon}14,600")
    assert env.fake.events(EVENT_AFFON) == [{"sn": 14, "duration": NOW + 600}]
    assert env.plugin._api_skill_is_affected(14)
    env.fake.feed("{affoff}14")
    assert env.fake.events(EVENT_AFFOFF) == [{"sn": 14}]
    assert not env.plugin._api_skill_is_affected(14)
    assert env.fake.shown[-2:] == ["{affon}14,600", "{affoff}14"]


def test_recon_and_recoff(env: Env) -> None:
    """The recovery tags set the duration and raise events."""
    env.load_all()
    env.fake.feed("{recon}4,300")
    assert env.fake.events(EVENT_RECON) == [{"sn": 4, "duration": NOW + 300}]
    assert env.plugin._api_skill_is_blocked_by_recovery(15)
    env.fake.feed("{recoff}4")
    assert env.fake.events(EVENT_RECOFF) == [{"sn": 4}]
    assert not env.plugin._api_skill_is_blocked_by_recovery(15)


def test_tags_for_an_unknown_sn_raise_nothing(env: Env) -> None:
    """A tag for an sn the table does not know is ignored without an error."""
    env.fake.feed("{affon}99,5", "{affoff}99", "{recon}99,5", "{recoff}99", "{skillgain}99,50")
    assert env.fake.raised == []


def test_skillgain(env: Env) -> None:
    """A skill gain sets the percent and raises an event."""
    env.load_all()
    env.fake.feed("{skillgain}14,86")
    assert env.fake.events(EVENT_GAIN) == [{"sn": 14, "percent": 86}]
    assert env.plugin.table.skills[14]["percent"] == 86


def test_sfail_raises_named_codes(env: Env) -> None:
    """A fail raises the reason and the target by name."""
    env.load_all()
    env.fake.feed("{sfail}14,0,4,-1")
    assert env.fake.events(EVENT_FAIL) == [
        {"sn": 14, "reason": "nomana", "target": "self", "recovery": -1}
    ]
    assert env.fake.queued == [FULL_Q, SPELLUP_Q]


def test_sfail_dontknow_with_percent_refreshes(env: Env) -> None:
    """A spell that is not known but has a percent is read again."""
    env.load_all()
    env.fake.queued.clear()
    env.fake.feed("{sfail}14,0,8,-1")
    assert env.fake.queued == [FULL_Q, SPELLUP_Q]
    env.fake.queued.clear()
    env.fake.pending.clear()
    env.fake.current = None
    env.fake.feed("{sfail}20,1,8,-1")  # bash door is 5 percent: still more than 0
    assert env.fake.queued == [FULL_Q, SPELLUP_Q]


def test_sfail_dontknow_without_percent_does_not_refresh(env: Env) -> None:
    """A spell at 0 percent that is not known does not refresh."""
    env.load_all()
    env.plugin.table.set_percent(14, 0)
    env.fake.queued.clear()
    env.fake.feed("{sfail}14,0,8,-1")
    assert env.fake.queued == []
    assert len(env.fake.events(EVENT_FAIL)) == 1


def test_sfail_unknown_sn_and_codes(env: Env) -> None:
    """An unknown sn or code does not error."""
    env.fake.feed("{sfail}99,0,8,-1", "{sfail}99,5,7,-1")
    assert env.fake.events(EVENT_FAIL) == [
        {"sn": 99, "reason": "dontknow", "target": "self", "recovery": -1},
        {"sn": 99, "reason": "7", "target": "5", "recovery": -1},
    ]


def test_level_events_queue_a_refresh(env: Env) -> None:
    """A remort or a tier reads the skills again."""
    env.plugin._eventcb_level_remort()
    assert env.fake.queued == [FULL_Q, SPELLUP_Q]
    env.fake.queued.clear()
    env.fake.pending.clear()
    env.fake.current = None
    env.plugin._eventcb_level_tier()
    assert env.fake.queued == [FULL_Q, SPELLUP_Q]


def test_disconnect_resets_and_abandons_a_block(env: Env) -> None:
    """A disconnect forgets the skills, stops hiding and turns the groups off."""
    env.load_all()
    env.plugin._refresh()
    env.fake.feed("{spellheaders noprompt}", SPELLS[0])
    assert env.fake.core.is_open()
    env.disconnect()
    assert env.plugin.table.count() == 0
    assert not env.plugin.table.uptodate
    assert not env.fake.core.is_open()
    assert env.plugin._current is None
    assert not env.fake.group_on("slist")
    env.fake.feed(SPELLS[1])
    assert env.fake.shown[-1] == SPELLS[1]
    assert env.plugin.table.count() == 0


def test_apis(env: Env) -> None:
    """Each API gives what the old one did."""
    env.load_all()
    plugin = env.plugin
    skill = plugin._api_skill_get("armor")
    assert skill is not None
    assert skill["sn"] == 14
    assert plugin._api_skill_get("zzz") is None
    recovery = plugin._api_recovery_get("leadership")
    assert recovery is not None
    assert recovery["sn"] == 4
    assert plugin._api_skill_is_spellup(14)
    assert not plugin._api_skill_is_spellup(15)
    assert plugin._api_skill_is_practiced(14)
    assert not plugin._api_skill_is_practiced(20)
    assert plugin._api_skill_can_use(14)
    assert not plugin._api_skill_can_use(20)
    assert plugin._api_skill_is_bad(15)  # the regression for the old skill.gets typo
    assert plugin._api_skill_is_bad("bash door")
    assert not plugin._api_skill_is_bad(14)
    assert not plugin._api_skill_is_bad(99)
    assert plugin._api_is_up_to_date()


def test_skill_send(env: Env) -> None:
    """A spell sends cast <sn>; a skill sends the first word of its name."""
    env.load_all()
    assert env.plugin._api_skill_send(14) is True
    assert env.plugin._api_skill_send("bash door") is True
    assert env.plugin._api_skill_send(99) is False
    assert env.sent == ["cast 14", "bash"]


def test_command_refresh(env: Env) -> None:
    """The refresh command queues both slists."""
    result = env.plugin._command_refresh()
    assert env.fake.queued == [FULL_Q, SPELLUP_Q]
    assert result.success


def test_command_lu(env: Env) -> None:
    """The lu command shows the old fields, including the duration and the recovery."""
    env.load_all()
    env.fake.feed("{affon}15,600", "{recon}4,300")
    env.fake.args = {"skill": "fireball"}
    result = env.plugin._command_lu()
    assert result.message == [
        "SN       : 15",
        "Name     : fireball",
        "Percent  : 90",
        "Duration : 600s",
        "Target   : attack",
        "Spellup  : False",
        "Type     : spell",
        "Recovery : leadership (300s)",
    ]


def test_command_lu_without_duration_or_recovery_time(env: Env) -> None:
    """A skill without a duration or a running recovery shows neither."""
    env.load_all()
    env.fake.args = {"skill": "14"}
    result = env.plugin._command_lu()
    assert "Duration : " not in "\n".join(result.message)
    assert result.message[-1] == "Type     : spell"
    env.fake.args = {"skill": "fireball"}
    assert env.plugin._command_lu().message[-1] == "Recovery : leadership"


def test_command_lu_not_found(env: Env) -> None:
    """An unknown skill says so."""
    env.fake.args = {"skill": "x"}
    assert env.plugin._command_lu().message == ["Could not find: x"]


def test_uninitialize_toggles_the_tags_off_once(env: Env) -> None:
    """Uninitialize turns both options off, and only once."""
    env.fake.a102.clear()
    env.plugin._phook_uninitialize()
    assert env.fake.a102 == [(name, False) for name in A102_OPTIONS]
    env.plugin._phook_uninitialize()
    assert len(env.fake.a102) == len(A102_OPTIONS)


def test_failed_trigger_add_is_logged_and_group_not_toggled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A trigger that could not be added never has its group toggled."""
    monkeypatch.setenv("BASTPROXY_HOME", str(tmp_path))
    fake = FakeApi()
    fake.add_ok = False
    plugin = build(fake)
    plugin._toggle_all_groups(True)
    assert fake.toggles == []


def test_types_hide_their_output_through_mudcmds(env: Env) -> None:
    """Each slist type asks mudcmds to hide its reply between its own start and end tags."""
    expected = {
        CMDTYPE: (HIDE_START_FULL, HIDE_END_FULL),
        CMDTYPE_SPELLUP: (HIDE_START_SPELLUP, HIDE_END_SPELLUP),
    }
    for cmdtype, (start, end) in expected.items():
        kwargs = env.fake.types[cmdtype]
        assert kwargs["hide_output"] is True
        assert kwargs["hide_start"] == start
        assert kwargs["hide_end"] == end
        # mudcmds counts the opening line, so the type gets one more than the cap
        assert kwargs["hide_max"] == HIDE_MAX_LINES + 1
        assert env.fake.core.core.cmds[cmdtype].hide_output is True


def test_refresh_queues_each_slist_under_its_own_type(env: Env) -> None:
    """The full and the spellup slist are two types, and each block finishes its own."""
    env.plugin._refresh()
    assert env.fake.queued == [FULL_Q, SPELLUP_Q]
    assert env.fake.pending == [(CMDTYPE_SPELLUP, SPELLUP_Q)]
    env.fake.feed(*full_block())
    assert env.fake.started == [CMDTYPE, CMDTYPE_SPELLUP]
    env.fake.feed(*spellup_block(SPELLS[0]))
    assert env.fake.finished == [CMDTYPE, CMDTYPE_SPELLUP]


def test_spellup_window_closes_at_the_end_of_the_spell_headers(env: Env) -> None:
    """A spellup slist has no recoveries, so its window ends at the spell headers."""
    env.plugin._refresh()
    env.fake.feed(*full_block())
    env.fake.feed(*spellup_block(SPELLS[0]))
    assert not env.fake.core.is_open()
    env.fake.feed("after")
    assert env.fake.hidden == [*full_block(), *spellup_block(SPELLS[0])]
    assert env.fake.shown == ["after"]


def test_full_window_stays_open_past_the_end_of_the_spell_headers(env: Env) -> None:
    """A full slist prints the end of the spell headers midway; it ends at the recoveries."""
    env.plugin._refresh()
    env.fake.feed("{spellheaders noprompt}", SPELLS[0], "{/spellheaders}")
    assert env.fake.core.is_open()
    env.fake.feed("a stray line", "{recoveries noprompt}", *RECOVERIES)
    assert env.fake.core.is_open()
    env.fake.feed("{/recoveries}")
    assert not env.fake.core.is_open()
    env.fake.feed("after")
    assert "a stray line" in env.fake.hidden
    assert env.fake.shown == ["after"]
