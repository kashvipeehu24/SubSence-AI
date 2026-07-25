from typing import Any, Dict

from flask import Blueprint, current_app, jsonify

report_bp = Blueprint("report", __name__)


def _get_store() -> Dict[str, Any]:
    return current_app.extensions["subsense_state"]["results_store"]


@report_bp.get("/api/dashboard")
def get_dashboard() -> Any:
    latest = None
    if _get_store():
        latest = list(_get_store().values())[-1]
    if not latest:
        return jsonify({"error": "No analysis available"}), 404
    return jsonify(latest["dashboard"])


@report_bp.get("/api/report")
def get_report() -> Any:
    latest = None
    if _get_store():
        latest = list(_get_store().values())[-1]
    if not latest:
        return jsonify({"error": "No analysis available"}), 404
    return jsonify({"analysis_id": latest["analysis_id"], "dashboard": latest["dashboard"]})
