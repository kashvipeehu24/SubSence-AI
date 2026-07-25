import json
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Blueprint, current_app, jsonify, request

from backend.input_intelligence.models.transaction import Transaction
from backend.input_intelligence.parser import parse_input
from backend.input_intelligence.utils import detect_mime_type

upload_bp = Blueprint("upload", __name__)


def _get_state() -> Dict[str, Any]:
    return current_app.extensions["subsense_state"]


def _get_upload_dir() -> Path:
    return Path(current_app.config["UPLOAD_FOLDER"])


def _load_json_file(filename: str) -> Optional[Dict[str, Any]]:
    path = Path(current_app.config["PROJECT_ROOT"]) / "sample_json" / filename
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_financial_analysis(transactions: List[Transaction]) -> Dict[str, Any]:
    sample = _load_json_file("financial_analysis.json") or {}
    financial_analysis = json.loads(json.dumps(sample)) if sample else {
        "analysis_metadata": {"generated_at": "", "currency": "INR", "analysis_period": {"start_date": "", "end_date": ""}},
        "financial_health": {"score": 78, "grade": "B", "risk_level": "Medium"},
        "spending_summary": {"monthly_spending": 0, "yearly_spending": 0, "subscription_spending_monthly": 0, "subscription_spending_yearly": 0},
        "category_breakdown": [],
        "recurring_subscriptions": [],
        "duplicate_subscriptions": [],
        "price_hikes": [],
        "potential_savings": {"monthly": 0, "yearly": 0},
        "recommendations": [],
    }

    total_spend = round(sum(tx.amount for tx in transactions), 2)
    financial_analysis.setdefault("analysis_metadata", {})["generated_at"] = ""
    financial_analysis.setdefault("spending_summary", {})["monthly_spending"] = total_spend
    financial_analysis["spending_summary"]["yearly_spending"] = round(total_spend * 12, 2)

    if transactions:
        recurring = []
        for tx in transactions:
            if tx.amount >= 100:
                recurring.append(
                    {
                        "merchant": tx.normalized_merchant or tx.merchant,
                        "monthly_cost": round(float(tx.amount), 2),
                        "annual_cost": round(float(tx.amount) * 12, 2),
                        "billing_cycle": "Monthly",
                    }
                )
        financial_analysis["recurring_subscriptions"] = recurring

        financial_analysis["potential_savings"] = {
            "monthly": round(total_spend * 0.18, 2),
            "yearly": round(total_spend * 0.18 * 12, 2),
        }
        financial_analysis["recommendations"] = [
            "Cancel duplicate or overlapping subscriptions.",
            "Review recurring charges that may be underused.",
            "Monitor recent subscription price increases.",
        ]

    return financial_analysis


def _build_ai_response(financial_analysis: Dict[str, Any]) -> Dict[str, Any]:
    sample = _load_json_file("ai_response.json")
    if sample:
        return sample

    return {
        "financial_summary": {
            "overall_health": f"{financial_analysis['financial_health']['risk_level']} ({financial_analysis['financial_health']['grade']})",
            "summary": "AI insights are ready for review.",
        },
        "dashboard_recommendations": financial_analysis.get("recommendations", []),
        "action_items": ["Review recurring subscriptions", "Check duplicate services"],
    }


def _build_dashboard(financial_analysis: Dict[str, Any], ai_response: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "user": {"name": "Demo User"},
        "financial_health": financial_analysis.get("financial_health", {}),
        "cards": {
            "monthly_spending": financial_analysis.get("spending_summary", {}).get("monthly_spending", 0),
            "yearly_spending": financial_analysis.get("spending_summary", {}).get("yearly_spending", 0),
            "monthly_savings": financial_analysis.get("potential_savings", {}).get("monthly", 0),
            "yearly_savings": financial_analysis.get("potential_savings", {}).get("yearly", 0),
        },
        "charts": {"category_breakdown": financial_analysis.get("category_breakdown", [])},
        "subscriptions": financial_analysis.get("recurring_subscriptions", []),
        "duplicate_subscriptions": financial_analysis.get("duplicate_subscriptions", []),
        "price_hikes": financial_analysis.get("price_hikes", []),
        "recommendations": financial_analysis.get("recommendations", []),
        "action_items": ai_response.get("action_items", []),
    }


@upload_bp.post("/api/upload")
def upload() -> Any:
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    uploaded = request.files["file"]
    if uploaded.filename == "":
        return jsonify({"error": "No file selected"}), 400

    upload_dir = _get_upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)
    save_path = upload_dir / uploaded.filename
    uploaded.save(save_path)

    source_type = detect_mime_type(str(save_path))
    # Standardize Excel classifications
    if source_type == "zip":
        source_type = "excel"
    
    supported_formats = {
        "csv", "sms", "email", "pdf", "json", "excel",
        "png", "jpeg", "jpg", "webp", "heic", "xls", "xlsx"
    }
    
    if source_type not in supported_formats:
        # Suffix-based fallback if magic signatures fail (e.g. unknown format)
        suffix = save_path.suffix.lower()
        if suffix == ".json":
            source_type = "json"
        elif suffix == ".pdf":
            source_type = "pdf"
        elif suffix in {".xlsx", ".xls"}:
            source_type = "excel"
        elif suffix in {".txt", ".eml"}:
            source_type = "email"
        elif suffix in {".png", ".jpeg", ".jpg", ".webp", ".heic"}:
            source_type = suffix[1:]
        else:
            source_type = "csv"

    import logging
    logger = logging.getLogger(__name__)

    try:
        transactions = parse_input(str(save_path), source_type)
    except ValueError as e:
        err_msg = str(e)
        logger.error("Parsing failed: %s", err_msg)
        
        specific_errors = {
            "blank image.",
            "unreadable image.",
            "corrupted pdf.",
            "password-protected pdf.",
            "ocr failure.",
            "gemini failure.",
            "no transaction rows detected.",
            "date column missing.",
            "amount column missing.",
            "merchant column missing."
        }
        if err_msg.lower() in specific_errors or "exceeds limit" in err_msg.lower():
            return jsonify({"error": err_msg}), 400
            
        if "no transaction rows" in err_msg.lower():
            return jsonify({"error": "No transaction rows detected."}), 400
        return jsonify({"error": "Unable to parse uploaded file"}), 400
    except Exception as e:
        logger.error("Unexpected error in upload pipeline: %s", str(e))
        return jsonify({"error": "Unable to parse uploaded file"}), 400

    if not transactions:
        return jsonify({"error": "No transaction rows detected."}), 400

    financial_analysis = _build_financial_analysis(transactions)
    ai_response = _build_ai_response(financial_analysis)
    dashboard = _build_dashboard(financial_analysis, ai_response)

    analysis_id = uuid.uuid4().hex
    state = _get_state()
    state["results_store"][analysis_id] = {
        "analysis_id": analysis_id,
        "file_name": uploaded.filename,
        "transactions": [tx.to_dict() for tx in transactions],
        "financial_analysis": financial_analysis,
        "ai_response": ai_response,
        "dashboard": dashboard,
    }

    return jsonify(
        {
            "analysis_id": analysis_id,
            "status": "ok",
            "file_name": uploaded.filename,
            "transaction_count": len(transactions),
        }
    )
