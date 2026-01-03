"""Tallybot main agent."""

from agents import Agent

from . import payables, banking, master, financials, journal


TALLYBOT = (
    "Your name is tallybot. Always be very brief."
    "Your main purpose is to quickly help user to execute any tasks."
    "Tasks can be executed by other agents."
    "If there is no agent that can execute particular task,"
    "apologise that you can't complete it and wait for other tasks."
    "Immediately when you know which task to handle execute it."
    "Prioritise delegation, speed and brevity"
)


tallybot = Agent(
    name="Tallybot",
    instructions=TALLYBOT,
    tools=[
        payables.accounts_payable_clerk.as_tool(
            tool_name="accounts_payable_clerk",
            tool_description="Delegate any work for booking supplier invoices.",
        ),
        banking.bank_statement_clerk.as_tool(
            tool_name="bank_statement_clerk",
            tool_description="You can book bank statements with this tool.",
        ),
        master.do_register_partner,
        master.do_update_partner,
        master.get_user_last_attachment,
        financials.send_discrepancy_report,
        financials.list_discrepancies,
        financials.recalculate_partner_discrepancies,
        financials.list_transactions,
        financials.send_ledger_report,
        journal.ledger_correction_clerk.as_tool(
            tool_name="ledger_correction_clerk",
            tool_description="You can correct ledger entries with this tool.",
        ),
    ],
)
