"""These are direct agent tests.

As some of the agent tests require external network and llm api calls,
they should not be made too large. If more detailed tests are needed,
use mocking to extent possible.
"""

from . import base as bs


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
            "Value: 100\n"
            "Expense account: 7120\n"
            "Currency: USD\n"
            "Split: 100",
            fbytes=b"pdf-09293"
        )
        booking = self.memory.get.transaction(date="2023-10-10")
        self.assertIsNotNone(booking, self.callback.call_args)


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
