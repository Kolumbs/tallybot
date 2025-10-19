"""Agents for accounting compliance and coordination."""

from agents import Agent, function_tool, RunContextWrapper
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


accounts_compliance_officer = Agent(
    name="accounts_compliance_officer",
    instructions=(
        "You are Accounting Compliance & Coordination Officer"
        "Main focus: Ensure consistent financial data and compliance with deadlines."
        "Monitor key accounting deadlines (tax declarations, month-end closing)."
        "Coordinate with internal stakeholders to collect necessary information."
        "Ensure accuracy of entered financial data by checking discrepancy reports"
        "Track and follow up on pending items that may delay reporting."
        "Maintain a shared calendar of accounting and tax deadlines"
        "Communicate reminders and updates to relevant teams."
        "Prepare and circulate summary reports on accounting compliance progress."
    ),
    tools=[
        send_discrepancy_report,
    ],
)
