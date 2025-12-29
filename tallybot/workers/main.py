"""Tallybot main agent."""

from agents import Agent

from . import invoicing, master, financials


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
        invoicing.accounts_payable_clerk.as_tool(
            tool_name="accounts_payable_clerk",
            tool_description="Delegate any work for booking supplier invoices.",
        ),
        invoicing.bank_statement_clerk.as_tool(
            tool_name="bank_statement_clerk",
            tool_description="You can book bank statements with this tool.",
        ),
        master.do_register_partner,
        financials.send_discrepancy_report,
        financials.list_discrepancies,
        financials.recalculate_partner_discrepancies,
        financials.update_transaction,
        financials.create_transaction,
        financials.list_transactions,
        financials.send_ledger_report,
    ],
)
