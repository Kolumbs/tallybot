"""Functions related to financial reports."""

from typing import Optional

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


@function_tool
async def list_discrepancies(
    w: RunContextWrapper[TallybotContext],
    year: str,
    partner: Optional[str] = None,
) -> str:
    """List discrepancies for given year, with optional partner filter.

    Generally discrepancies indicate that some particular transactions
    that have been booked, do not have corresponding double booking entry
    accordingly for that particular partner.

    Sometimes it can happen that discrepancies need to be recalculated
    for a given year and partner.

    For correct accounting there should be no outstandind discrepancies.
    """
    msg, _, _ = do_task(
        w.context.conf,
        w.context.memory,
        "do_get_outstanding_items",
        [{"year": year, "partner": partner}],
    )
    return msg


@function_tool
async def recalculate_partner_discrepancies(
    w: RunContextWrapper[TallybotContext],
    year: str,
    partner: str,
) -> str:
    """Recalculate discrepancies for given year and partner.

    Only needed if there was some corrections made that did not apply afterwards
    in the discrepancy report.
    """
    msg, _, _ = do_task(
        w.context.conf,
        w.context.memory,
        "do_get_outstanding_items",
        [{"year": year, "partner": partner}],
    )
    return msg
