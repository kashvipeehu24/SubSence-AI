"""
Configuration for the AI Intelligence Module.
"""

import os
from pathlib import Path

# Gemini Model - using gemini-flash-latest as default supported model
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

# AI Response Version
AI_RESPONSE_VERSION = "1.0"

# Default Input JSON
FINANCIAL_ANALYSIS_PATH = Path("sample_json/financial_analysis.json")

# Default Output JSON
AI_RESPONSE_PATH = Path("sample_json/ai_response.json")