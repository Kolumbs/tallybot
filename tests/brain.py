"""Tests for brain interface."""
import datetime
import unittest

from tallybot.brain import ledger


class GetIntervalDates(unittest.TestCase):
    """Tests on get_interval_dates function."""

    def setUp(self):
        """Add today."""
        self.today = datetime.date.today()

    def test_quarter(self):
        """Call with filter_by_quarter should return quarter for current year."""
        data = {"filter_by_quarter": "q4"}
        start, end = ledger.get_interval_dates(data)
        must_start = datetime.date(year=self.today.year, month=10, day=1)
        must_end = datetime.date(year=self.today.year + 1, month=1, day=1)
        self.assertEqual(must_start, start)
        self.assertEqual(must_end, end)

    def test_last(self):
        """Calling last will give last full quarter."""
        data = {"filter_by_quarter": "last"}
        start, end = ledger.get_interval_dates(data)
        if self.today.month < 4:
            must_start = datetime.date(year=self.today.year - 1, month=10, day=1)
            must_end = datetime.date(year=self.today.year, month=1, day=1)
        elif self.today.month < 7:
            must_start = datetime.date(year=self.today.year, month=1, day=1)
            must_end = datetime.date(year=self.today.year, month=4, day=1)
        elif self.today.month < 10:
            must_start = datetime.date(year=self.today.year, month=4, day=1)
            must_end = datetime.date(year=self.today.year, month=7, day=1)
        else:
            must_start = datetime.date(year=self.today.year, month=7, day=1)
            must_end = datetime.date(year=self.today.year, month=10, day=1)
        self.assertEqual(must_start, start)
        self.assertEqual(must_end, end)

    def test_january(self):
        """Choose just one month."""
        data = {"filter_by_month": "2022-01"}
        start, end = ledger.get_interval_dates(data)
        must_start = datetime.date(year=2022, month=1, day=1)
        must_end = datetime.date(year=2022, month=2, day=1)
        self.assertEqual(must_start, start)
        self.assertEqual(must_end, end)

    def test_december(self):
        """Choose just one month."""
        data = {"filter_by_month": "2022-12"}
        start, end = ledger.get_interval_dates(data)
        must_start = datetime.date(year=2022, month=12, day=1)
        must_end = datetime.date(year=2023, month=1, day=1)
        self.assertEqual(must_start, start)
        self.assertEqual(must_end, end)
