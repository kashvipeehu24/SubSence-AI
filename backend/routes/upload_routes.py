import json
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Blueprint, current_app, jsonify, request

from backend.input_intelligence.models.transaction import Transaction
from backend.input_intelligence.parser import parse_input

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

    source_type = "csv"
    suffix = save_path.suffix.lower()
    if suffix == ".json":
        source_type = "json"
    elif suffix == ".pdf":
        source_type = "pdf"
    elif suffix in {".txt", ".eml"}:
        source_type = "email"

    transactions: List[Transaction] = []
    if source_type == "json":
        with save_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        raw_transactions = payload.get("transactions", [])
        transactions = [Transaction.from_dict(item) for item in raw_transactions]
    else:
        transactions = parse_input(str(save_path), source_type)

    if not transactions:
        return jsonify({"error": "Unable to parse the uploaded file"}), 400

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
