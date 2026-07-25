"""
Unit tests for SMS alert parser.

Author: SubSense AI Team
"""

import unittest
from backend.input_intelligence.parsers.sms_parser import parse_sms


class TestSMSParser(unittest.TestCase):
    """
    Test suite for checking SMS notification parser helper.
    """

    def test_parse_valid_sms(self) -> None:
        sms_logs = (
            "Dear Customer, your a/c was debited by INR 649.00 on 15-07-2026 at Netflix India.\n"
            "Sent Rs. 250 to Starbucks on 16/07/2026.\n"
            "Your card spent USD 100.50 at Amazon on 17 July 2026."
        )
        txs = parse_sms(sms_logs)
        self.assertEqual(len(txs), 3)

        self.assertEqual(txs[0].merchant, "Netflix India")
        self.assertEqual(txs[0].amount, 649.00)
        self.assertEqual(txs[0].date, "2026-07-15")

        self.assertEqual(txs[1].merchant, "Starbucks")
        self.assertEqual(txs[1].amount, 250.00)
        self.assertEqual(txs[1].date, "2026-07-16")

        self.assertEqual(txs[2].merchant, "Amazon")
        self.assertEqual(txs[2].amount, 100.50)
        self.assertEqual(txs[2].date, "2026-07-17")

    def test_parse_invalid_sms(self) -> None:
        # Non-transactional alerts should be skipped
        sms_logs = (
            "Hello, your OTP for Netflix registration is 123456.\n"
            "Your order is out for delivery today."
        )
        txs = parse_sms(sms_logs)
        self.assertEqual(len(txs), 0)


if __name__ == "__main__":
    unittest.main()
