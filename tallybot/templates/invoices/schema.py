"""Invoice generator schema."""
from dataclasses import dataclass, field


@dataclass
class InvoiceRow:
    """One invoice row."""

    description: str
    hours: str  # must convert to number
    total: str = field(init=False)


@dataclass
class BankInfo:
    """Bank account information."""

    name: str
    iban: str
    bic: str


@dataclass
class InvoiceData:
    """Invoice creation data container."""

    no: str
    biller: list[str]
    biller_bank: BankInfo
    payer: list[str]
    rows: list[tuple[str, str]]
    terms: int
    rate: str  # must convert to number
    currency: str
