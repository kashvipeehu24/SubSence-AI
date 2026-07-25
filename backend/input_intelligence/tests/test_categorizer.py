"""
Unit tests for the Transaction Categorizer processor.

Author: SubSense AI Team
"""

import json
import os
import tempfile
import unittest
from backend.input_intelligence.processors.categorizer import (
    load_categories,
    categorize_transaction,
)


class TestCategorizer(unittest.TestCase):
    """
    Test suite for checking loader and categorization rules behavior.
    """

    def setUp(self) -> None:
        self.categories_config = {
            "categories": {
                "Video Streaming": {
                    "merchants": ["netflix", "prime video"],
                    "keywords": ["netflix", "streaming", "subscription"],
                },
                "Music Streaming": {
                    "merchants": ["spotify"],
                    "keywords": ["spotify", "music", "audio"],
                },
                "Food & Dining": {
                    "merchants": ["starbucks", "zomato"],
                    "keywords": ["coffee", "dining", "food"],
                },
            },
            "default_category": "Uncategorized",
        }

        # Create a temporary config file for testing
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as temp_file:
            json.dump(self.categories_config, temp_file)
            self.temp_path = temp_file.name

    def tearDown(self) -> None:
        if os.path.exists(self.temp_path):
            os.remove(self.temp_path)

    def test_load_categories_valid(self) -> None:
        config = load_categories(self.temp_path)
        self.assertEqual(config.get("default_category"), "Uncategorized")
        self.assertIn("Video Streaming", config.get("categories", {}))

    def test_load_categories_missing(self) -> None:
        config = load_categories("non_existent_file.json")
        self.assertEqual(config.get("default_category"), "Other")
        self.assertEqual(config.get("categories"), {})

    def test_load_categories_invalid_json(self) -> None:
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as bad_file:
            bad_file.write("{invalid json}")
            bad_path = bad_file.name

        try:
            config = load_categories(bad_path)
            self.assertEqual(config.get("default_category"), "Other")
            self.assertEqual(config.get("categories"), {})
        finally:
            os.remove(bad_path)

    def test_categorize_by_merchant(self) -> None:
        # Match exact merchant (case-insensitive)
        self.assertEqual(
            categorize_transaction("Netflix India", "", config_path=self.temp_path),
            "Video Streaming",
        )
        self.assertEqual(
            categorize_transaction("SPOTIFY", "Premium", config_path=self.temp_path),
            "Music Streaming",
        )

    def test_categorize_by_description_keywords(self) -> None:
        # Match keyword inside description
        self.assertEqual(
            categorize_transaction("Unknown Merchant", "Monthly streaming pay", config_path=self.temp_path),
            "Video Streaming",
        )
        self.assertEqual(
            categorize_transaction("Unknown Merchant", "Buy coffee beans", config_path=self.temp_path),
            "Food & Dining",
        )

    def test_categorize_default_fallback(self) -> None:
        # No matching merchant or description keywords
        self.assertEqual(
            categorize_transaction("Some Store", "Weekly groceries shopping", config_path=self.temp_path),
            "Uncategorized",
        )

    def test_empty_inputs(self) -> None:
        # Empty inputs should fall back to default category
        self.assertEqual(
            categorize_transaction("", "", config_path=self.temp_path),
            "Uncategorized",
        )


if __name__ == "__main__":
    unittest.main()
