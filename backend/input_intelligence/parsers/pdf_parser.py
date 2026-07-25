"""
PDF Statement Parser

Extracts text blocks from transaction PDF statements and parses them into Transaction objects.

Author: SubSense AI Team
"""

from __future__ import annotations

import logging
import os
import re
from typing import List
from PyPDF2 import PdfReader
from backend.input_intelligence.models.transaction import Transaction
from backend.input_intelligence.utils import clean_amount, parse_date, clean_text

logger = logging.getLogger(__name__)


def parse_pdf(file_path: str) -> List[Transaction]:
    """Parses a transaction PDF statement into a list of draft Transaction objects.

    Args:
        file_path: Absolute path to the PDF statement file.

    Returns:
        List[Transaction]: Parsed draft transaction instances.
    """
    transactions: List[Transaction] = []
    if not file_path or not isinstance(file_path, str) or not os.path.exists(file_path):
        logger.error("PDF file path does not exist or is invalid: %s", file_path)
        return transactions

    # Regular expression patterns
    # Matches dates: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, or DD Mon YYYY
    date_pat = re.compile(
        r'(?:\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b|\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}\b)'
    )

    # Matches amounts prefixed with currency symbols or having decimal places
    amount_pat_decimal = re.compile(
        r'(?i)(?:INR|Rs\.?|USD|EUR|GBP|\$|₹|€|£)\s*([0-9,]+(?:\.[0-9]{1,2})?)\b|([0-9,]+\.[0-9]{2})\b'
    )

    # General number fallback matching (any integer or float)
    amount_pat_general = re.compile(
        r'\b([0-9,]+(?:\.[0-9]{1,2})?)\b'
    )

    rows_extracted = 0
    rows_validated = 0
    rows_rejected = 0

    try:
        # Extract text using PyPDF2
        text_content = []
        with open(file_path, "rb") as f:
            reader = PdfReader(f)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)

        full_text = "\n".join(text_content)
        lines = full_text.splitlines()
        rows_extracted = len(lines)

        for line_idx, line in enumerate(lines):
            line_str = line.strip()
            if not line_str:
                continue

            # 1. Search for Date first to prevent year confusion
            date_match = date_pat.search(line_str)
            if not date_match:
                # Silent skip for random non-transaction document text lines
                continue

            raw_date = date_match.group(0)

            # Strip date from line to search for amount safely
            rem_line = line_str.replace(raw_date, "")

            # 2. Search for Amount in the remaining text
            amt_match = amount_pat_decimal.search(rem_line) or amount_pat_general.search(rem_line)
            if not amt_match:
                logger.warning(
                    "PDF Line %d rejected: Date found ('%s'), but no amount detected (Field: amount). Line: '%s'",
                    line_idx + 1, raw_date, line_str
                )
                rows_rejected += 1
                continue

            raw_amt = amt_match.group(0)

            # 3. Strip date and amount from the line to locate the merchant/description
            rem_text = rem_line.replace(raw_amt, "")

            # Split by double or more spaces, or tabs, to separate columns
            parts = [p.strip() for p in re.split(r'\s{2,}', rem_text) if p.strip()]

            # Filter noise from columns to locate the merchant
            merchant_parts = []
            for part in parts:
                cleaned_part = re.sub(
                    r'(?i)\b(?:INR|Rs\.?|USD|EUR|GBP|\$|₹|€|£|debit|credit|dr|cr|txn|id|ref|payment|deposit|withdrawal)\b',
                    "",
                    part
                )
                cleaned_part = clean_text(cleaned_part)
                if cleaned_part:
                    merchant_parts.append(cleaned_part)

            merchant_name = merchant_parts[0] if merchant_parts else ""
            if not merchant_name:
                logger.warning(
                    "PDF Line %d rejected: Could not extract merchant/description name (Field: merchant). Line: '%s'",
                    line_idx + 1, line_str
                )
                rows_rejected += 1
                continue

            parsed_amt = abs(clean_amount(raw_amt))
            parsed_dt = parse_date(raw_date)

            if not parsed_dt:
                logger.warning(
                    "PDF Line %d rejected: Unparseable date format '%s' (Field: date). Line: '%s'",
                    line_idx + 1, raw_date, line_str
                )
                rows_rejected += 1
                continue

            if parsed_amt <= 0:
                logger.warning(
                    "PDF Line %d rejected: Amount must be positive, got '%s' (Field: amount). Line: '%s'",
                    line_idx + 1, parsed_amt, line_str
                )
                rows_rejected += 1
                continue

            # Determine transaction type from line contents
            tx_type = "Debit"
            if re.search(r'(?i)\b(?:credit|cr|deposit|receipt|received|in)\b', line_str):
                tx_type = "Credit"

            try:
                tx = Transaction(
                    transaction_id="DRAFT",
                    merchant=merchant_name,
                    normalized_merchant="",
                    amount=parsed_amt,
                    currency="INR",
                    transaction_type=tx_type,
                    date=parsed_dt,
                    category="",
                    description=line_str,
                    source="PDF Statement",
                    confidence_score=0.0,
                    is_recurring_candidate=False,
                    tags=[]
                )
                transactions.append(tx)
                rows_validated += 1
            except Exception as e:
                logger.warning(
                    "PDF Line %d rejected: Model validation error: %s (Field: Transaction model). Line: '%s'",
                    line_idx + 1, str(e), line_str
                )
                rows_rejected += 1

    except Exception as e:
        logger.error("Error parsing PDF statement: %s", str(e))

    from backend.input_intelligence import utils
    utils._latest_extracted_text = full_text if 'full_text' in locals() else ""
    utils._latest_stats["extracted"] = rows_extracted
    utils._latest_stats["validated"] = rows_validated
    utils._latest_stats["rejected"] = rows_rejected

    logger.info(
        "PDF Ingestion - Total Extracted: %d, Validated: %d, Rejected: %d",
        rows_extracted,
        rows_validated,
        rows_rejected,
    )
    return transactions
