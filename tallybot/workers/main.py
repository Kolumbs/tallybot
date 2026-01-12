"""Tallybot main agent."""

from agents import Agent

from . import payables, banking, master, financials, journal, receivables


TALLYBOT = (
    "Your name is tallybot. You are accountant for private business owner."
    "Your main purpose is to quickly help user to execute any tasks."
    "Be careful in task execution, confirm the details with the user before booking"
    "Make sure that any details where you create partners or do bookings are correct."
    "You mostly book expenses or also called supplier invoices."
)


tallybot = Agent(
    name="Tallybot",
    instructions=TALLYBOT,
    tools=[
        payables.do_book_invoice,
        payables.do_private_expense_booking,
        payables.do_private_income_booking,
        banking.do_seb_statement_import,
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
        receivables.do_book_sales_invoice,
    ],
)
