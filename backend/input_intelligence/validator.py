"""
Validator Utility for Input Intelligence

Provides validation helper functions to check file existence, extension,
file size, CSV/PDF/text structures, and overall upload validation.

Author: SubSense AI Team
"""

from __future__ import annotations

import csv
import os
from typing import Any, Dict
from PyPDF2 import PdfReader


def validate_file_exists(path: str) -> Dict[str, Any]:
    """Validates if a file exists at the given path."""
    if not path or not isinstance(path, str):
        return {"valid": False, "errors": ["Invalid file path type."], "warnings": []}
    if not os.path.exists(path):
        return {"valid": False, "errors": [f"File does not exist: {path}"], "warnings": []}
    if not os.path.isfile(path):
        return {"valid": False, "errors": [f"Path is not a file: {path}"], "warnings": []}
    return {"valid": True, "errors": [], "warnings": []}


def validate_extension(path: str) -> Dict[str, Any]:
    """Validates if the file has a supported extension (.csv, .pdf, .txt)."""
    if not path or not isinstance(path, str):
        return {"valid": False, "errors": ["Invalid file path type."], "warnings": []}
    _, ext = os.path.splitext(path.lower())
    supported = {".csv", ".pdf", ".txt"}
    if ext not in supported:
        return {
            "valid": False,
            "errors": [f"Unsupported file extension '{ext}'. Supported: {', '.join(supported)}"],
            "warnings": []
        }
    return {"valid": True, "errors": [], "warnings": []}


def validate_file_size(path: str, max_size_mb: float = 10.0) -> Dict[str, Any]:
    """Validates that the file size does not exceed the specified limit in megabytes."""
    exists_res = validate_file_exists(path)
    if not exists_res["valid"]:
        return exists_res
    try:
        size_bytes = os.path.getsize(path)
        size_mb = size_bytes / (1024 * 1024)
        if size_mb > max_size_mb:
            return {
                "valid": False,
                "errors": [f"File size ({size_mb:.2f} MB) exceeds limit of {max_size_mb} MB."],
                "warnings": []
            }
        return {"valid": True, "errors": [], "warnings": []}
    except OSError as e:
        return {"valid": False, "errors": [f"Failed to read file size: {str(e)}"], "warnings": []}


def validate_csv(path: str) -> Dict[str, Any]:
    """Validates if the file is a structurally valid CSV file."""
    exists_res = validate_file_exists(path)
    if not exists_res["valid"]:
        return exists_res
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            rows = []
            for i, row in enumerate(reader):
                rows.append(row)
                if i >= 9:
                    break
        if not rows:
            return {"valid": False, "errors": ["CSV file is empty."], "warnings": []}
        num_cols = len(rows[0])
        if num_cols == 0:
            return {"valid": False, "errors": ["CSV header contains no columns."], "warnings": []}
        warnings = []
        for idx, r in enumerate(rows):
            if len(r) != num_cols:
                warnings.append(f"Inconsistent column count at row {idx + 1}. Expected {num_cols}, got {len(r)}.")
        return {"valid": True, "errors": [], "warnings": warnings}
    except (csv.Error, UnicodeDecodeError, IOError) as e:
        return {"valid": False, "errors": [f"Invalid CSV structure: {str(e)}"], "warnings": []}


def validate_pdf(path: str) -> Dict[str, Any]:
    """Validates if the file is a structurally valid PDF file."""
    exists_res = validate_file_exists(path)
    if not exists_res["valid"]:
        return exists_res
    try:
        with open(path, "rb") as f:
            reader = PdfReader(f)
            num_pages = len(reader.pages)
            f.seek(0)
            header = f.read(5)
            if header != b"%PDF-":
                return {"valid": False, "errors": ["File does not have a valid PDF header."], "warnings": []}
        warnings = []
        if num_pages == 0:
            warnings.append("PDF contains 0 pages.")
        return {"valid": True, "errors": [], "warnings": warnings}
    except Exception as e:
        return {"valid": False, "errors": [f"Invalid PDF structure or corrupted: {str(e)}"], "warnings": []}


def validate_text(path: str) -> Dict[str, Any]:
    """Validates if the file is a valid decodable plain text file."""
    exists_res = validate_file_exists(path)
    if not exists_res["valid"]:
        return exists_res
    try:
        with open(path, "r", encoding="utf-8") as f:
            f.read(1024 * 1024)  # Read up to 1MB
        return {"valid": True, "errors": [], "warnings": []}
    except (UnicodeDecodeError, IOError) as e:
        return {"valid": False, "errors": [f"Invalid text file or decoding error: {str(e)}"], "warnings": []}


def validate_upload(path: str) -> Dict[str, Any]:
    """Performs comprehensive validation checks on an upload file."""
    res = validate_file_exists(path)
    if not res["valid"]:
        return res
    ext_res = validate_extension(path)
    if not ext_res["valid"]:
        return ext_res
    size_res = validate_file_size(path, max_size_mb=10)
    if not size_res["valid"]:
        return size_res
    _, ext = os.path.splitext(path.lower())
    if ext == ".csv":
        type_res = validate_csv(path)
    elif ext == ".pdf":
        type_res = validate_pdf(path)
    elif ext == ".txt":
        type_res = validate_text(path)
    else:
        type_res = {"valid": False, "errors": [f"Unsupported extension: {ext}"], "warnings": []}
    warnings = ext_res.get("warnings", []) + size_res.get("warnings", []) + type_res.get("warnings", [])
    return {
        "valid": type_res["valid"],
        "errors": type_res.get("errors", []),
        "warnings": warnings
    }
