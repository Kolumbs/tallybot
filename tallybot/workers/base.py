"""Shared objects within workers package."""

import membank

from dataclasses import dataclass


@dataclass
class TallybotContext:
    """Context for Tallybot."""

    conf: dict
    memory: membank.LoadMemory
