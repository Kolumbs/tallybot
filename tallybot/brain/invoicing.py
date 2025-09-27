"""Invoicing module."""
import datetime
from io import BytesIO

from .. import memories, managers, handlers, lookups
from ..templates.invoices import write_invoice, schema
from ..lookups import get_default_partner, get_mydata


def get_invoice_no(partner, memory):
    """Get next invoice number."""
    seq = memory.get.sequences(relation=partner.id)
    if not seq:
        seq = memories.Sequences(relation=partner.id, sequence=1)
        memory.put(seq)
    return partner.invoice_prefix + str(seq.sequence).zfill(3)


def confirm_invoice_no(seq, partner_id, memory):
    """Confirm invoice number."""
    seq += 1
    s = memories.Sequences(relation=partner_id, sequence=seq)
    memory.put(s)


def get_contact_header(name, address, phone=None, email=None):
    """Return valid contact address header."""
    header = [name]
    header += address
    if phone:
        header.append(phone)
    if email:
        header.append(email)
    return header


def get_invoice_bank_info(bank_name, bank_account, bank_code):
    """Return valid invoice bank info."""
    return [bank_name, bank_account, bank_code]


def get_invoice_terms(terms):
    """Return valid invoice terms in days."""
    if not terms:
        return 0
    if terms.isdigit():
        return int(terms)
    raise ValueError(f"Not supported terms format yet {terms}")


def get_invoice_rows(fmt, params):
    """Return valid invoice rows."""
    rows = []
    r_len = len(params)
    today = datetime.date.today()
    cal = today.isocalendar()
    weeks = [i for i in params if i.startswith("week")]
    for i, w in enumerate(weeks):
        params["auto_week_no"] = cal.week - r_len + i
        rows.append(schema.InvoiceRow(fmt.format(**params), params[w]))
    return rows


def get_currency(cur1, cur2):
    """Return valid currency."""
    if cur1:
        return cur1
    if cur2:
        return cur2
    return "EUR"


def add_invoicing(cls):
    """Decorate class with invoicing methods."""

    class Invoicing(cls):
        """Invoicing methods."""

        def do_book_invoice(self):
            """Book invoice."""
            pdf_text = handlers.get_pdf(self.binary)[0]
            invoice = handlers.get_my_invoice(pdf_text)
            path = self.generate_path("out_invoice", "pdf")
            partner_id = lookups.get_partner(self.memory, invoice["partner"])
            booking = memories.Booking("out_invoice", self.memory, **{
                "date": invoice["date"],
                "reference": invoice["invoice_no"],
                "source": path,
                "comment": "sales invoice",
                "debit_amount": float(invoice["amount"]),
                "debit_currency": "EUR",
                "partner": partner_id,
            })
            booking.save()
            handlers.save_file(path, binary=self.binary)
            seq = int(invoice["no"])
            confirm_invoice_no(seq, partner_id, self.memory)

        def do_create_invoice(self):
            """Create new invoice."""
            partner = get_default_partner(self.memory)
            if partner is None:
                self.status = "No default partner set."
                return
            if partner.invoice_prefix is None:
                self.status = "No partner invoice prefix set."
                return
            myself = get_mydata(self.memory)
            addr_mgr = managers.AddressManager(self.memory)
            my_header = get_contact_header(
                myself.name,
                addr_mgr.get(myself.address_id).address_lines,
                myself.phone,
                myself.email)
            payer_header = get_contact_header(
                partner.name,
                addr_mgr.get(partner.address_id).address_lines,)
            my_bank = get_invoice_bank_info(
                myself.bank_name, myself.bank_account, myself.bank_code)
            inv_no = get_invoice_no(partner, self.memory)
            invoice_data = schema.InvoiceData(
                no=inv_no,
                biller=my_header,
                biller_bank=schema.BankInfo(*my_bank),
                payer=payer_header,
                rows=get_invoice_rows(partner.invoice_row_format, self.data[0]),
                terms=get_invoice_terms(partner.terms),
                rate=str(myself.rate),
                currency=get_currency(partner.currency, myself.currency),
            )
            i_bytes = BytesIO()
            write_invoice(i_bytes, invoice_data)
            self.attachment = i_bytes.getvalue()
            self.attachment_filename = f"{inv_no}.pdf"

    return Invoicing
