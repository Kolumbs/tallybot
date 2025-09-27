"""Module defines chat subject interfaces."""
import dataclasses as data
from dataclasses import dataclass

from . import process


@dataclass
class Interface():
    """Interface to the chat command handling."""

    required: set = data.field(default_factory=set)
    optional: set = data.field(default_factory=set)
    attachment: bool = False
    # must contain callables that accept text and conversation memory item, if non empty
    auxiliaries: set = data.field(default_factory=set)
    one_optional: bool = False  # if True, at least one optional field is required


def do_add_default_partner():
    """Add default partner by it's name."""
    return Interface(
        required={"name"},
    )


def do_update_myself():
    """Update myself data."""
    return Interface(
        optional={
            "name",
            "address1",
            "address2",
            "address3",
            "address4",
            "phone",
            "email",
            "bank_name",
            "bank_account",
            "bank_code",
            "rate",
            "currency"},
        one_optional=True,
    )


def do_create_invoice():
    """Create a new invoice."""
    return Interface(
        required={"week1"},
        optional={"week" + str(i) for i in range(2, 6)},
    )


def do_book_invoice():
    """Book attached invoice."""
    return Interface(attachment=True)


def do_private_income():
    """Do private income."""
    return Interface(
        required={"date", "partner", "value"},
    )


def do_get_partner():
    """Get partner data."""
    return Interface(
        required={"name"},
    )


def do_remove_transaction():
    """Remove transaction."""
    return Interface(
        required={"id"},
    )


def do_transaction():
    """Create new transaction."""
    return Interface(
        required={
            "date",
            "reference",
            "source",
            "comment",
            "debit_amount",
            "debit",
            "credit",
        },
        optional={
            "partner",
            "credit_amount",
            "deal_value",
            "rate",
            "debit_currency",
            "credit_currency",
            "debit_stack",
            "credit_stack",
        },
    )


def do_add_expense():
    """Define add expense subject requirements."""
    return Interface(
        required={"date", "reference", "comment", "partner", "value"},
        optional={"expense_account", "currency", "split"},
        attachment=True,
        auxiliaries={allow_no_attachment, }
    )


def do_private_expense():
    """Private expense."""
    return Interface(
        required={"date", "partner", "value"},
    )


def do_get_help():
    """Define help requirements."""
    return Interface()


def do_get_myself():
    """Define myself requirements."""
    return Interface()


def do_recalculate_outstanding():
    """Recalculate outstanding items per partner."""
    return Interface(
        required={"year", "partner"},
    )


def do_get_outstanding():
    """Define report requirements."""
    return Interface()


def do_create_partner():
    """Define partner requirements."""
    return Interface(
        required={"name"},
        optional={"other_names", "id"},
    )


def do_update_partner():
    """Define partner update requirements."""
    return Interface(
        required={"name"},
        optional={
            "reg_no",
            "bank_account",
            "bank_name",
            "invoice_prefix",
            "invoice_row_format",
            "terms",
            "currency",
            "address1",
            "address2",
            "address3",
            "address4",
            "new_name",
        }
    )


def allow_no_attachment(text, talk):
    """Support function to drop attachment requirement."""
    cmds = ["no attachment", "without attachment", "skip attachment", "drop attachment"]
    pos = process.extractOne(text, cmds)
    if pos[1] > 98:
        talk.attachment = b'Attachment explicitly skipped'
        return "Skipping attachment"
    return ""


def do_upwork_invoices():
    """Upwork invoice upload."""
    return Interface(
        attachment=True,
    )


def do_seb_statement():
    """Seb statement upload."""
    return Interface(
        attachment=True,
    )


def do_upwork_statement():
    """Upwork statement upload."""
    return Interface(
        attachment=True,
    )


def do_get_ledger():
    """Full ledger report in excel."""
    return Interface(
        required={"filter_by_quarter"},
    )


def do_update_ledger():
    """Manual ledger update."""
    return Interface(
        attachment=True,
    )
