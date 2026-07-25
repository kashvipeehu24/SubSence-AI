"""
Unit tests for the Merchant Normalizer processor.

Author: SubSense AI Team
"""

import json
import logging
import os
import tempfile
import unittest
from unittest.mock import patch
from backend.input_intelligence.processors.merchant_normalizer import (
    load_aliases,
    load_alias_choices,
    load_settings,
    normalize_merchant,
)


class TestMerchantNormalizer(unittest.TestCase):
    """
    Test suite for testing loading configurations, caching, settings, and normalizer behavior.
    """

    def setUp(self) -> None:
        self.custom_aliases = {
            "netflix india": "Netflix",
            "netflix": "Netflix",
            "netflix.com": "Netflix",
            "spotify premium": "Spotify",
            "spotify": "Spotify",
        }
        # Clear caches before each test run
        load_aliases.cache_clear()
        load_alias_choices.cache_clear()
        load_settings.cache_clear()

    def tearDown(self) -> None:
        # Clear caches after each test run
        load_aliases.cache_clear()
        load_alias_choices.cache_clear()
        load_settings.cache_clear()

    def test_load_aliases_valid_file(self) -> None:
        aliases_data = {
            "Netflix": ["Netflix India", "NETFLIX", "Netflix.com"],
            "Spotify": ["Spotify Premium"],
        }
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as temp_file:
            json.dump(aliases_data, temp_file)
            temp_path = temp_file.name

        try:
            aliases = load_aliases(config_path=temp_path)
            self.assertEqual(aliases.get("netflix india"), "Netflix")
            self.assertEqual(aliases.get("netflix"), "Netflix")
            self.assertEqual(aliases.get("netflix.com"), "Netflix")
            self.assertEqual(aliases.get("spotify premium"), "Spotify")
            self.assertEqual(aliases.get("spotify"), "Spotify")
        finally:
            os.remove(temp_path)

    def test_load_aliases_missing_file_logs_warning(self) -> None:
        # Missing file should log warning and return empty dictionary
        with self.assertLogs("backend.input_intelligence.processors.merchant_normalizer", level="WARNING") as log:
            aliases = load_aliases(config_path="non_existing_file_path.json")
            self.assertEqual(aliases, {})
            self.assertTrue(any("Merchant aliases configuration file not found" in message for message in log.output))

    def test_load_aliases_invalid_json_logs_warning(self) -> None:
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as temp_file:
            temp_file.write("{invalid json}")
            temp_path = temp_file.name

        try:
            with self.assertLogs("backend.input_intelligence.processors.merchant_normalizer", level="WARNING") as log:
                aliases = load_aliases(config_path=temp_path)
                self.assertEqual(aliases, {})
                self.assertTrue(any("Failed to decode JSON from merchant aliases config" in message for message in log.output))
        finally:
            os.remove(temp_path)

    def test_load_aliases_invalid_structure_root(self) -> None:
        # Root is a list instead of a dict
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as temp_file:
            json.dump(["not", "a", "dict"], temp_file)
            temp_path = temp_file.name

        try:
            with self.assertLogs("backend.input_intelligence.processors.merchant_normalizer", level="WARNING") as log:
                aliases = load_aliases(config_path=temp_path)
                self.assertEqual(aliases, {})
                self.assertTrue(any("Root must be a JSON object" in message for message in log.output))
        finally:
            os.remove(temp_path)

    def test_load_aliases_invalid_structure_values(self) -> None:
        # Map values are not lists
        aliases_data = {"Netflix": "Netflix India"}
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as temp_file:
            json.dump(aliases_data, temp_file)
            temp_path = temp_file.name

        try:
            with self.assertLogs("backend.input_intelligence.processors.merchant_normalizer", level="WARNING") as log:
                aliases = load_aliases(config_path=temp_path)
                self.assertEqual(aliases, {})
                self.assertTrue(any("Values must be lists of strings" in message for message in log.output))
        finally:
            os.remove(temp_path)

    def test_load_aliases_invalid_structure_list_elements(self) -> None:
        # List contains non-string elements
        aliases_data = {"Netflix": ["Netflix India", 123]}
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as temp_file:
            json.dump(aliases_data, temp_file)
            temp_path = temp_file.name

        try:
            with self.assertLogs("backend.input_intelligence.processors.merchant_normalizer", level="WARNING") as log:
                aliases = load_aliases(config_path=temp_path)
                self.assertEqual(aliases, {})
                self.assertTrue(any("Aliases list must contain strings only" in message for message in log.output))
        finally:
            os.remove(temp_path)

    def test_load_aliases_caching(self) -> None:
        aliases_data = {
            "Netflix": ["Netflix India"]
        }
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as temp_file:
            json.dump(aliases_data, temp_file)
            temp_path = temp_file.name

        try:
            # First call: miss
            load_aliases(config_path=temp_path)
            info_before = load_aliases.cache_info()
            self.assertEqual(info_before.misses, 1)
            self.assertEqual(info_before.hits, 0)

            # Second call: hit
            load_aliases(config_path=temp_path)
            info_after = load_aliases.cache_info()
            self.assertEqual(info_after.misses, 1)
            self.assertEqual(info_after.hits, 1)
        finally:
            os.remove(temp_path)

    def test_load_alias_choices_caching(self) -> None:
        aliases_data = {
            "Netflix": ["Netflix India"]
        }
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as temp_file:
            json.dump(aliases_data, temp_file)
            temp_path = temp_file.name

        try:
            # First call: miss
            load_alias_choices(config_path=temp_path)
            info_before = load_alias_choices.cache_info()
            self.assertEqual(info_before.misses, 1)
            self.assertEqual(info_before.hits, 0)

            # Second call: hit
            load_alias_choices(config_path=temp_path)
            info_after = load_alias_choices.cache_info()
            self.assertEqual(info_after.misses, 1)
            self.assertEqual(info_after.hits, 1)
        finally:
            os.remove(temp_path)

    @patch("backend.input_intelligence.processors.merchant_normalizer.load_settings")
    @patch("backend.input_intelligence.processors.merchant_normalizer.load_aliases")
    @patch("backend.input_intelligence.processors.merchant_normalizer.load_alias_choices")
    def test_settings_loading_and_override(self, mock_choices, mock_aliases, mock_settings) -> None:
        mock_settings.return_value = {"merchant_matching_threshold": 95.0}
        mock_aliases.return_value = {"netflix": "Netflix"}
        mock_choices.return_value = ["netflix"]

        # Since matching threshold is 95.0, fuzzy match similarity (~83) is less than 95.0,
        # so it should fallback to title-cased "Netflx"
        self.assertEqual(normalize_merchant("Netflx"), "Netflx")

        # Providing explicit threshold=80.0 should override settings.json and resolve to Netflix
        self.assertEqual(normalize_merchant("Netflx", threshold=80.0), "Netflix")

    def test_exact_alias_normalization(self) -> None:
        self.assertEqual(normalize_merchant("Netflix India", aliases=self.custom_aliases), "Netflix")
        self.assertEqual(normalize_merchant("Netflix.com", aliases=self.custom_aliases), "Netflix")
        self.assertEqual(normalize_merchant("spotify premium", aliases=self.custom_aliases), "Spotify")

    def test_case_insensitivity(self) -> None:
        self.assertEqual(normalize_merchant("NETFLIX", aliases=self.custom_aliases), "Netflix")
        self.assertEqual(normalize_merchant("NeTfLiX InDiA", aliases=self.custom_aliases), "Netflix")

    def test_fuzzy_matching(self) -> None:
        self.assertEqual(normalize_merchant("Netflx", aliases=self.custom_aliases), "Netflix")
        self.assertEqual(normalize_merchant("Spotfy", aliases=self.custom_aliases), "Spotify")

    def test_fallback_behavior(self) -> None:
        self.assertEqual(normalize_merchant("starbucks coffee", aliases=self.custom_aliases), "Starbucks Coffee")
        self.assertEqual(normalize_merchant("  google   cloud  ", aliases=self.custom_aliases), "Google Cloud")

    def test_empty_inputs(self) -> None:
        self.assertEqual(normalize_merchant("", aliases=self.custom_aliases), "")
        self.assertEqual(normalize_merchant("   ", aliases=self.custom_aliases), "")

    def test_empty_alias_file(self) -> None:
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as temp_file:
            json.dump({}, temp_file)
            temp_path = temp_file.name
        try:
            aliases = load_aliases(config_path=temp_path)
            self.assertEqual(aliases, {})
        finally:
            os.remove(temp_path)

    @patch("backend.input_intelligence.processors.merchant_normalizer.load_settings")
    @patch("backend.input_intelligence.processors.merchant_normalizer.load_aliases")
    @patch("backend.input_intelligence.processors.merchant_normalizer.load_alias_choices")
    def test_threshold_boundary(self, mock_choices, mock_aliases, mock_settings) -> None:
        mock_settings.return_value = {"merchant_matching_threshold": 80.0}
        mock_aliases.return_value = {"netflix": "Netflix"}
        mock_choices.return_value = ["netflix"]

        # fuzzy match WRatio similarity score of Netflx to netflix is around 92.3.
        # score (92.3) >= threshold (92.0) -> match
        self.assertEqual(normalize_merchant("Netflx", threshold=92.0), "Netflix")
        # score (92.3) < threshold (93.0) -> fallback
        self.assertEqual(normalize_merchant("Netflx", threshold=93.0), "Netflx")

    def test_unicode_merchant_names(self) -> None:
        unicode_aliases = {
            "café de flore": "Cafe De Flore",
            "日本語ショップ": "Nihongo Shop",
        }
        self.assertEqual(normalize_merchant("Café de Flore", aliases=unicode_aliases), "Cafe De Flore")
        self.assertEqual(normalize_merchant("日本語ショップ", aliases=unicode_aliases), "Nihongo Shop")
        self.assertEqual(normalize_merchant("München Markt", aliases={}), "München Markt")

    def test_empty_merchant_name(self) -> None:
        self.assertEqual(normalize_merchant(""), "")
        self.assertEqual(normalize_merchant("   "), "")
        self.assertEqual(normalize_merchant("\n\t  \r"), "")

    def test_long_merchant_name(self) -> None:
        long_name = "A" * 1000
        self.assertEqual(normalize_merchant(long_name, aliases=self.custom_aliases), long_name.title())


if __name__ == "__main__":
    unittest.main()
