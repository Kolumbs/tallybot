"""Interface on any logical tasks accountant can perform.

>>> with Perform(conf, mem, "do_get_help", {}, b'') as job:
>>>     print(job.status, job.attachment, job.attachment_filename)
>>> assert job.status == "Done"
"""

import csv
from dataclasses import asdict
import datetime
import sys
import traceback
import urllib.request

from tallybot import handlers
from tallybot import memories
from tallybot import learner
from tallybot import managers
from tallybot.lookups import get_mydata, get_partner

from . import frontal_lobe
from .reports import add_reports
from .ledger import add_ledger
from .invoicing import add_invoicing


def do_task(conf, mem, cmd, data=None, attachment=None):
    """Perform a single task in the brain.

    Returns always a tuple of (msg, attachment, attachment_filename).
    msg should contain some text, attachments are optional (could be
    None)
    """
    try:
        with Perform(conf, mem, cmd, data, attachment) as job:
            return (job.status, job.attachment, job.attachment_filename)
    except RuntimeWarning as err:
        return (str(err), None, None)
    except Exception:
        msg = traceback.format_exception(*sys.exc_info())
        msg = "".join(msg)
        msg = "-" * 80 + "\n" + msg + "\n" + "-" * 80
        msg = (
            "Oh my, madness in my brain :sweat: Send this to my developer:\n"
            + msg
        )
        return (msg, None, None)


def generate_help():
    """Generate help message from cmds available in this module."""
    msg = "I did not understand your message\n\n"
    msg += "Send new one with following choices in subject:\n"
    for i in generate_cmd_list():
        msg += " ".join(i.split("_"))
        msg += " - "
        msg += getattr(Perform, i).__doc__
        msg += "\n"
    return msg


def generate_cmd_list():
    """Generate available command list."""
    return [i for i in dir(Perform) if i.startswith("do_")]


def check_required(content, fields):
    """Check if required fields exist in content."""
    misf = []
    for i in fields:
        if i not in content or not content[i]:
            misf.append(i)
    if misf:
        msg = f"Missing required field '{misf[0]}'"
        for i in misf[1:]:
            msg += f", '{i}'"
        raise RuntimeWarning(msg)


def get_invoice_prefix(name):
    """Get invoice prefix from name."""
    return name[:3].upper()


