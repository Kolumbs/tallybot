"""Agent for invoice booking."""

import datetime
import logging
from dataclasses import dataclass
from typing import Optional

import pydantic
from agents import Agent, RunContextWrapper, function_tool

from ..brain import do_task
from . import base, master

log = logging.getLogger(__name__)


class InvoiceData(pydantic.BaseModel):
    """Data for booking invoice."""

    date: str = pydantic.Field(description="Invoice date in YYYY-MM-DD format")
    reference: str = pydantic.Field(description="Invoice reference number")
    comment: str = pydantic.Field(description="Comment for the invoice")
    partner: str = pydantic.Field(description="Partner name")
    value: float = pydantic.Field(description="Invoice amount")
    expense_account: Optional[str] = pydantic.Field(
        default=None, description="Expense account code, e.g., 7120"
    )
    currency: Optional[str] = pydantic.Field(
        default=None, description="Currency code, e.g., EUR"
    )
    split: Optional[float] = pydantic.Field(
        default=None, description="Split percentage, e.g., 100 for full amount"
    )


@dataclass
class JobResult:
    """Imaginary interface for the brain do_task return."""

    status: str
    attachment: bytes
    attachment_filename: str


@function_tool
@base.assert_single_attachment("application/pdf", "image/png", "image/jpeg")
async def do_book_invoice(
    w: RunContextWrapper[base.TallybotContext], invoice_data: InvoiceData
) -> str:
    """Book supplier invoice in accounting system."""
    msg, fbytes, fname = do_task(
        w.context.conf,
        w.context.memory,
        "do_add_expense",
        [invoice_data.model_dump(exclude_unset=True, exclude_none=True)],
        w.context.get_attachment().binary,
    )
    return msg


class PrivateTransaction(pydantic.BaseModel):
    """Required data to register private bookings."""

    date: datetime.date = pydantic.Field(
        description="Date of the transaction in YYYY-MM-DD format"
    )
    amount: float = pydantic.Field(description="Value of the booking")
    partner: str = pydantic.Field(
        description="Precise name of the partner that the boooking relates to"
    )


@function_tool
async def do_private_expense_booking(
    w: RunContextWrapper[base.TallybotContext],
    data: PrivateTransaction,
) -> str:
    """Book a non business related expense.

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
        [
            {
                "value": data.amount,
                "date": data.date.isoformat(),
                "partner": data.partner,
            }
        ],
    )
    return msg


@function_tool
async def do_private_income_booking(
    w: RunContextWrapper[base.TallybotContext],
    data: PrivateTransaction,
) -> str:
    """Book a non business related private income.

    These are single bookings that do not require proof documents and
    are outside scope of the accounting.

    Private income bookings are done to remove outstanding items that do
    not relate to business activities. Outstanding items are bookings
    from discrepancy report.
    """
    msg, _, _ = do_task(
        w.context.conf,
        w.context.memory,
        "do_private_income",
        [
            {
                "value": data.amount,
                "date": data.date.isoformat(),
                "partner": data.partner,
            }
        ],
    )
    return msg


accounts_payable_clerk = Agent(
    name="accounts_payable_clerk",
    instructions=(
        "You are Invoice Processing / AP Clerk"
        "Main focus: Booking supplier invoices into the accounting system."
        "Receive and verify invoices have required data for booking."
        "Enter invoices accurately into accounting system using provided tools."
        "Only if user confirms or requests explicitly, book a non business related"
        " private expense or income to clear outstanding items."
    ),
    tools=[
        do_book_invoice,
        do_private_expense_booking,
        do_private_income_booking,
        master.get_user_last_attachment,
    ],
)
