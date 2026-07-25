"""
Utility functions for the Input Intelligence module.

This module provides pure, highly reusable helper functions for string cleaning,
amount parsing, date conversion, deterministic ID generation, and safe JSON loading.

Author: SubSense AI Team
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


def normalize_whitespace(text: str) -> str:
    """Normalizes consecutive whitespace characters in a string to a single space.

    Args:
        text: The string to normalize.

    Returns:
        The normalized string with leading and trailing whitespaces stripped.

    Raises:
        TypeError: If the input is not a string.
    """
    if not isinstance(text, str):
        raise TypeError("normalize_whitespace expects a string input")
    return " ".join(text.split())


def clean_text(text: Optional[str]) -> str:
    """Cleans the input text by stripping outer whitespace and normalizing internal spaces.

    Args:
        text: The input string to clean. Can be None.

    Returns:
        The cleaned string. Returns an empty string if input is None or not a string.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        return ""
    return normalize_whitespace(text)


def clean_amount(amount: Any) -> float:
    """Cleans currency or numeric input and converts it to a float.

    Handles symbols ($, ₹, €, £), alphabetic codes (INR, USD, EUR, GBP, Rs., Rs),
    thousands separators (commas), and negative signs/parentheses.

    Args:
        amount: The input representing the amount. Can be a string, float, int, or None.

    Returns:
        The cleaned amount as a float. Returns 0.0 if cleanup/parsing fails.
    """
    if amount is None:
        return 0.0
    if isinstance(amount, (int, float)):
        return float(amount)

    val_str = str(amount).strip()
    is_negative = False
    if val_str.startswith("(") and val_str.endswith(")"):
        is_negative = True
        val_str = val_str[1:-1].strip()

    # Strip known currency symbols
    val_str = re.sub(r"[₹$€£¥,]", "", val_str)

    # Remove common currency text codes case-insensitively
    # Sort Rs. before Rs to ensure Rs. is matched first
    currency_codes = ["INR", "USD", "EUR", "GBP", "Rs.", "Rs"]
    for code in currency_codes:
        val_str = re.sub(re.escape(code), "", val_str, flags=re.IGNORECASE)

    val_str = val_str.strip()
    if val_str.startswith("-"):
        is_negative = not is_negative
        val_str = val_str[1:].strip()

    try:
        val_float = float(val_str) if val_str else 0.0
        return -val_float if is_negative else val_float
    except ValueError:
        return 0.0


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely converts a value to float, returning a default value on failure.

    Args:
        value: The value to convert.
        default: The fallback float value if conversion fails. Defaults to 0.0.

    Returns:
        The converted float or the default value.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_date(date_string: Optional[str]) -> Optional[str]:
    """Parses a date string in various common formats and converts it to ISO format (YYYY-MM-DD).

    Supported formats include YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY, DD-MM-YYYY, DD Mon YYYY,
    epoch timestamps, and ISO date-times.

    Args:
        date_string: The string representing the date. Can be None.

    Returns:
        The parsed date string in 'YYYY-MM-DD' format, or None if parsing fails.
    """
    if not date_string:
        return None

    cleaned_date = clean_text(str(date_string))
    if not cleaned_date:
        return None

    # Handle ISO DateTimes or dates with space-separated times
    if "T" in cleaned_date:
        cleaned_date = cleaned_date.split("T")[0]
    elif " " in cleaned_date:
        parts = cleaned_date.split()
        if len(parts) > 1 and ":" in parts[-1]:
            cleaned_date = " ".join(parts[:-1])

    cleaned_date = cleaned_date.strip()

    # Handle epoch timestamps
    if re.match(r"^\d+$", cleaned_date):
        try:
            val = int(cleaned_date)
            if len(cleaned_date) == 13:
                val = val // 1000
            return datetime.fromtimestamp(val).strftime("%Y-%m-%d")
        except (ValueError, OSError, OverflowError):
            pass

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%d-%b-%Y",
        "%d-%B-%Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%Y%m%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(cleaned_date, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def generate_transaction_id(merchant: str, amount: float, date: str) -> str:
    """Generates a deterministic transaction ID using SHA-256 based on key transaction details.

    Args:
        merchant: The merchant name.
        amount: The transaction amount.
        date: The transaction date (normally ISO YYYY-MM-DD format).

    Returns:
        A 16-character hexadecimal SHA-256 hash substring.

    Raises:
        TypeError: If any parameters are of invalid type.
    """
    if not isinstance(merchant, str):
        raise TypeError("merchant must be a string")
    if not isinstance(amount, (int, float)):
        raise TypeError("amount must be a float or int")
    if not isinstance(date, str):
        raise TypeError("date must be a string")

    clean_merc = clean_text(merchant).lower()
    formatted_amt = f"{float(amount):.2f}"
    clean_dt = clean_text(date)

    raw_payload = f"{clean_merc}|{formatted_amt}|{clean_dt}"
    return hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()[:16]


