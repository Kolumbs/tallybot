"""Tallybot main agent."""

import pydantic
from agents import Agent

from . import invoicing, master, financials, bookings


TALLYBOT = (
    "Your name is tallybot. Always be very brief."
    "Your main purpose is to quickly help user to execute any tasks."
    "Tasks can be executed by other agents."
    "If there is no agent that can execute particular task,"
    "apologise that you can't complete it and wait for other tasks."
    "Immediately when you know which task to handle execute it."
    "Prioritise delegation, speed and brevity"
)


class Attachments(pydantic.BaseModel):
    """Data for creating new partner."""

    name: str = pydantic.Field(
        description="Partner name as shown in accounting system"
    )
    other_names: list[str] = pydantic.Field(
        description="Other names or aliases for the partner"
    )


tallybot = Agent(
    name="Tallybot",
    instructions=TALLYBOT,
    tools=[
        invoicing.accounts_payable_clerk.as_tool(
            tool_name="accounts_payable_clerk",
            tool_description="You can book invoices with this tool.",
        ),
        invoicing.bank_statement_clerk.as_tool(
            tool_name="bank_statement_clerk",
            tool_description="You can book bank statements with this tool.",
        ),
        master.get_user_last_attachments,
        master.do_register_partner,
        financials.send_discrepancy_report,
        financials.list_discrepancies,
        financials.recalculate_partner_discrepancies,
        financials.update_transaction,
        financials.create_transaction,
        financials.list_transactions,
        financials.send_ledger_report,
        bookings.do_private_expense_booking,
        bookings.do_private_income_booking,
    ],
)
