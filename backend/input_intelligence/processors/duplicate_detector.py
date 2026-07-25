"""
Duplicate Detector Processor

Filters out duplicate transactions from a list, preserving order and keeping
the first occurrence. Handles fallback deduplication based on transaction fields.

Author: SubSense AI Team
"""

from __future__ import annotations

from typing import List
from backend.input_intelligence.models.transaction import Transaction


def remove_duplicates(transactions: List[Transaction]) -> List[Transaction]:
    """Removes duplicate transactions from a list, preserving order and keeping the first occurrence.

    Duplicates are identified by:
      1. Matching exact non-empty 'transaction_id'.
      2. If 'transaction_id' is missing (None, empty, or whitespace-only), matching the combination of
         'merchant' (case-insensitive and whitespace-stripped), 'amount', and 'date'.

    Args:
        transactions: A list of Transaction objects. The input list is not modified.

    Returns:
        List[Transaction]: A new list containing only unique Transaction objects.
    """
    if not transactions:
        return []
    if len(transactions) == 1:
        return [transactions[0]]

    unique_txs: List[Transaction] = []
    seen_ids: set[str] = set()
    seen_keys: set[tuple[str, float, str]] = set()

    for tx in transactions:
        tx_id = tx.transaction_id.strip() if tx.transaction_id else ""
        if tx_id == "DRAFT":
            tx_id = ""
        key = (tx.merchant.strip().lower(), float(tx.amount), tx.date.strip())
        
        if tx_id:
            # Check by transaction_id
            if tx_id in seen_ids:
                continue
            seen_ids.add(tx_id)
            seen_keys.add(key)
        else:
            # transaction_id is missing, check by merchant, amount, date
            if key in seen_keys:
                continue
            seen_keys.add(key)
            
        unique_txs.append(tx)

    return unique_txs
