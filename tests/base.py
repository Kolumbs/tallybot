"""Common classes and methods for tests."""

import email
import datetime
from dataclasses import dataclass
import logging
import io
import os
import random
import tomllib
from types import MappingProxyType
import unittest
import uuid

import membank
import openpyxl

from tallybot import brain
from zoozl.tests import TestEmailbot


TEMP_STORAGE_PATH = "tests/tmp/"
logging.basicConfig(level=logging.WARNING)

class TestCase(unittest.IsolatedAsyncioTestCase):
    """Base test case."""

    config_file = "tests/config.toml"

    @classmethod
    def setUpClass(cls):
        """Setup testcase with configuration."""
        cls.config = cls.load_configuration(cls.config_file)

    @staticmethod
    def load_configuration(config_file):
        """Load configuration."""
        with open(config_file, "rb") as f:
            c = tomllib.load(f)
            c["extensions"] = ["tallybot.plugin"]
            return MappingProxyType(c)


def unique_name(self=None):
    """Return unique name."""
    name = ""
    if self:
        cls = getattr(self, "__class__", False)
        if cls:
            name = getattr(cls, "__name__", "Unknown")
    if not name:
        name = "Random"
    return name + "_" + str(uuid.uuid1()).split("-", maxsplit=1)[0]


def random_amount():
    """Return random decimal amount."""
    base = random.random()
    return base * 10 ** random.randrange(10)


def correct_dates(fname, output):
    """Correct dates in testdata files.

    testdata files were generated months ago and dates for
    them must be corrected to sooner ones

    fname - testdata file name
    output - file content read by readlines()
    """
    today = datetime.date.today()
    cur_month = datetime.date(year=today.year, month=today.month - 1, day=1)
    cur_month = cur_month.strftime("%b")
    prev_month = datetime.date(year=today.year, month=today.month - 2, day=1)
    prev_month = prev_month.strftime("%b")
    if "test_upwork_statement" == fname:
        for i, line in enumerate(output[1:]):
            if line[1:4] == "Apr":
                line = line[0] + prev_month + line[4:]
            else:
                line = line[0] + cur_month + line[4:]
            output[i + 1] = line
    else:
        print(fname)
    return "".join(output)


def load_email(fname=False, subtype=False, fn_obj=0, content=""):
    """Load test email.

    If fname and subtype present loads a fname as attachment to email
    message.
    """
    path = "tests/data/"
    if (fname or subtype) and (not fname or not subtype):
        raise ValueError("Both fname and subtype must be present")
    test_email = email.message.EmailMessage()
    test_email.set_content(content)
    test_email["from"] = "<requestor@mailinator.com>"
    if fname:
        kwargs = {"subtype": subtype, "filename": f"{fname}.{subtype}"}
        if fn_obj == 1:
            if subtype == "csv":
                output = "0"
            else:
                output = b"0"
                kwargs["maintype"] = "application"
        elif fn_obj:
            if subtype != "csv":
                kwargs["maintype"] = "application"
            output = fn_obj
        else:
            if subtype == "csv":
                with open(path + fname, mode="r", encoding="utf-8") as read:
                    output = read.read()
            else:
                with open(path + fname, mode="rb") as bin_read:
                    output = bin_read.read()
                    kwargs["maintype"] = "application"
        test_email.add_attachment(output, **kwargs)
    return test_email


def remove_temps():
    """Clean temporary test data on local disk."""
    for root, dirs, files in os.walk(TEMP_STORAGE_PATH):
        for fn in files:
            if fn != "test_database.db":
                os.remove(os.path.join(root, fn))


def delete_file(fname):
    """Delete specific file from tests temp directory."""
    for root, dirs, files in os.walk(TEMP_STORAGE_PATH):
        for fn in files:
            if fn == fname:
                os.remove(os.path.join(root, fn))


