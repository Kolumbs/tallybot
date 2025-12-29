"""Agent for invoice booking."""

import logging
from dataclasses import dataclass
from typing import Optional

import pydantic
from agents import Agent, RunContextWrapper, function_tool

from ..brain import do_task
from . import base, master, bookings

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
    """Book invoice in accounting system."""
    msg, fbytes, fname = do_task(
        w.context.conf,
        w.context.memory,
        "do_add_expense",
        [invoice_data.model_dump(exclude_unset=True)],
        w.context.get_attachment().binary,
    )
    return msg


accounts_payable_clerk = Agent(
    name="accounts_payable_clerk",
    instructions=(
        "You are Invoice Processing / AP Clerk"
        "Main focus: Booking supplier invoices into the accounting system."
        "Receive and verify invoices have required data for booking."
        "Enter invoices accurately into accounting system using provided tools."
    ),
    tools=[
        do_book_invoice,
        master.get_user_last_attachment,
        bookings.do_private_expense_booking,
        bookings.do_private_income_booking,
    ],
)


@function_tool
@base.catch_exceptions
@base.assert_single_attachment("text/csv")
async def do_seb_statement_import(
    w: RunContextWrapper[base.TallybotContext],
) -> str:
    """Import SEB bank statement into accounting system."""
    msg, fbytes, fname = do_task(
        w.context.conf,
        w.context.memory,
        "do_seb_statement",
        [],
        w.context.get_attachment().binary,
    )
    return msg


bank_statement_clerk = Agent(
    name="bank_statement_clerk",
    instructions=(
        "You are Bank Statement Clerk."
        "Main focus: Loading bank statements into the accounting system."
        "Save or load bank statement from your desktop."
        "Process bank statement through the accounting system."
    ),
    tools=[
        do_seb_statement_import,
    ],
)
