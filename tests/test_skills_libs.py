"""Tests for the pure helpers of the skills plugin."""

import re
from typing import Any

import pytest

from aardwolf.skills.libs import (
    CMD_REGEX,
    CMD_SPELLUP_REGEX,
    EVENTS,
    FAILREASON,
    GROUP_RECOVERIES,
    GROUP_SPELLS,
    HIDE_END_FULL,
    HIDE_END_SPELLUP,
    HIDE_START_FULL,
    HIDE_START_SPELLUP,
    TRIGGERS,
    SkillTable,
    code_name,
    fail_payload,
    find_by_name,
)

NOW = 1000.0


def spell(sn: int = 14, name: str = "armor", **over: int | str) -> dict[str, Any]:
    """Return the fields of a spell line."""
    fields: dict[str, Any] = {
        "sn": sn,
        "name": name,
        "target": 2,
        "duration": 0,
        "pct": 85,
        "rcvy": -1,
        "type": 1,
    }
    fields.update(over)
    return fields


def make_table() -> SkillTable:
    """Return a table with armor (spell, recovery 4), fireball and bash (skills)."""
    table = SkillTable()
    table.add_skill(spell(rcvy=4), NOW)
    table.add_skill(spell(15, "fireball", target=1), NOW)
    table.add_skill(spell(20, "bash door", target=0, type=2, pct=5), NOW)
    table.add_recovery({"sn": 4, "name": "leadership", "duration": 0}, NOW)
    return table


def test_find_by_name_exact_prefix_and_substring() -> None:
    """Exact wins, then a unique prefix, then a unique substring."""
    names = ["armor", "arm lock", "fireball", "ball"]
    assert find_by_name("armor", names) == "armor"
    assert find_by_name("fire", names) == "fireball"
    assert find_by_name("eba", names) == "fireball"
    assert find_by_name("ball", names) == "ball"


def test_find_by_name_ambiguous_or_unknown() -> None:
    """More than one hit in the deciding step, or none, returns None."""
    assert find_by_name("ar", ["armor", "arm lock"]) is None
    assert find_by_name("zzz", ["armor"]) is None


def test_code_name_falls_back_to_the_code() -> None:
    """An unknown code gives its text."""
    assert code_name(FAILREASON, 1) == "lostconc"
    assert code_name(FAILREASON, 7) == "7"


def test_add_skill_names_codes_and_stores_expiry() -> None:
    """Target and type are named, and the duration becomes now plus the seconds, or 0."""
    table = SkillTable()
    table.add_skill(spell(duration=60), NOW)
    table.add_skill(spell(15, "x", target=9, type=7), NOW)
    assert table.skills[14]["target"] == "spellup"
    assert table.skills[14]["type"] == "spell"
    assert table.skills[14]["duration"] == NOW + 60
    assert table.skills[14]["spellup"] is False
    assert table.skills[15]["duration"] == 0
    assert table.skills[15]["target"] == "9"
    assert table.skills[15]["type"] == "7"


def test_add_recovery_stores_expiry() -> None:
    """A recovery keeps its expiry."""
    table = SkillTable()
    table.add_recovery({"sn": 4, "name": "leadership", "duration": 30}, NOW)
    assert table.recoveries[4] == {"sn": 4, "name": "leadership", "duration": NOW + 30}


@pytest.mark.parametrize("key", [14, "14", "armor", "arm", "rmo"])
def test_get_skill_keys(key: int | str) -> None:
    """A skill is found by int, digit string, exact name, prefix or substring."""
    table = make_table()
    skill = table.get_skill(key)
    assert skill is not None
    assert skill["sn"] == 14
    assert skill["recovery"] == {"sn": 4, "name": "leadership", "duration": 0}


@pytest.mark.parametrize("key", ["", "zzz", 99, "99", "r"])
def test_get_skill_unknown_or_ambiguous(key: int | str) -> None:
    """An unknown or ambiguous key returns None."""
    assert make_table().get_skill(key) is None


