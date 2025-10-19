"""Shared objects within workers package."""

import sys
import logging
import traceback
import uuid
import membank
from functools import wraps

from dataclasses import dataclass
from zoozl.chatbot import Package, MessagePart


log = logging.getLogger(__name__)


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
    message_parts: list[MessagePart]


def catch_exceptions(coro):
    """Decorator to catch exceptions in coros."""

    @wraps(coro)
    async def wrapper(*args, **kwargs):
        try:
            return await coro(*args, **kwargs)
        except Exception:
            log.exception("Exception in %s", coro.__name__)
            return "".join(traceback.format_exception(*sys.exc_info()))

    return wrapper
