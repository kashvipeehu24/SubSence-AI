"""
CSV Statement Parser

Parses transaction lines from a CSV file into a list of draft Transaction objects.

Author: SubSense AI Team
"""

from __future__ import annotations

import csv
from typing import List, Dict, Any
from backend.input_intelligence.models.transaction import Transaction
from backend.input_intelligence.utils import clean_amount, parse_date


def parse_csv(file_path: str) -> List[Transaction]:
    """Parses a CSV statement file into a list of draft Transaction objects.

    Args:
        file_path: Absolute path to the CSV file.

    Returns:
        List[Transaction]: List of draft transaction objects.
    """
    transactions: List[Transaction] = []
    if not file_path or not isinstance(file_path, str) or not os.path.exists(file_path):
        return transactions

    try:
        with open(file_path, "r", encoding="utf-8", newline="") as f:
            # Read all lines to handle clean check
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                return []

            # Create case and character insensitive header mapping
            header_map: Dict[str, str] = {}
            for col in reader.fieldnames:
                norm = col.strip().lower().replace("_", "").replace(" ", "")
                header_map[norm] = col

            def get_val(keys: List[str], row: Dict[str, str], default: str = "") -> str:
                for k in keys:
                    norm_k = k.replace("_", "").replace(" ", "").lower()
                    if norm_k in header_map:
                        actual_col = header_map[norm_k]
                        if row[actual_col] is not None:
                            return row[actual_col].strip()
                return default

            for row in reader:
                # Skip completely blank lines
                if not any(row.values()):
                    continue

                merchant = get_val(["merchant", "vendor", "payee", "store"], row)
                raw_amt = get_val(["amount", "value", "price", "charge"], row)
                raw_date = get_val(["date", "transaction_date", "time"], row)
                
                # Minimum fields validation
                if not merchant or not raw_amt or not raw_date:
                    continue

                parsed_amt = clean_amount(raw_amt)
                parsed_dt = parse_date(raw_date)

                # Skip rows with invalid date or invalid amount (positive check)
                if not parsed_dt or parsed_amt <= 0:
                    continue

                # Extract optional fields
                tx_id = get_val(["transaction_id", "id", "txn_id", "transactionid", "txnid"], row, "")
                if not tx_id:
                    tx_id = "DRAFT"
                desc = get_val(["description", "narration", "memo", "details"], row, "")
                currency = get_val(["currency"], row, "INR")
                tx_type = get_val(["transaction_type", "type", "direction"], row, "Debit")
                category = get_val(["category"], row, "")
                source = get_val(["source"], row, "CSV Statement")

                # Tags parsing: support comma-separated tags or JSON array strings
                raw_tags = get_val(["tags"], row, "")
                tags: List[str] = []
                if raw_tags:
                    if raw_tags.startswith("[") and raw_tags.endswith("]"):
                        try:
                            tags = json.loads(raw_tags)
                        except json.JSONDecodeError:
                            tags = [t.strip() for t in raw_tags[1:-1].split(",") if t.strip()]
                    else:
                        tags = [t.strip() for t in raw_tags.split(",") if t.strip()]

                tx = Transaction(
                    transaction_id=tx_id,
                    merchant=merchant,
                    normalized_merchant="",
                    amount=parsed_amt,
                    currency=currency,
                    transaction_type=tx_type,
                    date=parsed_dt,
                    category=category,
                    description=desc,
                    source=source,
                    confidence_score=0.0,
                    is_recurring_candidate=False,
                    tags=tags,
                )
                transactions.append(tx)
    except IOError:
        pass

    return transactions


import json
import os
