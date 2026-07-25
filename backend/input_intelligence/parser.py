"""
Core Input Intelligence Orchestrator Pipeline

Implements the main parse_input function which orchestrates the entire validation,
parsing, normalization, categorization, tagging, confidence scoring, and deduplication
ingestion pipeline workflow.

Author: SubSense AI Team
"""

from __future__ import annotations

import logging
import os
from typing import List
from backend.input_intelligence.models.transaction import Transaction
from backend.input_intelligence.validator import validate_upload
from backend.input_intelligence.parsers.csv_parser import parse_csv
from backend.input_intelligence.parsers.json_parser import parse_json
from backend.input_intelligence.parsers.excel_parser import parse_excel
from backend.input_intelligence.parsers.sms_parser import parse_sms
from backend.input_intelligence.parsers.email_parser import parse_email
from backend.input_intelligence.parsers.pdf_parser import parse_pdf
from backend.input_intelligence.parsers.ocr_parser import parse_ocr
from backend.input_intelligence.processors.merchant_normalizer import normalize_merchant
from backend.input_intelligence.processors.categorizer import categorize_transaction
from backend.input_intelligence.processors.tag_generator import generate_tags
from backend.input_intelligence.processors.confidence import calculate_confidence
from backend.input_intelligence.processors.duplicate_detector import remove_duplicates
from backend.input_intelligence.utils import generate_transaction_id, is_empty, _latest_stats, clean_amount, parse_date

logger = logging.getLogger(__name__)


def is_scanned_pdf(file_path: str) -> bool:
    """Helper to detect if a PDF contains only scanned images (no text)."""
    try:
        from PyPDF2 import PdfReader
        with open(file_path, "rb") as f:
            reader = PdfReader(f)
            text = ""
            for page in reader.pages[:5]:
                t = page.extract_text()
                if t:
                    text += t
            return len(text.strip()) < 10
    except Exception:
        return True


def run_gemini_fallback(raw_text: str) -> List[Transaction]:
    """Uses Gemini API as a fallback to extract structured transactions from unstructured text.

    Args:
        raw_text: Unstructured text data.

    Returns:
        List[Transaction]: List of draft Transaction objects.
    """
    from backend.ai.gemini_client import GeminiClient
    import json
    from backend.input_intelligence import utils

    try:
        client = GeminiClient()
    except Exception as e:
        logger.error("Failed to initialize GeminiClient for fallback: %s", str(e))
        raise ValueError("Gemini failure.")

    prompt = f"""
    You are an expert financial statement parsing tool.
    Extract all transaction records from the unstructured text below.

    UNSTRUCTURED TEXT:
    \"\"\"
    {raw_text}
    \"\"\"

    You MUST return a JSON object containing a "transactions" key with a list of transaction objects.
    Each transaction object must conform to the following schema:
    {{
      "date": "YYYY-MM-DD",
      "merchant": "Merchant Name",
      "amount": 0.00,
      "currency": "INR",
      "category": "Optional Category",
      "description": "Short description"
    }}

    Rules:
    1. Extract every transaction.
    2. Ensure the "amount" is a positive number.
    3. Ensure the "date" matches format "YYYY-MM-DD". If the year is missing or ambiguous, use "2026". If the date is completely missing, default to "2026-07-26".
    4. If currency is not specified, default to "INR".
    5. Output ONLY the raw JSON block. No markdown wrappers, comments, or extra text.
    """

    try:
        raw_res = client.generate(prompt)
        cleaned = raw_res.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        data = json.loads(cleaned)
        tx_list = data.get("transactions", [])
        if not isinstance(tx_list, list):
            raise ValueError("Transactions is not a list.")
    except Exception as e:
        logger.error("Gemini failed to extract transactions: %s", str(e))
        raise ValueError("Gemini failure.")

    drafts = []
    for idx, item in enumerate(tx_list):
        if not isinstance(item, dict):
            continue

        merchant = item.get("merchant", "")
        raw_date = item.get("date", "")
        amount_val = item.get("amount", 0.0)

        amt = abs(clean_amount(amount_val))
        parsed_date = parse_date(str(raw_date)) or "2026-07-26"

        if not merchant or amt <= 0:
            logger.warning("Gemini row %d skipped: invalid merchant or amount", idx + 1)
            continue

        tx = Transaction(
            transaction_id="DRAFT",
            merchant=str(merchant).strip(),
            normalized_merchant="",
            amount=amt,
            currency=str(item.get("currency", "INR")).strip(),
            transaction_type="Debit",
            date=parsed_date,
            category=str(item.get("category", "")).strip(),
            description=str(item.get("description", "")).strip() or str(merchant).strip(),
            source="Gemini Fallback Ingestion",
            confidence_score=0.0,
            is_recurring_candidate=False,
            tags=[]
        )
        drafts.append(tx)

    utils._latest_stats["extracted"] = len(tx_list)
    utils._latest_stats["validated"] = len(drafts)
    utils._latest_stats["rejected"] = len(tx_list) - len(drafts)

    return drafts


