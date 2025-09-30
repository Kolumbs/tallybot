"""Agent for invoice booking."""

from dataclasses import dataclass
from typing_extensions import TypedDict
from agents import Agent, function_tool, RunContextWrapper
import logging

import membank
import pydantic

from ..brain import do_task
from .base import TallybotContext


log = logging.getLogger(__name__)


class InvoiceData(pydantic.BaseModel):
    """Data for booking invoice."""

    date: str = pydantic.Field(description="Invoice date in YYYY-MM-DD format")
    reference: str = pydantic.Field(description="Invoice reference number")
    comment: str = pydantic.Field(description="Comment for the invoice")
    partner: str = pydantic.Field(description="Partner name")
    value: float = pydantic.Field(description="Invoice amount")
    expense_account: str = pydantic.Field(
        description="Expense account code, e.g., 7120"
    )
    currency: str = pydantic.Field(description="Currency code, e.g., EUR")
    split: float = pydantic.Field(
        description="Split percentage, e.g., 100 for full amount"
    )


@dataclass
class JobResult:
    """Imaginary interface for the brain do_task return."""

    status: str
    attachment: bytes
    attachment_filename: str


@function_tool
async def do_book_invoice(
    w: RunContextWrapper[TallybotContext], invoice_data: InvoiceData
) -> str:
    """Book invoice in accounting system."""
    if len(w.context.attachments) > 1:
        return "Too many attachments, please attach only one invoice file."
    attachment = None
    if len(w.context.attachments) == 1:
        attachment = w.context.attachments[0].binary
    msg, fbytes, fname = do_task(
        w.context.conf,
        w.context.memory,
        "do_add_expense",
        [invoice_data.model_dump()],
        attachment,
    )
    return msg


@function_tool
async def get_user_last_attachments(
    w: RunContextWrapper[TallybotContext],
) -> str:
    """Return a list of filenames attached to the last message."""
    return [i.filename for i in w.context.attachments]


accounts_payable_clerk = Agent(
    name="accounts_payable_clerk",
    instructions=(
        "You are Invoice Processing / AP Clerk"
        "Main focus: Booking invoices into the accounting system."
        "Receive and verify invoices have required data for booking."
        "Enter invoices accurately into accounting system using provided tools."
        "Ensure coding to correct accounts."
        "Flag discrepancies for resolution."
        "Maintain the digital invoice filing system."
        "Each invoice booked must contain attachment from user as proof of entry"
    ),
    tools=[
        do_book_invoice,
        get_user_last_attachments,
    ],
)
