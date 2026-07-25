from typing import Any, Dict

from flask import Blueprint, current_app, jsonify

ai_bp = Blueprint("ai", __name__)


def _get_store() -> Dict[str, Any]:
    return current_app.extensions["subsense_state"]["results_store"]


@ai_bp.get("/api/ai")
def get_ai() -> Any:
    latest = None
    if _get_store():
        latest = list(_get_store().values())[-1]
    if not latest:
        return jsonify({"error": "No analysis available"}), 404
    return jsonify(latest["ai_response"])
