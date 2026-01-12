"""Agent for handling sales invoices."""

from agents import RunContextWrapper, function_tool

from ..brain import do_task
from . import base


@function_tool
@base.assert_single_attachment("application/pdf", "image/png", "image/jpeg")
async def do_book_sales_invoice(
    w: RunContextWrapper[base.TallybotContext],
) -> str:
    """Book sales invoice in accounting system."""
    if not w.context.attachment:
        return "No attachment found to book as sales invoice."
    msg, fbytes, fname = do_task(
        w.context.conf,
        w.context.memory,
        "do_book_invoice",
        data=None,
        attachment=w.context.get_attachment().binary,
    )
    return msg
