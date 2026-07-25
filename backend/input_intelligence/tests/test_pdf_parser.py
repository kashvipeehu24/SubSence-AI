"""
Unit tests for PDF statement parser.

Author: SubSense AI Team
"""

import os
import tempfile
import unittest
from reportlab.pdfgen import canvas
from backend.input_intelligence.parsers.pdf_parser import parse_pdf


class TestPDFParser(unittest.TestCase):
    """
    Test suite for checking PDF statement parser.
    """

    def setUp(self) -> None:
        self.statement_lines = [
            "2026-07-15   Netflix India   INR 649.00 Debit   Netflix Monthly",
            "16/07/2026   Starbucks Coffee   250.00 Debit   Coffee Purchase",
            "This is a random line without transactions",
            "17-07-2026   Amazon   USD 100.50 Credit   Shopping Refund"
        ]
        self.temp_pdf_path = self.create_pdf_statement(self.statement_lines)

    def tearDown(self) -> None:
        if os.path.exists(self.temp_pdf_path):
            os.remove(self.temp_pdf_path)

    def create_pdf_statement(self, lines: list[str]) -> str:
        # Create a temporary PDF file using reportlab
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".pdf") as f:
            path = f.name
        c = canvas.Canvas(path)
        y = 750
        for line in lines:
            c.drawString(50, y, line)
            y -= 30
        c.save()
        return path

    def test_parse_valid_pdf_statement(self) -> None:
        txs = parse_pdf(self.temp_pdf_path)
        # Note: 'INR 649.00', '250.00', and 'USD 100.50' are valid amounts
        # Wait, the Credit line has amount 100.50. Let's make sure it is matched.
        self.assertEqual(len(txs), 3)

        self.assertEqual(txs[0].merchant, "Netflix India")
        self.assertEqual(txs[0].amount, 649.00)
        self.assertEqual(txs[0].date, "2026-07-15")

        self.assertEqual(txs[1].merchant, "Starbucks Coffee")
        self.assertEqual(txs[1].amount, 250.00)
        self.assertEqual(txs[1].date, "2026-07-16")

        self.assertEqual(txs[2].merchant, "Amazon")
        self.assertEqual(txs[2].amount, 100.50)
        self.assertEqual(txs[2].date, "2026-07-17")

    def test_parse_invalid_file(self) -> None:
        # Rejects non-existing file paths
        txs = parse_pdf("non_existing_file.pdf")
        self.assertEqual(txs, [])


if __name__ == "__main__":
    unittest.main()
