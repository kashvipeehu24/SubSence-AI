from typing import Any, Dict

from flask import Blueprint, current_app, jsonify

analysis_bp = Blueprint("analysis", __name__)


def _get_store() -> Dict[str, Any]:
    return current_app.extensions["subsense_state"]["results_store"]


@analysis_bp.get("/api/analysis/<analysis_id>")
def get_analysis(analysis_id: str) -> Any:
    result = _get_store().get(analysis_id)
    if not result:
        return jsonify({"error": "Analysis not found"}), 404
    return jsonify(result)
