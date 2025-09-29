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
        await self.ask("Book an invoice for 110 USD")
        await self.ask(
                "Invoice date: 2023-10-10\n"
                "Reference: INV-1001\n"
                "Comment: Office supplies\n"
                "Partner: OfficeMart\n"
                "Value: 100\n"
                "Expense account: 6120\n"
                "Currency: USD\n"
                "Split: 100"
        )
        self.callback.assert_called_with("Zub")
