"""
Response Parser

Converts Gemini's raw response into a validated Python dictionary.
"""

import json
import logging
import re
from typing import Any, Dict

from backend.ai.response_schema import ResponseSchema

logger = logging.getLogger(__name__)


class ResponseParser:
    """Parses and validates Gemini responses."""

    @staticmethod
    def parse(raw_response: str) -> Dict[str, Any]:
        """
        Parse Gemini response into validated JSON.

        Args:
            raw_response: Raw text returned by Gemini.

        Returns:
            Parsed and validated dictionary.

        Raises:
            ValueError: If the response is not valid JSON or fails schema validation.
        """
        if not raw_response or not raw_response.strip():
            logger.error("Empty raw response received from Gemini.")
            raise ValueError("Raw response from Gemini is empty.")

        cleaned = raw_response.strip()

        # Strip markdown code fences if present
        pattern = r"^```(?:json)?\s*\n?(.*?)\n?```$"
        match = re.search(pattern, cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
        else:
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        try:
            response = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error("JSONDecodeError while parsing Gemini response.")
            raise ValueError(
                f"Gemini returned invalid JSON:\n{cleaned}"
            ) from exc

        ResponseSchema.validate(response)
        logger.info("Successfully parsed and validated Gemini JSON response.")

        return response