# pylint: disable=too-many-public-methods
@add_reports
@add_ledger
@add_invoicing
class Perform(frontal_lobe.Functions):
    """Map all possible actions to what received msg may ask and execute action
    found."""

    def do_get_help(self):
        """Get help as list of commands available."""
        self.status = ""
        for i in generate_cmd_list():
            self.status += " ".join(i.split("_")) + "\n"

    def do_add_default_partner(self):
        """Add default partner by it's name."""
        data = self.data[0]
        check_required(data, {"name"})
        value = data["name"]
        partner = self.memory.get.partner(name=value)
        if not partner:
            self.status = f"Partner with name '{value}' does not exist"
        else:
            me = memories.MySelf(key="default_partner", text=partner.id)
            self.memory.put(me)

    def do_update_ledger(self):
        """Update transactions given in excel ledger."""
        ws_sheet = handlers.get_excel(self.binary).active
        headers = False
        self.status = ""
        for row in ws_sheet:
            if not headers:
                headers = [i.value.lower() for i in row]
                continue
            book = dict(zip(headers, [i.value for i in row]))
            update = self.memory.get.transaction(id=book.pop("id"))
            for attr, value in book.items():
                if attr == "date":
                    value = datetime.date.fromisoformat(value)
                elif attr == "partner":
                    partner = self.memory.get.partner(name=value)
                    if not partner:
                        self.status += (
                            f"Fail {update.id} as partner {value} not found\n"
                        )
                    value = partner.id
                setattr(update, attr, value)
            self.memory.put(update)
        self.status += "Done"

    def do_private_income(self):
        """Add private income entry.

        date: YYYY-MM-DD
        partner: {partner_name}
        value: {amount}
        """
        data = self.data[0]
        date = datetime.date.fromisoformat(data["date"])
        partner = frontal_lobe.get_partner(self.memory, data.pop("partner"))
        booking = memories.Booking(
            "private-income",
            self.memory,
            **{
                "date": date,
                "reference": "",
                "comment": "private income",
                "partner": partner,
                "source": "",
                "debit_amount": float(data["value"]),
            },
        )
        booking.save()

    def do_delete_transaction(self):
        """Delete a transaction.

        id: str
        """
        del_id = self.data[0]["id"]
        trans = self.memory.get.transaction(id=del_id)
        if not trans:
            self.status = (
                "Transaction with id '{del_id}' not found so not deleted"
            )
        self.memory.delete(trans)

    def do_add_initial_asset(self):
        """Add initial asset with depreciation calculations.

        date: YYYY-MM-DD
        name: str
        reference: str
        value: float
        utility: int (months)
        """
        asset = self.data[0]
        asset["date"] = datetime.datetime.strptime(asset["date"], "%Y-%m-%d")
        path = self.generate_path("inc_invoice", "pdf")
        asset_name = asset.pop("name")
        asset["debit_amount"] = float(asset.pop("value"))
        asset["comment"] = f"Initial asset {asset_name}"
        asset["source"] = path
        utility = int(asset.pop("utility"))
        booking = memories.Booking("init-asset", self.memory, **asset)
        booking.save()
        data = {
            "date": asset["date"],
            "comment": f"Monthly depreciation for {asset_name}",
        }
        data["debit_amount"] = round(asset["debit_amount"] / utility, 2)
        data["source"] = path
        for i in range(utility):
            data["reference"] = (
                f"Depreciation costs on asset '{asset_name}' for month no: {i}"
            )
            if data["date"].month == 12:
                data["date"] = datetime.date(
                    year=data["date"].year + 1,
                    month=1,
                    day=data["date"].day,
                )
            else:
                data["date"] = datetime.date(
                    year=data["date"].year,
                    month=data["date"].month + 1,
                    day=data["date"].day,
                )
            depreciate = memories.Booking(
                "asset-depreciate", self.memory, **data
            )
            depreciate.save()
        handlers.save_file(path, self.binary)

    def do_get_social_report(self):
        """Get report for social tax.

        quarter: YYYY-Qn
        """
        quarter = self.data[0]["quarter"]
        date = datetime.datetime.strptime(quarter[:4], "%Y")
        months = {
            "1": [1, 2, 3],
            "2": [4, 5, 6],
            "3": [7, 8, 9],
            "4": [10, 11, 12],
        }
        self.status = "Social report (profit with 500 deducted already)\n\n"
        for month in months[quarter[-1]]:
            start_date = datetime.date(year=date.year, month=month, day=1)
            end_date = datetime.date(year=date.year, month=month + 1, day=1)
            book = self.memory.get(
                self.memory.transaction.date >= start_date,
                self.memory.transaction.date < end_date,
            )
            income = 0
            expense = 0
            for i in book:
                if 6000 <= i.credit < 7000:
                    income += i.deal_value
                elif 7000 <= i.debit < 8000:
                    expense += i.deal_value
                elif i.debit == 8250:
                    expense += i.deal_value
                elif i.credit == 8150:
                    income += i.deal_value
            profit = round(income - expense - 500, 2)  # profit above 500
            self.status += start_date.strftime("%Y-%m") + f": {profit}\n"

    def do_add_carwash(self):
        """Add expense on carwash.

        date: YYYY-MM-DD
        reference: str
        value: float
        """
        expense = self.data[0]
        expense["partner"] = "Circle K"
        expense["comment"] = "auto car wash"
        expense["expense_account"] = "7760"
        path = self.generate_path("inc_invoice", "pdf")
        expense["path"] = path
        self.make_expense_booking(expense)
        handlers.save_file(path, self.binary)

    def do_add_trip(self):
        """Add new trip.

        date: YYYY-MM-DD
        ----------------
        # Fuel Receipt
        receipt_ref: str
        receipt_litres: float
        receipt_value: float

        attach receipt as pdf
        ----------------
        # Trip
        trip: str
        description: str
        distance: float
        """
        trips = self.data
        if len(trips) > 1:
            raise RuntimeWarning("Only one trip per request")
        trip = trips[0]
        if "receipt_ref" in trip:
            check_required(trip, ["receipt_litres", "receipt_value"])
            trip["trip"] = "Mārupe - Circle K"
            trip["description"] = "add fuel"
            trip["distance"] = 5
            path = self.generate_path("inc_invoice", "pdf")
        check_required(trip, ["trip", "description", "date", "distance"])
        try:
            to_save = memories.Trip(**trip)
        except TypeError as error:
            raise RuntimeWarning(str(error)[11:]) from None
        self.memory.put(to_save)
        car = self.memory.get.car(id=memories.DEFAULT_CAR_PLATE)
        if not car:
            car = memories.Car()
        car.total_km += to_save.distance
        self.memory.put(car)
        if "receipt_ref" in trip:
            handlers.save_file(path, self.binary)

    def do_trip_summary(self):
        """Perform trip summary.

        date: YYYY-MM
        """
        body = self.data
        if len(body) < 1:
            raise RuntimeWarning("There is no date found in message body")
        date = datetime.datetime.strptime(body[0]["date"], "%Y-%m")
        self.prepare_trip_report(date)

    def do_remove_transaction(self):
        """Remove a transaction by it's id."""
        booking = self.data[0]
        item = self.memory.get.transaction(id=booking["id"])
        if item:
            self.memory.delete(item)
        else:
            self.status = f"Id: '{booking['id']}' not found"

    def do_add_fuel_expense(self):
        """Add fuel expense transaction.

        date: YYYY-MM
        tahometer: int
        force:
        """
        expense = self.data[0]
        date = datetime.datetime.strptime(expense["date"], "%Y-%m")
        today = datetime.date.today()
        if (
            date.month != today.month + 1 or today.day > 10
        ) and "force" not in expense:
            msg = "It is recommended to do fuel expense in the first 5 days"
            msg += " of next month or use 'force' to ignore this warning"
            raise RuntimeWarning(msg)
        self.prepare_trip_report(date, tahometer=expense["tahometer"])
        metrics = memories.TripMetrics()
        for i in self.trips:
            metrics.distance += i.distance
            metrics.litres += i.receipt_litres
        if metrics.litres == 0:
            msg = f"There are no fuel receipts for {date.strftime('%Y-%m')}"
            raise RuntimeWarning(msg)
        split = metrics.distance / 100 * 8 / metrics.litres * 100
        for i in self.trips:
            if i.receipt_ref:
                expense = {"split": split, "partner": "Circle K"}
                expense["value"] = i.receipt_value
                expense["date"] = i.date.isoformat()
                expense["reference"] = i.receipt_ref
                expense["comment"] = i.description
                expense["expense_account"] = "7760"
                expense["path"] = self.generate_path("inc_invoice", "pdf")
                self.make_expense_booking(expense)

    def do_private_expense(self):
        """Add private expense.

        date: YYYY-MM-DD
        partner: {partner_name}
        value: {amount}
        """
        expense = self.data[0]
        date = datetime.date.fromisoformat(expense["date"])
        partner = frontal_lobe.get_partner(self.memory, expense.pop("partner"))
        booking = memories.Booking(
            "private-expense",
            self.memory,
            **{
                "date": date,
                "reference": "",
                "comment": "private expense",
                "partner": partner,
                "source": "",
                "debit_amount": float(expense["value"]),
            },
        )
        booking.save()

    def do_add_expense(self):
        """Add expense transaction.

        date: YYYY-MM-DD
        reference: {invoice_no}
        comment: {comment}
        partner: {partner_name}
        value: {amount}
        expense_account: {expense_account} = 7120
        currency: {currency_code} = EUR
        split: {split_percent} = 100
        """
        data = self.data
        l_data = len(data)
        if l_data != 1:
            raise RuntimeWarning(
                f"Exactly one expense invoice per request got {l_data}"
            )
        expense = data[0]
        expense["path"] = self.generate_path("inc_invoice", "pdf")
        self.make_expense_booking(expense)
        handlers.save_file(expense["path"], self.binary)

    def do_get_carinfo(self):
        """Provide car info."""
        car = self.memory.get.car(id=memories.DEFAULT_CAR_PLATE)
        self.status = f"Car {memories.DEFAULT_CAR_PLATE}\n"
        self.status += 10 * "-" + "\n\n"
        self.status += f"Tahometer: {car.total_km}"

    def do_list_partners(self):
        """Provide excel list on existing partners."""
        r_structs = []
        items = self.memory.get("partner")
        r_structs.append(memories.ReportStruct("partners", items, self.memory))
        items = self.memory.get("partnerindex")
        r_structs.append(
            memories.ReportStruct("partnerindex", items, self.memory)
        )
        self.attachment = handlers.ExcelGenerator(*r_structs).binary()
        self.attachment_filename = "partners.xlsx"

    def do_get_myself(self):
        """Provide information about myself."""
        myself = get_mydata(self.memory)
        self.status = ""
        for i, j in asdict(myself).items():
            self.status += i + ": " + str(j) + "\n"

    def do_update_myself(self):
        """Update myself."""
        params = self.data[0]
        myself = get_mydata(self.memory)
        address = managers.AddressManager(self.memory).update(
            params, myself.address_id
        )
        if address:
            params["address_id"] = address.id
        for field in memories.data.fields(memories.Me):
            if field.name in params:
                payload = {"key": field.name}
                if field.type == str:
                    payload["text"] = params[field.name]
                if field.type == float:
                    payload["value"] = float(params[field.name])
                if field.type == list:
                    payload["lst"] = params[field.name]
                if field.type == dict:
                    payload["dct"] = params[field.name]
                if len(payload) == 1:
                    raise ValueError(f"Field {field.name} is not supported")
                ms = memories.MySelf(**payload)
                self.memory.put(ms)

    def do_get_partner(self):
        """Retrieve partner information."""
        partner_name = self.data[0].pop("name")
        partner_id = get_partner(self.memory, partner_name)
        partner = self.memory.get.partner(id=partner_id)
        if not partner:
            raise RuntimeWarning(
                f"Partner with name '{partner_name}' does not exist"
            )
        self.status = ""
        for i, j in asdict(partner).items():
            self.status += i + ": " + str(j) + "\n"
        partner_index = self.memory.get(
            self.memory.partnerindex.partner_id == partner.id
        )
        self.status += "Indexes: "
        for index in partner_index:
            self.status += index.text + ", "

    def do_update_partner(self):
        """Update partner."""
        mgr = managers.PartnerManager(self.memory)
        try:
            mgr.update(self.data[0])
        except AssertionError as e:
            self.status = str(e)

    def do_create_partner(self):
        """Add or update partner in register.

        Use:
            name: {your partner name}
            other_names: {OPTIONAL: similar, similar2}
        """
        for item in self.data:
            if "id" not in item:
                partner = self.memory.get.partner(name=item["name"])
                if partner:
                    self.status += (
                        f"'{partner.name}' exists with id: {partner.id}\n"
                    )
                    continue
            other_names = []
            if "other_names" in item:
                others = [i.strip() for i in item.pop("other_names").split(",")]
                other_names += others
            try:
                item["invoice_prefix"] = get_invoice_prefix(item["name"])
                partner = memories.Partner(**item)
                self.memory.put(partner)
                other_names.append(partner.name)
                for text in other_names:
                    index = self.memory.get.partnerindex(text=text)
                    if index:
                        self.memory.delete(index)
                    self.memory.put(memories.PartnerIndex(text, partner.id))
            except TypeError as error:
                msg = str(error).split(")")[1].strip().capitalize()
                raise RuntimeWarning(msg) from None

    # pylint: disable=R0914, R0912
    # too many statements and local variables
    def do_seb_statement(self):
        """Do seb statement upload."""
        if isinstance(self.binary, str):
            self.binary = self.binary.encode()
        csv_input = self.binary.decode().splitlines()
        csv_reader = csv.reader(csv_input, delimiter=";")
        fname = "seb_" + datetime.date.today().isoformat()
        path = self.generate_path("statement", fname, "csv")
        header = 2
        bookings = []
        errs = []
        for i in csv_reader:
            book_type = False
            if header:
                header -= 1
                continue
            date = datetime.datetime.strptime(i[1], "%d.%m.%Y")
            date = datetime.date(date.year, date.month, date.day)
            value = float(i[3])
            partner = i[4].split("\\")[0].strip()
            if i[14] == "D":
                book_type = "seb-expense"
            elif i[14] == "C":
                if "upwork" in i[4].lower():
                    book_type = "seb-upwork-income"
                else:
                    book_type = "seb-income"
            if "pamatsumma" in i[9] and "KT08093" in i[9]:
                partner = "SEB banka"
            try:
                partner = frontal_lobe.get_partner(self.memory, partner)
            except RuntimeWarning as error:
                errs.append(str(error))
            booking = {
                "date": date,
                "reference": i[10],
                "source": path,
                "comment": i[9],
                "debit_amount": value,
                "partner": partner,
                "book_type": book_type,
            }
            bookings.append(booking)
            # Special auto-bookings
            bookings += learner.get_bookings(booking, i)
        if errs:
            raise RuntimeWarning("\n".join(errs))
        for booking in bookings:
            book_type = booking.pop("book_type")
            booking = memories.Booking(book_type, self.memory, **booking)
            booking.save()
        handlers.save_file(path, self.binary)

    def do_upwork_statement(self):
        """Do upwork statement upload."""
        if isinstance(self.binary, str):
            self.binary = self.binary.encode()
        csv_input = self.binary.decode().splitlines()
        csv_reader = csv.reader(csv_input, delimiter=",")
        fname = "upwork_" + datetime.date.today().isoformat()
        path = self.generate_path("statement", fname, "csv")
        header = True
        for i in csv_reader:
            if header:
                header = False
                continue
            date = datetime.datetime.strptime(i[0], "%b %d, %Y")
            date = datetime.date(date.year, date.month, date.day)
            value = abs(float(i[9]))
            currency = self.exchange_rate(date, "USD")
            partner = ""
            if "VAT" in i[2] or "Service Fee" in i[2] or "Withdrawal" in i[2]:
                partner = frontal_lobe.get_partner(self.memory, "Upwork")
            elif i[6]:
                partner = frontal_lobe.get_partner(self.memory, i[6])
            if i[11]:
                credit_curr = i[11]
                credit_value = float(i[10])
            else:
                credit_curr = "USD"
                credit_value = value
            booking = memories.Booking(
                i[2],
                self.memory,
                **{
                    "date": date,
                    "reference": i[1],
                    "source": path,
                    "comment": i[3],
                    "debit_amount": value,
                    "credit_amount": credit_value,
                    "rate": currency.rate,
                    "debit_currency": "USD",
                    "credit_currency": credit_curr,
                    "partner": partner,
                },
            )
            booking.save()
        handlers.save_file(path, self.binary)

    def do_upwork_invoices(self):
        """Upload invoices from Upwork."""
        zip_file = handlers.get_zip(self.binary)
        for i in zip_file:
            pdf_text = handlers.get_pdf(i)[0]
            invoice = handlers.get_invoice(pdf_text)
            rate = self.exchange_rate(invoice[0], "USD")
            if "Upwork" in invoice[4]:
                inv_type = "inc_invoice"
                partner = frontal_lobe.get_partner(self.memory, "Upwork")
            else:
                inv_type = "out_invoice"
                partner = frontal_lobe.get_partner(self.memory, invoice[5])
            path = self.generate_path(inv_type, "pdf")
            booking = memories.Booking(
                inv_type,
                self.memory,
                **{
                    "date": invoice[0],
                    "reference": invoice[1],
                    "source": path,
                    "comment": invoice[2],
                    "debit_amount": float(invoice[3]),
                    "rate": rate.rate,
                    "debit_currency": "USD",
                    "credit_currency": "USD",
                    "partner": partner,
                },
            )
            booking.save()
            handlers.save_file(path, binary=i)

    def do_accounts_update(self):
        """Upload accounts from external source."""
        url = "http://www.vid.lv/kontu-pl257ns.html"
        with urllib.request.urlopen(url) as response:
            html = response.read()
            parser = frontal_lobe.VIDPageParser(self.memory)
            parser.feed(html.decode(encoding="utf-8"))
