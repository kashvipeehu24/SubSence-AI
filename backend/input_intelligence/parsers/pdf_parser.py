"""
PDF Statement Parser

Extracts text blocks from transaction PDF statements and parses them into Transaction objects.

Author: SubSense AI Team
"""

from __future__ import annotations

import os
import re
from typing import List
from PyPDF2 import PdfReader
from backend.input_intelligence.models.transaction import Transaction
from backend.input_intelligence.utils import clean_amount, parse_date, clean_text


def parse_pdf(file_path: str) -> List[Transaction]:
    """Parses a transaction PDF statement into a list of draft Transaction objects.

    Args:
        file_path: Absolute path to the PDF statement file.

    Returns:
        List[Transaction]: Parsed draft transaction instances.
    """
    transactions: List[Transaction] = []
    if not file_path or not isinstance(file_path, str) or not os.path.exists(file_path):
        return transactions

    # Regular expression patterns
    date_pat = re.compile(
        r'(?:\b\d{4}-\d{2}-\d{2}\b|\b\d{2}[/\-]\d{2}[/\-]\d{4}\b|\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b)'
    )
    amount_pat = re.compile(
        r'(?i)(?:INR|Rs\.?|USD|EUR|GBP|\$|₹|€|£)?\s*([0-9,]+\.[0-9]{2})\b'
    )

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

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Check if line contains both date and amount
            date_match = date_pat.search(line_str)
            amt_match = amount_pat.search(line_str)

            if not date_match or not amt_match:
                continue

            raw_date = date_match.group(0)
            raw_amt = amt_match.group(0)

            # Strip date and amount from the line to locate the merchant/description
            rem_text = line_str.replace(raw_date, "").replace(raw_amt, "")
            
            # Split by double or more spaces, or tabs, to separate columns
            parts = [p.strip() for p in re.split(r'\s{2,}', rem_text) if p.strip()]
            
            # Filter noise from columns to locate the merchant
            merchant_parts = []
            for part in parts:
                cleaned_part = re.sub(r'(?i)\b(?:INR|Rs\.?|USD|EUR|GBP|\$|₹|€|£|debit|credit|dr|cr|txn|id|ref)\b', "", part)
                cleaned_part = clean_text(cleaned_part)
                if cleaned_part:
                    merchant_parts.append(cleaned_part)

            merchant_name = merchant_parts[0] if merchant_parts else ""
            parsed_amt = clean_amount(raw_amt)
            parsed_dt = parse_date(raw_date)

            if not parsed_dt or parsed_amt <= 0 or not merchant_name:
                continue

            tx = Transaction(
                transaction_id="DRAFT",
                merchant=merchant_name,
                normalized_merchant="",
                amount=parsed_amt,
                currency="INR",
                transaction_type="Debit",
                date=parsed_dt,
                category="",
                description=line_str,
                source="PDF Statement",
                confidence_score=0.0,
                is_recurring_candidate=False,
                tags=[]
            )
            transactions.append(tx)
    except Exception:
        pass

    return transactions
