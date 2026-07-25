"""
Unit tests for duplicate detector processor.

Author: SubSense AI Team
"""

import unittest
from backend.input_intelligence.models.transaction import Transaction
from backend.input_intelligence.processors.duplicate_detector import remove_duplicates


class TestDuplicateDetector(unittest.TestCase):
    """
    Test suite for checking duplicate detection logic.
    """

    def setUp(self) -> None:
        self.tx1 = Transaction(
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
            confidence_score=0.99,
            is_recurring_candidate=True,
            tags=["subscription"]
        )
        self.tx2 = Transaction(
            transaction_id="TXN001",  # Duplicate ID
            merchant="Netflix.com",
            normalized_merchant="Netflix",
            amount=649.0,
            currency="INR",
            transaction_type="Debit",
            date="2026-07-15",
            category="Video Streaming",
            description="Netflix Monthly Subscription",
            source="Bank Statement",
            confidence_score=0.99,
            is_recurring_candidate=True,
            tags=["subscription"]
        )
        self.tx3 = Transaction(
            transaction_id="TXN002",
            merchant="Spotify Premium",
            normalized_merchant="Spotify",
            amount=119.0,
            currency="INR",
            transaction_type="Debit",
            date="2026-07-16",
            category="Music Streaming",
            description="Spotify Subscription",
            source="Bank Statement",
            confidence_score=0.95,
            is_recurring_candidate=True,
            tags=["subscription"]
        )
        # Transactions with missing transaction_id
        self.tx_no_id1 = Transaction(
            transaction_id="DRAFT",
            merchant="Starbucks Coffee",
            normalized_merchant="Starbucks",
            amount=250.0,
            currency="INR",
            transaction_type="Debit",
            date="2026-07-17",
            category="Food & Dining",
            description="Coffee",
            source="SMS Alert",
            confidence_score=0.85,
            is_recurring_candidate=False,
            tags=["coffee"]
        )
        self.tx_no_id2 = Transaction(
            transaction_id="DRAFT",  # Duplicate merchant+amount+date
            merchant="Starbucks Coffee",
            normalized_merchant="Starbucks",
            amount=250.0,
            currency="INR",
            transaction_type="Debit",
            date="2026-07-17",
            category="Food & Dining",
            description="Coffee",
            source="SMS Alert",
            confidence_score=0.85,
            is_recurring_candidate=False,
            tags=["coffee"]
        )
        self.tx_no_id3 = Transaction(
            transaction_id="DRAFT",  # Different amount, not duplicate
            merchant="Starbucks Coffee",
            normalized_merchant="Starbucks",
            amount=500.0,
            currency="INR",
            transaction_type="Debit",
            date="2026-07-17",
            category="Food & Dining",
            description="Coffee Gift Card",
            source="SMS Alert",
            confidence_score=0.85,
            is_recurring_candidate=False,
            tags=["coffee"]
        )

    def test_empty_list(self) -> None:
        self.assertEqual(remove_duplicates([]), [])

    def test_single_transaction(self) -> None:
        self.assertEqual(remove_duplicates([self.tx1]), [self.tx1])

    def test_duplicate_transaction_id(self) -> None:
        # tx2 has duplicate ID of tx1, should be removed
        input_list = [self.tx1, self.tx2, self.tx3]
        result = remove_duplicates(input_list)
        self.assertEqual(result, [self.tx1, self.tx3])

    def test_duplicate_merchant_amount_date(self) -> None:
        # tx_no_id2 has duplicate merchant+amount+date of tx_no_id1, should be removed
        input_list = [self.tx_no_id1, self.tx_no_id2, self.tx_no_id3]
        result = remove_duplicates(input_list)
        self.assertEqual(result, [self.tx_no_id1, self.tx_no_id3])

    def test_preserve_ordering(self) -> None:
        # Order should match input insertion index order
        input_list = [self.tx3, self.tx_no_id1, self.tx1, self.tx_no_id2]
        result = remove_duplicates(input_list)
        self.assertEqual(result, [self.tx3, self.tx_no_id1, self.tx1])

    def test_no_duplicates(self) -> None:
        input_list = [self.tx1, self.tx3, self.tx_no_id1, self.tx_no_id3]
        result = remove_duplicates(input_list)
        self.assertEqual(result, input_list)

    def test_original_list_unchanged(self) -> None:
        # Input list is copy protected and remains mutated-free
        input_list = [self.tx1, self.tx2, self.tx3]
        original_copy = list(input_list)
        remove_duplicates(input_list)
        self.assertEqual(input_list, original_copy)


if __name__ == "__main__":
    unittest.main()
