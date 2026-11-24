"""The item cache and containers of the eq plugin, and the rules that follow invmon."""

import copy
from collections.abc import Iterable
from typing import Any, NamedTuple

from aardwolf._libs.itemu import WEARLOCS, WEARLOCSREV

from ._eq import (
    CONTAINER_ITYPE,
    EVENT_INVENTORY_ADDED,
    EVENT_INVENTORY_REMOVED,
    EVENT_PUT,
    EVENT_REMOVED,
    EVENT_TAKEN,
    EVENT_WORN,
    INVENTORY,
    KEYRING,
    VAULT,
    WORN,
)

_LISTS = (INVENTORY, KEYRING, VAULT)


class InvmonOutcome(NamedTuple):
    """What an invmon line did: the events to raise and the containers to read again."""

    events: list[tuple[str, dict[str, Any]]]
    refresh: list[str]
    new_containers: list[str]
    dropped_containers: list[str]


class EqState:
    """The items the character has seen and where each one is. One location per item."""

    def __init__(self) -> None:
        """Start empty."""
        self.items: dict[int, dict[str, Any]] = {}
        self.containers: dict[str, list[int]] = {}
        self.worn: list[int | None] = []
        self.lastworn: dict[int, int] = {}
        self.vault_counts: dict[str, int] | None = None
        self.vault_read = False
        self.reset()

    def reset(self) -> None:
        """Forget everything."""
        self.items = {}
        self.containers = {name: [] for name in _LISTS}
        self.worn = [None] * len(WEARLOCS)
        self.lastworn = {}
        self.vault_counts = None
        self.vault_read = False

    # containers

    def ensure_container(self, cid: str) -> bool:
        """Make sure a container exists; return True when it is new."""
        if cid == WORN or cid in self.containers:
            return False
        self.containers[cid] = []
        return True

    def has_container(self, cid: str) -> bool:
        """Return True when the container exists."""
        return cid == WORN or cid in self.containers

    def serials(self, cid: str) -> list[int]:
        """Return the serials in a container, in order; for Worn, in slot order."""
        if cid == WORN:
            return [serial for serial in self.worn if serial is not None]
        return list(self.containers.get(cid, []))

    def bag_cids(self) -> list[str]:
        """Return the container ids that are bags."""
        return [cid for cid in self.containers if cid not in _LISTS]

    def _detach(self, serial: int) -> None:
        """Take an item out of whatever container holds it."""
        for serials in self.containers.values():
            while serial in serials:
                serials.remove(serial)
        for slot, held in enumerate(self.worn):
            if held == serial:
                self.worn[slot] = None
        item = self.items.get(serial)
        if item is not None:
            item["container"] = None

    # items

    def upsert(self, parsed: dict[str, Any]) -> dict[str, Any]:
        """Add an item or update the one with the same serial, keeping where it is."""
        serial = int(parsed["serial"])
        item = self.items.get(serial)
        if item is None:
            item = {"container": None, "origcontainer": None, "hasbeenided": False}
            self.items[serial] = item
        item.update(parsed)
        return item

    def move(self, serial: int, cid: str, place: int | None = None) -> bool:
        """Move an item to a container, removing it from where it was. Return False if unknown.

        ``place`` is the wear slot for Worn, the index for another container, and the end of
        the list for None.
        """
        item = self.items.get(serial)
        if item is None:
            return False
        if cid == WORN:
            if place is None or not 0 <= place < len(self.worn):
                return False
            occupant = self.worn[place]
            self._detach(serial)
            if occupant is not None and occupant != serial:
                self.move(occupant, INVENTORY, 0)
            self.worn[place] = serial
        else:
            self.ensure_container(cid)
            self._detach(serial)
            serials = self.containers[cid]
            if place is None:
                serials.append(serial)
            else:
                serials.insert(place, serial)
        item["container"] = cid
        if item.get("origcontainer") == cid:
            item["origcontainer"] = None
        return True

    def drop_item(self, serial: int) -> None:
        """Forget an item."""
        self._detach(serial)
        self.items.pop(serial, None)
        self.lastworn.pop(serial, None)

    def drop_container(self, cid: str) -> list[int]:
        """Forget a bag and the items in it, and any bag in it. Return the serials dropped."""
        serials = list(self.containers.get(cid, []))
        self.containers.pop(cid, None)
        dropped = list(serials)
        for serial in serials:
            if str(serial) in self.containers:
                dropped.extend(self.drop_container(str(serial)))
            self.drop_item(serial)
        return dropped

    def commit(self, cid: str, parsed: Iterable[dict[str, Any]]) -> list[str]:
        """Replace the contents of a container with the lines read. Return the new bag ids."""
        self.ensure_container(cid)
        if cid == VAULT:
            self.vault_read = True
        for serial in self.serials(cid):
            self._detach(serial)
        new_bags: list[str] = []
        for data in list(parsed):
            serial = int(data["serial"])
            slot = data.get("wearslot", -1)
            if cid == WORN and not 0 <= slot < len(self.worn):
                continue
            item = self.upsert(data)
            self._detach(serial)
            if cid == WORN:
                self.move(serial, WORN, slot)
            else:
                self.move(serial, cid)
            holds_bags = cid == INVENTORY or cid in self.bag_cids()
            if (
                item["itype"] == CONTAINER_ITYPE
                and holds_bags
                and self.ensure_container(str(serial))
            ):
                new_bags.append(str(serial))
        if cid == INVENTORY:
            self._drop_stale_bags()
        return new_bags

    def _drop_stale_bags(self) -> None:
        """Forget the bags whose item is no longer anywhere the character has it."""
        for bag in self.bag_cids():
            item = self.items.get(int(bag)) if bag.isdecimal() else None
            if bag in self.containers and (item is None or item["container"] is None):
                self.drop_container(bag)

    def set_origin(self, serial: int) -> None:
        """Note where an item is, so a later put can send it back there."""
        item = self.items.get(serial)
        if item is not None and item["container"] not in (None, INVENTORY):
            item["origcontainer"] = item["container"]

    # reads, which all return copies

    def item_copy(self, serial: int) -> dict[str, Any] | None:
        """Return a copy of an item, or None."""
        item = self.items.get(serial)
        return copy.deepcopy(item) if item is not None else None

    def container_copy(self, cid: int | str) -> dict[str, Any] | None:
        """Return a copy of a container as ``{cid, items}``, or None when there is none.

        ``items`` holds serials. Worn adds ``slots``, one serial or None per wear location, and
        Vault adds ``counts``.
        """
        cid = str(cid)
        if not self.has_container(cid):
            return None
        result: dict[str, Any] = {"cid": cid, "items": self.serials(cid)}
        if cid == WORN:
            result["slots"] = list(self.worn)
        elif cid == VAULT:
            result["counts"] = dict(self.vault_counts) if self.vault_counts else None
        return result

    def worn_at(self, location: int | str) -> dict[str, Any] | None:
        """Return a copy of the item worn at a slot number or location name, or None."""
        slot: int | None = None
        if isinstance(location, bool):
            return None
        if isinstance(location, int):
            slot = location
        elif isinstance(location, str):
            text = location.strip().lower()
            slot = int(text) if text.isdecimal() else WEARLOCSREV.get(text)
        if slot is None or not 0 <= slot < len(self.worn):
            return None
        serial = self.worn[slot]
        return self.item_copy(serial) if serial is not None else None

    def find_by_name(self, name: str) -> list[dict[str, Any]]:
        """Return copies of the items with ``name`` in their name; the match is case sensitive."""
        return [copy.deepcopy(item) for item in self.items.values() if name in item.get("name", "")]

    # invmon

    def apply_invmon(
        self, action: int, serial: int, container: int, location: int
    ) -> InvmonOutcome:
        """Apply an invmon line, and return the events to raise and the containers to read."""
        out = InvmonOutcome([], [], [], [])
        bags_before = set(self.bag_cids())
        handler = _ACTIONS.get(action)
        if handler is not None:
            handler(self, out, serial, container, location)
        out.dropped_containers.extend(sorted(bags_before - set(self.bag_cids())))
        return out

    def _refresh(self, out: InvmonOutcome, *cids: str) -> None:
        """Ask for containers to be read again."""
        for cid in cids:
            if cid not in out.refresh:
                out.refresh.append(cid)

    def _note_bag(self, out: InvmonOutcome, serial: int) -> None:
        """A bag reached the inventory: give it a container, read when it is new."""
        item = self.items.get(serial)
        if item is not None and item["itype"] == CONTAINER_ITYPE:
            cid = str(serial)
            if self.ensure_container(cid):
                out.new_containers.append(cid)
                self._refresh(out, cid)

    def _event(self, out: InvmonOutcome, name: str, serial: int, cid: str) -> None:
        """Add a put or taken event."""
        payload = {"serial": serial, "container": cid, "item": self.item_copy(serial)}
        out.events.append((name, payload))

    def _bag_cid(self, out: InvmonOutcome, container: int) -> tuple[str | None, bool]:
        """Return the id of a bag named by invmon and whether it was known before.

        An unknown bag is created, so it can be read.
        """
        if container <= 0:
            return None, False
        cid = str(container)
        if self.ensure_container(cid):
            out.new_containers.append(cid)
            return cid, False
        return cid, True

    def _a_remove(self, out: InvmonOutcome, serial: int, _c: int, _l: int) -> None:
        if serial in self.worn:
            slot = self.worn.index(serial)
            self.lastworn[serial] = slot
            self.move(serial, INVENTORY, 0)
            out.events.append((EVENT_REMOVED, {"item": self.item_copy(serial), "location": slot}))
            self._note_bag(out, serial)
        else:
            self._refresh(out, WORN, INVENTORY)

    def _a_wear(self, out: InvmonOutcome, serial: int, _c: int, location: int) -> None:
        if serial in self.containers[INVENTORY] and self.move(serial, WORN, location):
            out.events.append((EVENT_WORN, {"item": self.item_copy(serial), "location": location}))
        else:
            self._refresh(out, INVENTORY, WORN)

    def _a_gone(self, out: InvmonOutcome, serial: int, _c: int, _l: int) -> None:
        if serial in self.containers[INVENTORY]:
            item = self.item_copy(serial)
            if str(serial) in self.containers:
                self.drop_container(str(serial))
            self.drop_item(serial)
            out.events.append((EVENT_INVENTORY_REMOVED, {"item": item}))
        else:
            self._refresh(out, INVENTORY)

    def _a_added(self, out: InvmonOutcome, serial: int, _c: int, _l: int) -> None:
        if serial in self.items:
            self.move(serial, INVENTORY, 0)
            self._note_bag(out, serial)
            out.events.append((EVENT_INVENTORY_ADDED, {"item": self.item_copy(serial)}))
        else:
            self._refresh(out, INVENTORY)
        self._event(out, EVENT_PUT, serial, INVENTORY)

    def _a_bag_take(self, out: InvmonOutcome, serial: int, container: int, _l: int) -> None:
        cid, known = self._bag_cid(out, container)
        if cid is not None and known and serial in self.containers[cid]:
            self.move(serial, INVENTORY)
            self._note_bag(out, serial)
        else:
            self._refresh(out, *([cid] if cid else []), INVENTORY)
        self._event(out, EVENT_TAKEN, serial, cid or str(container))

    def _a_bag_put(self, out: InvmonOutcome, serial: int, container: int, _l: int) -> None:
        cid, known = self._bag_cid(out, container)
        if cid is not None and known and serial in self.containers[INVENTORY]:
            self.move(serial, cid, 0)
        else:
            self._refresh(out, *([cid] if cid else []), INVENTORY)
        self._event(out, EVENT_PUT, serial, cid or str(container))

    def _a_vault_put(self, out: InvmonOutcome, serial: int, _c: int, _l: int) -> None:
        if serial in self.items:
            self.move(serial, VAULT)
        else:
            self._refresh(out, VAULT, INVENTORY)
        self._event(out, EVENT_PUT, serial, VAULT)

    def _a_vault_take(self, out: InvmonOutcome, serial: int, _c: int, _l: int) -> None:
        if serial in self.containers[VAULT]:
            self.move(serial, INVENTORY, 0)
            self._note_bag(out, serial)
        else:
            self._refresh(out, VAULT, INVENTORY)
        self._event(out, EVENT_TAKEN, serial, VAULT)

    def _a_keyring_put(self, out: InvmonOutcome, serial: int, _c: int, _l: int) -> None:
        if serial in self.containers[INVENTORY]:
            self.move(serial, KEYRING, 0)
        else:
            self._refresh(out, INVENTORY, KEYRING)
        self._event(out, EVENT_PUT, serial, KEYRING)

    def _a_keyring_take(self, out: InvmonOutcome, serial: int, _c: int, _l: int) -> None:
        if serial in self.containers[KEYRING]:
            self.move(serial, INVENTORY, 0)
        else:
            self._refresh(out, KEYRING, INVENTORY)
        self._event(out, EVENT_TAKEN, serial, KEYRING)


_ACTIONS = {
    1: EqState._a_remove,
    2: EqState._a_wear,
    3: EqState._a_gone,
    4: EqState._a_added,
    5: EqState._a_bag_take,
    6: EqState._a_bag_put,
    7: EqState._a_gone,
    9: EqState._a_vault_put,
    10: EqState._a_vault_take,
    11: EqState._a_keyring_put,
    12: EqState._a_keyring_take,
}
