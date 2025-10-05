"""Shared objects within workers package."""

import uuid
import membank

from dataclasses import dataclass
from zoozl.chatbot import Package


@dataclass
class FileContext:
    """Context for file attachments."""

    binary: bytes
    media_type: str
    filename: str = ""
    uuid: str = ""

    def __post_init__(self):
        """Initialize."""
        if not self.uuid:
            self.uuid = str(uuid.uuid4())


@dataclass
class TallybotContext:
    """Context for Tallybot."""

    conf: dict
    memory: membank.LoadMemory
    package: Package
    attachments: list[FileContext]
