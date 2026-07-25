import json
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, current_app, jsonify, request, send_from_directory
from flask_cors import CORS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.input_intelligence.models.transaction import Transaction
from backend.input_intelligence.parser import parse_input
from backend.routes.ai_routes import ai_bp
from backend.routes.analysis_routes import analysis_bp
from backend.routes.report_routes import report_bp
from backend.routes.upload_routes import upload_bp


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(PROJECT_ROOT / "frontend"), static_url_path="")
    app.config["PROJECT_ROOT"] = str(PROJECT_ROOT)
    app.config["UPLOAD_FOLDER"] = str(PROJECT_ROOT / "backend" / "uploads")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    app.extensions["subsense_state"] = {
        "results_store": {},
        "uploads_dir": Path(app.config["UPLOAD_FOLDER"]),
        "project_root": PROJECT_ROOT,
    }

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    CORS(app)

    app.register_blueprint(ai_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(upload_bp)

    @app.get("/api/health")
    def health() -> Any:
        return jsonify({"status": "ok", "service": "SubSence-AI backend"})

    @app.get("/api/endpoints")
    def endpoints() -> Any:
        return jsonify(
            {
                "health": "/api/health",
                "upload": "/api/upload",
                "analysis": "/api/analysis/<analysis_id>",
                "dashboard": "/api/dashboard",
                "ai": "/api/ai",
                "report": "/api/report",
            }
        )

    @app.route("/")
    def index() -> Any:
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/<path:path>")
    def static_file(path: str) -> Any:
        return send_from_directory(app.static_folder, path)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
