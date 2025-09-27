"""Holds all memory data structures used by accountant."""

import dataclasses as data
from dataclasses import dataclass
import datetime
import hashlib
import uuid

import membank


DEFAULT_CAR_PLATE = "XX0000"
DEFAULT_CAR_ODO_KM = 0
PARTNER_ACCOUNTS = (
    2310,
    5310,
)  # Accounts that are observed for partner matching


@dataclass
class Conversation:
    """Accountant conversations with people who request actions."""

    talker: str = data.field(default=None, metadata={"key": True})
    ongoing: bool = False
    subject: str = ""
    data: dict = data.field(default_factory=dict)
    attachment: bytes = b""


@dataclass
class ChatSubjectLookup:
    """Accountant subject lookup from chat messages."""

    cmd: str
    sentence: str


class Booking:
    """Automates accounting transactions.

    Decides debit and credit accounts Reassigns correctly closing
    balances also on impacted transactions already stored.
    """

    def __init__(self, text, memory, **kargs):
        """Text value decides what booking will it be."""
        self.memory = memory
        self.comp = self.memory.transaction
        self.load_records()
        text = text.lower()
        splitter = text.find(":")
        set_acc = False
        if splitter != -1:
            text, set_acc = text[0:splitter], int(text[splitter + 1 :])
        if text not in self.records:
            raise RuntimeError(f"No such record '{text}'")
        if set_acc:
            acc_pair = self.records[text]
            if text == "expense":
                acc_pair.insert(0, set_acc)
        kargs["debit"] = self.records[text][0]
        kargs["credit"] = self.records[text][1]
        self.transaction = Transaction(**kargs)
        self.matched_deals = []

    def load_records(self):
        """Add records how to make bookings."""
        self.records = {
            "vat": (5310, 2670),
            "inc_invoice": (7170, 5310),
            "service fee": (5310, 2670),
            "out_invoice": (2310, 6110),
            "hourly": (2670, 2310),
            "fixed price": (2670, 2310),
            "withdrawal fee": (7170, 2670),
            "withdrawal": (2680, 2670),
            "seb-commission": (7640, 5310),
            "upwork-commission": (7170, 2670),
            "seb-expense": (5310, 2620),
            "seb-income": (2620, 2310),
            "seb-upwork-income": (2620, 2680),
            "private-income": (2310, 8900),
            "private-expense": (8900, 5310),
            "fx-profit": (2670, 8150),
            "fx-loss": (8250, 2670),
            "expense": [5310],
            "init-asset": (1230, 3110),
            "asset-depreciate": (7420, 1290),
        }

    def correct_balances(self, node):
        """Apply closing balance recalculations."""
        if not node.right:
            return
        next_node = self.memory.get.node(transaction=node.right)
        next_node.closing = round(node.closing + next_node.value, 2)
        self.memory.put(next_node)
        self.correct_balances(next_node)

    def match_deals(self):
        """Check if other leg of deal is present, if so matches those."""
        to_check = self.transaction
        partner_match = [2310, 5310]
        last_year = datetime.date(year=to_check.date.year - 1, month=12, day=31)
        next_year = datetime.date(year=to_check.date.year + 1, month=1, day=1)
        args = [
            self.comp.partner == to_check.partner,
            self.comp.date > last_year,
            self.comp.date < next_year,
        ]
        if to_check.credit in partner_match:
            args.append(self.comp.debit == to_check.credit)
            args.append(self.comp.debit_currency == to_check.credit_currency)
            args.append(self.comp.debit_stack > 0)
            orphan_deals = self.memory.get(*args)
            self.make_match(orphan_deals, side="debit")
        elif to_check.debit in partner_match:
            args.append(self.comp.credit == to_check.debit)
            args.append(self.comp.credit_currency == to_check.debit_currency)
            args.append(self.comp.credit_stack > 0)
            orphan_deals = self.memory.get(*args)
            self.make_match(orphan_deals, side="credit")

    def make_match(self, orphan_deals, side="debit"):
        """Do a match for a to_check transaction."""
        check = self.transaction
        orphan_deals.sort(key=lambda x: x.date)
        matched_deals = []
        for deal in orphan_deals:
            if side == "debit":
                deal_stack = "debit_stack"
                check_stack = "credit_stack"
            else:
                deal_stack = "credit_stack"
                check_stack = "debit_stack"
            deal_side = getattr(deal, deal_stack)
            check_side = getattr(check, check_stack)
            if deal_side >= check_side:
                setattr(deal, deal_stack, round(deal_side - check_side, 2))
                setattr(check, check_stack, 0)
                self.memory.put(deal)
                matched_deals.append(deal)
                break
            setattr(check, check_stack, round(check_side - deal_side, 2))
            setattr(deal, deal_stack, 0)
            self.memory.put(deal)
            matched_deals.append(deal)
        self.matched_deals = matched_deals

    def convert_currency(self):
        """Handle Upwork currency exchange."""
        item = self.transaction
        mem = self.memory
        if item.debit_currency != item.credit_currency:
            invoices_not_paid = mem.get(
                mem.transaction.credit == 6110,
                mem.transaction.credit_currency == "USD",
                mem.transaction.credit_stack > 0,
            )
            self.make_match(invoices_not_paid, side="credit")
            t_eur = [
                (i.credit_amount - i.credit_stack) / i.rate
                for i in self.matched_deals
            ]
            fx_margin = sum(t_eur) - item.deal_value
            fx_trans = {"date": item.date}
            fx_trans["source"] = item.source
            fx_booking = dict(fx_trans)
            fx_booking["reference"] = item.date.isoformat() + "fx_margin"
            fx_booking["comment"] = item.comment
            fx_booking["debit_amount"] = round(abs(fx_margin), 2)
            if fx_margin > 0:
                fx_type = "fx-profit"
            else:
                fx_type = "fx-loss"
            fx_booking = Booking(fx_type, mem, **fx_booking)
            fx_booking.save()
            fx_commission = dict(fx_trans)
            fx_commission["debit_amount"] = round(
                item.deal_value - item.credit_amount, 2
            )
            fx_commission["reference"] = item.reference + "fx_commission"
            fx_commission["comment"] = "upwork fx commission"
            fx_commission = Booking("upwork-commission", mem, **fx_commission)
            fx_commission.save()

    def save(self):
        """Save transaction into memory."""
        to_save = self.transaction
        booking = self.memory.get(
            "transaction",
            date=to_save.date,
            reference=to_save.reference,
            debit_amount=to_save.debit_amount,
            debit=to_save.debit,
            credit=to_save.credit,
        )
        if not booking:
            self.convert_currency()
            self.match_deals()
            comp = self.memory.transaction
            sides = (
                (
                    comp.debit == to_save.debit,
                    to_save.debit,
                    to_save.debit_amount,
                ),
                (
                    comp.credit == to_save.credit,
                    to_save.credit,
                    -to_save.debit_amount,
                ),
            )
            for side in sides:
                node = Node(
                    transaction=to_save.id,
                    account=side[1],
                    value=side[2],
                    closing=side[2],
                )
                prev_booking = self.memory.get(
                    comp.date <= to_save.date, side[0]
                )
                prev_booking = sorted(prev_booking, key=lambda x: x.date)
                if prev_booking:
                    prev_node = self.memory.get.node(
                        transaction=prev_booking[0].id
                    )
                    node.closing += prev_node.closing
                    node.left = prev_node.transaction
                    if prev_node.right and prev_node.rigth != node.transaction:
                        node.right = prev_node.right
                        self.correct_balances(node)
                        prev_node.right = node.transaction
                        self.memory.put(prev_node)
                self.memory.put(node)
            self.memory.put(to_save)


