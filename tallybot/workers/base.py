"""Shared objects within workers package."""

import logging
import sys
import traceback
from dataclasses import dataclass
from functools import wraps

import membank
from agents import Agent, RunContextWrapper, function_tool
from zoozl.chatbot import MessagePart, Package

log = logging.getLogger(__name__)

__all__ = [
    "Agent",
    "function_tool",
    "RunContextWrapper",
    "TallybotContext",
    "catch_exceptions",
    "assert_single_attachment",
]


@dataclass
class TallybotContext:
    """Context for Tallybot."""

    conf: dict
    memory: membank.LoadMemory
    package: Package
    message_parts: list[MessagePart]

    def get_attachment(self) -> MessagePart | None:
        """Return last valid attachment."""
        attachments = self.package.get_attachments(5, consumed=False)
        return attachments[-1] if attachments else None


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


def assert_single_attachment(*media_types):
    """Return file attachment decorator for a coroutine."""

    def decorator(coro):
        """Decorator to acquire single attachment from context."""

        @wraps(coro)
        async def wrapper(
            w: RunContextWrapper[TallybotContext], *args, **kwargs
        ):
            """Acquire single attachment from context."""
            attachments = w.context.package.get_attachments(5)
            if len(attachments) == 0:
                return "No attachment found, please attach a file."
            attachment = attachments[-1]
            if media_types and attachment.media_type not in media_types:
                my_media = attachment.media_type
                support_media = ", ".join(media_types)
                return (
                    f"Attachment media type is {my_media}, "
                    f"but it must be one of supported media types: {support_media}."
                )
            if attachment.consumed:
                return "This attachment has already been consumed."
            try:
                return await coro(w, *args, **kwargs)
            except Exception as e:
                raise e
            else:
                attachment.consumed = True

        return wrapper

    return decorator
