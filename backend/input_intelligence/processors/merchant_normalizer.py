"""
Merchant Normalizer Processor

Provides functionality to normalize raw merchant names using alias lookup maps
and fuzzy matching based on RapidFuzz. Caches parsed rules for performance.

Author: SubSense AI Team
"""

from __future__ import annotations

from functools import lru_cache
import json
import logging
import os
from typing import Any, Dict, List, Optional
from rapidfuzz import fuzz, process
from backend.input_intelligence.utils import clean_text

logger = logging.getLogger(__name__)


class _DefaultThreshold(float):
    """Sentinel class representing the default configuration threshold value."""
    pass


DEFAULT_THRESHOLD = _DefaultThreshold(80.0)


@lru_cache(maxsize=1)
def load_settings(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Loads application settings from a JSON file.

    Args:
        config_path: Custom path to the settings JSON file. If None, resolves to default.

    Returns:
        Dict[str, Any]: Parsed settings configuration dict.
    """
    if config_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(os.path.dirname(current_dir), "config", "settings.json")

    if not os.path.exists(config_path):
        logger.warning("Settings configuration file not found at: %s", config_path)
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            logger.warning("Invalid settings config format at %s: Root must be a dict", config_path)
            return {}
    except json.JSONDecodeError as e:
        logger.warning("Failed to decode JSON from settings config at %s: %s", config_path, str(e))
        return {}
    except IOError as e:
        logger.warning("Failed to read settings config file at %s: %s", config_path, str(e))
        return {}


@lru_cache(maxsize=1)
def load_aliases(config_path: Optional[str] = None) -> Dict[str, str]:
    """Loads merchant aliases from a JSON configuration file.

    The JSON file is expected to map normalized merchant names to lists of their aliases:
    {
        "Netflix": ["Netflix India", "NETFLIX", "Netflix.com"]
    }

    This function flattens that mapping into a case-insensitive alias-to-normalized lookup dict:
    {
        "netflix india": "Netflix",
        "netflix": "Netflix",
        "netflix.com": "Netflix"
    }

    Args:
        config_path: Custom path to the aliases JSON file. If None, looks for
            the file in the default location under the config directory.

    Returns:
        Dict[str, str]: A flattened case-insensitive lookup mapping of aliases to normalized names.
    """
    if config_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(os.path.dirname(current_dir), "config", "merchant_aliases.json")

    if not os.path.exists(config_path):
        logger.warning("Merchant aliases configuration file not found at: %s", config_path)
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            logger.warning("Invalid structure in merchant aliases config at %s: Root must be a JSON object (dict)", config_path)
            return {}

        aliases: Dict[str, str] = {}
        for normalized, alias_list in data.items():
            if not isinstance(normalized, str):
                logger.warning("Invalid structure in merchant aliases config at %s: Keys must be strings", config_path)
                return {}
            if not isinstance(alias_list, list):
                logger.warning("Invalid structure in merchant aliases config at %s: Values must be lists of strings", config_path)
                return {}
            for alias in alias_list:
                if not isinstance(alias, str):
                    logger.warning("Invalid structure in merchant aliases config at %s: Aliases list must contain strings only", config_path)
                    return {}

            # Populate lookup dictionaries
            aliases[normalized.lower()] = normalized
            for alias in alias_list:
                aliases[alias.lower()] = normalized

        return aliases
    except json.JSONDecodeError as e:
        logger.warning("Failed to decode JSON from merchant aliases config at %s: %s", config_path, str(e))
        return {}
    except IOError as e:
        logger.warning("Failed to read merchant aliases config file at %s: %s", config_path, str(e))
        return {}


@lru_cache(maxsize=1)
def load_alias_choices(config_path: Optional[str] = None) -> List[str]:
    """Loads the list of alias keys for reuse to prevent reconstruction during normalization.

    Args:
        config_path: Custom path to the aliases JSON file. If None, resolves to default.

    Returns:
        List[str]: The list of lowercase choice strings for fuzzy matching.
    """
    return list(load_aliases(config_path).keys())


def normalize_merchant(
    name: str,
    aliases: Optional[Dict[str, str]] = None,
    threshold: float = DEFAULT_THRESHOLD,
) -> str:
    """Normalizes a merchant name string using aliases config and fuzzy matching.

    Args:
        name: The raw merchant name to normalize.
        aliases: Optional lookup mapping. If None, aliases will be loaded from default config.
        threshold: Minimum similarity score threshold (0.0 to 100.0) for fuzzy matches.

    Returns:
        The normalized merchant name string, or title-cased cleaned name if no match is found.
    """
    cleaned_name = clean_text(name)
    if not cleaned_name:
        return ""

    # Load custom or default aliases/choices
    if aliases is None:
        choices = load_alias_choices()
        aliases = load_aliases()
    else:
        choices = list(aliases.keys())

    # Resolve threshold settings if default sentinel is used
    if isinstance(threshold, _DefaultThreshold):
        settings = load_settings()
        threshold = settings.get("merchant_matching_threshold", 80.0)

    lower_name = cleaned_name.lower()

    # 1. Exact case-insensitive match
    if lower_name in aliases:
        return aliases[lower_name]

    # 2. Fuzzy match using RapidFuzz
    if aliases:
        match_res = process.extractOne(lower_name, choices, scorer=fuzz.WRatio)
        if match_res:
            best_match, score, _ = match_res
            if score >= threshold:
                return aliases[best_match]

    # 3. Fallback to title-cased original cleaned name
    return cleaned_name.title()