@dataclass
class Trip:
    """Trips."""

    date: datetime.date
    trip: str
    description: str
    distance: int
    year: int = 0
    month: int = 0
    day: int = 0
    receipt_ref: str = ""
    receipt_litres: float = 0
    receipt_value: float = 0

    def __post_init__(self):
        """Add year, month, day to index."""
        if isinstance(self.distance, str):
            self.distance = int(self.distance)
        if isinstance(self.date, str):
            self.date = datetime.datetime.strptime(self.date, "%Y-%m-%d")
        if isinstance(self.receipt_litres, str):
            self.receipt_litres = float(self.receipt_litres)
        if isinstance(self.receipt_value, str):
            self.receipt_value = float(self.receipt_value)
        self.year = self.date.year
        self.month = self.date.month
        self.day = self.date.day


@dataclass
class Car:
    """Car information."""

    id: str = data.field(default=DEFAULT_CAR_PLATE, metadata={"key": True})
    total_km: int = DEFAULT_CAR_ODO_KM


@dataclass
class PartnerIndex:
    """Names matching patners."""

    text: str
    partner_id: str


@dataclass
class MySelf:
    """Meta storage for the user of accountant."""

    key: str = data.field(metadata={"key": True})
    text: str = ""
    value: float = 0
    dct: dict = data.field(default_factory=dict)
    lst: list = data.field(default_factory=list)
    blob: bytes = b""


@dataclass
class Me:
    """My data."""

    name: str = ""
    address_id: str = ""
    phone: str = ""
    email: str = ""
    bank_name: str = ""
    bank_account: str = ""
    bank_code: str = ""
    rate: float = 0.0
    currency: str = ""


@dataclass
class Partner:
    """Client or Supplier info."""

    name: str
    reg_no: str = ""
    address_id: str = ""
    bank_account: str = ""
    bank_name: str = ""
    invoice_prefix: str = ""
    invoice_row_format: str = ""
    terms: str = ""
    currency: str = ""
    id: str = data.field(default=None, metadata={"key": True})

    def __post_init__(self):
        """Add unique id to partner."""
        if not self.id:
            self.id = str(uuid.uuid1())