def parse_input(source: str, source_type: str) -> List[Transaction]:
    """Orchestrates the ingestion pipeline for statements or alert notifications.

    Workflow:
      1. Validate input source.
      2. Parse source text/file to get raw Transaction objects.
      3. Process transaction fields (Normalize merchant, Categorize, Tag, Confidence, Generate ID).
      4. Remove duplicate occurrences.
      5. Return unique processed Transactions list.

    Args:
        source: The file path (for CSV/PDF/JSON/Excel/Images) or the raw text logs (for SMS/Email).
        source_type: One of 'csv', 'sms', 'email', 'pdf', 'json', 'excel', 'png', 'jpeg', 'jpg', 'webp', 'heic', 'xls', 'xlsx'.

    Returns:
        List[Transaction]: List of finalized, unique Transaction objects.

    Raises:
        ValueError: If source_type is not supported or parsing fails.
    """
    supported_types = {
        "csv", "sms", "email", "pdf", "json", "excel",
        "png", "jpeg", "jpg", "webp", "heic", "xls", "xlsx"
    }
    if source_type not in supported_types:
        logger.error("Unsupported source type: %s", source_type)
        raise ValueError("Unsupported statement format.")

    # Reset metrics container
    _latest_stats["extracted"] = 0
    _latest_stats["validated"] = 0
    _latest_stats["rejected"] = 0

    from backend.input_intelligence import utils
    utils._latest_extracted_text = ""

    parser_names = {
        "csv": "CSV Parser",
        "json": "JSON Parser",
        "excel": "Excel Parser",
        "pdf": "PDF Text Parser",
        "scanned_pdf": "PDF OCR Parser",
        "sms": "SMS Parser",
        "email": "Email Parser",
        "png": "Image OCR Parser",
        "jpeg": "Image OCR Parser",
        "jpg": "Image OCR Parser",
        "webp": "Image OCR Parser",
        "heic": "Image OCR Parser",
        "xls": "Excel Parser",
        "xlsx": "Excel Parser",
    }
    selected_parser = parser_names.get(source_type, "Unknown Parser")
    logger.info("Starting parsing pipeline for source type '%s' using '%s'", source_type, selected_parser)

    # 1. Validation Stage
    if source_type in {"csv", "pdf", "json", "excel", "png", "jpeg", "jpg", "webp", "heic", "xls", "xlsx"}:
        val_res = validate_upload(source)
        if not val_res["valid"]:
            err_msg = val_res["errors"][0] if val_res["errors"] else "Validation failed."
            logger.error("Validation failed for %s statement '%s': %s", source_type, source, err_msg)
            # Re-raise specific error messages so routes can map them directly
            raise ValueError(err_msg)
    else:
        # String-based text validation
        text_content = source
        if os.path.exists(source) and os.path.isfile(source):
            with open(source, "r", encoding="utf-8", errors="ignore") as f:
                text_content = f.read()
        if is_empty(text_content):
            logger.warning("SMS/Email text input is empty")
            raise ValueError("No transaction rows detected.")

    # 2. Select and Execute Parsing Stage
    drafts: List[Transaction] = []
    parsing_error: Exception | None = None

    try:
        if source_type == "csv":
            drafts = parse_csv(source)
        elif source_type == "pdf":
            if is_scanned_pdf(source):
                logger.info("PDF '%s' identified as scanned. Routing to OCR Ingestion.", source)
                selected_parser = "PDF OCR Parser"
                drafts = parse_ocr(source, "pdf")
            else:
                logger.info("PDF '%s' identified as text. Routing to standard PDF Ingestion.", source)
                drafts = parse_pdf(source)
        elif source_type in {"png", "jpeg", "jpg", "webp", "heic"}:
            drafts = parse_ocr(source, source_type)
        elif source_type in {"excel", "xls", "xlsx"}:
            drafts = parse_excel(source)
        elif source_type == "json":
            drafts = parse_json(source)
        elif source_type == "sms":
            text_content = source
            if os.path.exists(source) and os.path.isfile(source):
                with open(source, "r", encoding="utf-8", errors="ignore") as f:
                    text_content = f.read()
            drafts = parse_sms(text_content)
            _latest_stats["extracted"] = len(drafts)
            _latest_stats["validated"] = len(drafts)
            _latest_stats["rejected"] = 0
            utils._latest_extracted_text = text_content
        else:
            text_content = source
            if os.path.exists(source) and os.path.isfile(source):
                with open(source, "r", encoding="utf-8", errors="ignore") as f:
                    text_content = f.read()
            drafts = parse_email(text_content)
            _latest_stats["extracted"] = len(drafts)
            _latest_stats["validated"] = len(drafts)
            _latest_stats["rejected"] = 0
            utils._latest_extracted_text = text_content
    except Exception as e:
        parsing_error = e

    # Compute average confidence score
    avg_conf = 0.0
    if drafts:
        confs = [calculate_confidence(tx) for tx in drafts]
        avg_conf = sum(confs) / len(confs)

    # 3. Check for Fallback condition
    trigger_fallback = (
        (parsing_error is not None or not drafts or avg_conf < 0.5)
        and source_type in {"pdf", "png", "jpeg", "jpg", "webp", "heic", "txt", "eml", "sms", "email"}
    )

    if trigger_fallback and utils._latest_extracted_text and utils._latest_extracted_text.strip():
        logger.warning(
            "Deterministic parsing failed or returned low confidence (Avg: %.2f). Executing Gemini Fallback Parser...",
            avg_conf
        )
        try:
            drafts = run_gemini_fallback(utils._latest_extracted_text)
            selected_parser = "Gemini Fallback Parser"
            parsing_error = None
        except Exception as exc:
            logger.error("Gemini Fallback Ingestion failed: %s", str(exc))
            if parsing_error:
                raise parsing_error
            raise ValueError("Gemini failure.")

    if parsing_error:
        raise parsing_error

    if not drafts:
        logger.warning("No transactions could be parsed from the source '%s'", source)
        raise ValueError("No transaction rows detected.")

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

        # Generate deterministic transaction ID if empty, missing, or set to fallback DRAFT
        if not tx.transaction_id or not tx.transaction_id.strip() or tx.transaction_id == "DRAFT":
            tx.transaction_id = generate_transaction_id(
                tx.normalized_merchant,
                tx.amount,
                tx.date
            )

        processed_txs.append(tx)

    # 4. Deduplication Stage
    final_txs = remove_duplicates(processed_txs)

    # Log ingestion statistics
    logger.info(
        "Ingestion Pipeline Summary:\n"
        "-------------------------------------\n"
        "  Selected Parser:          %s\n"
        "  Detected File Type:       %s\n"
        "  Rows Extracted:           %d\n"
        "  Rows Validated:           %d\n"
        "  Rows Rejected:            %d\n"
        "  Final Transaction Count:  %d\n"
        "-------------------------------------",
        selected_parser,
        source_type,
        _latest_stats["extracted"],
        _latest_stats["validated"],
        _latest_stats["rejected"],
        len(final_txs)
    )

    return final_txs
