"""
Confidence Calculator Processor

Calculates a normalized, clamped confidence score for Transaction instances based on
field availability checks.

Author: SubSense AI Team
"""

from __future__ import annotations

from backend.input_intelligence.models.transaction import Transaction


def calculate_confidence(transaction: Transaction) -> float:
    """Calculates a confidence score between 0.0 and 1.0 for a Transaction.

    The score is calculated based on the availability of 6 key fields:
      - merchant (non-empty string)
      - amount (non-zero positive float)
      - date (non-empty string)
      - category (non-empty string)
      - description (non-empty string)
      - tags (non-empty list)

    Args:
        transaction: The Transaction object to evaluate.

    Returns:
        float: The calculated confidence score, clamped between 0.0 and 1.0.
    """
    checks = [
        bool(transaction.merchant and transaction.merchant.strip()),
        bool(transaction.amount and transaction.amount > 0),
        bool(transaction.date and transaction.date.strip()),
        bool(transaction.category and transaction.category.strip()),
        bool(transaction.description and transaction.description.strip()),
        bool(transaction.tags and len(transaction.tags) > 0)
    ]
    score = sum(checks) / len(checks)
    return max(0.0, min(1.0, score))
