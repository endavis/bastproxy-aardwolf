"""Aardwolf mobk plugin: follow the combat output and raise an event for each kill."""

import copy
import logging
import time
from collections.abc import Callable, Mapping
from typing import Any

from bastproxy.libs.logger import get_logger, log_to
from bastproxy.plugins._baseplugin import BasePlugin, RegisterPluginHook
from bastproxy.plugins.core.commands import AddCommand, AddParser, CommandResult
from bastproxy.plugins.core.events import RegisterToEvent

from aardwolf._libs import aardu

from ..libs import (
    EQ_WORN_API,
    EVENT_GMCP_STATUS,
    EVENT_KILL,
    EVENTS,
    SECOND_SLOT,
    TRIGGERS,
    WIELDED_SLOT,
    TriggerSpec,
    add_to_damage,
    damage_default,
    new_kill,
    parse_gold,
    sum_xp,
    to_int,
    total_xp,
)

# the special-kill flags of a kill, shown by the last command when set
SPECIAL_FLAGS = (
    "tp",
    "vorpal",
    "assassinate",
    "deathblow",
    "slit",
    "disintegrate",
    "banishment",
)


class MobkPlugin(BasePlugin):
    """Collect the facts of a kill and raise an event once, when the corpse is gone."""

    @RegisterPluginHook("__init__")
    def _phook_init_plugin(self) -> None:
        """Start with an empty kill."""
        self.kill: dict[str, Any] = new_kill()
        # True once an xp line was seen for the kill, so it is worth raising
        self._pending = False
        # a copy of the last raised kill, kept in memory only
        self.last_kill: dict[str, Any] | None = None
        self.mobdamcache: dict[str, dict[str, Any]] = {}

    @RegisterPluginHook("after_load")
    def _phook_initialize(self) -> None:
        """Add the event and the triggers."""
        add_event = self.api("plugins.core.events:event.add")
        for event_name, info in EVENTS.items():
            add_event(
                event_name,
                self.plugin_id,
                description=info["description"],
                arg_descriptions=info["arg_descriptions"],
            )
        callbacks = self._trigger_callbacks()
        for spec in TRIGGERS:
            self._add_trigger(spec, callbacks.get(spec.name))

    def _trigger_callbacks(self) -> dict[str, Callable[[], None]]:
        """Return the callback of each trigger, by trigger name."""
        return {
            "mobk_xp": self._trigger_xp,
            "mobk_rarexp": self._trigger_rarexp,
            "mobk_blessxp": self._trigger_blessxp,
            "mobk_bonusxp": self._trigger_bonusxp,
            "mobk_xpptless": self._trigger_pointless,
            "mobk_switch": self._trigger_switch,
            "mobk_flee": self._trigger_none,
            "mobk_retreat": self._trigger_none,
            "mobk_gold": self._trigger_gold,
            "mobk_splitgold": self._trigger_gold,
            "mobk_corpseget": self._trigger_corpseget,
            "mobk_sac": self._trigger_corpse,
            "mobk_consume": self._trigger_corpse,
            "mobk_trivia": self._trigger_trivia,
            "mobk_trivia2": self._trigger_trivia,
            "mobk_vorpal": self._trigger_vorpal,
            "mobk_assassin": self._trigger_assassinate,
            "mobk_deathblow": self._trigger_deathblow,
            "mobk_slit": self._trigger_finisher("slit"),
            "mobk_disintegrate": self._trigger_finisher("disintegrate"),
            "mobk_banish": self._trigger_finisher("banishment"),
            "mobk_damage": self._trigger_damage,
            "mobk_damage2": self._trigger_damage,
            "mobk_bsincombat": self._trigger_backstab,
        }

    def _add_trigger(self, spec: TriggerSpec, func: Callable[[], None] | None) -> None:
        """Add a trigger and register its callback."""
        kwargs: dict[str, Any] = {}
        if spec.argtypes:
            kwargs["argtypes"] = spec.argtypes
        result = self.api("plugins.core.triggers:trigger.add")(spec.name, spec.regex, **kwargs)
        if not result.success:
            get_logger(self.plugin_id).error("could not add the %s trigger", spec.name)
            return
        if func is not None:
            self.api("plugins.core.triggers:trigger.register")(result.trigger.trigger_id, func)

    @staticmethod
    def _now() -> float:
        """Return the current time."""
        return time.time()

    def _gmcp_value(self, path: str) -> object:
        """Return the cached GMCP value at a dotted path, or None."""
        return self.api("libs.net.protocols:gmcp.value.get")(path)

    def _record(self) -> dict[str, Any]:
        """Return the record of the current trigger event."""
        return dict(self.api("plugins.core.events:event.current.record.get")() or {})

    def _matches(self) -> dict[str, Any]:
        """Return the groups the current trigger matched."""
        return dict(self._record().get("matches") or {})

    def _line_text(self) -> str:
        """Return the current line without colour."""
        line = self._record().get("line")
        return str(getattr(line, "noansi", line)) if line is not None else ""

    def _strip_colour(self, text: str) -> str:
        """Remove the colour codes of the text; GMCP strings carry them."""
        return str(self.api("plugins.core.colors:colorcode.strip")(text))

    def _reset_kill(self) -> None:
        """Start a new kill."""
        self.kill = new_kill()
        self._pending = False

    def _reset_damage(self) -> None:
        """Forget the damage and the times of the kill."""
        self.kill["damage"] = {}
        self.kill["immunities"] = {}
        self.kill["starttime"] = None
        self.kill["finishtime"] = None

    # experience

    def _trigger_xp(self) -> None:
        """The experience of the kill."""
        matches = self._matches()
        self.kill["xp"] = sum_xp(str(matches.get("xp", "")))
        self._pending = True
        if matches.get("dont"):
            self.kill["noexp"] = 1

    def _trigger_rarexp(self) -> None:
        """The rare kill bonus."""
        self.kill["rarexp"] = to_int(self._matches().get("xp"))

    def _trigger_blessxp(self) -> None:
        """The bonus of the daily blessing."""
        self.kill["blessingxp"] = to_int(self._matches().get("xp"))

    def _trigger_bonusxp(self) -> None:
        """Any other bonus."""
        self.kill["bonusxp"] = to_int(self._matches().get("xp"))

    def _trigger_pointless(self) -> None:
        """A kill with no experience."""
        self.kill["xp"] = 0
        self._pending = True

    # the mob

    def _trigger_switch(self) -> None:
        """The character switched targets."""
        self.kill["name"] = self._matches().get("name", "")
        self._reset_damage()

    def _trigger_none(self) -> None:
        """The character fled or retreated: forget the mob."""
        self.kill["name"] = ""
        self._reset_damage()

    def _trigger_gold(self) -> None:
        """The gold of the kill."""
        matches = self._matches()
        gold = parse_gold(str(matches.get("gold", "")))
        if gold is None:
            log_to([self.plugin_id], logging.DEBUG, "invalid gold in mobk_gold: %s", matches)
        else:
            self.kill["gold"] = gold
        if not self.kill["name"]:
            self.kill["name"] = matches.get("name", "")

    def _trigger_corpseget(self) -> None:
        """Something was taken from a corpse; only the sacrifice or consume ends the kill."""
        log_to(
            [self.plugin_id], logging.DEBUG, "got from a corpse of %s", self._matches().get("name")
        )

    def _trigger_corpse(self) -> None:
        """The corpse was sacrificed or consumed."""
        if self.kill["name"]:
            self._raise_kill()

    def _trigger_trivia(self) -> None:
        """A trivia point mob."""
        self.kill["tp"] = 1

    def _trigger_vorpal(self) -> None:
        """A vorpal kill."""
        self.kill["vorpal"] = 1

    def _trigger_assassinate(self) -> None:
        """An assassination."""
        self.kill["name"] = self._matches().get("name", "")
        self.kill["assassinate"] = 1

    def _trigger_deathblow(self) -> None:
        """A death blow."""
        self.kill["name"] = self._matches().get("name", "")
        self.kill["deathblow"] = 1

    def _trigger_finisher(self, flag: str) -> Callable[[], None]:
        """Return the callback of a kill with no corpse, which raises the kill at once."""

        def callback() -> None:
            self.kill["name"] = self._matches().get("name", "")
            self.kill[flag] = 1
            self._pending = True
            self._raise_kill()

        return callback

    # damage

    def _trigger_damage(self) -> None:
        """A damage line."""
        tdam = aardu.parse_damage_line(self._line_text())
        if not self.kill["starttime"]:
            self.kill["starttime"] = self._now()
        enemy = tdam["enemy"]
        if enemy and self.kill["name"] and enemy != self.kill["name"]:
            add_to_damage(tdam, self.mobdamcache.setdefault(enemy, {}))
            return
        if enemy in self.mobdamcache:
            self.kill["damage"] = self.mobdamcache.pop(enemy)
        add_to_damage(tdam, self.kill["damage"])
        if not self.kill["name"]:
            self.kill["name"] = enemy

    def _trigger_backstab(self) -> None:
        """A backstab in combat."""
        log_to([self.plugin_id], logging.DEBUG, "saw a backstab in combat")
        self.kill["damage"].setdefault("backstab", damage_default())["incombat"] = True

    @RegisterToEvent(event_name=EVENT_GMCP_STATUS)
    def _eventcb_char_status(self) -> None:
        """Take the enemy of GMCP char.status as the mob, when there is none yet."""
        enemy = self._gmcp_value("char.status.enemy")
        if enemy and isinstance(enemy, str) and not self.kill["name"]:
            self.kill["name"] = self._strip_colour(enemy)
            self._reset_damage()

    # the kill

    def _weapon_serials(self) -> tuple[str, str]:
        """Return the serials of the wielded and the second weapon; empty without an eq plugin."""
        if not self.api("libs.api:api.exists")(EQ_WORN_API):
            return "", ""
        worn = self.api(EQ_WORN_API)
        return self._serial(worn(WIELDED_SLOT)), self._serial(worn(SECOND_SLOT))

    @staticmethod
    def _serial(item: object) -> str:
        """Return the serial of a worn item, empty when there is none."""
        if item is None:
            return ""
        if isinstance(item, Mapping):
            return str(item.get("serial", ""))
        return str(getattr(item, "serial", ""))

    def _raise_kill(self) -> None:
        """Raise the kill, when an xp line was seen, and start a new one."""
        now = self._now()
        self.kill["finishtime"] = now
        self.kill["time"] = now
        room = self._gmcp_value("room.info.num")
        self.kill["room_id"] = -1 if room is None else to_int(room)
        self.kill["level"] = aardu.actual_level_from_gmcp(self._gmcp_value)
        wielded, second = self._weapon_serials()
        self.kill["wielded_weapon"] = wielded
        self.kill["second_weapon"] = second
        if self._pending:
            if not self.kill["name"]:
                self.kill["name"] = "Unknown"
            self.kill["totalxp"] = total_xp(self.kill)
            log_to([self.plugin_id], logging.DEBUG, "raising a mobkill: %s", self.kill)
            self.last_kill = copy.deepcopy(dict(self.kill))
            self.api("plugins.core.events:event.raise")(
                EVENT_KILL, event_args=copy.deepcopy(dict(self.kill))
            )
        self._reset_kill()

    # commands

    @AddCommand()
    @AddParser(description="show the last kill")
    def _command_last(self) -> CommandResult:
        """Show the last raised kill."""
        kill = self.last_kill
        if kill is None:
            return CommandResult(True, ["No kill since the plugin loaded"])
        flags = [name for name in SPECIAL_FLAGS if kill.get(name)]
        start, finish = kill.get("starttime"), kill.get("finishtime")
        fight = f"{finish - start:.1f}s" if start is not None and finish is not None else "unknown"
        lines = [
            f"Mob: {kill.get('name', '')}",
            f"Room: {kill.get('room_id', -1)}  Level: {kill.get('level', -1)}",
            f"XP: normal {kill.get('xp', 0)}, rare {kill.get('rarexp', 0)}, "
            f"bonus {kill.get('bonusxp', 0)}, blessing {kill.get('blessingxp', 0)}, "
            f"total {kill.get('totalxp', 0)}",
            f"Gold: {kill.get('gold', 0)}",
            f"Special kills: {', '.join(flags) if flags else 'none'}",
            f"Fight time: {fight}",
            f"{'Damage type':<20} {'Hits':>6} {'Misses':>7} {'Damage':>10}",
            "@G" + "-" * 46,
        ]
        for damtype, entry in kill.get("damage", {}).items():
            lines.append(
                f"@w{damtype:<20} {entry.get('hits', 0):>6} "
                f"{entry.get('misses', 0):>7} {entry.get('damage', 0):>10}"
            )
        return CommandResult(True, lines)
