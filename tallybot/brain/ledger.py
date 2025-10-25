"""Functions related to creating bookings in ledger."""

import datetime

from ..memories import Transaction, ReportStruct, PARTNER_ACCOUNTS
from ..handlers import ExcelGenerator, get_csv_text
from ..lookups import get_partner


def get_debitsum_by_partner(mem, year, partner, account):
    """Return sum of all transaction debit amounts for a partner."""
    return sum(
        i.debit_amount
        for i in get_partner_bookings(mem, year, partner, debit=account)
    )


def get_creditsum_by_partner(mem, year, partner, account):
    """Return sum of all transaction credit amounts for a partner."""
    return sum(
        i.credit_amount
        for i in get_partner_bookings(mem, year, partner, credit=account)
    )


def get_partner_bookings(mem, year, partner, debit=None, credit=None):
    """Return sum of all transaction for a partner."""
    this_year = datetime.date(year=year, month=1, day=1)
    next_year = datetime.date(year=year + 1, month=1, day=1)
    partner = get_partner(mem, partner)
    filters = {"partner": partner}
    if debit:
        filters["debit"] = debit
    if credit:
        filters["credit"] = credit
    return mem.get(
        "transaction",
        mem.transaction.date >= this_year,
        mem.transaction.date < next_year,
        **filters,
    )


def get_previous_quarter(today=None):
    """Return start date and end date for previous quarter.

    Depending on today's date or given date, return tuple of date
    objects in format of [start, end), where start is inclusive and end
    is exclusive.
    """
    if today is None:
        today = datetime.date.today()
    if today.month < 4:
        start = datetime.date(year=today.year - 1, month=10, day=1)
        end = datetime.date(year=today.year, month=1, day=1)
    else:
        current_quarter = (today.month - 1) // 3 + 1
        q_month = (current_quarter - 2) * 3 + 1
        start = datetime.date(year=today.year, month=q_month, day=1)
        if start.month == 10:
            end = datetime.date(year=start.year + 1, month=1, day=1)
        else:
            end = datetime.date(year=start.year, month=start.month + 3, day=1)
    return start, end


def get_interval_dates(data):
    """From data dictionary input deduce start and end date for ledger.

    Expects dictionary returns tuple that is date interval of start and
    end (excluding) In case fails returns False in both values.
    """
    start = end = False
    if "filter_by_quarter" in data:
        year = (
            int(data["filter_by_year"])
            if data["filter_by_year"]
            else datetime.date.today().year
        )
        if data["filter_by_quarter"].startswith("q"):
            q_month = int(data["filter_by_quarter"][1]) * 3 - 2
            start = datetime.date(year=year, month=q_month, day=1)
            if start.month == 10:
                end = datetime.date(year=start.year + 1, month=1, day=1)
            else:
                end = datetime.date(
                    year=start.year, month=start.month + 3, day=1
                )
        elif data["filter_by_quarter"].startswith("l"):
            start, end = get_previous_quarter()
    elif "filter_by_month" in data:
        start = datetime.datetime.strptime(data["filter_by_month"], "%Y-%m")
        start = datetime.date(year=start.year, month=start.month, day=1)
        if start.month == 12:
            end = datetime.date(year=start.year + 1, month=1, day=1)
        else:
            end = datetime.date(year=start.year, month=start.month + 1, day=1)
    return start, end


def update_transaction(data: dict, memory) -> None:
    """Update transaction from data dictionary.

    If unsuccessful, always raises ValueError.
    """
    if "id" not in data:
        raise ValueError("Missing id for transaction update")
    update = memory.get.transaction(id=data["id"])
    for attr, value in data.items():
        if attr == "date":
            value = datetime.date.fromisoformat(value)
        elif attr == "partner":
            partner = memory.get.partner(name=value)
            if not partner:
                raise ValueError(f"There is no such partner '{value}'")
            value = partner.id
        setattr(update, attr, value)
    memory.put(update)


def add_ledger(cls):
    """Decorate cls with ledger functions."""

    class Ledger(cls):
        """Ledger functions for accountant."""

        def do_get_ledger(self):
            """Return general ledger in Excel."""
            data = self.data
            data = data[0] if data else {}
            attrs = [i for i in data.keys() if not i.startswith("filter_by")]
            start, end = get_interval_dates(data)
            if start:
                comp = self.memory.transaction
                args = ["transaction"]
                args.append(comp.date >= start)
                args.append(comp.date < end)
                items = self.memory.get(*args)
            else:
                items = self.memory.get("transaction")
            r_struct = ReportStruct("ledger", items, self.memory, attrs=attrs)
            self.attachment = ExcelGenerator(r_struct).binary()
            self.attachment_filename = "ledger.xlsx"

        def do_list_transactions(self):
            """List transactions in ledger."""
            data = self.data[0]
            filters = {}
            if data.get("partner"):
                filters["partner"] = get_partner(self.memory, data["partner"])
            today = datetime.date.today()
            year = data["year"] if data.get("year") else today.year
            month = data.get("month")
            earliest_date = datetime.date(year=year, month=month or 1, day=1)
            latest_date = datetime.date(
                year=year if month and month < 12 else year + 1,
                month=month + 1 if month else 1,
                day=1,
            )
            items = self.memory.get(
                "transaction",
                self.memory.transaction.date >= earliest_date,
                self.memory.transaction.date < latest_date,
                **filters,
            )
            r_struct = ReportStruct("ledger", items, self.memory)
            self.status = get_csv_text(r_struct)

        def do_transaction(self):
            """Create transaction in ledger."""
            self.data = self.data[0]
            if "partner" in self.data:
                partner_id = get_partner(self.memory, self.data["partner"])
                self.data["partner"] = partner_id
            self.data["date"] = datetime.date.fromisoformat(self.data["date"])
            self.data["debit_amount"] = float(self.data["debit_amount"])
            if "debit" in self.data:
                self.data["debit"] = int(self.data["debit"])
            if "credit" in self.data:
                self.data["credit"] = int(self.data["credit"])
            booking = Transaction(**self.data)
            self.memory.put(booking)

        def do_update_transaction(self):
            """Update transaction in ledger."""
            self.data = self.data[0]
            update_transaction(self.data, self.memory)

        def do_recalculate_outstanding(self):
            """Recalculate outstanding entries for a given year and partner."""
            year = int(self.data[0]["year"])
            partner = self.data[0]["partner"]
            for acc in PARTNER_ACCOUNTS:
                debit_stack = get_debitsum_by_partner(
                    self.memory, year, partner, acc
                )
                credit_stack = get_creditsum_by_partner(
                    self.memory, year, partner, acc
                )
                for booking in get_partner_bookings(
                    self.memory, year, partner, debit=acc
                ):
                    credit_stack -= booking.debit_amount
                    if round(credit_stack, 2) < 0:
                        booking.debit_stack = round(credit_stack, 2)
                        break
                    booking.debit_stack = 0
                    self.memory.put(booking)
                for booking in get_partner_bookings(
                    self.memory, year, partner, credit=acc
                ):
                    debit_stack -= booking.credit_amount
                    if round(debit_stack, 2) < 0:
                        booking.credit_stack = round(debit_stack, 2)
                        break
                    booking.credit_stack = 0
                    self.memory.put(booking)

    return Ledger
