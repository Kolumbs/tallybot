"""Functions for looking up data from memories."""
import dataclasses

from . import memories, token_set_ratio


def get_default_partner(memory):
    """Get default partner."""
    default = memory.get.myself(key="default_partner")
    if not default:
        return None
    return memory.get.partner(id=default.text)


def return_item_val(item):
    """Retun item value based on it's available value."""
    if item.text:
        return item.text
    if item.value:
        return item.value
    if item.dct:
        return item.dct
    if item.lst:
        return item.lst
    if item.blob:
        return item.blob


def get_mydata(memory):
    """Get myself data."""
    myself = memory.get("myself")
    loader = {}
    fields = [i.name for i in dataclasses.fields(memories.Me)]
    for item in myself:
        if item.key in fields:
            loader[item.key] = return_item_val(item)
    return memories.Me(**loader)


def get_partner(memory, text):
    """Return valid partner id from given text and memory access.

    Either finds a partner by text or raises not found First tries text
    to partner index, if that fails performs deep search within Partner
    names
    """
    partner = memory.get(memory.partnerindex.text == text)
    if partner:
        return partner[0].partner_id
    partners = memory.get("partnerindex")
    for i in partners:
        ratio = token_set_ratio(text, i.text)
        if ratio > 95:
            memory.put(memories.PartnerIndex(text, i.partner_id))
            return i.partner_id
    raise RuntimeWarning(f"Partner with name '{text}' could not be found")
