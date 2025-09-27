"""Managers are objects that allow to interact with memories on a more abstract level.

Managers promise to raise AssertionError with user friendly text upon any error.
"""
from dataclasses import replace

from . import memories
from .lookups import get_partner


class AbstractManager:
    """Abstract manager class."""

    def __init__(self, memory):
        """Initialize with memory access."""
        self.memory = memory


class PartnerManager(AbstractManager):
    """Interact with Partner memory."""

    def __init__(self, memory):
        """Initialize with memory access."""
        super().__init__(memory)
        self.address = AddressManager(memory)

    def update(self, payload):
        """Update partner data."""
        name = payload.pop("name")
        partner_id = get_partner(self.memory, name)
        partner = self.memory.get.partner(id=partner_id)
        if not partner:
            raise AssertionError(f"Partner '{name}' not found")
        address = self.address.update(payload, partner.address_id)
        if address:
            payload["address_id"] = address.id
        if "new_name" in payload:
            self.memory.put(memories.PartnerIndex(name, partner_id))
            payload["name"] = payload.pop("new_name")
        partner = replace(partner, **payload)
        self.memory.put(partner)
        return partner


def addressor(payload, address: memories.Address):
    """Update address data."""
    for i in range(1, 5):
        if f"address{i}" in payload:
            if len(address.address_lines) < i:
                address.address_lines.append(payload.pop(f"address{i}"))
            else:
                address.address_lines[i - 1] = payload.pop(f"address{i}")


class AddressManager(AbstractManager):
    """Interact with Address memory."""

    def extract_valid(self, payload):
        """Extract valid address fields."""
        extract = {}
        for i in range(1, 5):
            if f"address{i}" in payload:
                extract[f"address{i}"] = payload.pop(f"address{i}")
        return extract

    def update(self, payload, address_id):
        """Update address data."""
        changes = self.extract_valid(payload)
        if not changes:
            return None
        address = None
        if address_id:
            address = self.memory.get.address(id=address_id)
        if not address:
            address = memories.Address()
        addressor(changes, address)
        address = replace(address, **changes)
        self.memory.put(address)
        return address

    def get(self, address_id):
        """Get address data."""
        address = self.memory.get.address(id=address_id)
        if address:
            return address
        return memories.Address()
