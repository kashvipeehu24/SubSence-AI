"""
Unit tests for the utility functions in backend/input_intelligence/utils.py.

Author: SubSense AI Team
"""

import unittest
from backend.input_intelligence.utils import (
    normalize_whitespace,
    clean_text,
    clean_amount,
    safe_float,
    parse_date,
    generate_transaction_id,
    is_empty,
    safe_json_load,
)


class TestUtils(unittest.TestCase):
    """
    Test cases for each helper function in utils.py.
    """

    def test_normalize_whitespace(self) -> None:
        # Valid strings
        self.assertEqual(normalize_whitespace("  hello   world  "), "hello world")
        self.assertEqual(normalize_whitespace("hello\t\nworld"), "hello world")
        # Invalid input type should raise TypeError
        with self.assertRaises(TypeError):
            normalize_whitespace(None)  # type: ignore
        with self.assertRaises(TypeError):
            normalize_whitespace(123)  # type: ignore

    def test_clean_text(self) -> None:
        # Normal inputs
        self.assertEqual(clean_text("  hello   world  "), "hello world")
        self.assertEqual(clean_text(None), "")
        self.assertEqual(clean_text(123), "")  # type: ignore
        self.assertEqual(clean_text([]), "")  # type: ignore

    def test_clean_amount(self) -> None:
        # None input
        self.assertEqual(clean_amount(None), 0.0)
        # Numeric inputs
        self.assertEqual(clean_amount(123), 123.0)
        self.assertEqual(clean_amount(123.45), 123.45)
        # Currency symbols and codes
        self.assertEqual(clean_amount("₹1,299.50"), 1299.50)
        self.assertEqual(clean_amount("$ 50.00"), 50.00)
        self.assertEqual(clean_amount("100 €"), 100.0)
        self.assertEqual(clean_amount("INR 500"), 500.0)
        self.assertEqual(clean_amount("Rs. 250"), 250.0)
        self.assertEqual(clean_amount("250 Rs"), 250.0)
        # Thousands separator
        self.assertEqual(clean_amount("1,234,567.89"), 1234567.89)
        # Negative formatting
        self.assertEqual(clean_amount("-123.45"), -123.45)
        self.assertEqual(clean_amount("($123.45)"), -123.45)
        self.assertEqual(clean_amount("-₹ 10"), -10.0)
        # Invalid string
        self.assertEqual(clean_amount("abc"), 0.0)

    def test_safe_float(self) -> None:
        # Valid conversions
        self.assertEqual(safe_float(123), 123.0)
        self.assertEqual(safe_float("123.45"), 123.45)
        # Invalid conversions (should fall back to default)
        self.assertEqual(safe_float("abc"), 0.0)
        self.assertEqual(safe_float(None), 0.0)
        self.assertEqual(safe_float("abc", default=9.99), 9.99)

    def test_parse_date(self) -> None:
        # None and empty
        self.assertIsNone(parse_date(None))
        self.assertIsNone(parse_date(""))
        # YYYY-MM-DD
        self.assertEqual(parse_date("2026-07-15"), "2026-07-15")
        # DD/MM/YYYY
        self.assertEqual(parse_date("15/07/2026"), "2026-07-15")
        # DD-MM-YYYY
        self.assertEqual(parse_date("15-07-2026"), "2026-07-15")
        # DD Mon YYYY
        self.assertEqual(parse_date("15 Jul 2026"), "2026-07-15")
        self.assertEqual(parse_date("15 July 2026"), "2026-07-15")
        # Invalid format
        self.assertIsNone(parse_date("2026/07/15"))
        self.assertIsNone(parse_date("32-07-2026"))
        self.assertIsNone(parse_date("not-a-date"))

    def test_generate_transaction_id(self) -> None:
        # Deterministic checks
        id1 = generate_transaction_id("Netflix India", 649, "2026-07-15")
        id2 = generate_transaction_id("netflix india", 649.0, "2026-07-15")
        id3 = generate_transaction_id("  Netflix   India  ", 649.00, " 2026-07-15 ")
        self.assertEqual(id1, id2)
        self.assertEqual(id1, id3)
        self.assertEqual(len(id1), 16)
        
        # Test developer type errors
        with self.assertRaises(TypeError):
            generate_transaction_id(None, 100, "2026-07-15")  # type: ignore
        with self.assertRaises(TypeError):
            generate_transaction_id("Merchant", "100", "2026-07-15")  # type: ignore
        with self.assertRaises(TypeError):
            generate_transaction_id("Merchant", 100, None)  # type: ignore

    def test_is_empty(self) -> None:
        # Empty cases
        self.assertTrue(is_empty(None))
        self.assertTrue(is_empty(""))
        self.assertTrue(is_empty("   "))
        self.assertTrue(is_empty([]))
        self.assertTrue(is_empty({}))
        self.assertTrue(is_empty(()))
        self.assertTrue(is_empty(set()))
        
        # Non-empty cases
        self.assertFalse(is_empty("abc"))
        self.assertFalse(is_empty([1]))
        self.assertFalse(is_empty({"a": 1}))
        self.assertFalse(is_empty(123))
        self.assertFalse(is_empty(False))

    def test_safe_json_load(self) -> None:
        # Empty and non-string checks
        self.assertIsNone(safe_json_load(None))
        self.assertIsNone(safe_json_load(""))
        self.assertIsNone(safe_json_load("   "))
        self.assertIsNone(safe_json_load(123))  # type: ignore
        
        # Valid JSON objects and lists
        self.assertEqual(safe_json_load('{"a": 1}'), {"a": 1})
        self.assertEqual(safe_json_load('[1, 2, 3]'), [1, 2, 3])
        
        # Non-dictionary / Non-list JSON values (e.g. primitive types)
        self.assertIsNone(safe_json_load('"string"'))
        self.assertIsNone(safe_json_load("123"))
        self.assertIsNone(safe_json_load("true"))
        
        # Invalid JSON syntax
        self.assertIsNone(safe_json_load('{"a": 1'))


if __name__ == "__main__":
    unittest.main()
