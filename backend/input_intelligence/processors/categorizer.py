"""
Transaction Categorizer Processor

Categorizes financial transactions based on the merchant name and transaction
description using configured category maps and keywords.

Author: SubSense AI Team
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from backend.input_intelligence.utils import clean_text


def load_categories(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads transaction categories and matching rules from a JSON file.

    Args:
        config_path: Custom path to categories JSON file. If None, the default
            path is resolved under the config directory.

    Returns:
        Dict[str, Any]: The loaded configuration dictionary containing 'categories'
            rules and the 'default_category'.
    """
    if config_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(os.path.dirname(current_dir), "config", "categories.json")

    if not os.path.exists(config_path):
        return {"categories": {}, "default_category": "Other"}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
        return {"categories": {}, "default_category": "Other"}
    except (json.JSONDecodeError, IOError):
        return {"categories": {}, "default_category": "Other"}


def categorize_transaction(
    merchant: str,
    description: str,
    config_path: Optional[str] = None,
) -> str:
    """Categorizes a transaction based on the merchant and description strings.

    Args:
        merchant: The raw merchant name.
        description: The raw transaction description.
        config_path: Optional custom configuration file path.

    Returns:
        The matched category name string, or the default category if unmatched.
    """
    clean_merchant = clean_text(merchant).lower()
    clean_desc = clean_text(description).lower()

    config = load_categories(config_path)
    categories = config.get("categories", {})
    default_cat = config.get("default_category", "Other")

    if not categories:
        return default_cat

    # 1. Match by merchant rules
    if clean_merchant:
        for category_name, rules in categories.items():
            merchants = [m.lower() for m in rules.get("merchants", [])]
            if any(m in clean_merchant for m in merchants):
                return category_name

    # 2. Match by keywords rules in merchant or description
    for category_name, rules in categories.items():
        keywords = [k.lower() for k in rules.get("keywords", [])]
        if any(k in clean_merchant or k in clean_desc for k in keywords):
            return category_name

    return default_cat
