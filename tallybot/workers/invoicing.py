"""Agent for invoice booking."""

from dataclasses import dataclass
from agents import Agent, function_tool, RunContextWrapper
import logging

import pydantic

from ..brain import do_task, Perform
from .. import handlers
from . import master
from .base import TallybotContext, FileContext, catch_exceptions


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
    if len(w.context.attachments) == 0:
        return "No attachment found, please attach the invoice file."
    msg, fbytes, fname = do_task(
        w.context.conf,
        w.context.memory,
        "do_add_expense",
        [invoice_data.model_dump()],
        w.context.attachments[0].binary,
    )
    return msg


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
    ),
    tools=[
        do_book_invoice,
        master.get_user_last_attachments,
    ],
)


@function_tool
async def do_seb_statement_import(
    w: RunContextWrapper[TallybotContext],
) -> str:
    """Import SEB bank statement into accounting system."""
    if len(w.context.attachments) > 1:
        return (
            "Too many attachments, please attach only one bank statement file."
        )
    if len(w.context.attachments) == 0:
        return "No attachment found, please attach the bank statement file."
    if w.context.attachments[0].media_type != "text/csv":
        return "Unsupported file type, please attach a csv file format."
    msg, fbytes, fname = do_task(
        w.context.conf,
        w.context.memory,
        "do_seb_statement",
        [],
        w.context.attachments[0].binary,
    )
    return msg


@function_tool
@catch_exceptions
async def save_bank_statement(w: RunContextWrapper[TallybotContext]) -> str:
    """Save bank statement on desktop."""
    if len(w.context.attachments) > 1:
        return (
            "Too many attachments, please attach only one bank statement file."
        )
    if len(w.context.attachments) == 0:
        return "No attachment found, please attach the bank statement file."
    with Perform(
        w.context.conf,
        w.context.memory,
    ) as job:
        handlers.save_file(
            job.generate_path("desktop", "csv", "seb_statement"),
            w.context.attachments[0].binary,
        )
    return "Bank statement `seb_statement.csv` saved."


@function_tool
@catch_exceptions
async def retrieve_bank_statement(
    w: RunContextWrapper[TallybotContext],
) -> str:
    """Retrieve bank statement from desktop."""
    if len(w.context.attachments) > 0:
        return "There is already attachment attached. Cannot overwrite"
    with Perform(
        w.context.conf,
        w.context.memory,
    ) as job:
        w.context.attachments = [
            FileContext(
                binary=handlers.get_file(
                    job.generate_path(
                        "uploaded_documents", "csv", "seb_statement"
                    )
                ),
                media_type="text/csv",
                filename="seb_statement.csv",
            )
        ]


bank_statement_clerk = Agent(
    name="bank_statement_clerk",
    instructions=(
        "You are Bank Statement Clerk."
        "Main focus: Loading bank statements into the accounting system."
        "Save bank statement on your desktop."
        "Process bank statement through the accounting system. If necessary load file"
        "from your desktop"
    ),
    tools=[
        save_bank_statement,
        retrieve_bank_statement,
        do_seb_statement_import,
        master.get_user_last_attachments,
    ],
)
