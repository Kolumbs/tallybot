"""Agent for invoice booking."""

import logging

from agents import Agent, RunContextWrapper, function_tool

from ..brain import do_task
from . import base, master

log = logging.getLogger(__name__)


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
        master.get_user_last_attachment,
    ],
)
