"""
Advanced OCR Statement Parser

Renders scanned PDFs to images using pypdfium2, registers HEIC support, pre-processes
low confidence images, runs PaddleOCR or EasyOCR engines, and parses transactions
from single-transaction screenshots or printed lists.

Author: SubSense AI Team
"""

from __future__ import annotations

import logging
import os
import re
import json
from typing import Any, Dict, List, Tuple
from PIL import Image

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

from backend.input_intelligence.models.transaction import Transaction
from backend.input_intelligence.utils import clean_amount, parse_date, clean_text
from backend.input_intelligence.processors.ocr_preprocessor import preprocess_image

logger = logging.getLogger(__name__)

# Global mock variable for unit tests to run without deep learning dependency downloads
_mock_ocr_result: str | None = None


def render_pdf_to_images(file_path: str) -> List[Image.Image]:
    """Renders PDF document pages to PIL images using pypdfium2.

    Args:
        file_path: Path to the PDF file.

    Returns:
        List[Image.Image]: A list of extracted page PIL Image objects.
    """
    images = []
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(file_path)
        for page in doc:
            bitmap = page.render(scale=2)
            images.append(bitmap.to_pil())
    except Exception as e:
        logger.error("Failed to render scanned PDF pages using pypdfium2: %s", str(e))
    return images


def run_raw_ocr(img: Image.Image) -> Tuple[str, float]:
    """Invokes PaddleOCR or EasyOCR engines on the PIL Image.

    Args:
        img: The PIL Image object.

    Returns:
        Tuple[str, float]: Combined extracted string text and the average confidence score.
    """
    global _mock_ocr_result
    if _mock_ocr_result is not None:
        logger.info("OCR Parser: Injecting mocked test OCR result")
        return _mock_ocr_result, 0.95

    import numpy as np
    img_np = np.array(img)
    text_blocks = []
    confidences = []

    # 1. Primary Engine: PaddleOCR
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        result = ocr.ocr(img_np, cls=True)
        if result and result[0]:
            for line in result[0]:
                text = line[1][0]
                conf = line[1][1]
                text_blocks.append(text)
                confidences.append(conf)
            combined_text = "\n".join(text_blocks)
            avg_conf = sum(confidences) / len(confidences) if confidences else 1.0
            return combined_text, avg_conf
    except ImportError:
        pass
    except Exception as e:
        logger.warning("PaddleOCR primary scan failed: %s. Trying fallback...", str(e))

    # 2. Fallback Engine: EasyOCR
    try:
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False)
        result = reader.readtext(img_np)
        if result:
            for _, text, conf in result:
                text_blocks.append(text)
                confidences.append(conf)
            combined_text = "\n".join(text_blocks)
            avg_conf = sum(confidences) / len(confidences) if confidences else 1.0
            return combined_text, avg_conf
    except ImportError:
        pass
    except Exception as e:
        logger.warning("EasyOCR fallback scan failed: %s", str(e))

    logger.error("Both PaddleOCR and EasyOCR are not installed. OCR ingestion failed.")
    raise RuntimeError("PaddleOCR and EasyOCR are not installed. OCR scanning is unavailable.")


def ocr_image(img: Image.Image) -> str:
    """Extracts text from a PIL image, applying enhancement pre-processors if confidence is low.

    Args:
        img: The PIL Image object.

    Returns:
        str: Extracted text block.
    """
    text, conf = run_raw_ocr(img)
    logger.info("Initial OCR scan completed. Confidence: %.2f", conf)

    if conf < 0.6:
        logger.info("OCR confidence is low (%.2f < 0.6). Executing PIL preprocessing enhancement filters...", conf)
        enhanced_img = preprocess_image(img)
        text, conf_enhanced = run_raw_ocr(enhanced_img)
        logger.info("Enhanced OCR scan completed. Confidence: %.2f", conf_enhanced)

    return text


