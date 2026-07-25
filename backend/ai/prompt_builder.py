"""
Prompt Builder

Builds the prompt that is sent to Gemini.
This module DOES NOT call the Gemini API.
"""

import json
from typing import Any, Dict


class PromptBuilder:
    """Builds prompts for Gemini."""

    OUTPUT_TEMPLATE: Dict[str, Any] = {
        "report_metadata": {
            "generated_at": "",
            "ai_model": "Gemini",
            "version": "1.0",
        },
        "financial_summary": {
            "overall_health": "",
            "summary": "",
        },
        "financial_health_score_explanation": {
            "score": 0,
            "grade": "",
            "reason": "",
        },
        "monthly_summary": {
            "total_spent": 0,
            "subscriptions": 0,
            "potential_savings": 0,
        },
        "yearly_summary": {
            "total_spent": 0,
            "subscription_cost": 0,
            "potential_savings": 0,
        },
        "duplicate_subscription_explanations": [],
        "price_hike_explanations": [],
        "recurring_subscription_explanations": [],
        "savings_suggestions": [],
        "action_items": [],
        "dashboard_recommendations": [],
    }

    @classmethod
    def build(cls, financial_analysis: Dict[str, Any]) -> str:
        """
        Build the prompt for Gemini.

        Args:
            financial_analysis: Parsed financial_analysis.json

        Returns:
            Prompt string.
        """
        analysis_json = json.dumps(financial_analysis, indent=2)
        template_json = json.dumps(cls.OUTPUT_TEMPLATE, indent=2)

        prompt = (
            "You are an expert AI Financial Advisor for SubSence-AI.\n\n"
            "You will receive a JSON input called financial_analysis.json containing pre-analyzed financial metrics.\n\n"
            "CRITICAL RULES:\n"
            "- DO NOT calculate any financial metrics.\n"
            "- DO NOT calculate Financial Health Score.\n"
            "- DO NOT detect subscriptions.\n"
            "- DO NOT detect duplicate subscriptions.\n"
            "- DO NOT detect recurring subscriptions.\n"
            "- DO NOT detect price hikes.\n"
            "- Everything has already been calculated.\n"
            "- Your job is ONLY to explain the analysis and generate recommendations.\n\n"
            "=========================\n"
            "INPUT JSON\n"
            "=========================\n"
            f"{analysis_json}\n\n"
            "=========================\n"
            "OUTPUT JSON CONTRACT\n"
            "=========================\n"
            "Return ONLY valid JSON matching EXACTLY this structure:\n"
            f"{template_json}\n\n"
            "=========================\n"
            "YOUR TASK\n"
            "=========================\n"
            "1. Populate 'report_metadata' with current ISO timestamp ('generated_at'), 'ai_model': 'Gemini', 'version': '1.0'.\n"
            "2. Populate 'financial_summary' with overall health and a concise summary.\n"
            "3. Populate 'financial_health_score_explanation' explaining why the score is what it is.\n"
            "4. Fill 'monthly_summary' and 'yearly_summary' with total_spent, subscriptions/subscription_cost, and potential_savings from the input JSON.\n"
            "5. Provide list of objects for 'duplicate_subscription_explanations', 'price_hike_explanations', and 'recurring_subscription_explanations'.\n"
            "6. Provide actionable recommendations for 'savings_suggestions', 'action_items', and 'dashboard_recommendations'.\n\n"
            "Write natural, concise and helpful explanations.\n\n"
            "Do NOT return Markdown.\n"
            "Do NOT wrap the response inside triple backticks.\n"
            "Return ONLY valid JSON.\n"
        )

        return prompt