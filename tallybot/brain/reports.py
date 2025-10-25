"""Functions related to different reports.

Primarily functions on handling Excel reports
"""

import datetime

from .. import handlers, memories


def get_report_struct(data, mem):
    """Get report structure from data."""
    if data:
        year = int(data.get("year", datetime.date.today().year))
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
    args += [
        mem.transaction.date >= year_start,
        mem.transaction.date <= year_end,
    ]
    for i in filters:
        # pylint: disable=C0121
        args[0] = i[0] > 0
        for account in [2310, 5310]:
            args[1] = i[1] == account
            items += mem.get(*args)
    return memories.ReportStruct("outstanding", items, mem)


def add_reports(cls):
    """Decorate cls with report functions."""

    class ReportFunctions(cls):
        """Report functions for accountant."""

        def do_get_outstanding(self):
            """Get list of oustanding deals."""
            self.data = self.data[0] if self.data else self.data
            r_struct = get_report_struct(self.data, self.memory)
            self.attachment = handlers.ExcelGenerator(r_struct).binary()
            self.attachment_filename = "outstanding.xlsx"

        def do_get_outstanding_items(self):
            """Get list of outstanding items in text format."""
            self.data = self.data[0] if self.data else self.data
            r_struct = get_report_struct(self.data, self.memory)
            self.status = handlers.get_csv_text(r_struct)

    return ReportFunctions
