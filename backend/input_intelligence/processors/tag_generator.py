"""
Tag Generator Processor

Generates a list of unique tags for financial transactions based on the merchant name,
assigned category, and transaction description using configured mapping rules.

Author: SubSense AI Team
"""

from __future__ import annotations

from functools import lru_cache
import json
import os
from typing import Any, Dict, List, Optional
from backend.input_intelligence.utils import clean_text


@lru_cache(maxsize=1)
def load_tag_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads tags rules and mappings from a JSON configuration file.

    Args:
        config_path: Custom path to the tags rules JSON file. If None, resolves
            to the default config path relative to the module.

    Returns:
        Dict[str, Any]: The loaded tag rules mapping.
    """
    if config_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(os.path.dirname(current_dir), "config", "tags.json")

    if not os.path.exists(config_path):
        return {"mappings": {}, "keyword_mappings": {}}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
        return {"mappings": {}, "keyword_mappings": {}}
    except (json.JSONDecodeError, IOError):
        return {"mappings": {}, "keyword_mappings": {}}


def generate_tags(
    merchant: str,
    category: str,
    description: str,
    config_path: Optional[str] = None,
) -> List[str]:
    """Generates a sorted, unique list of tags based on transaction fields and configuration.

    Args:
        merchant: Raw merchant name.
        category: Assigned transaction category name.
        description: Raw transaction description.
        config_path: Optional custom config file path.

    Returns:
        List[str]: A sorted list of unique tag strings.
    """
    clean_merchant = clean_text(merchant).lower()
    clean_category = clean_text(category).lower()
    clean_desc = clean_text(description).lower()

    config = load_tag_config(config_path)
    mappings = config.get("mappings", {})
    keyword_mappings = config.get("keyword_mappings", {})

    tags_set: set[str] = set()

    # 1. Direct merchant matching
    if clean_merchant:
        for m_key, m_tags in mappings.items():
            if m_key in clean_merchant:
                tags_set.update(m_tags)

    # 2. Keyword mapping in category or description or merchant
    for kw, kw_tags in keyword_mappings.items():
        kw_lower = kw.lower()
        if (kw_lower in clean_category) or (kw_lower in clean_desc) or (kw_lower in clean_merchant):
            tags_set.update(kw_tags)

    return sorted(list(tags_set))
