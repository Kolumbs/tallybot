# pylint: disable=C0115,C0116
"""Email interface tests for accountant."""
import csv
import datetime
import io
from unittest.mock import patch, MagicMock
import unittest

import membank
from openpyxl import load_workbook

from tallybot import brain, memories
from tests import base


# SMTP mock
smtp_call = MagicMock()
enter_smtp = MagicMock()
enter_smtp.__enter__.return_value = smtp_call
smtp_mock = MagicMock(return_value=enter_smtp)
# Brain Perform mock
brain_call = ["", b"", ""]
brain_mock = MagicMock(return_value=brain_call)
# Brain Perform mock with RuntimeError
brain_mock_exception = MagicMock(side_effect=RuntimeError("oh"))


def get_table(rows):
    """Get from openpyxl rows objec a string table."""
    msg = "\n"
    for row in rows:
        msg += " ".join([str(i.value) for i in row]) + "\n"
    return msg


class PrivateIncome(base.AbstractEmailInterfaceTest):
    """Testcases on doing private income."""

    def setUp(self):
        """Prepare private income email."""
        super().setUp()
        self.email = base.load_email()
        self.email["subject"] = "do private income"
        self.val = 83.18
        partner = "Upwork"
        date = datetime.date(year=2022, month=3, day=24)
        content = f"""date: {date.strftime("%Y-%m-%d")}
            partner: {partner}
            value: {self.val}"""
        self.email.set_content(content)

    def test(self):
        """Make private income entry."""
        self.do_job_call()
        memory = membank.LoadMemory(self.conf["db_path"])
        booking = memory.get(
            memory.transaction.debit == 2310,
            memory.transaction.credit == 8900,
            memory.transaction.debit_amount == self.val,
        )
        self.assertEqual(1, len(booking), list(booking))


class UpdateTransaction(base.AbstractEmailInterfaceTest):
    """Testcase on editing transactions from ledger excel."""

    def setUp(self):
        base.AbstractEmailInterfaceTest.setUp(self)
        self.load_partners()
        self.load_seb_statement()

    def test_edit(self):
        """Edit transaction with excel."""
        excel = self.get_excel_ledger()
        sheets = excel.active
        header = True
        for i in sheets:
            if header:
                header = False
                continue
            i[0].value = "2022-03-05"
        tmp = io.BytesIO()
        excel.save(tmp)
        tmp.seek(0)
        excel_bytes = tmp.read()
        tmp.close()
        email = base.load_email(
            fname="ledg", fn_obj=excel_bytes, subtype="xlsx"
        )
        email["subject"] = "do update ledger"
        self.do_job_call(email)
        excel = self.get_excel_ledger()
        new_sheets = excel.active
        for row, new_row in zip(sheets, new_sheets):
            for cell, new_cell in zip(row, new_row):
                self.assertEqual(cell.value, new_cell.value)

    def get_excel_ledger(self):
        email = base.load_email()
        email["subject"] = "do get ledger"
        self.do_job_call(email)
        tmp = io.BytesIO()
        tmp.write(self.response[1])
        tmp.seek(0)
        excel = load_workbook(tmp)
        tmp.close()
        return excel


class DeleteTransaction(base.AbstractEmailInterfaceTest):
    """Testcase on deleting transactions."""

    def test_delete(self):
        """Calling delete should delete a transaction."""
        mem = self.memory
        self.load_transactions()
        trans = mem.get("transaction")
        self.assertTrue(len(trans) > 0)
        for i in trans:
            email = base.load_email(content=f"id: {i.id}")
            email["subject"] = "do delete transaction"
            self.do_job_call(email)
        trans = mem.get("transaction")
        self.assertEqual(len(trans), 0)


class Assets(base.AbstractEmailInterfaceTest):
    """Testcase on asset depreciation."""

    def test_asset_calculation(self):
        mem = self.memory
        val = 1000
        content = f"""
            date: 2022-03-22
            name: Laptop
            reference: 5698934
            value: {val}
            utility: 23
        """
        email = base.load_email(
            content=content, fname="asset", subtype="pdf", fn_obj=1
        )
        email["subject"] = "do add initial asset"
        self.do_job_call(email, assert_status=False)
        books = mem.get(mem.transaction.debit == 7420)
        self.assertEqual(len(books), 23)
        for i in books:
            self.assertEqual(round(val / 23, 2), i.debit_amount)


