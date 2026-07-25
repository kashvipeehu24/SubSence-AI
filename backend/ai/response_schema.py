"""
Response Schema

Validates that the AI response contains the required
top-level fields and nested structures defined by the project JSON contract.
"""

from typing import Any, Dict


REQUIRED_OBJECT_SCHEMAS = {
    "report_metadata": {"generated_at", "ai_model", "version"},
    "financial_summary": {"overall_health", "summary"},
    "financial_health_score_explanation": {"score", "grade", "reason"},
    "monthly_summary": {"total_spent", "subscriptions", "potential_savings"},
    "yearly_summary": {"total_spent", "subscription_cost", "potential_savings"},
}

REQUIRED_ARRAY_FIELDS = {
    "duplicate_subscription_explanations",
    "price_hike_explanations",
    "recurring_subscription_explanations",
    "savings_suggestions",
    "action_items",
    "dashboard_recommendations",
}

REQUIRED_TOP_LEVEL_FIELDS = set(REQUIRED_OBJECT_SCHEMAS.keys()) | REQUIRED_ARRAY_FIELDS


class ResponseSchema:
    """Validate AI response structure against the JSON contract."""

    @staticmethod
    def validate(response: Dict[str, Any]) -> bool:
        """
        Validate required fields exist, have correct types, and contain required nested keys.

        Args:
            response: Parsed AI JSON response dictionary.

        Returns:
            True if valid.

        Raises:
            ValueError: If required fields are missing, have invalid types, or miss nested keys.
        """
        if not isinstance(response, dict):
            raise ValueError(
                f"AI response must be a JSON object (dict), got {type(response).__name__}"
            )

        missing_top = REQUIRED_TOP_LEVEL_FIELDS - response.keys()
        if missing_top:
            raise ValueError(
                f"AI response missing required top-level fields: {sorted(missing_top)}"
            )

        for obj_key, nested_keys in REQUIRED_OBJECT_SCHEMAS.items():
            val = response[obj_key]
            if not isinstance(val, dict):
                raise ValueError(
                    f"Field '{obj_key}' must be a JSON object (dict), got {type(val).__name__}"
                )
            missing_nested = nested_keys - val.keys()
            if missing_nested:
                raise ValueError(
                    f"Field '{obj_key}' is missing required nested keys: {sorted(missing_nested)}"
                )

        for arr_key in REQUIRED_ARRAY_FIELDS:
            val = response[arr_key]
            if not isinstance(val, list):
                raise ValueError(
                    f"Field '{arr_key}' must be a JSON array (list), got {type(val).__name__}"
                )

        return True