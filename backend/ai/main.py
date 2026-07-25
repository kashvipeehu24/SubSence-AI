"""
Main entry point for the AI Intelligence Module.
"""

import logging
import sys

from backend.ai.config import (
    AI_RESPONSE_PATH,
    FINANCIAL_ANALYSIS_PATH,
)
from backend.ai.financial_advisor import FinancialAdvisor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the AI Intelligence pipeline."""
    try:
        advisor = FinancialAdvisor()

        advisor.generate_ai_response(
            input_path=str(FINANCIAL_ANALYSIS_PATH),
            output_path=str(AI_RESPONSE_PATH),
        )

        print("✅ AI response generated successfully.")
        print(f"Saved to: {AI_RESPONSE_PATH}")

    except (ValueError, FileNotFoundError, RuntimeError) as err:
        print(f"❌ AI Module Error: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()