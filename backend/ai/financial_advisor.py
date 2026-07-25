"""
Financial Advisor

Main orchestration module for the AI Intelligence layer.

Flow:
financial_analysis.json
        ↓
PromptBuilder
        ↓
GeminiClient
        ↓
ResponseParser
        ↓
ai_response.json
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from backend.ai.gemini_client import GeminiClient
from backend.ai.prompt_builder import PromptBuilder
from backend.ai.response_parser import ResponseParser

logger = logging.getLogger(__name__)


class FinancialAdvisor:
    """Coordinates the AI Intelligence workflow."""

    def __init__(self, client: Optional[GeminiClient] = None) -> None:
        self.client = client or GeminiClient()

    def generate_ai_response(
        self,
        input_path: str,
        output_path: str,
    ) -> Dict[str, Any]:
        """
        Generate ai_response.json from financial_analysis.json.

        Args:
            input_path: Path to financial_analysis.json
            output_path: Path where ai_response.json will be written

        Returns:
            Parsed AI response dictionary.
        """
        input_file = Path(input_path)
        if not input_file.exists():
            logger.error("Input file not found: %s", input_path)
            raise FileNotFoundError(f"Input file not found: {input_path}")

        logger.info("Reading input analysis file from: %s", input_path)
        with open(input_file, "r", encoding="utf-8") as f:
            financial_analysis = json.load(f)

        logger.info("Building prompt via PromptBuilder...")
        prompt = PromptBuilder.build(financial_analysis)

        logger.info("Requesting Gemini AI reasoning...")
        raw_response = self.client.generate(prompt)

        logger.info("Parsing and validating AI response...")
        parsed_response = ResponseParser.parse(raw_response)

        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Saving validated AI response to: %s", output_path)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(parsed_response, f, indent=2)

        return parsed_response