def parse_ocr_text(text: str) -> List[Transaction]:
    """Parses raw OCR extracted text string into structured transaction records.

    Heuristically differentiates between single-transaction screenshots and multi-transaction lists.

    Args:
        text: Raw text string block.

    Returns:
        List[Transaction]: List of draft Transaction objects.
    """
    transactions: List[Transaction] = []
    if not text or not text.strip():
        return transactions

    # Regular expressions for date and amount signatures
    date_pat = re.compile(
        r'(?:\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b|\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}\b)'
    )
    amount_pat = re.compile(
        r'(?i)(?:INR|Rs\.?|USD|EUR|GBP|\$|₹|€|£)?\s*\b([0-9,]+\.[0-9]{2})\b'
    )
    amount_pat_general = re.compile(
        r'(?i)(?:INR|Rs\.?|USD|EUR|GBP|\$|₹|€|£)?\s*\b([0-9,]+)\b'
    )

    all_dates = date_pat.findall(text)
    all_amounts = []

    # Map amount values
    for m in amount_pat.finditer(text):
        all_amounts.append((m.group(0), clean_amount(m.group(0))))
    if not all_amounts:
        for m in amount_pat_general.finditer(text):
            val = clean_amount(m.group(0))
            if val > 1.0:  # Ignore small indexes, page numbers, or noise
                all_amounts.append((m.group(0), val))

    # 1. Single-Transaction Screenshot (PhonePe, Google Pay, Paytm, screenshot)
    if len(all_dates) <= 2 and len(all_amounts) <= 2:
        logger.info("OCR Parser: Classified as Single-Transaction Screenshot")
        if not all_dates or not all_amounts:
            logger.warning("Single transaction screenshot missing date or amount parameters.")
            return transactions

        # Pick the largest amount matched as the main transaction amount
        raw_amt, amt = max(all_amounts, key=lambda x: x[1])
        raw_date = all_dates[0]
        parsed_date = parse_date(raw_date)

        if not parsed_date or amt <= 0:
            logger.warning("Single transaction parsing failed: Invalid date '%s' or amount '%.2f'", raw_date, amt)
            return transactions

        # Heuristic merchant name lookup
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        merchant_name = ""

        merchant_labels = re.compile(
            r'(?i)\b(?:paid\s+to|transfer\s+to|spent\s+at|to|merchant:?|payment\s+to|sent\s+to)\b'
        )

        for idx, line in enumerate(lines):
            if merchant_labels.search(line):
                # Check inline merchant name
                inline_match = re.search(
                    r'(?i)\b(?:paid\s+to|transfer\s+to|spent\s+at|to|merchant:?|payment\s+to|sent\s+to)\s+([A-Za-z0-9\s\.\-\&]+)',
                    line
                )
                if inline_match and clean_text(inline_match.group(1)):
                    merchant_name = clean_text(inline_match.group(1))
                    break
                # Check subsequent line
                if idx + 1 < len(lines):
                    candidate = clean_text(lines[idx + 1])
                    if (
                        candidate
                        and not date_pat.search(candidate)
                        and not amount_pat_general.search(candidate)
                        and len(candidate) > 2
                    ):
                        merchant_name = candidate
                        break

        # Fallback to the first capitalized text row that is not status noise
        if not merchant_name:
            noise_words = {
                "successful", "completed", "paid", "received", "transaction", "payment",
                "bank", "date", "amount", "debit", "credit", "phonepe", "paytm",
                "google pay", "gpay", "transfer"
            }
            for line in lines:
                cleaned = clean_text(line)
                cleaned_lower = cleaned.lower()
                if (
                    len(cleaned) > 2
                    and not any(char.isdigit() for char in cleaned)
                    and not any(w in cleaned_lower for w in noise_words)
                ):
                    merchant_name = cleaned
                    break
            if not merchant_name and lines:
                merchant_name = lines[0]

        if merchant_name:
            # Strip noise prefixes/suffixes
            merchant_name = re.sub(
                r'(?i)\b(?:phonepe|paytm|gpay|google\s+pay|successful|completed|rs\.?|inr)\b',
                "",
                merchant_name
            )
            merchant_name = clean_text(merchant_name)

        if not merchant_name:
            merchant_name = "Unknown Merchant"

        tx = Transaction(
            transaction_id="DRAFT",
            merchant=merchant_name,
            normalized_merchant="",
            amount=amt,
            currency="INR",
            transaction_type="Debit",
            date=parsed_date,
            category="",
            description=text.replace("\n", " ")[:200],
            source="Screenshot Ingestion",
            confidence_score=0.0,
            is_recurring_candidate=False,
            tags=[]
        )
        transactions.append(tx)
        logger.info("Extracted screenshot transaction: Merchant='%s', Amt=%.2f, Date='%s'", merchant_name, amt, parsed_date)

    # 2. Multi-Transaction List (Printed statements)
    else:
        logger.info("OCR Parser: Classified as Multi-Transaction List (Printed Statement)")
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            line_str = line.strip()
            if not line_str:
                continue

            date_match = date_pat.search(line_str)
            amt_match = amount_pat.search(line_str) or amount_pat_general.search(line_str)

            if not date_match or not amt_match:
                continue

            raw_date = date_match.group(0)
            raw_amt = amt_match.group(0)

            # Strip identifiers to parse merchant name from remaining tokens
            rem_text = line_str.replace(raw_date, "").replace(raw_amt, "")
            parts = [p.strip() for p in re.split(r'\s{2,}', rem_text) if p.strip()]

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
            parsed_amt = abs(clean_amount(raw_amt))
            parsed_dt = parse_date(raw_date)

            if not parsed_dt or parsed_amt <= 0 or not merchant_name:
                continue

            tx_type = "Debit"
            if re.search(r'(?i)\b(?:credit|cr|deposit|receipt|received|in)\b', line_str):
                tx_type = "Credit"

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
                source="Printed Statement Ingestion",
                confidence_score=0.0,
                is_recurring_candidate=False,
                tags=[]
            )
            transactions.append(tx)

    return transactions


