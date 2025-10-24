"""Functions related to financial reports."""

from agents import function_tool, RunContextWrapper
from zoozl.chatbot import MessagePart
from .base import TallybotContext
from ..brain import do_task


@function_tool
async def send_discrepancy_report(
    w: RunContextWrapper[TallybotContext], year: str
) -> str:
    """Send descrepancy report to user for given year."""
    msg, fbytes, fname = do_task(
        w.context.conf,
        w.context.memory,
        "do_get_outstanding",
        [{"year": year}],
    )
    if fbytes:
        w.context.message_parts.append(
            MessagePart(
                text="Outstanding Discrepancy Report.",
                binary=fbytes,
                filename=fname,
                media_type=(
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
            )
        )
    return msg
