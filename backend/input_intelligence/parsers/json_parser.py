"""
JSON Statement Parser

Parses transaction lines from a JSON file into a list of draft Transaction objects.

Author: SubSense AI Team
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List
from backend.input_intelligence.models.transaction import Transaction
from backend.input_intelligence.utils import clean_amount, parse_date

logger = logging.getLogger(__name__)


def parse_json(file_path: str) -> List[Transaction]:
    """Parses a JSON statement file into a list of draft Transaction objects.

    Args:
        file_path: Absolute path to the JSON file.

    Returns:
        List[Transaction]: List of draft transaction objects.
    """
    transactions: List[Transaction] = []
    if not file_path or not isinstance(file_path, str) or not os.path.exists(file_path):
        logger.error("JSON file path does not exist or is invalid: %s", file_path)
        return transactions

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error("Failed to decode JSON from %s: %s", file_path, str(e))
        raise ValueError("Unsupported statement format.")

    # Resolve items list
    items: List[Dict[str, Any]] = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for key in ["transactions", "data", "rows", "items"]:
            if key in data and isinstance(data[key], list):
                items = data[key]
                break
        if not items:
            for val in data.values():
                if isinstance(val, list):
                    items = val
                    break

    if not isinstance(items, list) or not items:
        logger.warning("No transaction items list found in JSON file '%s'", file_path)
        raise ValueError("No transaction rows detected.")

    # Determine all keys present across items for synonym mapping
    all_keys = set()
    for item in items:
        if isinstance(item, dict):
            all_keys.update(item.keys())

    # Create mapping for normalized keys to actual JSON keys
    normalized_keys = {k.lower().replace("_", "").replace(" ", ""): k for k in all_keys}

    def has_any_key(synonyms: List[str]) -> bool:
        for syn in synonyms:
            norm_syn = syn.lower().replace("_", "").replace(" ", "")
            if norm_syn in normalized_keys:
                return True
        return False

    date_synonyms = ["date", "transactiondate", "txndate", "postingdate", "time", "valuedate", "bookingdate"]
    merchant_synonyms = ["merchant", "vendor", "payee", "store", "merchantname", "beneficiary"]
    description_synonyms = ["description", "narration", "memo", "details", "remarks", "particulars"]
    amount_synonyms = ["amount", "value", "price", "charge", "txnamount"]
    debit_synonyms = ["debit", "withdrawal", "dr", "payment", "out", "spent"]
    credit_synonyms = ["credit", "deposit", "cr", "receipt", "in", "received"]

    # Verify column existence
    if not has_any_key(date_synonyms):
        logger.warning("Missing date column in JSON keys: %s", all_keys)
        raise ValueError("Date column missing.")
    if not has_any_key(amount_synonyms) and not (has_any_key(debit_synonyms) or has_any_key(credit_synonyms)):
        logger.warning("Missing amount/debit/credit column in JSON keys: %s", all_keys)
        raise ValueError("Amount column missing.")
    if not has_any_key(merchant_synonyms) and not has_any_key(description_synonyms):
        logger.warning("Missing merchant/description column in JSON keys: %s", all_keys)
        raise ValueError("Merchant column missing.")

    def get_val(item: Dict[str, Any], synonyms: List[str], default: Any = "") -> Any:
        for syn in synonyms:
            norm_syn = syn.lower().replace("_", "").replace(" ", "")
            if norm_syn in normalized_keys:
                actual_key = normalized_keys[norm_syn]
                val = item.get(actual_key)
                if val is not None:
                    return val
        return default

    rows_extracted = len(items)
    rows_validated = 0
    rows_rejected = 0

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            logger.warning("JSON row %d rejected: Row is not an object/dictionary (Field: row)", idx + 1)
            rows_rejected += 1
            continue

        raw_date = get_val(item, date_synonyms, None)
        raw_merchant = get_val(item, merchant_synonyms, None)
        raw_desc = get_val(item, description_synonyms, "")
        raw_amt = get_val(item, amount_synonyms, None)
        raw_debit = get_val(item, debit_synonyms, None)
        raw_credit = get_val(item, credit_synonyms, None)

        # Merchant fallback
        merchant = raw_merchant or raw_desc
        if not merchant or not str(merchant).strip():
            logger.warning("JSON row %d rejected: Merchant field is missing or empty (Field: merchant)", idx + 1)
            rows_rejected += 1
            continue

        # Date parsing
        parsed_date = parse_date(str(raw_date) if raw_date is not None else None)
        if not parsed_date:
            logger.warning("JSON row %d rejected: Invalid/unparseable date '%s' (Field: date)", idx + 1, raw_date)
            rows_rejected += 1
            continue

        # Amount and transaction type mapping
        amt = 0.0
        tx_type = "Debit"

        if raw_amt is not None and str(raw_amt).strip():
            amt = clean_amount(raw_amt)
            tx_type = get_val(item, ["transaction_type", "type", "direction"], "Debit")
        elif raw_debit is not None and str(raw_debit).strip():
            amt = abs(clean_amount(raw_debit))
            tx_type = "Debit"
        elif raw_credit is not None and str(raw_credit).strip():
            amt = abs(clean_amount(raw_credit))
            tx_type = "Credit"

        if amt <= 0:
            logger.warning("JSON row %d rejected: Amount must be positive, got '%s' (Field: amount)", idx + 1, amt)
            rows_rejected += 1
            continue

        # Extract other metadata fields
        currency = get_val(item, ["currency"], "INR")
        tx_id = get_val(item, ["transaction_id", "id", "txnid", "txn_id"], "DRAFT")
        category = get_val(item, ["category"], "")
        source = get_val(item, ["source"], "JSON Statement")

        raw_tags = get_val(item, ["tags"], [])
        tags: List[str] = []
        if isinstance(raw_tags, list):
            tags = [str(t).strip() for t in raw_tags if str(t).strip()]
        elif isinstance(raw_tags, str) and raw_tags.strip():
            if raw_tags.startswith("[") and raw_tags.endswith("]"):
                try:
                    tags = json.loads(raw_tags)
                except Exception:
                    tags = [t.strip() for t in raw_tags[1:-1].split(",") if t.strip()]
            else:
                tags = [t.strip() for t in raw_tags.split(",") if t.strip()]

        try:
            tx = Transaction(
                transaction_id=tx_id,
                merchant=str(merchant).strip(),
                normalized_merchant="",
                amount=amt,
                currency=currency,
                transaction_type=tx_type,
                date=parsed_date,
                category=category,
                description=str(raw_desc).strip() or str(merchant).strip(),
                source=source,
                confidence_score=0.0,
                is_recurring_candidate=False,
                tags=tags,
            )
            transactions.append(tx)
            rows_validated += 1
        except Exception as e:
            logger.warning("JSON row %d rejected: Model validation error: %s (Field: Transaction model)", idx + 1, str(e))
            rows_rejected += 1

    from backend.input_intelligence import utils
    utils._latest_stats["extracted"] = rows_extracted
    utils._latest_stats["validated"] = rows_validated
    utils._latest_stats["rejected"] = rows_rejected

    logger.info(
        "JSON Ingestion - Total Extracted: %d, Validated: %d, Rejected: %d",
        rows_extracted,
        rows_validated,
        rows_rejected,
    )
    return transactions
