"""Logical functions performed by accountant."""
import datetime
from html.parser import HTMLParser
import os
import uuid

from .. import memories, handlers, exchange
from ..lookups import get_partner


class Functions():
    """Adds function set to main brain.Perform class."""

    # pylint: disable=too-many-instance-attributes,too-many-arguments
    def __init__(self, conf, memory, cmd, data, attachment):
        """Init and call executor."""
        self.attachment = None
        self.attachment_filename = None
        self.ecb_xml_memory = None
        self.binary = attachment
        self.data = data
        self.memory = memory
        self.conf = conf
        self.trips = set()
        self.status = "Done"
        getattr(self, cmd)()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_msg, exc_tr):
        pass

    def prepare_trip_report(self, date, tahometer=False):
        """Prepare an excel binary report of trips."""
        title = "tripsummary"
        trips = self.memory.get(
            self.memory.trip.year == date.year,
            self.memory.trip.month == date.month,
        )
        r_struct = memories.ReportStruct(
            title,
            trips,
            self.memory,
            report_args={"tahometer": tahometer}
        )
        self.trips = trips
        self.attachment = handlers.ExcelGenerator(r_struct).binary()
        self.attachment_filename = f"{title}.xlsx"

    def generate_path(self, group, extension, filename=""):
        """Pre-generates file save path."""
        if not filename:
            filename = str(uuid.uuid1()).split('-', maxsplit=1)[0]
        if group not in ["out_invoice", "inc_invoice", "statement"]:
            raise RuntimeWarning(f"Not possible to find a path to save '{group}'")
        path = self.conf[group + "_path"]
        dirname = os.path.dirname(path)
        if not os.path.exists(dirname):
            raise RuntimeWarning(f"Path '{dirname}' does not exist")
        return path + filename + "." + extension

    def exchange_rate(self, date, pair):
        """Give an exchange rate for a date on given pair.

        Otherwise raises Exception.
        """
        date = datetime.date(date.year, date.month, date.day)
        now_date = datetime.date.today()
        msg = "Rates are not available, as requested "
        if date > now_date:
            msg += f"{date} is in future"
            raise RuntimeWarning(msg)
        currency = self.memory.get.currency(date=date, currency=pair)
        if currency:
            return currency
        rate = exchange.get_rate(pair, date)
        currency = memories.Currency(*(date, pair, rate))
        self.memory.put(currency)
        return currency

    def make_expense_booking(self, expense):
        """Do expense transaction."""
        book_type = "expense:"
        if "expense_account" not in expense:
            book_type += "7120"
        else:
            if expense["expense_account"][0] != "7":
                raise RuntimeWarning("Expense account must start with '7'")
            book_type += expense["expense_account"]
        split_expense = False
        if "split" in expense and float(expense["split"]) < 100:
            split_expense = True
            value = round(float(expense["value"]) * float(expense["split"]) / 100, 2)
        else:
            value = float(expense["value"])
        date = datetime.date.fromisoformat(expense["date"])
        ref = expense["reference"]
        partner = get_partner(self.memory, expense.pop("partner"))
        booking = memories.Booking(book_type, self.memory, **{
            "date": date,
            "reference": ref,
            "comment": expense["comment"],
            "partner": partner,
            "source": expense["path"],
            "debit_amount": value,
        })
        booking.save()
        if split_expense:
            booking = memories.Booking("private-expense", self.memory, **{
                "date": date,
                "reference": ref,
                "comment": "private expense",
                "partner": partner,
                "source": expense["path"],
                "debit_amount": round(float(expense["value"]) - value, 2),
            })
            booking.save()


# pylint: disable=W0223
class VIDPageParser(HTMLParser):
    """Parse www.vid.lv page into accounts list."""

    content = False
    div_nest = []
    accounts = []

    def __init__(self, memory):
        """Add memory access."""
        HTMLParser.__init__(self)
        self.memory = memory

    def handle_starttag(self, tag, attrs):
        """As soon as wsite-content div found store it."""
        if tag == "div":
            for i in attrs:
                if i[0] == "id" and i[1] == "wsite-content":
                    self.content = True
        if self.content and tag == "div":
            self.div_nest.append(0)

    def handle_endtag(self, tag):
        """Clean content when wsite-content exits."""
        if tag == "div":
            if self.content and self.div_nest:
                self.div_nest.pop()
            elif self.content:
                self.content = False

    def handle_data(self, data):
        """Parse data and store accounts."""
        if self.content and len(data) > 5 and data[:4].isdigit():
            account = memories.Account(int(data[:4]), data[5:].strip())
            self.memory.put(account)
