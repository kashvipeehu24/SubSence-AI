"""
Unit tests for the core Input Intelligence Orchestrator Pipeline.

Author: SubSense AI Team
"""

import unittest
from unittest.mock import patch, MagicMock
from backend.input_intelligence.models.transaction import Transaction
from backend.input_intelligence.parser import parse_input


class TestOrchestrator(unittest.TestCase):
    """
    Test suite checking orchestrator delegate mappings and post-processing integrations.
    """

    def setUp(self) -> None:
        self.raw_tx = Transaction(
            transaction_id="DRAFT",
            merchant="Netflix India",
            normalized_merchant="",
            amount=649.0,
            currency="INR",
            transaction_type="Debit",
            date="2026-07-15",
            category="",
            description="Netflix subscription",
            source="Test Log",
            confidence_score=0.0,
            is_recurring_candidate=False,
            tags=[]
        )

    @patch("backend.input_intelligence.parser.validate_upload")
    @patch("backend.input_intelligence.parser.parse_csv")
    def test_csv_ingestion_path(self, mock_parse_csv, mock_validate_upload) -> None:
        mock_validate_upload.return_value = {"valid": True, "errors": [], "warnings": []}
        mock_parse_csv.return_value = [self.raw_tx]

        # Normalization and processor mapping will run on raw_tx
        results = parse_input("fake_statement.csv", "csv")
        self.assertEqual(len(results), 1)
        tx = results[0]
        
        # Verify orchestration updates
        self.assertEqual(tx.normalized_merchant, "Netflix")
        self.assertEqual(tx.category, "Video Streaming")
        self.assertEqual(tx.tags, ["entertainment", "streaming", "subscription"])
        self.assertGreater(tx.confidence_score, 0.0)
        self.assertTrue(len(tx.transaction_id) > 0)

    def test_unsupported_source_type(self) -> None:
        with self.assertRaises(ValueError):
            parse_input("some_source", "invalid_type")


if __name__ == "__main__":
    unittest.main()
