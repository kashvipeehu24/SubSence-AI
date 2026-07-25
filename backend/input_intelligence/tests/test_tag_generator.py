"""
Unit tests for the Tag Generator processor.

Author: SubSense AI Team
"""

import json
import os
import tempfile
import unittest
from backend.input_intelligence.processors.tag_generator import (
    load_tag_config,
    generate_tags,
)


class TestTagGenerator(unittest.TestCase):
    """
    Test suite for checking loader and tag generation behavior.
    """

    def setUp(self) -> None:
        self.tags_config = {
            "mappings": {
                "netflix": ["subscription", "streaming", "entertainment"],
                "swiggy": ["food", "delivery", "restaurant"],
                "amazon": ["shopping", "ecommerce"],
            },
            "keyword_mappings": {
                "streaming": ["streaming"],
                "subscription": ["subscription"],
                "delivery": ["delivery"],
                "shopping": ["shopping"],
            },
        }

        # Create temporary config file
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as temp_file:
            json.dump(self.tags_config, temp_file)
            self.temp_path = temp_file.name

        load_tag_config.cache_clear()

    def tearDown(self) -> None:
        if os.path.exists(self.temp_path):
            os.remove(self.temp_path)
        load_tag_config.cache_clear()

    def test_load_tag_config_valid(self) -> None:
        config = load_tag_config(self.temp_path)
        self.assertIn("netflix", config.get("mappings", {}))
        self.assertIn("streaming", config.get("keyword_mappings", {}))

    def test_load_tag_config_missing(self) -> None:
        config = load_tag_config("non_existent_file.json")
        self.assertEqual(config.get("mappings"), {})
        self.assertEqual(config.get("keyword_mappings"), {})

    def test_tag_generation_netflix(self) -> None:
        tags = generate_tags("Netflix India", "Video Streaming", "netflix billing", config_path=self.temp_path)
        expected = sorted(["subscription", "streaming", "entertainment"])
        self.assertEqual(tags, expected)

    def test_tag_generation_swiggy(self) -> None:
        tags = generate_tags("Swiggy", "Food Delivery", "lunch order", config_path=self.temp_path)
        expected = sorted(["food", "delivery", "restaurant"])
        self.assertEqual(tags, expected)

    def test_tag_generation_amazon(self) -> None:
        tags = generate_tags("Amazon.co.in", "Online Shopping", "bought gadgets", config_path=self.temp_path)
        expected = sorted(["shopping", "ecommerce"])
        self.assertEqual(tags, expected)

    def test_unique_tags(self) -> None:
        # Match keywords in both category and description, ensuring no duplicates in output
        tags = generate_tags("unknown", "Streaming Services", "monthly subscription", config_path=self.temp_path)
        self.assertEqual(tags, ["streaming", "subscription"])

    def test_unmatched_fallback(self) -> None:
        # Standard unmatched inputs should return an empty list
        tags = generate_tags("Some Random Store", "Uncategorized", "simple transaction", config_path=self.temp_path)
        self.assertEqual(tags, [])


if __name__ == "__main__":
    unittest.main()
