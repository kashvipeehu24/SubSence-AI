"""
Transaction Model

Defines the Transaction dataclass for the SubSense AI platform, matching the JSON contract
and containing validation logic, serialization, and deserialization helpers.

Author: SubSense AI Team
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Union


@dataclass
class Transaction:
    """
    Represents a normalized financial transaction with intelligence metadata.

    This class serves as the core data transfer object for transactions processed
    by the Input Intelligence module. It enforces structure and validity at
    instantiation time.
    """
    transaction_id: str
    merchant: str
    normalized_merchant: str
    amount: float
    currency: str
    transaction_type: str
    date: str
    category: str
    description: str
    source: str
    confidence_score: float
    is_recurring_candidate: bool
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        Validates the fields of the Transaction after initialization.

        Raises:
            TypeError: If a field has an incorrect type.
            ValueError: If a field value violates constraints.
        """
        # Validate transaction_id
        if not isinstance(self.transaction_id, str):
            raise TypeError(f"transaction_id must be a string, got {type(self.transaction_id).__name__}")
        if not self.transaction_id.strip():
            raise ValueError("transaction_id cannot be empty or whitespace only")

        # Validate merchant
        if not isinstance(self.merchant, str):
            raise TypeError(f"merchant must be a string, got {type(self.merchant).__name__}")
        if not self.merchant.strip():
            raise ValueError("merchant cannot be empty or whitespace only")

        # Validate normalized_merchant
        if not isinstance(self.normalized_merchant, str):
            raise TypeError(f"normalized_merchant must be a string, got {type(self.normalized_merchant).__name__}")

        # Validate amount
        if not isinstance(self.amount, (int, float)):
            raise TypeError(f"amount must be an int or float, got {type(self.amount).__name__}")
        # Normalize to float
        self.amount = float(self.amount)
        if self.amount <= 0:
            raise ValueError(f"amount must be positive, got {self.amount}")

        # Validate currency
        if not isinstance(self.currency, str):
            raise TypeError(f"currency must be a string, got {type(self.currency).__name__}")
        allowed_currencies = {"INR", "USD", "EUR", "GBP"}
        if self.currency not in allowed_currencies:
            raise ValueError(f"currency must be one of {allowed_currencies}, got '{self.currency}'")

        # Validate transaction_type
        if not isinstance(self.transaction_type, str):
            raise TypeError(f"transaction_type must be a string, got {type(self.transaction_type).__name__}")
        allowed_types = {"Debit", "Credit"}
        if self.transaction_type not in allowed_types:
            raise ValueError(f"transaction_type must be one of {allowed_types}, got '{self.transaction_type}'")

        # Validate date matches YYYY-MM-DD
        if not isinstance(self.date, str):
            raise TypeError(f"date must be a string, got {type(self.date).__name__}")
        try:
            # Check date format validity, keeping date as string
            datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"date must match format YYYY-MM-DD, got '{self.date}'") from e

        # Validate category
        if not isinstance(self.category, str):
            raise TypeError(f"category must be a string, got {type(self.category).__name__}")

        # Validate description
        if not isinstance(self.description, str):
            raise TypeError(f"description must be a string, got {type(self.description).__name__}")

        # Validate source
        if not isinstance(self.source, str):
            raise TypeError(f"source must be a string, got {type(self.source).__name__}")

        # Validate confidence_score
        if not isinstance(self.confidence_score, (int, float)):
            raise TypeError(f"confidence_score must be an int or float, got {type(self.confidence_score).__name__}")
        # Normalize to float
        self.confidence_score = float(self.confidence_score)
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError(f"confidence_score must be between 0.0 and 1.0, got {self.confidence_score}")

        # Validate is_recurring_candidate
        if not isinstance(self.is_recurring_candidate, bool):
            raise TypeError(f"is_recurring_candidate must be a boolean, got {type(self.is_recurring_candidate).__name__}")

        # Validate tags is a list of strings
        if not isinstance(self.tags, list):
            raise TypeError(f"tags must be a list of strings, got {type(self.tags).__name__}")
        for idx, tag in enumerate(self.tags):
            if not isinstance(tag, str):
                raise TypeError(f"tag at index {idx} must be a string, got {type(tag).__name__}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Transaction instance to a dictionary representation matching the JSON contract.

        Returns:
            Dict[str, Any]: Dictionary containing transaction fields.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Transaction:
        """
        Creates a Transaction instance from a dictionary.

        Args:
            data (Dict[str, Any]): Dictionary containing transaction fields.

        Returns:
            Transaction: An initialized and validated Transaction instance.

        Raises:
            KeyError: If any required field is missing.
            TypeError / ValueError: If any field values fail validation constraints.
        """
        required_keys = {
            "transaction_id",
            "merchant",
            "normalized_merchant",
            "amount",
            "currency",
            "transaction_type",
            "date",
            "category",
            "description",
            "source",
            "confidence_score",
            "is_recurring_candidate",
        }
        missing_keys = required_keys - data.keys()
        if missing_keys:
            raise KeyError(f"Missing required fields for Transaction: {', '.join(missing_keys)}")

        # Extract values, allowing 'tags' to fall back to the default_factory list if not present.
        kwargs: Dict[str, Any] = {k: data[k] for k in required_keys}
        if "tags" in data:
            kwargs["tags"] = data["tags"]

        return cls(**kwargs)

    def to_json(self, indent: Optional[int] = None) -> str:
        """
        Converts the Transaction instance to a JSON string.

        Args:
            indent (Optional[int]): If provided, formats the JSON string with this indentation level.

        Returns:
            str: JSON string of the transaction.
        """
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> Transaction:
        """
        Creates a Transaction instance from a JSON string.

        Args:
            json_str (str): A valid JSON string representing a transaction.

        Returns:
            Transaction: An initialized and validated Transaction instance.

        Raises:
            json.JSONDecodeError: If the JSON string is invalid.
            TypeError / ValueError / KeyError: If the decoded JSON fails validation constraints.
        """
        data = json.loads(json_str)
        if not isinstance(data, dict):
            raise TypeError(f"Expected a JSON object (dict), got {type(data).__name__}")
        return cls.from_dict(data)