@dataclass
class Address:
    """Physical address."""

    address_lines: list = data.field(default_factory=list)
    city: str = ""
    country: str = ""
    postal_code: str = ""
    id: str = data.field(default=None, metadata={"key": True})

    def __post_init__(self):
        """Add unique id if not given."""
        if not self.id:
            self.id = str(uuid.uuid1())


@dataclass
class Node:
    """Node that keeps balances on accounts."""

    transaction: str
    account: int
    value: float
    closing: float
    left: str = ""
    right: str = ""


@dataclass
class Account:
    """Accounts used in General Ledger."""

    id: int
    name: str


@dataclass
class Currency:
    """Currencies and their rates with EUR."""

    date: datetime.date
    currency: str
    rate: float


@dataclass
class Sequences:
    """Generic sequences."""

    relation: str = data.field(metadata={"key": True})
    sequence: int


@dataclass
class TransactionAttachment:
    """Attachments to transactions in GL."""

    transaction_id: str = data.field(metadata={"key": True})
    file_name: str
    file_type: str
    blob: bytes


@dataclass
class Transaction:
    """Transactions in General Ledger."""

    date: datetime.date
    reference: str
    source: str
    comment: str
    debit_amount: float
    credit_amount: float = 0
    partner: str = ""
    debit: int = 0
    credit: int = 0
    deal_value: float = 0
    rate: float = 1
    debit_currency: str = "EUR"
    credit_currency: str = "EUR"
    debit_stack: float = -1
    credit_stack: float = -1
    id: str = data.field(default=None, metadata={"key": True})

    def __post_init__(self):
        """Add unique id to transaction."""
        if not self.id:
            new_id = hashlib.sha1()
            byte_string = self.date.strftime("%Y%m%d").encode()
            byte_string += self.reference.encode()
            byte_string += str(self.debit_amount).encode()
            byte_string += str(self.debit_currency).encode()
            byte_string += str(self.credit_currency).encode()
            byte_string += str(self.debit).encode()
            byte_string += str(self.credit).encode()
            new_id.update(byte_string)
            self.id = new_id.hexdigest()
        if not self.deal_value:
            self.deal_value = round(self.debit_amount / self.rate, 2)
        if not self.credit_amount:
            self.credit_amount = self.debit_amount
        if self.debit_stack == -1:
            self.debit_stack = self.debit_amount
        if self.credit_stack == -1:
            self.credit_stack = self.credit_amount


report_table = {
    "ledger": [
        "date",
        "reference",
        "partner",
        "comment",
        "debit",
        "debit_currency",
        "debit_amount",
        "credit",
        "credit_currency",
        "credit_amount",
        "deal_value",
        "id",
    ],
    "outstanding": [
        "date",
        "reference",
        "partner",
        "debit",
        "debit_currency",
        "debit_amount",
        "debit_stack",
        "credit",
        "credit_currency",
        "credit_amount",
        "credit_stack",
        "deal_value",
    ],
    "partners": [
        "name",
        "reg_no",
        "address_id",
        "bank_account",
        "bank_name",
        "id",
    ],
    "partnerindex": [
        "text",
        "partner_id",
    ],
    "tripsummary": [
        "date",
        "receipt_ref",
        "receipt_litres",
        "trip",
        "description",
        "distance",
    ],
    "": [
        "",
    ],
}


@dataclass
class ReportStruct:
    """Report structure that supports Excel generation."""

    title: str
    items: list
    memory: data.InitVar[membank.LoadMemory]
    report_args: dict = data.field(default_factory=dict)
    callbacks: dict = data.field(default_factory=dict)
    attrs: list = data.field(default_factory=list)
    start: int = 1
    header: list = data.field(default_factory=list)

    def __post_init__(self, memory):
        """Initialise attributes according to title."""
        if self.title not in report_table:
            raise RuntimeError(f"Report '{self.title}' is not supported")
        if not self.attrs:
            self.attrs = report_table[self.title]
        if self.title in ["ledger", "outstanding"]:
            self.callbacks = {
                "date": lambda x: x.strftime("%Y-%m-%d"),
                "partner": lambda x: memory.get.partner(id=x).name if x else "",
            }
        if self.title == "tripsummary":
            self.callbacks = {
                "receipt_litres": lambda x: x if x else "",
                "date": lambda x: x.strftime("%Y-%m-%d"),
            }
            self.start = 10
            end = len(self.items)
            today = datetime.date.today().strftime("%Y-%m-%d")
            self.header = [
                ("D4", "Business Trip Report: {DEFAULT_CAR_PLATE}"),
                ("A3", f"Date: {today}"),
                ("A5", "Fuel: diesel"),
                ("A6", "Consumption: 8l/100km"),
                ("E9", "Total:"),
                ("F9", f"=SUM(F{self.start + 1}:F{self.start + 1 + end})"),
            ]
            if self.report_args and "tahometer" in self.report_args:
                self.header.append(
                    ("A7", f"Tahometer: {self.report_args['tahometer']}")
                )


@dataclass
class TripMetrics:
    """Metrics to perform expense calculation."""

    distance: int = 0
    litres: float = 0
