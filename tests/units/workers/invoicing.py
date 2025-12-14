"""Invoicing agent unittests."""

import json
from tallybot.workers import invoicing

from tests.units.workers import TestCase


class StatementImport(TestCase):
    """Test bank statement import agent."""

    async def run_statement_tool(self, attachments=None):
        """Run bank statement import tool."""
        if attachments is None:
            attachments = tuple()
        return await self.run_function_tool(
            invoicing.do_seb_statement_import,
            self.create_package(attachments=attachments),
            "",
        )

    async def test_no_attachment(self):
        """Test bank statement without attachment."""
        result = await self.run_statement_tool()
        self.assertIn("No attachment found", result)

    async def test(self):
        """Test bank statement import."""
        result = await self.run_statement_tool(
            attachments=((b"pdf;09293", "statement.csv", "text/csv"),)
        )
        self.assertIn("Done", result)


class InvoiceBooking(TestCase):
    """Test invoice booking tool."""

    async def run_invoice_tool(self, attachments=None, invoice_data=None):
        """Run invoice booking tool."""
        if attachments is None:
            attachments = tuple()
        if invoice_data is None:
            text = "{}"
        else:
            text = json.dumps({"invoice_data": invoice_data})
        return await self.run_function_tool(
            invoicing.do_book_invoice,
            self.create_package(attachments=attachments),
            text,
        )

    async def test(self):
        """Book single invoice."""
        result = await self.run_invoice_tool(
            attachments=((b"pdf;09293", "invoice.pdf", "application/pdf"),),
            invoice_data={
                "date": "2023-10-10",
                "reference": "INV-1001",
                "comment": "Office supplies",
                "partner": "OfficeMart",
                "value": 110,
                "currency": "USD",
                "split": 100,
            },
        )
        self.assertIn("Partner", result)
