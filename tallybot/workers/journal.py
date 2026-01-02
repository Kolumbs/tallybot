"""Single booking operations functions."""

from typing import Optional

from ..brain import do_task
from . import base


@base.function_tool
async def update_transaction(
    w: base.RunContextWrapper[base.TallybotContext],
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


@base.function_tool
async def create_transaction(
    w: base.RunContextWrapper[base.TallybotContext],
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
        "debit_amount": amount,
        "debit": debit,
        "credit": credit,
    }
    if partner is not None:
        payload["partner"] = partner
    msg, _, _ = do_task(
        w.context.conf,
        w.context.memory,
        "do_transaction",
        [payload],
    )
    return msg


ledger_correction_clerk = base.Agent(
    name="ledger_correction_clerk",
    instructions=(
        "You are Ledger Correction Clerk."
        "Main focus: Correcting and creating accounting ledger transactions."
        "Never make any changes to the ledger unless explicitly instructed by the user."
        "Never make any changes to the ledger based on your own assumptions."
        "Never make any changes to the ledger without confirmation from the user."
    ),
    tools=[
        update_transaction,
        create_transaction,
    ],
)