class SocialReport(base.AbstractEmailInterfaceTest):
    """Testcase on social tax report."""

    @patch("accountant.brain.main.handlers.save_file", new=MagicMock())
    def test_report(self):
        self.load_transactions()
        self.load_upwork_invoices()
        email = base.load_email(content="quarter: 2022-Q1")
        email["subject"] = "do get social report"
        self.do_job_call(email, assert_status=False)
        self.assertIn("Social report", self.response[0])


class CarWash(base.AbstractEmailInterfaceTest):
    """Testcases on carwash receipts."""

    def setUp(self):
        base.AbstractEmailInterfaceTest.setUp(self)
        self.memory = membank.LoadMemory(self.conf["db_path"])
        self.load_partners()

    @patch("accountant.brain.main.handlers.save_file")
    def test_wash(self, save_file):
        self.do_add_carwash()
        expense = self.memory.get(self.memory.transaction.debit == 7760)
        self.assertEqual(len(expense), 1)
        save_file.assert_called()


class ManageTrips(base.AbstractEmailInterfaceTest):
    """Testcases on car trips."""

    def setUp(self):
        base.AbstractEmailInterfaceTest.setUp(self)
        self.email = base.load_email(fname="receipt", subtype="pdf")
        self.load_partners()
        self.load_seb_statement()
        self.memory = membank.LoadMemory(self.conf["db_path"])
        self.excel_rows = {}
        self.args = {
            "date": "2022-03-05",
            "trip": "Rīga - Madona",
            "description": "Maintenance of server room",
            "distance": 230,
        }

    def test_trip_errors(self):
        date = "date: 2022-03-24\n"
        dist = "distance: 200\n"
        desc = "description:\n"
        trip = "trip:\n"
        ref = "receipt_ref: some\n"
        val = "receipt_value:\n"
        lit = "receipt_litres\n"
        cases = []
        cases.append([date, dist, desc])
        cases.append([date, dist, trip])
        cases.append([date + ref, val])
        cases.append([date + ref, lit])
        for i in cases:
            self.error_checks(i)
        email = base.load_email()
        email["subject"] = "do trip summary"
        self.do_job_call(email, assert_status=False)
        self.assertIn("There is no date found", self.response[0])

    def error_checks(self, args, flag="missing"):
        content = ""
        for i in args:
            content += i
            email = base.load_email(
                content=content, fname="receipt", subtype="pdf"
            )
            email["subject"] = "do add trip"
            self.do_job_call(email, assert_status=False)
            if flag == "missing":
                self.assertIn(
                    "Missing required field", self.response[0], content
                )

    @patch("accountant.brain.main.handlers.save_file")
    def test_trip_booking(self, save_file):
        self.args["receipt_ref"] = "576"
        self.args["receipt_litres"] = 67
        self.args["receipt_value"] = 68
        self.make_trip(**self.args)
        save_file.assert_called_once()
        self.assertIn(
            "tests/tmp/ienakosie_rekini/", save_file.call_args.args[0]
        )
        self.assertEqual(b"0", save_file.call_args.args[1])
        email = base.load_email()
        email["subject"] = "do get carinfo"
        self.do_job_call(email, assert_status=False)
        self.assertIn(str(memories.DEFAULT_CAR_ODO_KM + 5), self.response[0])

    def test_add_trip(self):
        args = self.args
        self.make_trip(**args)
        self.check_trip_summary()
        tests = (
            (args["date"], "A11"),
            (None, "B11"),
            (None, "C11"),
            (args["trip"], "D11"),
            (args["description"], "E11"),
            (args["distance"], "F11"),
        )
        self.assert_values(tests)

    @patch("accountant.brain.main.handlers.save_file")
    def test_add_trips(self, save_file):
        total_distance = self.make_trips()[0]
        self.check_trip_summary()
        tests = (
            ("2022-03-01", "A11"),
            ("2022-03-04", "A14"),
        )
        self.assert_values(tests)
        distance = sum(self.excel_rows["F" + str(11 + i)] for i in range(5))
        self.assertEqual(total_distance, distance)
        car = self.memory.get("car")[0]
        self.assertEqual(car.total_km, total_distance)
        save_file.assert_called()

    def assert_values(self, values):
        for value, cell in values:
            msg = f"{value} not found in {cell}"
            self.assertEqual(value, self.excel_rows[cell], msg)

    def test_get_trip(self):
        self.check_trip_summary()
        self.check_trip_summary()

    @patch("accountant.brain.main.handlers.save_file", new=MagicMock())
    def test_fuel_expense(self):
        total_distance, litres = self.make_trips(9)
        split = total_distance * 8 / 100 / litres
        content = "date: 2022-03\n"
        content += "tahometer: 1800000\n"
        content += "force:"
        email = base.load_email(fn_obj=1, content=content)
        email["subject"] = "do add fuel expense"
        self.do_job_call(email)
        self.assertTrue(self.response[1])
        fuel_booking = self.memory.get(self.memory.transaction.debit == 7760)
        self.assertEqual(len(fuel_booking), 4)
        for booking in fuel_booking:
            self.assertEqual(booking.credit, 5310)
            self.assertEqual(booking.debit_amount, round(100 * split, 2))
            self.assertEqual(booking.debit_amount, booking.credit_amount)

    def test_fuel_expense_force(self):
        content = ""
        for i, val in enumerate(["date: 2022-01\ntahometer: 0\n", "force:"]):
            content += val
            email = base.load_email(fn_obj=1, content=content)
            email["subject"] = "do add fuel expense"
            self.do_job_call(email, assert_status=False)
            if i == 0:
                self.assertIn("first 5 days of next month", self.response[0])
            else:
                self.assertIn("There are no fuel receipts", self.response[0])

    def make_trip(self, **kargs):
        lit = kargs.get("receipt_litres", "")
        ref = kargs.get("receipt_ref", "")
        val = kargs.get("receipt_value", "")
        if any((lit, ref, val)):
            content = f"""
                date: {kargs["date"]}
                receipt_ref: {ref}
                receipt_litres: {lit}
                receipt_value: {val}
            """
        else:
            content = f"""
                date: {kargs["date"]}
                trip: {kargs["trip"]}
                description: {kargs["description"]}
                distance: {kargs["distance"]}
            """
        email = base.load_email(
            fname="receipt", subtype="pdf", fn_obj=1, content=content
        )
        email["subject"] = "do add trip"
        self.do_job_call(email)

    def make_trips(self, count=6):
        total_distance = total_litres = 0
        keys = ["trip", "description", "distance"]
        for i in range(1, count):
            trip = dict(zip(keys, ["something"] * len(keys)))
            trip["date"] = f"2022-03-0{i}"
            if i % 2 == 0:
                trip["distance"] = "5"
                trip["receipt_litres"] = f"{i * 4}"
                trip["receipt_value"] = 100
                trip["receipt_ref"] = "something"
            else:
                trip["distance"] = f"10{i}"
            self.make_trip(**trip)
            total_distance += int(trip["distance"])
            if "receipt_litres" in trip:
                total_litres += float(trip["receipt_litres"])
        return total_distance, total_litres

    def check_trip_summary(self, date="2022-03"):
        email = base.load_email(content=f"date: {date}")
        email["subject"] = "do trip summary"
        self.do_job_call(email)
        rows = self.get_excel_rows()
        coords = {
            i[j].coordinate: i[j].value for i in rows for j in range(len(i))
        }
        self.assertIn("Business Trip Report", coords["D4"])
        self.assertIn("Date", coords["A3"])
        self.assertIn("Fuel: diesel", coords["A5"])
        self.assertIn("Consumption: 8l/100km", coords["A6"])
        self.assertIn("Total", coords["E9"])
        self.assertIn("SUM", coords["F9"])
        self.assertIn("Date", coords["A10"])
        self.excel_rows = coords


