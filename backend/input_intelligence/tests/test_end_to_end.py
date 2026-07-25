"""
End-to-End Integration Tests for the Input Intelligence pipeline.

Author: SubSense AI Team
"""

import os
import tempfile
import unittest
from backend.input_intelligence.models.transaction import Transaction
from backend.input_intelligence.parser import parse_input


class TestEndToEndPipeline(unittest.TestCase):
    """
    E2E integration test suite for verifying full orchestration from a CSV file.
    """

    def setUp(self) -> None:
        self.csv_headers = "transaction_id,merchant,amount,date,category,description,tags\n"
        # Row 1: Valid row with duplicate ID to follow
        self.csv_row1 = "TXN001,Netflix India,649.00,2026-07-15,Video Streaming,Netflix Monthly,subscription,streaming\n"
        # Row 2: Duplicate ID of Row 1 (should be removed)
        self.csv_row2 = "TXN001,Netflix.com,649.00,2026-07-15,Video Streaming,Netflix Monthly,subscription,streaming\n"
        # Row 3: Valid Swiggy transaction
        self.csv_row3 = ",Swiggy India,350.00,16/07/2026,,Order lunch,\n"
        # Row 4: Duplicate of Row 3 based on merchant+amount+date fallback (should be removed)
        self.csv_row4 = ",Swiggy India,350.00,16/07/2026,,Order lunch,\n"
        # Row 5: Empty blank line (should be skipped)
        self.csv_row5 = "\n"
        # Row 6: Invalid row (corrupted amount, should be skipped)
        self.csv_row6 = "TXN002,Amazon,invalid_amount,2026-07-15,,Order,\n"

        # Create temporary CSV file
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write(
                self.csv_headers +
                self.csv_row1 +
                self.csv_row2 +
                self.csv_row3 +
                self.csv_row4 +
                self.csv_row5 +
                self.csv_row6
            )
            self.temp_csv_path = f.name

    def tearDown(self) -> None:
        if os.path.exists(self.temp_csv_path):
            os.remove(self.temp_csv_path)

    def test_e2e_csv_pipeline_ingestion(self) -> None:
        # Run through orchestrator parser
        txs = parse_input(self.temp_csv_path, "csv")

        # 1. Verify duplicates removed and blank/invalid rows skipped
        # Row 1 (valid) - KEPT
        # Row 2 (duplicate ID) - REMOVED
        # Row 3 (valid ID-less) - KEPT
        # Row 4 (duplicate key fallback) - REMOVED
        # Row 5 (blank) - SKIPPED
        # Row 6 (invalid amount) - SKIPPED
        self.assertEqual(len(txs), 2)

        # 2. Verify Output schema matches Transaction model exactly
        for tx in txs:
            self.assertIsInstance(tx, Transaction)

        # 3. Verify normalization, categorization, tagging, confidence, ID generation for Row 1
        tx1 = txs[0]
        self.assertEqual(tx1.transaction_id, "TXN001")
        self.assertEqual(tx1.normalized_merchant, "Netflix")
        self.assertEqual(tx1.category, "Video Streaming")
        self.assertEqual(tx1.tags, ["entertainment", "streaming", "subscription"])
        self.assertGreater(tx1.confidence_score, 0.0)

        # 4. Verify post-processing for Row 3 (ID-less)
        tx3 = txs[1]
        self.assertEqual(tx3.normalized_merchant, "Swiggy")
        self.assertEqual(tx3.category, "Food & Dining")
        self.assertEqual(tx3.tags, ["delivery", "food", "restaurant"])
        self.assertGreater(tx3.confidence_score, 0.0)
        # Verify transaction ID was deterministically generated
        self.assertTrue(len(tx3.transaction_id) > 0)


if __name__ == "__main__":
    unittest.main()