def create_body(r_keys, content):
    """R_keys of tuple added to dict content if not present."""
    if not content:
        content = {}
    for key, value in r_keys:
        if key not in content:
            content[key] = value
    msg_body = ""
    for key, value in content.items():
        msg_body += f"{key}: {value}\n"
    return msg_body


def construct_memory(conf: dict):
    """Construct memory object from configuration."""
    if "tallybot" not in conf:
        raise ValueError(f"Configuration must contain tallybot: {conf}")
    if "database" not in conf["tallybot"]:
        raise ValueError(f"tallybot config must contain database: {conf['tallybot']}")
    db_path = f'sqlite://{conf["tallybot"]["database"]}'
    return membank.LoadMemory(db_path)


def add_memory(setup):
    """Decorate setUp function to include memory."""

    def wrap(self):
        """Add memory method."""
        setup(self)
        self.memory = construct_memory(self.config)

    return wrap


def add_clean_memory(setup):
    """Decorate setUp function to include clean memory."""

    def wrap(self):
        """Clean memory."""
        setup(self)
        self.memory.clean_all_data()
        self.memory = construct_memory(self.config)

    return wrap


def add_unique_name(setup):
    """Decorate setUp function to include unique_name attribute."""

    def wrap(self):
        """Add unique_name to self."""
        self.unique_name = f"{self.__class__.__name__}:{uuid.uuid4()}"
        setup(self)

    return wrap


class AbstractEmailInterfaceTest(TestCase):
    """Common methods for email interface testcases."""

    @add_clean_memory
    @add_memory
    def setUp(self):
        """Enable email interface."""
        super().setUp()
        self.response = email.message.EmailMessage()
        self.email = load_email()
        self.maxDiff = None
        self.email_bot = TestEmailbot()
        self.email_bot.load(self.config)

    def tearDown(self):
        """Clean up of test data."""
        remove_temps()
        self.email_bot.close()

    def do_add_expense(self, content=False):
        """Create expense email and executes."""
        r_keys = [
            ("date", "2022-03-22"),
            ("reference", "expense"),
            ("value", 20),
            ("partner", "Upwork"),
            ("comment", "generic expense"),
        ]
        msg_body = create_body(r_keys, content)
        msg = load_email(content=msg_body, fname="receipt", subtype="pdf")
        msg["subject"] = "do add expense"
        self.do_job_call(msg, assert_status=False)

    def do_add_carwash(self, content=False):
        """Make carwash call."""
        r_keys = [
            ("date", "2022-03-22"),
            ("reference", "carwash"),
            ("value", 20),
        ]
        msg_body = create_body(r_keys, content)
        msg = load_email(content=msg_body, fname="receipt", subtype="pdf")
        msg["subject"] = "do add carwash"
        self.do_job_call(msg)

    def load_transactions(self):
        """Load transactions into memory."""
        self.load_partners()
        self.load_seb_statement()
        msg = load_email(fname="test_upwork_statement", subtype="csv")
        msg["subject"] = "do upwork statement"
        self.do_job_call(msg)

    def load_seb_statement(self):
        """Load seb statement example."""
        msg = load_email(fname="test_seb_statement", subtype="csv")
        msg["subject"] = "do seb statement"
        self.do_job_call(msg)

    def load_upwork_invoices(self):
        """Load upwork invoices."""
        msg = load_email(fname="test_upwork_invoices", subtype="zip")
        msg["subject"] = "do upwork invoices"
        self.do_job_call(msg)

    def load_upwork_statement(self):
        """Load upwork statement."""
        msg = load_email(fname="test_upwork_statement", subtype="csv")
        msg["subject"] = "do upwork statement"
        self.do_job_call(msg)

    def do_job_call(self, msg: email.message.Message = None, assert_status=True):
        """Perform a job call."""
        if not msg:
            msg = self.email
        self.email_bot.ask(msg)
        self.response = self.email_bot.last_message()
        if assert_status:
            self.assertEqual("Done", self.email_bot.last_text(), self.response)

    def get_excel_rows(self):
        """Return openpyxl excel sheet type."""
        self.assertIsNotNone(self.response[1])
        self.assertIsNotNone(self.response[2])
        excel = get_excel(self.response[1])
        sheet = excel.active
        return sheet