def parse_ocr(file_path: str, file_type: str) -> List[Transaction]:
    """Entry point for parsing scanned PDFs and Image files using OCR.

    Args:
        file_path: Absolute path to the statement file.
        file_type: File format classification (e.g. 'pdf' or raw image extension like 'png').

    Returns:
        List[Transaction]: List of draft Transaction objects.
    """
    images: List[Image.Image] = []
    if file_type == "pdf":
        logger.info("OCR Parser: Converting scanned PDF pages '%s' to images", file_path)
        images = render_pdf_to_images(file_path)
    else:
        logger.info("OCR Parser: Opening image file '%s'", file_path)
        try:
            img = Image.open(file_path)
            images.append(img)
        except Exception as e:
            logger.error("Failed to open image file '%s': %s", file_path, str(e))
            raise ValueError("Unsupported statement format.")

    if not images:
        logger.error("No pages or images resolved for file '%s'", file_path)
        raise ValueError("No transaction rows detected.")

    full_ocr_text = []
    for idx, img in enumerate(images):
        try:
            text = ocr_image(img)
            if text:
                full_ocr_text.append(text)
        except Exception as e:
            logger.error("OCR scan execution failed on page/image %d: %s", idx + 1, str(e))
            raise ValueError("OCR failure.")

    combined_text = "\n".join(full_ocr_text)
    if not combined_text.strip():
        logger.error("OCR Parser: No readable text extracted from file '%s'.", file_path)
        raise ValueError("Unreadable image.")

    transactions = parse_ocr_text(combined_text)

    # Store in the shared container for Gemini fallback
    from backend.input_intelligence import utils
    utils._latest_extracted_text = combined_text

    # Close PIL images to prevent ResourceWarnings
    for img in images:
        try:
            img.close()
        except Exception:
            pass

    # Register statistics
    from backend.input_intelligence import utils
    utils._latest_stats["extracted"] = len(images)
    utils._latest_stats["validated"] = len(transactions)
    utils._latest_stats["rejected"] = 0

    return transactions
