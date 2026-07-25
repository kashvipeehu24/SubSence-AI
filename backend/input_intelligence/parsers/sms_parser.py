"""
SMS Ingestion Parser

Extracts transactions from raw SMS notification logs into Transaction objects.

Author: SubSense AI Team
"""

from __future__ import annotations

import re
from typing import List
from backend.input_intelligence.models.transaction import Transaction
from backend.input_intelligence.utils import clean_amount, parse_date


def parse_sms(text: str) -> List[Transaction]:
    """Parses raw SMS alerts into a list of draft Transaction objects.

    Each line of the text input represents a candidate SMS notification.

    Args:
        text: Raw SMS logs content string.

    Returns:
        List[Transaction]: Parsed draft transaction instances.
    """
    transactions: List[Transaction] = []
    if not text or not isinstance(text, str):
        return transactions

    # Regular expression patterns
    # 1. Date matches YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, or DD Mon YYYY
    date_pat = re.compile(
        r'(?:\b\d{4}-\d{2}-\d{2}\b|\b\d{2}[/\-]\d{2}[/\-]\d{4}\b|\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b)'
    )
    # 2. Currency Amount matches e.g. INR 500, Rs. 250, $20.00, ₹499
    amount_pat = re.compile(
        r'(?i)(?:INR|Rs\.?|USD|EUR|GBP|\$|₹|€|£)\s*([0-9,]+(?:\.[0-9]{2})?)'
    )
    # 3. Merchant matches string following 'at', 'paid to', 'spent at', or 'to' (with infinitive verb filtering)
    primary_merchant_pat = re.compile(
        r'(?i)\b(?:at|paid\s+to|spent\s+at|merchant:?)\s+([A-Za-z0-9\s\.\-\&]+?)(?=\s+(?:on|for|info|ref)\b|\s*[\.!,]|\s*$)'
    )
    fallback_merchant_pat = re.compile(
        r'(?i)\b(?:to)\s+(?!(?:confirm|notify|inform|verify|view|check|cancel|renew)\b)([A-Za-z0-9\s\.\-\&]+?)(?=\s+(?:on|for|info|ref)\b|\s*[\.!,]|\s*$)'
    )

    lines = text.splitlines()
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue

        # Extract amount, date, and merchant
        amt_match = amount_pat.search(line_str)
        date_match = date_pat.search(line_str)
        
        merchant_match = primary_merchant_pat.search(line_str)
        if not merchant_match:
            merchant_match = fallback_merchant_pat.search(line_str)

        if not amt_match or not date_match or not merchant_match:
            continue

        raw_amt = amt_match.group(0)
        raw_date = date_match.group(0)
        merchant_name = merchant_match.group(1).strip()

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
            source="SMS Alert",
            confidence_score=0.0,
            is_recurring_candidate=False,
            tags=[]
        )
        transactions.append(tx)

    return transactions
