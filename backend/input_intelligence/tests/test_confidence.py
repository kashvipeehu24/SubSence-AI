"""
Unit tests for confidence calculator processor.

Author: SubSense AI Team
"""

import unittest
from backend.input_intelligence.models.transaction import Transaction
from backend.input_intelligence.processors.confidence import calculate_confidence


class TestConfidenceCalculator(unittest.TestCase):
    """
    Test suite for checking confidence score logic.
    """

    def setUp(self) -> None:
        # 6 fields: merchant, amount, date, category, description, tags
        self.valid_tx = Transaction(
            transaction_id="TXN001",
            merchant="Netflix India",
            normalized_merchant="Netflix",
            amount=649.0,
            currency="INR",
            transaction_type="Debit",
            date="2026-07-15",
            category="Video Streaming",
            description="Netflix Monthly Subscription",
            source="Bank Statement",
            confidence_score=0.0,
            is_recurring_candidate=True,
            tags=["subscription"]
        )

    def test_full_confidence(self) -> None:
        # All 6 fields are present/valid
        score = calculate_confidence(self.valid_tx)
        self.assertEqual(score, 1.0)

    def test_missing_fields_reduces_score(self) -> None:
        # Missing tags -> 5/6 = 0.8333333333333334
        tx = self.valid_tx
        tx.tags = []
        self.assertAlmostEqual(calculate_confidence(tx), 5/6)

        # Missing tags + description -> 4/6 = 0.6666666666666666
        tx.description = ""
        self.assertAlmostEqual(calculate_confidence(tx), 4/6)

        # Missing tags + description + category -> 3/6 = 0.5
        tx.category = "   "
        self.assertAlmostEqual(calculate_confidence(tx), 0.5)

    def test_invalid_amount_or_date(self) -> None:
        # Amount <= 0 is invalid
        tx = self.valid_tx
        tx.amount = -10.0
        # 5/6 = 0.8333333333333334
        self.assertAlmostEqual(calculate_confidence(tx), 5/6)

        # Date empty/invalid format is invalid
        tx.amount = 649.0
        tx.date = ""
        self.assertAlmostEqual(calculate_confidence(tx), 5/6)


if __name__ == "__main__":
    unittest.main()