class ManageTransactions(base.AbstractEmailInterfaceTest):
    """Testcase to delete transaction."""

    def setUp(self):
        base.AbstractEmailInterfaceTest.setUp(self)
        self.email = base.load_email()
        self.load_partners()
        self.load_seb_statement()
        self.memory = membank.LoadMemory(self.conf["db_path"])

    def test_delete(self):
        self.email["subject"] = "do remove transaction"
        bookings_delete = self.memory.get("transaction")
        self.assertTrue(len(bookings_delete) > 0)
        for i in bookings_delete:
            self.email.set_content(f"id: {i.id}")
            self.do_job_call(self.email)
        bookings_delete = self.memory.get("transaction")
        self.assertTrue(len(bookings_delete) == 0, bookings_delete)


class OutstandingDeals(base.AbstractEmailInterfaceTest):
    """Testcase to get outstanding deals."""

    def setUp(self):
        base.AbstractEmailInterfaceTest.setUp(self)
        self.email = base.load_email()
        self.email["subject"] = "do get outstanding"
        self.email.set_content("year: 2022")
        self.load_partners()

    def test(self):
        self.load_transactions()
        self.do_job_call(self.email)
        rows = self.get_excel_rows()
        self.assertEqual(36, len(list(rows)))
        header = True
        for i in rows:
            if header:
                header = False
                self.assertEqual(i[0].value, "Date")
                self.assertEqual(i[2].value, "Partner")
                continue
            self.assertEqual(len(i), 12)

    def test_upwork_matching(self):
        self.load_upwork_invoices()
        self.load_upwork_statement()
        self.do_job_call(self.email)
        rows = self.get_excel_rows()
        self.assertEqual(len(list(rows)), 1, get_table(rows))

    def test_seb_matching(self):
        self.load_seb_statement()
        self.do_job_call(self.email)
        rows = self.get_excel_rows()
        self.assertEqual(len(list(rows)), 24, get_table(rows))

    def test_split_expense(self):
        """Both private and business part should be matched."""
        self.do_add_expense({"split": 50, "value": 50})
        self.do_job_call(self.email)
        rows = self.get_excel_rows()
        self.assertEqual(len(list(rows)), 3, get_table(rows))


