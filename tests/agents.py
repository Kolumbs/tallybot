"""These are direct agent tests.

As some of the agent tests require external network and llm api calls,
they should not be made too large. If more detailed tests are needed,
use mocking to extent possible.
"""

from . import base as bs
from .data.pdfbinaries import BLANK_PAGE_PDF, HELLO_PDF


class DoInvoice(bs.AgentTestCase):
    """Test conversation to book an invoice."""

    async def test(self):
        """Verify booking correctly an invoice."""
        booking = self.memory.get.transaction(date="2023-10-10")
        self.assertIsNone(
            booking, "Precondition failed, booking already exists."
        )
        await self.ask(
            "Book an invoice for 110 USD and create partner, if needed.",
        )
        await self.ask(
            "Invoice date: 2023-10-10\n"
            "Reference: INV-1001\n"
            "Comment: Office supplies\n"
            "Partner: OfficeMart\n"
            "Value: 110\n"
            "Expense account: 7120\n"
            "Currency: USD\n"
            "Split: 100",
            fbytes=BLANK_PAGE_PDF,
        )
        booking = self.memory.get.transaction(date="2023-10-10")
        self.assertIsNotNone(booking, self.callback.call_args)


class FileRead(bs.AgentTestCase):
    """Test conversation to read a file."""

    async def test_plain(self):
        """Verify reading correctly a file."""
        await self.ask(
            "Read the attached file and summarize its content.",
            fbytes=b"This is a sample text file for testing.",
            fname="rubikon.txt",
            ftype="text/plain",
        )
        self.assertIn("test", self.get_agent_response().lower())

    async def test_pdf(self):
        """Verify reading correctly a PDF file."""
        await self.ask(
            "Read the attached file and summarize its content.",
            fbytes=HELLO_PDF,
            fname="rubikon.pdf",
            ftype="application/pdf",
        )
        self.assertIn("mars", self.get_agent_response().lower())


class DoStatement(bs.AgentTestCase):
    """Test conversation to process a bank statement."""

    async def test(self):
        """Verify processing correctly a bank statement."""
        booking = self.memory.get.transaction(date="2023-10-11")
        self.assertIsNone(
            booking, "Precondition failed, booking already exists."
        )
        await self.ask(
            "Process the attached bank statement and book the transactions.",
            fbytes=b"pdf;09293",
            fname="",
            ftype="text/csv",
        )