def get_excel(binary):
    """Return openpyxl excel object type."""
    exc_file = io.BytesIO(binary)
    return openpyxl.load_workbook(exc_file)


@dataclass
class BrainInterface:
    """Imaginary interface for the brain do_task return."""

    status: str
    attachment: bytes
    attachment_filename: str


def add_date(payload, fmt=None):
    """Add date to dict.

    If there is a year, month or day parameter, construct date out of
    them. Otherwise take today
    """
    today = datetime.date.today()
    dates = ["year", "month", "day"]
    for key in payload:
        if key in dates:
            date = datetime.date(
                year=payload.pop("year", today.year),
                month=payload.pop("month", today.month),
                day=payload.pop("day", today.day),
            )
            payload["date"] = date.strftime(fmt) if fmt else date.isoformat()
            break
    if "date" not in payload:
        payload["date"] = today.strftime(fmt) if fmt else today.isoformat()


class BrainTestCase(TestCase):
    """Abstract testcase for brain interface."""

    maxDiff = None

    @add_unique_name
    @add_clean_memory
    @add_memory
    def setUp(self):
        """Load required methods for brain do_task calls."""
        self.maxDiff = None  # In comparison assertions return full text

    def do(self, cmd, payload=None, attachment=None):
        """Do brain function."""
        return BrainInterface(
            *brain.do_task(
                self.conf,
                self.memory,
                "do_" + cmd,
                payload,
                attachment,
            )
        )

    def do_add_expense(self, **payload):
        """Add new expense."""
        add_date(payload)
        if "value" not in payload:
            payload["value"] = random_amount()
        if "reference" not in payload:
            payload["reference"] = unique_name(self)
        if "comment" not in payload:
            payload["comment"] = "comment" + unique_name()
        response = self.do("add_expense", [payload], b"")
        self.assertEqual("Done", response.status)

    def do_add_partner(self, name):
        """Add partner with name to ledger."""
        response = self.do("create_partner", [{"name": name}])
        self.assertIn("Done", response.status)

    def do_get_ledger(self):
        """Return ledger sheet."""
        response = self.do("get_ledger")
        self.assertEqual("Done", response.status)
        sheet = get_excel(response.attachment).active
        return sheet

    def do_add_bank_statement_line(self, **payload):
        """Import one specific bank statement line."""
        if "debit" in payload:
            payload["value"] = payload.pop("debit")
            payload["side"] = "D"
        if "credit" in payload:
            payload["value"] = payload.pop("credit")
            payload["side"] = "C"
        if "value" not in payload:
            payload["value"] = random_amount()
        if "side" not in payload:
            payload["side"] = "D"
        if "partner" not in payload:
            raise AssertionError("Partner is required")
        add_date(payload, fmt="%d.%m.%Y")
        line = "heading1\nheading2\n"
        line += f";{payload['date']};;{payload['value']};{payload['partner']}"
        line += f";;;;;;;;;;{payload['side']}\n"
        delete_file(f"csv.seb_{datetime.date.today().isoformat()}")
        response = self.do("seb_statement", attachment=line)
        self.assertEqual("Done", response.status)

    def do_transaction(self, **payload):
        """Do direct ledger transaction."""
        add_date(payload)
        if "amount" in payload:
            payload["debit_amount"] = payload.pop("amount")
        if "reference" not in payload:
            payload["reference"] = unique_name(self)
        if "source" not in payload:
            payload["source"] = "/path/to/source/file"
        if "comment" not in payload:
            payload["comment"] = "Comment of the goods"
        if "debit_amount" not in payload:
            payload["debit_amount"] = random_amount()
        response = self.do("transaction", [payload])
        self.assertTrue("Done", response.status)
        return response