def is_empty(value: Any) -> bool:
    """Checks if a value is effectively empty.

    A value is empty if it is None, an empty collection (list, dict, set, tuple),
    or a string consisting of only whitespace.

    Args:
        value: The value to inspect.

    Returns:
        True if the value is empty, False otherwise.
    """
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if hasattr(value, "__len__"):
        return len(value) == 0
    return False


def safe_json_load(json_string: Optional[str]) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """Safely decodes a JSON string into a python dictionary or list.

    Args:
        json_string: The raw JSON string to decode. Can be None.

    Returns:
        The decoded JSON object (typically Dict or List), or None if parsing fails or input is empty.
    """
    if not json_string or not isinstance(json_string, str) or not json_string.strip():
        return None
    try:
        data = json.loads(json_string)
        if isinstance(data, (dict, list)):
            return data
        return None
    except (json.JSONDecodeError, TypeError):
        return None


# Global stats container to allow parsers to report metrics back to the orchestrator
_latest_stats = {
    "extracted": 0,
    "validated": 0,
    "rejected": 0
}

# Shared container to pass raw/OCR text back to orchestrator for Gemini fallback
_latest_extracted_text = ""


def detect_mime_type(file_path: str) -> str:
    """Detects the file classification (MIME-like key) by checking the magic byte signatures.

    Args:
        file_path: Absolute path to the statement file.

    Returns:
        str: Classification label ('pdf', 'png', 'jpeg', 'webp', 'heic', 'xlsx', 'xls',
             'json', 'csv', 'txt', or 'unknown').
    """
    try:
        if not file_path or not os.path.exists(file_path):
            return "unknown"

        with open(file_path, "rb") as f:
            header = f.read(2048)
        if not header:
            return "unknown"

        # 1. PDF signature check
        if header.startswith(b"%PDF-"):
            return "pdf"

        # 2. PNG signature check
        if header.startswith(b"\x89PNG\r\n"):
            return "png"

        # 3. JPEG/JPG signature check
        if header.startswith(b"\xff\xd8\xff"):
            return "jpeg"

        # 4. WEBP signature check
        if header.startswith(b"RIFF") and len(header) >= 12 and header[8:12] == b"WEBP":
            return "webp"

        # 5. HEIC signature check
        if len(header) >= 12 and header[4:8] == b"ftyp" and header[8:12] in {b"heic", b"mif1", b"heix", b"msf1"}:
            return "heic"

        # 6. XLS (OLECF Format) signature check
        if header.startswith(b"\xd0\xcf\x11\xe0"):
            return "xls"

        # 7. XLSX (ZIP Format) signature check
        if header.startswith(b"PK\x03\x04"):
            _, ext = os.path.splitext(file_path.lower())
            if ext in {".xlsx", ".xls"}:
                return "xlsx"
            return "zip"

        # 8. JSON check
        decoded_start = ""
        for encoding in ["utf-8", "utf-8-sig", "latin1"]:
            try:
                decoded_start = header[:100].decode(encoding).strip()
                break
            except Exception:
                continue
        if decoded_start.startswith("{") or decoded_start.startswith("["):
            return "json"

        # 9. Text Decodability Check (TXT / CSV)
        try:
            header.decode("utf-8")
            _, ext = os.path.splitext(file_path.lower())
            if ext == ".csv":
                return "csv"
            if ext in {".txt", ".eml"}:
                return "txt"
            if "," in decoded_start or ";" in decoded_start or "\t" in decoded_start:
                return "csv"
            return "txt"
        except UnicodeDecodeError:
            pass

        return "binary"
    except Exception:
        return "unknown"