def test_get_skill_returns_a_copy_without_recovery() -> None:
    """The result is a copy, and a skill with rcvy -1 has no recovery."""
    table = make_table()
    skill = table.get_skill("fireball")
    assert skill is not None
    assert skill["recovery"] is None
    skill["percent"] = 1
    assert table.skills[15]["percent"] == 85
    armor = table.get_skill(14)
    assert armor is not None
    armor["recovery"]["name"] = "x"
    assert table.recoveries[4]["name"] == "leadership"


def test_get_skill_with_a_missing_recovery() -> None:
    """A recovery sn the table does not know gives None."""
    table = SkillTable()
    table.add_skill(spell(rcvy=9), NOW)
    skill = table.get_skill(14)
    assert skill is not None
    assert skill["recovery"] is None


def test_get_recovery_by_name() -> None:
    """A recovery is found by sn or name."""
    table = make_table()
    found = table.get_recovery("leader")
    assert found is not None
    assert found["sn"] == 4
    assert table.get_recovery(4) == found
    assert table.get_recovery("zzz") is None


def test_setters_return_false_for_unknown_sn() -> None:
    """An unknown sn changes nothing."""
    table = make_table()
    before = (dict(table.skills), dict(table.recoveries))
    assert table.set_duration(99, 5, NOW) is False
    assert table.set_recovery_duration(99, 5, NOW) is False
    assert table.set_percent(99, 5) is False
    assert table.flag_spellup(99) is False
    assert (table.skills, table.recoveries) == before


def test_setters_change_known_sn() -> None:
    """The setters store values for a known sn."""
    table = make_table()
    assert table.set_duration(14, 30, NOW)
    assert table.skills[14]["duration"] == NOW + 30
    assert table.set_duration(14, 0, NOW)
    assert table.skills[14]["duration"] == 0
    assert table.set_recovery_duration(4, 9, NOW)
    assert table.recoveries[4]["duration"] == NOW + 9
    assert table.set_percent(14, 90)
    assert table.skills[14]["percent"] == 90
    assert table.flag_spellup(14)
    assert [s["sn"] for s in table.spellups()] == [14]


def test_reset_and_reset_affected() -> None:
    """reset clears everything; reset_affected zeroes the durations only."""
    table = make_table()
    table.set_duration(14, 30, NOW)
    table.set_recovery_duration(4, 30, NOW)
    table.uptodate = True
    table.reset_affected()
    assert table.skills[14]["duration"] == 0
    assert table.recoveries[4]["duration"] == 0
    assert table.count() == 3
    assert table.uptodate
    table.reset()
    assert (table.skills, table.recoveries, table.uptodate) == ({}, {}, False)


def test_predicates_are_false_for_unknown_sn() -> None:
    """Every predicate returns False for an unknown sn."""
    table = make_table()
    for func in (
        table.is_affected,
        table.is_blocked_by_recovery,
        table.is_practiced,
        table.is_spellup,
        table.can_use,
        table.is_bad,
    ):
        assert func(99) is False
        assert func("zzz") is False


def test_is_practiced_boundary() -> None:
    """More than 10 percent is practiced."""
    table = make_table()
    table.set_percent(14, 10)
    assert table.is_practiced(14) is False
    table.set_percent(14, 11)
    assert table.is_practiced(14) is True


def test_can_use() -> None:
    """A practiced skill that is not affected and not blocked can be used."""
    table = make_table()
    assert table.can_use(14)
    assert not table.can_use("bash door")
    table.set_duration(14, 30, NOW)
    assert not table.can_use(14)
    table.set_duration(14, 0, NOW)
    table.set_recovery_duration(4, 30, NOW)
    assert table.is_blocked_by_recovery(14)
    assert not table.can_use(14)


def test_is_bad() -> None:
    """An attack or special skill that is not a spellup is bad."""
    table = make_table()
    assert table.is_bad("fireball")
    assert table.is_bad("bash door")
    assert not table.is_bad("armor")
    table.flag_spellup(15)
    assert not table.is_bad("fireball")
    assert table.is_spellup("fireball")