class Expenses(base.AbstractEmailInterfaceTest):
    """Testcase to get expenses."""

    def setUp(self):
        base.AbstractEmailInterfaceTest.setUp(self)
        self.email = base.load_email()
        self.email["subject"] = "do add expense"
        self.load_partners()
        self.load_seb_statement()

    def test_wrong_expense_account(self):
        content = {"expense_account": 6570}
        self.do_add_expense(content)
        self.assertIn("must start with '7'", self.response[0])

    def test_private_expense(self):
        del self.email["subject"]
        self.email["subject"] = "do private expense"
        val = 83.18
        partner = "Klements un Peteris"
        date = datetime.date(year=2022, month=3, day=24)
        content = f"""date: {date.strftime("%Y-%m-%d")}
            partner: {partner}
            Value: {val}"""
        self.email.set_content(content)
        self.do_job_call(self.email)
        memory = membank.LoadMemory(self.conf["db_path"])
        expense = memory.get(
            memory.transaction.debit == 8900,
            memory.transaction.debit_amount == val,
        )
        self.assertEqual(1, len(expense), list(expense))
        expense = expense[0]
        self.assertEqual(expense.credit, 5310)
        self.assertEqual(expense.date, date)
        self.assertEqual(expense.debit_amount, val)
        self.assertEqual(expense.debit_amount, expense.credit_amount)

    def test(self):
        ref = "T394847585"
        val = 83.18
        comment = "Expense for buying retro"
        date = datetime.date(year=2022, month=3, day=23)
        partner = "Circle K"
        content = {
            "reference": ref,
            "comment": comment,
            "value": val,
            "partner": partner,
            "date": date.isoformat(),
        }
        self.do_add_expense(content)
        memory = membank.LoadMemory(self.conf["db_path"])
        expense = memory.get(memory.transaction.debit == 7120)
        self.assertEqual(1, len(expense))
        expense = expense[0]
        self.assertEqual(val, expense.debit_amount)
        self.assertEqual(expense.debit_amount, expense.credit_amount)
        self.assertEqual(0, expense.credit_stack)
        self.assertEqual(ref, expense.reference)
        self.assertEqual(date, expense.date)
        self.assertEqual(comment, expense.comment)
        self.assertEqual(5310, expense.credit)

    def test_split(self):
        val = 83.18
        split = 33
        ref = "splitted_expense_test"
        comment = "Expense with not 100% business"
        content = {
            "reference": ref,
            "comment": comment,
            "value": val,
            "partner": "Circle K",
            "split": split,
        }
        self.do_add_expense(content)
        memory = membank.LoadMemory(self.conf["db_path"])
        expense = memory.get(memory.transaction.reference == ref)
        self.assertEqual(2, len(expense))
        self.assertIn(8900, [i.debit for i in expense])
        self.assertIn(7120, [i.debit for i in expense])
        self.assertEqual(val, round(sum(i.debit_amount for i in expense), 2))
        for i in expense:
            self.assertEqual(0, i.credit_stack)
            self.assertEqual(i.debit_amount, i.credit_amount)
            if i.debit == 8900:
                self.assertEqual(
                    round(val * (100 - split) / 100, 2), i.debit_amount
                )
            else:
                self.assertEqual(
                    round(val * (split) / 100, 2), i.debit_amount, i
                )
            self.assertEqual(5310, i.credit, i)

    def test_split_100(self):
        val = 89.0
        split = 100
        ref = "splitted_expense_test"
        content = {
            "reference": ref,
            "value": val,
            "partner": "Circle K",
            "split": split,
        }
        self.do_add_expense(content)
        memory = membank.LoadMemory(self.conf["db_path"])
        expense = memory.get(memory.transaction.reference == ref)
        self.assertEqual(1, len(expense))


