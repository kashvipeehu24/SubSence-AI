"""
Core Input Intelligence Orchestrator Pipeline

Implements the main parse_input function which orchestrates the entire validation,
parsing, normalization, categorization, tagging, confidence scoring, and deduplication
ingestion pipeline workflow.

Author: SubSense AI Team
"""

from __future__ import annotations

from typing import List
from backend.input_intelligence.models.transaction import Transaction
from backend.input_intelligence.validator import validate_upload
from backend.input_intelligence.parsers.csv_parser import parse_csv
from backend.input_intelligence.parsers.sms_parser import parse_sms
from backend.input_intelligence.parsers.email_parser import parse_email
from backend.input_intelligence.parsers.pdf_parser import parse_pdf
from backend.input_intelligence.processors.merchant_normalizer import normalize_merchant
from backend.input_intelligence.processors.categorizer import categorize_transaction
from backend.input_intelligence.processors.tag_generator import generate_tags
from backend.input_intelligence.processors.confidence import calculate_confidence
from backend.input_intelligence.processors.duplicate_detector import remove_duplicates
from backend.input_intelligence.utils import generate_transaction_id, is_empty


def parse_input(source: str, source_type: str) -> List[Transaction]:
    """Orchestrates the ingestion pipeline for statements or alert notifications.

    Workflow:
      1. Validate input source.
      2. Parse source text/file to get raw Transaction objects.
      3. Process transaction fields (Normalize merchant, Categorize, Tag, Confidence, Generate ID).
      4. Remove duplicate occurrences.
      5. Return unique processed Transactions list.

    Args:
        source: The file path (for CSV/PDF) or the raw text logs (for SMS/Email).
        source_type: One of 'csv', 'sms', 'email', 'pdf'.

    Returns:
        List[Transaction]: List of finalized, unique Transaction objects.

    Raises:
        ValueError: If source_type is not supported.
    """
    supported_types = {"csv", "sms", "email", "pdf"}
    if source_type not in supported_types:
        raise ValueError(f"Unsupported source type: {source_type}. Supported: {supported_types}")

    # 1. Validation Stage
    if source_type in {"csv", "pdf"}:
        # File-based validation
        val_res = validate_upload(source)
        if not val_res["valid"]:
            return []
    else:
        # String-based text validation
        if is_empty(source):
            return []

    # 2. Select and Execute Parsing Stage
    if source_type == "csv":
        drafts = parse_csv(source)
    elif source_type == "pdf":
        drafts = parse_pdf(source)
    elif source_type == "sms":
        drafts = parse_sms(source)
    else:
        drafts = parse_email(source)

    if not drafts:
        return []

    # 3. Post-Processing Pipeline Stage
    processed_txs: List[Transaction] = []
    for tx in drafts:
        # Resolve normalized merchant name
        tx.normalized_merchant = normalize_merchant(tx.merchant)

        # Resolve category based on normalized merchant and description
        tx.category = categorize_transaction(tx.normalized_merchant, tx.description)

        # Generate unique sorted tags list
        tx.tags = generate_tags(tx.normalized_merchant, tx.category, tx.description)

        # Calculate confidence score
        tx.confidence_score = calculate_confidence(tx)

        # Generate deterministic transaction ID if empty or missing
        if not tx.transaction_id or not tx.transaction_id.strip():
            tx.transaction_id = generate_transaction_id(
                tx.normalized_merchant,
                tx.amount,
                tx.date
            )

        processed_txs.append(tx)

    # 4. Deduplication Stage
    final_txs = remove_duplicates(processed_txs)

    return final_txs
