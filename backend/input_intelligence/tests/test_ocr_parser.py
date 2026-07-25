"""
Unit Tests for Advanced OCR Parser and MIME Signature Detection.

Author: SubSense AI Team
"""

import os
import unittest
import tempfile
from PIL import Image
from backend.input_intelligence.utils import detect_mime_type
from backend.input_intelligence.processors.ocr_preprocessor import preprocess_image
from backend.input_intelligence.parsers.ocr_parser import parse_ocr
import backend.input_intelligence.parsers.ocr_parser as ocr_parser


class TestOCRAndMIMEDetection(unittest.TestCase):
    """Test suite validating file signature type mapping, PIL filters, and OCR transaction extraction."""

    def setUp(self) -> None:
        # Reset mock OCR results before each test
        ocr_parser._mock_ocr_result = None

    def tearDown(self) -> None:
        # Clean up any injected mocks
        ocr_parser._mock_ocr_result = None

    def test_detect_mime_type(self) -> None:
        # Verify file signature mapping on actual written mock byte strings
        test_cases = [
            (b"%PDF-1.4\n%...", ".pdf", "pdf"),
            (b"\x89PNG\r\n\x1a\n...", ".png", "png"),
            (b"\xff\xd8\xff\xe0...", ".jpg", "jpeg"),
            (b"RIFF\x00\x00\x00\x00WEBPvp8...", ".webp", "webp"),
            (b"PK\x03\x04...", ".xlsx", "xlsx"),
            (b"PK\x03\x04...", ".zip", "zip"),
            (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1...", ".xls", "xls"),
            (b"  { \n  \"transactions\": [] }", ".json", "json"),
            (b"date,merchant,amount\n2026-07-15,Netflix,649.00", ".csv", "csv"),
            (b"Simple plain text logs here.", ".txt", "txt")
        ]

        for data, suffix, expected in test_cases:
            with tempfile.NamedTemporaryFile("wb", delete=False, suffix=suffix) as f:
                f.write(data)
                path = f.name
            try:
                detected = detect_mime_type(path)
                self.assertEqual(detected, expected, f"Failed signature check for suffix {suffix}")
            finally:
                os.remove(path)

    def test_ocr_image_preprocessor(self) -> None:
        # Verify Pillow filter processing on dummy pixel map
        img = Image.new("L", (100, 100), color=200)
        enhanced = preprocess_image(img)
        self.assertIsInstance(enhanced, Image.Image)
        self.assertEqual(enhanced.mode, "L")

    def test_parse_ocr_single_transaction_screenshot(self) -> None:
        # Mock PhonePe successful transaction log screenshot
        ocr_parser._mock_ocr_result = (
            "PhonePe\n"
            "Paid to\n"
            "Netflix India\n"
            "₹649.00\n"
            "Successful\n"
            "2026-07-15\n"
            "Txn ID: T260715123456"
        )
        img = Image.new("RGB", (50, 50), color="white")
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".png") as f:
            img.save(f, format="PNG")
            path = f.name

        try:
            txs = parse_ocr(path, "png")
            self.assertEqual(len(txs), 1)
            self.assertEqual(txs[0].merchant, "Netflix India")
            self.assertEqual(txs[0].amount, 649.00)
            self.assertEqual(txs[0].date, "2026-07-15")
            self.assertEqual(txs[0].transaction_type, "Debit")
        finally:
            os.remove(path)

    def test_parse_ocr_multi_transaction_statement(self) -> None:
        # Mock printed bank statement with three items (two debits and a refund credit)
        ocr_parser._mock_ocr_result = (
            "STATEMENT OF ACCOUNT\n"
            "Date         Description               Amount    Type\n"
            "2026-07-15   Netflix India             649.00    Debit\n"
            "16/07/2026   Starbucks Coffee          250.00    Debit\n"
            "17-07-2026   Amazon Refund             100.50    Credit\n"
        )
        img = Image.new("RGB", (50, 50), color="white")
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".png") as f:
            img.save(f, format="PNG")
            path = f.name

        try:
            txs = parse_ocr(path, "png")
            self.assertEqual(len(txs), 3)

            self.assertEqual(txs[0].merchant, "Netflix India")
            self.assertEqual(txs[0].amount, 649.00)
            self.assertEqual(txs[0].date, "2026-07-15")
            self.assertEqual(txs[0].transaction_type, "Debit")

            self.assertEqual(txs[1].merchant, "Starbucks Coffee")
            self.assertEqual(txs[1].amount, 250.00)
            self.assertEqual(txs[1].date, "2026-07-16")
            self.assertEqual(txs[1].transaction_type, "Debit")

            self.assertEqual(txs[2].merchant, "Amazon Refund")
            self.assertEqual(txs[2].amount, 100.50)
            self.assertEqual(txs[2].date, "2026-07-17")
            self.assertEqual(txs[2].transaction_type, "Credit")
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