def test_fail_payload_codes() -> None:
    """Known codes are named, reason 7 and target 5 fall back to the code."""
    assert fail_payload(14, 0, 4, -1) == {
        "sn": 14,
        "reason": "nomana",
        "target": "self",
        "recovery": -1,
    }
    assert fail_payload(14, 5, 7, 4) == {
        "sn": 14,
        "reason": "7",
        "target": "5",
        "recovery": 4,
    }


SAMPLES = {
    "skills_affoff": "{affoff}14",
    "skills_affon": "{affon}14,600",
    "skills_recoff": "{recoff}4",
    "skills_recon": "{recon}4,300",
    "skills_skillgain": "{skillgain}14,86",
    "skills_sfail": "{sfail}14,0,2,-1",
    "skills_start": "{spellheaders noprompt}",
    "skills_spellheaders_end": "{/spellheaders}",
    "skills_recov_start": "{recoveries noprompt}",
    "skills_recoveries_end": "{/recoveries}",
    "skills_spell_line": "14,armor,2,0,85,-1,1",
    "skills_recov_line": "4,leadership,0",
}


def test_every_trigger_matches_its_sample() -> None:
    """Each trigger regex matches its sample line, with the arguments typed."""
    assert {spec.name for spec in TRIGGERS} == set(SAMPLES)
    for spec in TRIGGERS:
        match = re.match(spec.regex, SAMPLES[spec.name])
        assert match, spec.name
        for arg, argtype in (spec.argtypes or {}).items():
            assert isinstance(argtype(match.group(arg)), int)


@pytest.mark.parametrize("kind", ["affected", "learned", "spellup"])
def test_start_tags_carry_the_kind(kind: str) -> None:
    """The start tags read the kind of the slist."""
    starts = {spec.name: spec.regex for spec in TRIGGERS}
    found = re.match(starts["skills_start"], f"{{spellheaders {kind} noprompt}}")
    assert found is not None
    assert found.group("type") == kind
    plain = re.match(starts["skills_start"], "{spellheaders noprompt}")
    assert plain is not None
    assert plain.group("type") is None
    recov = re.match(starts["skills_recov_start"], f"{{recoveries {kind} noprompt}}")
    assert recov is not None
    assert recov.group("type") == kind


def test_spell_and_recovery_lines_have_their_own_groups() -> None:
    """The spell regex does not match a recovery line; each has its own group."""
    by_name = {spec.name: spec for spec in TRIGGERS}
    assert by_name["skills_spell_line"].group == GROUP_SPELLS
    assert by_name["skills_recov_line"].group == GROUP_RECOVERIES
    assert not re.match(by_name["skills_spell_line"].regex, SAMPLES["skills_recov_line"])


def test_events_are_described() -> None:
    """Every event has a description and arg descriptions."""
    assert len(EVENTS) == 8
    for info in EVENTS.values():
        assert info["description"]
        assert info["arg_descriptions"]


def test_hide_tags_match_their_slist_block() -> None:
    """Each type opens and closes its window on its own tags, and not on the other's."""
    assert re.search(HIDE_START_FULL, "{spellheaders noprompt}")
    assert not re.search(HIDE_START_FULL, "{spellheaders spellup noprompt}")
    assert re.search(HIDE_START_SPELLUP, "{spellheaders spellup noprompt}")
    assert not re.search(HIDE_START_SPELLUP, "{spellheaders noprompt}")
    assert re.search(HIDE_END_FULL, "{/recoveries}")
    assert not re.search(HIDE_END_FULL, "{/spellheaders}")
    assert re.search(HIDE_END_SPELLUP, "{/spellheaders}")


def test_the_spellup_command_regex_matches_only_the_spellup_slist() -> None:
    """The spellup type is for ``slist spellup noprompt``; the full regex still matches both."""
    assert re.search(CMD_SPELLUP_REGEX, "slist spellup noprompt")
    assert not re.search(CMD_SPELLUP_REGEX, "slist noprompt")
    assert not re.search(CMD_SPELLUP_REGEX, "slist learned noprompt")
    assert re.search(CMD_REGEX, "slist noprompt")
