"""
Unit tests for the Transaction model.

This module validates that the Transaction model enforces the correct type hints,
validation constraints, and serialization/deserialization methods (to/from dict/json).

Author: SubSense AI Team
"""

import json
import unittest
from datetime import datetime
from backend.input_intelligence.models.transaction import Transaction


class TestTransactionModel(unittest.TestCase):
    """
    Test suite for testing constraints, types, serialization, and deserialization of the Transaction model.
    """

    def setUp(self) -> None:
        # Standard valid transaction matching the JSON contract
        self.valid_data = {
            "transaction_id": "TXN001",
            "merchant": "Netflix India",
            "normalized_merchant": "Netflix",
            "amount": 649,
            "currency": "INR",
            "transaction_type": "Debit",
            "date": "2026-07-15",
            "category": "Video Streaming",
            "description": "Netflix Monthly Subscription",
            "source": "Bank Statement",
            "confidence_score": 0.99,
            "is_recurring_candidate": True,
            "tags": ["subscription", "streaming"],
        }

    def test_valid_transaction_instantiation(self) -> None:
        """Test instantiation with valid parameters."""
        tx = Transaction.from_dict(self.valid_data)
        self.assertEqual(tx.transaction_id, "TXN001")
        self.assertEqual(tx.merchant, "Netflix India")
        self.assertEqual(tx.normalized_merchant, "Netflix")
        self.assertEqual(tx.amount, 649.0)
        self.assertEqual(tx.currency, "INR")
        self.assertEqual(tx.transaction_type, "Debit")
        self.assertEqual(tx.date, "2026-07-15")
        self.assertEqual(tx.category, "Video Streaming")
        self.assertEqual(tx.description, "Netflix Monthly Subscription")
        self.assertEqual(tx.source, "Bank Statement")
        self.assertEqual(tx.confidence_score, 0.99)
        self.assertTrue(tx.is_recurring_candidate)
        self.assertEqual(tx.tags, ["subscription", "streaming"])

    def test_serialization_to_from_dict(self) -> None:
        """Test dict serialization and deserialization."""
        tx = Transaction.from_dict(self.valid_data)
        serialized_dict = tx.to_dict()

        # The amount in original JSON contract was an int (649), serialized will be float (649.0)
        # So we adjust for assertions
        expected_dict = self.valid_data.copy()
        expected_dict["amount"] = 649.0
        
        self.assertEqual(serialized_dict, expected_dict)

        # Deserialize back
        tx_recreated = Transaction.from_dict(serialized_dict)
        self.assertEqual(tx, tx_recreated)

    def test_serialization_to_from_json(self) -> None:
        """Test JSON serialization and deserialization."""
        tx = Transaction.from_dict(self.valid_data)
        json_str = tx.to_json()
        
        # De-serialize
        tx_recreated = Transaction.from_json(json_str)
        self.assertEqual(tx, tx_recreated)

    def test_validation_transaction_id(self) -> None:
        """Test validations for transaction_id."""
        data = self.valid_data.copy()
        
        # Test wrong type
        data["transaction_id"] = 123
        with self.assertRaises(TypeError):
            Transaction.from_dict(data)
            
        # Test empty string
        data["transaction_id"] = ""
        with self.assertRaises(ValueError):
            Transaction.from_dict(data)

    def test_validation_merchant(self) -> None:
        """Test validations for merchant."""
        data = self.valid_data.copy()
        
        # Test wrong type
        data["merchant"] = None
        with self.assertRaises(TypeError):
            Transaction.from_dict(data)
            
        # Test empty string
        data["merchant"] = "   "
        with self.assertRaises(ValueError):
            Transaction.from_dict(data)

    def test_validation_normalized_merchant(self) -> None:
        """Test validations for normalized_merchant."""
        data = self.valid_data.copy()
        
        # Test wrong type
        data["normalized_merchant"] = []
        with self.assertRaises(TypeError):
            Transaction.from_dict(data)

    def test_validation_amount(self) -> None:
        """Test validations for amount."""
        data = self.valid_data.copy()
        
        # Test wrong type
        data["amount"] = "649"
        with self.assertRaises(TypeError):
            Transaction.from_dict(data)
            
        # Test zero amount (must be positive)
        data["amount"] = 0
        with self.assertRaises(ValueError):
            Transaction.from_dict(data)
            
        # Test negative amount
        data["amount"] = -10.5
        with self.assertRaises(ValueError):
            Transaction.from_dict(data)

    def test_validation_currency(self) -> None:
        """Test validations for currency."""
        data = self.valid_data.copy()
        
        # Test wrong type
        data["currency"] = 100
        with self.assertRaises(TypeError):
            Transaction.from_dict(data)
            
        # Test unsupported currency
        data["currency"] = "CAD"
        with self.assertRaises(ValueError):
            Transaction.from_dict(data)
            
        # Test valid currency support
        for curr in ["INR", "USD", "EUR", "GBP"]:
            data["currency"] = curr
            tx = Transaction.from_dict(data)
            self.assertEqual(tx.currency, curr)

    def test_validation_transaction_type(self) -> None:
        """Test validations for transaction_type."""
        data = self.valid_data.copy()
        
        # Test wrong type
        data["transaction_type"] = True
        with self.assertRaises(TypeError):
            Transaction.from_dict(data)
            
        # Test unsupported transaction type
        data["transaction_type"] = "Transfer"
        with self.assertRaises(ValueError):
            Transaction.from_dict(data)
            
        # Test valid types
        for ttype in ["Debit", "Credit"]:
            data["transaction_type"] = ttype
            tx = Transaction.from_dict(data)
            self.assertEqual(tx.transaction_type, ttype)

    def test_validation_date(self) -> None:
        """Test validations for date format."""
        data = self.valid_data.copy()
        
        # Test wrong type
        data["date"] = 20260715
        with self.assertRaises(TypeError):
            Transaction.from_dict(data)
            
        # Test invalid date string format
        data["date"] = "15-07-2026"
        with self.assertRaises(ValueError):
            Transaction.from_dict(data)
            
        # Test out of range date (like leap year/invalid days)
        data["date"] = "2026-02-29"  # 2026 is not a leap year
        with self.assertRaises(ValueError):
            Transaction.from_dict(data)

    def test_validation_confidence_score(self) -> None:
        """Test validations for confidence_score."""
        data = self.valid_data.copy()
        
        # Test wrong type
        data["confidence_score"] = "high"
        with self.assertRaises(TypeError):
            Transaction.from_dict(data)
            
        # Test out of bounds (negative)
        data["confidence_score"] = -0.01
        with self.assertRaises(ValueError):
            Transaction.from_dict(data)
            
        # Test out of bounds (greater than 1)
        data["confidence_score"] = 1.01
        with self.assertRaises(ValueError):
            Transaction.from_dict(data)
            
        # Test boundaries 0.0 and 1.0
        data["confidence_score"] = 0.0
        tx = Transaction.from_dict(data)
        self.assertEqual(tx.confidence_score, 0.0)
        
        data["confidence_score"] = 1.0
        tx = Transaction.from_dict(data)
        self.assertEqual(tx.confidence_score, 1.0)

    def test_validation_is_recurring_candidate(self) -> None:
        """Test validations for is_recurring_candidate."""
        data = self.valid_data.copy()
        
        # Test wrong type
        data["is_recurring_candidate"] = "Yes"
        with self.assertRaises(TypeError):
            Transaction.from_dict(data)

    def test_validation_tags(self) -> None:
        """Test validations for tags."""
        data = self.valid_data.copy()
        
        # Test wrong type
        data["tags"] = "subscription"
        with self.assertRaises(TypeError):
            Transaction.from_dict(data)
            
        # Test list with wrong type elements
        data["tags"] = ["subscription", 123]
        with self.assertRaises(TypeError):
            Transaction.from_dict(data)


if __name__ == "__main__":
    unittest.main()
