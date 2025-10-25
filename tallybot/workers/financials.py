"""Functions related to financial reports."""

from typing import Optional

from agents import function_tool, RunContextWrapper
from zoozl.chatbot import MessagePart
from .base import TallybotContext
from ..brain import do_task


@function_tool
async def send_ledger_report(
    w: RunContextWrapper[TallybotContext],
    year: Optional[int] = None,
    quarter: Optional[int] = None,
    month: Optional[int] = None,
) -> str:
    """Send ledger report to user.

    If year is not provided, current year is used.

    If quarter is provided, month is ignored and report is generated for
    a specific quarter within the year.

    if month is provided, report is generated for that specific month
    within the year.
    """
    payload = {}
    if year:
        payload["filter_by_year"] = year
    if quarter:
        payload["filter_by_quarter"] = f"q{quarter}"
    if month:
        if not year:
            raise ValueError("Year must be provided when filtering by month.")
        payload["filter_by_month"] = f"{year}-{month:02d}"
    msg, fbytes, fname = do_task(
        w.context.conf,
        w.context.memory,
        "do_get_ledger",
        [{"year": year}],
    )
    if fbytes:
        w.context.message_parts.append(
            MessagePart(
                text="Ledger Report.",
                binary=fbytes,
                filename=fname,
                media_type=(
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
            )
        )
    return msg


@function_tool
async def list_transactions(
    w: RunContextWrapper[TallybotContext],
    year: Optional[str] = None,
    month: Optional[str] = None,
    partner: Optional[str] = None,
) -> str:
    """List booked accounting transactions in ledger.

    For performance reasons transaction list is capped to 100 entries.
    It is also advisable to filter by optional parameters to avoid too
    long lists.
    """
    msg, _, _ = do_task(
        w.context.conf,
        w.context.memory,
        "do_list_transactions",
        [{"year": year, "partner": partner, "month": month}],
    )
    return msg


@function_tool
async def update_transaction(
    w: RunContextWrapper[TallybotContext],
    id: str,
    date: Optional[str] = None,
    reference: Optional[str] = None,
    source: Optional[str] = None,
    comment: Optional[str] = None,
    debit: Optional[int] = None,
    credit: Optional[int] = None,
    partner: Optional[str] = None,
    debit_amount: Optional[float] = None,
    credit_amount: Optional[float] = None,
    deal_value: Optional[float] = None,
    rate: Optional[float] = None,
    debit_currency: Optional[str] = None,
    credit_currency: Optional[str] = None,
    debit_stack: Optional[float] = None,
    credit_stack: Optional[float] = None,
) -> str:
    """Update existing transaction in the ledger.

    Args:
        id: UUID identifier of the transaction to update.
        date: New date of the transaction in ISO format (YYYY-MM-DD).
        reference: New document reference that legalizes the transaction.
        source: New source of the related document.
        comment: New comment for the transaction.
        debit: New debit account number.
        credit: New credit account number.
        partner: New partner associated with the transaction.
        debit_amount: New debit amount.
        credit_amount: New credit amount.
        deal_value: New deal value.
        rate: New exchange rate.
        debit_currency: New debit currency.
        credit_currency: New credit currency.
        debit_stack: New debit stack value.
        credit_stack: New credit stack value.


    Most often use cases to make update in transaction is to correct the name of the
    partner, which most likely will require to recalculate discrepancies afterwards.

    Sometimes there might be need to correct debit or credit account numbers. There can
    be also cases when debit amount or credit amount was mistyped and needs correction.

    All other fields are very likely never to be in need for update.

    Updating transactions must be performed with extreme caution, as this changes the
    accounting ledger data. It should be done only in case we need to fix some incorrect
    data that is not possible to fix otherwise. It is most advisable to only update
    specific one field that needs correction and leave others intact.

    You have been warned!
    """
    payload = {"id": id}
    if date is not None:
        payload["date"] = date
    if reference is not None:
        payload["reference"] = reference
    if source is not None:
        payload["source"] = source
    if comment is not None:
        payload["comment"] = comment
    if debit is not None:
        payload["debit"] = debit
    if credit is not None:
        payload["credit"] = credit
    if partner is not None:
        payload["partner"] = partner
    if debit_amount is not None:
        payload["debit_amount"] = debit_amount
    if credit_amount is not None:
        payload["credit_amount"] = credit_amount
    if deal_value is not None:
        payload["deal_value"] = deal_value
    if rate is not None:
        payload["rate"] = rate
    if debit_currency is not None:
        payload["debit_currency"] = debit_currency
    if credit_currency is not None:
        payload["credit_currency"] = credit_currency
    if debit_stack is not None:
        payload["debit_stack"] = debit_stack
    if credit_stack is not None:
        payload["credit_stack"] = credit_stack
    msg, _, _ = do_task(
        w.context.conf,
        w.context.memory,
        "do_update_transaction",
        [payload],
    )
    return msg


@function_tool
async def create_transaction(
    w: RunContextWrapper[TallybotContext],
    date: str,
    reference: str,
    source: str,
    comment: str,
    amount: float,
    debit: str,
    credit: str,
    partner: Optional[str] = None,
) -> str:
    """Create a new transaction directly in the ledger.

    :param date: Date of the transaction in ISO format (YYYY-MM-DD).
    :param reference: Document reference that legalizes the transaction.
    :param source: Source of the related document.
    :param comment: Comment for the transaction.
    :param amount: Value of the transaction.
    :param debit: Debit account number.
    :param credit: Credit account number.
    :param partner: Optional partner associated with the transaction.

    Transactions should not be created manually, this function is reserved for
    exceptional measures, when there are no other means to fix issue with ledger.

    Although `partner` is optional, there are very rare cases where a transaction would
    not have a partner associated with it.
    """
    payload = {
        "date": date,
        "reference": reference,
        "source": source,
        "comment": comment,
        "amount": amount,
        "debit": debit,
        "credit": credit,
    }
    if partner is None:
        payload["partner"] = partner
    msg, _, _ = do_task(
        w.context.conf,
        w.context.memory,
        "do_transaction",
        [payload],
    )
    return msg


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


@function_tool
async def list_discrepancies(
    w: RunContextWrapper[TallybotContext],
    year: str,
    partner: Optional[str] = None,
) -> str:
    """List discrepancies for given year, with optional partner filter.

    Generally discrepancies indicate that some particular transactions
    that have been booked, do not have corresponding double booking
    entry accordingly for that particular partner.

    Sometimes it can happen that discrepancies need to be recalculated
    for a given year and partner.

    For correct accounting there should be no outstandind discrepancies.
    """
    msg, _, _ = do_task(
        w.context.conf,
        w.context.memory,
        "do_get_outstanding_items",
        [{"year": year, "partner": partner}],
    )
    return msg


@function_tool
async def recalculate_partner_discrepancies(
    w: RunContextWrapper[TallybotContext],
    year: str,
    partner: str,
) -> str:
    """Recalculate discrepancies for given year and partner.

    Only needed if there was some corrections made that did not apply
    afterwards in the discrepancy report.
    """
    msg, _, _ = do_task(
        w.context.conf,
        w.context.memory,
        "do_get_outstanding_items",
        [{"year": year, "partner": partner}],
    )
    return msg