class Partners(base.AbstractEmailInterfaceTest):
    """Testcase to get partners."""

    def setUp(self):
        base.AbstractEmailInterfaceTest.setUp(self)
        self.email = base.load_email()

    def create_partner(self, name="Funny"):
        self.email["subject"] = "do create partner"
        self.email.set_content(f"name: {name}")
        self.do_job_call(self.email, assert_status=False)

    def test_load_partners(self):
        self.load_partners()
        memory = membank.LoadMemory(self.conf["db_path"])
        partners = memory.get("partner")
        self.assertEqual(len(partners), 17)
        p_ids = {i.id for i in partners}
        self.assertEqual(len(p_ids), 17)

    def test_creation(self):
        self.create_partner()
        memory = membank.LoadMemory(self.conf["db_path"])
        partners = memory.get("partner")
        self.assertEqual(len(partners), 1)

    def test_update(self):
        self.create_partner("Funny K")
        self.email = base.load_email()
        self.email["subject"] = "do update partner"
        self.email.set_content("name: Funny K")
        response = self.do_job_call()
        memory = membank.LoadMemory(self.conf["db_path"])
        partner = memory.get("partner")[0]
        self.assertEqual("Funny K", partner.name)
        content = response[0].split("\n")
        content[0] = "name: FunnyDouble"
        content = "\n".join(content)
        self.email.set_content(content)
        del self.email["subject"]
        self.email["subject"] = "RE: do update partner"
        response = self.do_job_call()
        self.assertIn("Done", response[0])
        updated_partner = memory.get(memory.partner.id == partner.id)[0]
        self.assertEqual(updated_partner.name, "FunnyDouble")

    def test_get_partners(self):
        self.create_partner()
        self.email = base.load_email()
        self.email["subject"] = "do list partners"
        response = self.do_job_call()
        self.assertEqual(response[0], "Done")
        self.assertTrue(response[1])


class GetLedger(base.AbstractEmailInterfaceTest):
    """General ledger report tests."""

    def setUp(self):
        base.AbstractEmailInterfaceTest.setUp(self)
        self.load_transactions()

    def make_ledger_email(self, content=""):
        email = base.load_email(content=content)
        email["subject"] = "do get ledger"
        self.email = email

    def test_ledger(self):
        """Receive attachment as Excel report."""
        self.make_ledger_email()
        self.do_job_call(self.email)
        rows = self.get_excel_rows()
        header = True
        counter = 0
        for i in rows:
            counter += 1
            if header:
                header = False
                self.assertEqual(i[0].value, "Date")
                self.assertEqual(i[2].value, "Partner")
                continue
            self.assertEqual(len(i), 12, [i.value for i in i])
            date = i[0].value
            self.assertTrue(date[:4].isdigit(), date)
            self.assertTrue(i[1].value, "ledger misses reference")
            self.assertEqual(len(i[11].value), 40, "ledger misses id")
        self.assertEqual(counter, 43)

    def test_get_specific_fields(self):
        content = """
            date:
            debit_stack:
            id:
        """
        self.make_ledger_email(content)
        self.do_job_call(self.email)
        rows = self.get_excel_rows()
        for row in rows:
            self.assertEqual(len(row), 3, [i.value for i in row])

    def test_get_specific_month(self):
        content = """
            filter_by_month: 2022-03
            date:
            partner:
            id:
        """
        all_books = self.memory.get("transaction")
        books = self.memory.get(
            self.memory.transaction.date
            >= datetime.date(year=2022, month=3, day=1),
            self.memory.transaction.date
            < datetime.date(year=2022, month=4, day=1),
        )
        self.assertNotEqual(all_books, books)
        self.make_ledger_email(content)
        self.do_job_call(self.email)
        rows = self.get_excel_rows()
        counter = -1  # discount header row
        for row in rows:
            self.assertEqual(len(row), 3, [i.value for i in row])
            counter += 1
        self.assertEqual(len(books), counter)


