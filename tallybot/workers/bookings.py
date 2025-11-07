"""Single booking operations functions."""

from datetime import date

import pydantic
from agents import RunContextWrapper, function_tool

from ..brain import do_task
from .base import TallybotContext


class PrivateTransaction(pydantic.BaseModel):
    """Required data to register private bookings."""

    date: date = pydantic.Field(
        description="Date of the transaction in YYYY-MM-DD format"
    )
    amount: float = pydantic.Field(description="Value of the booking")
    partner: str = pydantic.Field(
        description="Precise name of the partner that the boooking relates to"
    )


@function_tool
async def do_private_expense_booking(
    w: RunContextWrapper[TallybotContext],
    data: PrivateTransaction,
) -> str:
    """Book a private expense.

    These are single bookings that do not require proof documents and
    are outside scope of the accounting.

    Private expense bookings are done to remove outstanding items that
    do not relate to business activities. Outstanding items are bookings
    from discrepancy report.
    """
    msg, _, _ = do_task(
        w.context.conf,
        w.context.memory,
        "do_private_expense",
        [{"value": data.amount, "date": data.date, "partner": data.partner}],
    )
    return msg


@function_tool
async def do_private_income_booking(
    w: RunContextWrapper[TallybotContext],
    data: PrivateTransaction,
) -> str:
    """Book a private income.

    These are single bookings that do not require proof documents and
    are outside scope of the accounting.

    Private income bookings are done to remove outstanding items that
    do not relate to business activities. Outstanding items are bookings
    from discrepancy report.
    """
    msg, _, _ = do_task(
        w.context.conf,
        w.context.memory,
        "do_private_income",
        [{"value": data.amount, "date": data.date, "partner": data.partner}],
    )
    return msg
