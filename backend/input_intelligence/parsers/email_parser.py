"""
Email Statement Parser

Extracts transactions from raw email body strings.

Author: SubSense AI Team
"""

from __future__ import annotations

import re
from typing import List
from backend.input_intelligence.models.transaction import Transaction
from backend.input_intelligence.utils import clean_amount, parse_date


def parse_email(text: str) -> List[Transaction]:
    """Parses raw transaction email text alerts into a list of draft Transaction objects.

    Splits the body content into blocks or paragraphs, extracting candidate alerts.

    Args:
        text: Email text body string.

    Returns:
        List[Transaction]: Parsed draft transaction instances.
    """
    transactions: List[Transaction] = []
    if not text or not isinstance(text, str):
        return transactions

    # We use similar patterns as SMS alerts
    date_pat = re.compile(
        r'(?:\b\d{4}-\d{2}-\d{2}\b|\b\d{2}[/\-]\d{2}[/\-]\d{4}\b|\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b)'
    )
    amount_pat = re.compile(
        r'(?i)(?:INR|Rs\.?|USD|EUR|GBP|\$|₹|€|£)\s*([0-9,]+(?:\.[0-9]{2})?)'
    )
    primary_merchant_pat = re.compile(
        r'(?i)\b(?:at|paid\s+to|spent\s+at|merchant:?)\s+([A-Za-z0-9\s\.\-\&]+?)(?=\s+(?:on|for|info|ref)\b|\s*[\.!,]|\s*$)'
    )
    fallback_merchant_pat = re.compile(
        r'(?i)\b(?:to)\s+(?!(?:confirm|notify|inform|verify|view|check|cancel|renew)\b)([A-Za-z0-9\s\.\-\&]+?)(?=\s+(?:on|for|info|ref)\b|\s*[\.!,]|\s*$)'
    )

    # Clean paragraphs
    blocks = [b.strip() for b in re.split(r'\n{2,}', text) if b.strip()]
    if not blocks:
        # Fallback to lines if no paragraphs
        blocks = [line.strip() for line in text.splitlines() if line.strip()]

    for block in blocks:
        amt_match = amount_pat.search(block)
        date_match = date_pat.search(block)
        
        merchant_match = primary_merchant_pat.search(block)
        if not merchant_match:
            merchant_match = fallback_merchant_pat.search(block)

        if not amt_match or not date_match or not merchant_match:
            continue

        raw_amt = amt_match.group(0)
        raw_date = date_match.group(0)
        merchant_name = merchant_match.group(1).strip()

        parsed_amt = clean_amount(raw_amt)
        parsed_dt = parse_date(raw_date)

        if not parsed_dt or parsed_amt <= 0 or not merchant_name:
            continue

        # Email description is a single line preview of the block context
        description = block.splitlines()[0] if "\n" in block else block

        tx = Transaction(
            transaction_id="DRAFT",
            merchant=merchant_name,
            normalized_merchant="",
            amount=parsed_amt,
            currency="INR",
            transaction_type="Debit",
            date=parsed_dt,
            category="",
            description=description,
            source="Email Alert",
            confidence_score=0.0,
            is_recurring_candidate=False,
            tags=[]
        )
        transactions.append(tx)

    return transactions
