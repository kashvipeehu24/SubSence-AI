"""
CSV Statement Parser

Parses transaction lines from a CSV file into a list of draft Transaction objects.

Author: SubSense AI Team
"""

from __future__ import annotations

import csv
import json
import logging
import os
from typing import Any, Dict, List
from backend.input_intelligence.models.transaction import Transaction
from backend.input_intelligence.utils import clean_amount, parse_date

logger = logging.getLogger(__name__)


def detect_delimiter(file_path: str) -> str:
    """Sniffs the CSV file header line to detect the delimiter character.

    Args:
        file_path: Path to the CSV file.

    Returns:
        str: Delimiter character (',', ';', or '\t'). Defaults to ','.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            first_line = f.readline()
            if not first_line:
                return ","
            counts = {
                ",": first_line.count(","),
                ";": first_line.count(";"),
                "\t": first_line.count("\t")
            }
            max_delim = max(counts, key=counts.get)
            if counts[max_delim] > 0:
                return max_delim
            return ","
    except Exception:
        return ","


def parse_csv(file_path: str) -> List[Transaction]:
    """Parses a CSV statement file into a list of draft Transaction objects.

    Args:
        file_path: Absolute path to the CSV file.

    Returns:
        List[Transaction]: List of draft transaction objects.
    """
    transactions: List[Transaction] = []
    if not file_path or not isinstance(file_path, str) or not os.path.exists(file_path):
        logger.error("CSV file path does not exist or is invalid: %s", file_path)
        return transactions

    # Store raw text for Gemini fallback
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            from backend.input_intelligence import utils
            utils._latest_extracted_text = f.read()
    except Exception:
        pass

    delim = detect_delimiter(file_path)
    logger.info("CSV Parser: Detected delimiter '%s' for file '%s'", delim, file_path)

    try:
        with open(file_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f, delimiter=delim)
            raw_rows = list(reader)
    except Exception as e:
        logger.error("Failed to read CSV file %s: %s", file_path, str(e))
        raise ValueError("Unsupported statement format.")

    if not raw_rows:
        logger.warning("CSV file is empty: %s", file_path)
        raise ValueError("No transaction rows detected.")

    # Synonym lists for automatic column mapping
    date_synonyms = ["date", "transactiondate", "txndate", "postingdate", "time", "valuedate", "bookingdate"]
    merchant_synonyms = ["merchant", "vendor", "payee", "store", "merchantname", "beneficiary"]
    description_synonyms = ["description", "narration", "memo", "details", "remarks", "particulars"]
    amount_synonyms = ["amount", "value", "price", "charge", "txnamount"]
    debit_synonyms = ["debit", "withdrawal", "dr", "payment", "out", "spent", "withdrawals"]
    credit_synonyms = ["credit", "deposit", "cr", "receipt", "in", "received", "deposits"]

    def normalize_col(val: str) -> str:
        return val.lower().strip().replace("_", "").replace(" ", "")

    # Look for header row within the first 20 rows
    header_row_idx = -1
    header_mapping: Dict[str, int] = {}

    for idx, row in enumerate(raw_rows[:20]):
        matches = 0
        temp_mapping: Dict[str, int] = {}
        for col_idx, col_val in enumerate(row):
            norm = normalize_col(col_val)
            if not norm:
                continue

            for syn in date_synonyms:
                if norm == syn:
                    temp_mapping["date"] = col_idx
                    matches += 1
                    break
            for syn in merchant_synonyms:
                if norm == syn:
                    temp_mapping["merchant"] = col_idx
                    matches += 1
                    break
            for syn in description_synonyms:
                if norm == syn:
                    temp_mapping["description"] = col_idx
                    matches += 1
                    break
            for syn in amount_synonyms:
                if norm == syn:
                    temp_mapping["amount"] = col_idx
                    matches += 1
                    break
            for syn in debit_synonyms:
                if norm == syn:
                    temp_mapping["debit"] = col_idx
                    matches += 1
                    break
            for syn in credit_synonyms:
                if norm == syn:
                    temp_mapping["credit"] = col_idx
                    matches += 1
                    break

            # Other optional columns mapping
            if norm in ["transactionid", "txnid", "id"]:
                temp_mapping["transaction_id"] = col_idx
            elif norm == "currency":
                temp_mapping["currency"] = col_idx
            elif norm in ["transactiontype", "type", "direction"]:
                temp_mapping["transaction_type"] = col_idx
            elif norm == "category":
                temp_mapping["category"] = col_idx
            elif norm == "source":
                temp_mapping["source"] = col_idx
            elif norm == "tags":
                temp_mapping["tags"] = col_idx

        if matches >= 2:
            header_row_idx = idx
            header_mapping = temp_mapping
            break

    # Fallback to row 0 if no header found
    if header_row_idx == -1:
        header_row_idx = 0
        row = raw_rows[0]
        for col_idx, col_val in enumerate(row):
            norm = normalize_col(col_val)
            for syn in date_synonyms:
                if syn in norm or norm in syn:
                    header_mapping["date"] = col_idx
                    break
            for syn in merchant_synonyms:
                if syn in norm or norm in syn:
                    header_mapping["merchant"] = col_idx
                    break
            for syn in description_synonyms:
                if syn in norm or norm in syn:
                    header_mapping["description"] = col_idx
                    break
            for syn in amount_synonyms:
                if syn in norm or norm in syn:
                    header_mapping["amount"] = col_idx
                    break
            for syn in debit_synonyms:
                if syn in norm or norm in syn:
                    header_mapping["debit"] = col_idx
                    break
            for syn in credit_synonyms:
                if syn in norm or norm in syn:
                    header_mapping["credit"] = col_idx
                    break

    # Required column presence checks
    if "date" not in header_mapping:
        logger.warning("Date column not detected in CSV headers. Mapping: %s", header_mapping)
        raise ValueError("Date column missing.")
    if "amount" not in header_mapping and "debit" not in header_mapping and "credit" not in header_mapping:
        logger.warning("Amount column not detected in CSV headers. Mapping: %s", header_mapping)
        raise ValueError("Amount column missing.")
    if "merchant" not in header_mapping and "description" not in header_mapping:
        logger.warning("Merchant column not detected in CSV headers. Mapping: %s", header_mapping)
        raise ValueError("Merchant column missing.")

    data_rows = raw_rows[header_row_idx + 1:]
    if not data_rows:
        logger.warning("No data rows found below header row in CSV file '%s'", file_path)
        raise ValueError("No transaction rows detected.")

    rows_extracted = len(data_rows)
    rows_validated = 0
    rows_rejected = 0

    for idx, row in enumerate(data_rows):
        # Skip completely blank lines
        if not row or not any(str(val).strip() for val in row):
            continue

        def get_cell(key: str) -> Any:
            col_idx = header_mapping.get(key)
            if col_idx is not None and col_idx < len(row):
                return row[col_idx]
            return None

        raw_date = get_cell("date")
        raw_merchant = get_cell("merchant")
        raw_desc = get_cell("description") or ""
        raw_amt = get_cell("amount")
        raw_debit = get_cell("debit")
        raw_credit = get_cell("credit")

        merchant = raw_merchant or raw_desc
        if not merchant or not str(merchant).strip():
            logger.warning("CSV row %d rejected: Merchant field is missing or empty (Field: merchant)", idx + header_row_idx + 2)
            rows_rejected += 1
            continue

        parsed_date = parse_date(str(raw_date) if raw_date is not None else None)
        if not parsed_date:
            logger.warning("CSV row %d rejected: Invalid/unparseable date '%s' (Field: date)", idx + header_row_idx + 2, raw_date)
            rows_rejected += 1
            continue

        amt = 0.0
        tx_type = "Debit"

        if raw_amt is not None and str(raw_amt).strip():
            amt = clean_amount(raw_amt)
            tx_type = str(get_cell("transaction_type") or "Debit")
        elif raw_debit is not None and str(raw_debit).strip():
            amt = abs(clean_amount(raw_debit))
            tx_type = "Debit"
        elif raw_credit is not None and str(raw_credit).strip():
            amt = abs(clean_amount(raw_credit))
            tx_type = "Credit"

        if amt <= 0:
            logger.warning("CSV row %d rejected: Amount must be positive, got '%s' (Field: amount)", idx + header_row_idx + 2, amt)
            rows_rejected += 1
            continue

        currency = str(get_cell("currency") or "INR")
        tx_id = str(get_cell("transaction_id") or "DRAFT")
        category = str(get_cell("category") or "")
        source = str(get_cell("source") or "CSV Statement")

        raw_tags = get_cell("tags") or ""
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
            logger.warning("CSV row %d rejected: Model validation error: %s (Field: Transaction model)", idx + header_row_idx + 2, str(e))
            rows_rejected += 1

    from backend.input_intelligence import utils
    utils._latest_stats["extracted"] = rows_extracted
    utils._latest_stats["validated"] = rows_validated
    utils._latest_stats["rejected"] = rows_rejected

    logger.info(
        "CSV Ingestion - Total Extracted: %d, Validated: %d, Rejected: %d",
        rows_extracted,
        rows_validated,
        rows_rejected,
    )
    return transactions