class ExchangeRateFetch(base.AbstractEmailInterfaceTest):
    """Verifies that exchange rate is always available."""

    def test(self):
        """Check rate available for yesterday."""
        now = datetime.date.today()
        day = datetime.timedelta(days=1)
        with brain.Perform(
            self.conf, self.memory, "do_get_help", {}, b""
        ) as job:
            job.exchange_rate(now - day, "USD")
        with brain.Perform(
            self.conf, self.memory, "do_get_help", {}, b""
        ) as job:
            rate = job.exchange_rate(now, "USD")
        with brain.Perform(
            self.conf, self.memory, "do_get_help", {}, b""
        ) as job:
            rate90 = job.exchange_rate(now - 90 * day, "USD")
        self.assertTrue(rate)
        with brain.Perform(
            self.conf, self.memory, "do_get_help", {}, b""
        ) as job:
            new_rate = job.exchange_rate(now, "USD")
        self.assertEqual(rate, new_rate)
        self.assertNotEqual(rate90, new_rate)

    def test_wrong_input(self):
        """Ask rates in future or too away in past."""
        now = datetime.date.today()
        day = datetime.timedelta(days=1)
        scenarios = ((now + day, "is in future"),)
        for i in scenarios:
            with self.assertRaises(RuntimeWarning) as exc:
                with brain.Perform(
                    self.conf, self.memory, "do_get_help", {}, b""
                ) as job:
                    job.exchange_rate(i[0], "USD")
                self.assertIn(i[1], str(exc))


class SebStatement(base.AbstractEmailInterfaceTest):
    """Check that SEB statement is uploaded."""

    def setUp(self):
        base.AbstractEmailInterfaceTest.setUp(self)
        self.load_partners()

    def test(self):
        """Upload seb statement."""
        self.load_seb_statement()
        memory = membank.LoadMemory(self.conf["db_path"])
        transactions = memory.get("transaction")
        transactions = {i.reference: i for i in transactions}
        tests = [
            ("RO1008215702L01", "Kafijas Draugs", 45.97, 5310),
            ("RO1002210337L01", "apkalpošanas maksa", 2.0, 5310),
        ]
        for test in tests:
            self.assertIn(test[0], transactions)
            expect = transactions[test[0]]
            self.assertIn(test[1], expect.comment, expect)
            self.assertEqual(test[2], expect.debit_amount, expect)
            self.assertEqual(test[2], expect.credit_amount, expect)
            self.assertEqual(test[3], expect.debit, expect)
            self.assertEqual("EUR", expect.debit_currency, expect)
            self.assertEqual("EUR", expect.credit_currency, expect)
            self.assertTrue(expect.partner, expect)


class UpworkInvoices(base.AbstractEmailInterfaceTest):
    """Check that Upwork invoices are uploaded."""

    def setUp(self):
        base.AbstractEmailInterfaceTest.setUp(self)
        self.load_partners()
        self.email = base.load_email(
            fname="test_upwork_invoices", subtype="zip"
        )

    def test(self):
        """Upload zipped PDF invoices."""
        self.email["subject"] = "do upwork invoices"
        memory = self.memory
        self.assertEqual(0, len(memory.get("transaction")))
        response = self.do_job_call()
        self.assertEqual(response[0], "Done")
        items = memory.get("transaction")
        base.remove_temps()
        response = self.do_job_call()
        self.assertEqual(response[0], "Done")
        self.assertEqual(len(items), len(memory.get("transaction")))
        items = {
            i.reference: i for i in items if self.assertTrue(i.partner) is None
        }
        expected = ["T463972580", "T462044954", "T463972580", "T460107076"]
        for i in expected:
            self.assertIn(i, items, items.keys())
        self.assertEqual(items["T462044954"].comment, "Service Fee")
        self.assertEqual(
            items["T463972580"].comment,
            "(27898219) Juris Kaminskis - 24:00 hrs @ $30.00/hr",
        )
        book_test = items["T463972580"]
        partner = memory.get.partner(id=book_test.partner)
        self.assertTrue(partner)
        self.assertEqual(partner.name, "UNIT9")
        self.assertEqual(book_test.debit, 2310)
        self.assertEqual(book_test.credit, 6110)
        self.assertEqual("T463972580", book_test.reference)
        book_test = items["T460107076"]
        partner = memory.get.partner(id=book_test.partner)
        self.assertTrue(partner, book_test.partner)
        self.assertEqual(partner.name, "Upwork")
        self.assertEqual(book_test.debit, 7170)
        self.assertEqual(book_test.credit, 5310)
        self.assertEqual("T460107076", book_test.reference)
        nodes = memory.get(memory.node.transaction == book_test.id)
        self.assertEqual(len(nodes), 2)
        for node in nodes:
            if node.account == 5310:
                self.assertEqual(node.closing, -9.07)
            else:
                self.assertEqual(node.closing, 92.57)


