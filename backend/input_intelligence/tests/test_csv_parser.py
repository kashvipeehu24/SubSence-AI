"""
Unit tests for CSV statement parser.

Author: SubSense AI Team
"""

import json
import os
import tempfile
import unittest
from backend.input_intelligence.parsers.csv_parser import parse_csv


class TestCSVParser(unittest.TestCase):
    """
    Test suite for checking CSV Statement Parsing helper.
    """

    def setUp(self) -> None:
        self.csv_headers = "transaction_id,merchant,amount,date,category,description,tags\n"
        self.csv_row1 = "TXN001,Netflix India,649.00,2026-07-15,Video Streaming,Netflix Monthly,subscription,streaming\n"
        self.csv_row2 = ",Spotify Premium,119.00,16/07/2026,Music Streaming,Spotify monthly,subscription\n"

    def test_parse_valid_csv(self) -> None:
        # Create temp file
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write(self.csv_headers + self.csv_row1 + self.csv_row2)
            temp_path = f.name

        try:
            txs = parse_csv(temp_path)
            self.assertEqual(len(txs), 2)
            self.assertEqual(txs[0].transaction_id, "TXN001")
            self.assertEqual(txs[0].merchant, "Netflix India")
            self.assertEqual(txs[0].amount, 649.00)
            self.assertEqual(txs[0].date, "2026-07-15")

            self.assertEqual(txs[1].transaction_id, "DRAFT")
            self.assertEqual(txs[1].merchant, "Spotify Premium")
            self.assertEqual(txs[1].amount, 119.00)
            self.assertEqual(txs[1].date, "2026-07-16")
        finally:
            os.remove(temp_path)

    def test_parse_blank_or_invalid_rows(self) -> None:
        # Check blank rows or bad dates/amounts are skipped
        bad_rows = (
            "\n"  # blank line
            ",Netflix India,,2026-07-15,,,\n"  # missing amount
            "TXN003,Amazon,500.0,not-a-date,,,\n"  # bad date
            "TXN004,Amazon,bad-amt,2026-07-15,,,\n"  # bad amount
            "TXN005,Amazon,-10.0,2026-07-15,,,\n"  # negative amount
        )
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write(self.csv_headers + bad_rows)
            temp_path = f.name

        try:
            txs = parse_csv(temp_path)
            self.assertEqual(len(txs), 0)
        finally:
            os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
