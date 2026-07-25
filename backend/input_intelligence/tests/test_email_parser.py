"""
Unit tests for Email text alert parser.

Author: SubSense AI Team
"""

import unittest
from backend.input_intelligence.parsers.email_parser import parse_email


class TestEmailParser(unittest.TestCase):
    """
    Test suite for checking email notification parser helper.
    """

    def test_parse_valid_emails(self) -> None:
        email_body = (
            "Hi User,\n\n"
            "This is to confirm your payment of INR 649.00 was successful at Netflix India on 2026-07-15.\n\n"
            "Thanks for choosing Netflix.\n\n"
            "-------------------\n\n"
            "Alert: Your credit card was charged Rs. 250.00 at Starbucks Coffee on 16-07-2026."
        )
        txs = parse_email(email_body)
        self.assertEqual(len(txs), 2)

        self.assertEqual(txs[0].merchant, "Netflix India")
        self.assertEqual(txs[0].amount, 649.00)
        self.assertEqual(txs[0].date, "2026-07-15")

        self.assertEqual(txs[1].merchant, "Starbucks Coffee")
        self.assertEqual(txs[1].amount, 250.0)
        self.assertEqual(txs[1].date, "2026-07-16")


if __name__ == "__main__":
    unittest.main()
