"""Functions related to different reports.

Primarily functions on handling Excel reports
"""
import datetime

from .. import handlers, memories


def add_reports(cls):
    """Decorate cls with report functions."""

    class ReportFunctions(cls):
        """Report functions for accountant."""

        def do_get_outstanding(self):
            """Get list of oustanding deals."""
            mem = self.memory
            self.data = self.data[0] if self.data else self.data
            if self.data:
                year = int(self.data.get("year", datetime.date.today().year))
            else:
                year = datetime.date.today().year
            year_start = datetime.date(year=year, month=1, day=1)
            year_end = datetime.date(year=year, month=12, day=31)
            items = []
            filters = (
                (mem.transaction.debit_stack, mem.transaction.debit),
                (mem.transaction.credit_stack, mem.transaction.credit),
            )
            args = [None, None]
            args += [mem.transaction.date >= year_start, mem.transaction.date <= year_end]
            for i in filters:
                # pylint: disable=C0121
                args[0] = i[0] > 0
                for account in [2310, 5310]:
                    args[1] = i[1] == account
                    items += self.memory.get(*args)
            r_struct = memories.ReportStruct("outstanding", items, mem)
            self.attachment = handlers.ExcelGenerator(r_struct).binary()
            self.attachment_filename = "outstanding.xlsx"

    return ReportFunctions