class Accounts(base.AbstractEmailInterfaceTest):
    """Check that accounts are uploaded."""

    # TODO: reimplement accounts update
    @unittest.skip("Reimplement accounts update")
    def test(self):
        """Send request to upload accounts."""
        self.email["subject"] = "do accounts update"
        response = self.do_job_call()
        self.assertEqual(response[0], "Done")
        memory = membank.LoadMemory(self.conf["db_path"])
        account = memory.get.account()
        self.assertEqual(account.id, 1110)
        self.assertEqual(
            account.name, "Pētniecības un uzņēmuma attīstības izmaksas"
        )


class UpworkStatement(base.AbstractEmailInterfaceTest):
    """Check that Upwork statement is uploaded."""

    @patch("accountant.brain.main.handlers.save_file", new=MagicMock())
    def test(self):
        """Basic upload."""
        self.load_partners()
        self.load_upwork_invoices()
        self.load_transactions()
        memory = self.memory
        items = memory.get("transaction")
        items = {i.reference: i for i in items}
        with open(
            "tests/data/test_upwork_statement", encoding="utf-8"
        ) as fname:
            csv_reader = csv.reader(fname, delimiter=",")
            header = True
            for row in csv_reader:
                if header:
                    header = False
                    continue
                self.assertIn(row[1], items)
                self.assertIn("upwork", items[row[1]].source)
                orig_amount = items[row[1]].debit_amount
                amount = items[row[1]].deal_value
                self.assertEqual(abs(orig_amount), orig_amount)
                self.assertEqual(abs(amount), amount)
                if "Service Fee" in items[row[1]].comment:
                    self.assertEqual(items[row[1]].debit, 5310, items[row[1]])
                    self.assertEqual(items[row[1]].credit, 2670, items[row[1]])
                    self.assertEqual(items[row[1]].credit, 2670, items[row[1]])
                    self.assertTrue(items[row[1]].partner, items[row[1]])
                elif "Invoice for" in items[row[1]].comment:
                    self.assertEqual(items[row[1]].debit, 2670, items[row[1]])
                    self.assertEqual(items[row[1]].credit, 2310, items[row[1]])
                    self.assertTrue(items[row[1]].partner, items[row[1]])
                elif "Withdrawal Fee" in items[row[1]].comment:
                    self.assertEqual(items[row[1]].debit, 7170, items[row[1]])
                    self.assertEqual(items[row[1]].credit, 2670, items[row[1]])
                else:
                    self.assertEqual(items[row[1]].debit, 2680, items[row[1]])
                    self.assertEqual(items[row[1]].credit, 2670, items[row[1]])
        self.assert_withdrawal_booking()

    def assert_withdrawal_booking(self):
        memory = self.memory
        upwork_send = memory.get(memory.transaction.debit == 2680)[0]
        seb_receive = memory.get(memory.transaction.credit == 2680)[0]
        exch_loss = upwork_send.deal_value - seb_receive.debit_amount
        exch_book = memory.get(memory.transaction.credit == 8150)
        self.assertEqual(len(exch_book), 1)
        exch_book = exch_book[0]
        self.assertEqual(exch_book.debit_amount, 19.56, exch_book)
        book = memory.get(
            memory.transaction.debit == 7170,
            memory.transaction.credit == 2670,
            memory.transaction.debit_amount == round(exch_loss, 2),
        )
        self.assertEqual(len(book), 1, book)
