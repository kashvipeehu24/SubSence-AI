"""
Integration and E2E Tests for SubSense AI Input Ingestion and downstream modules.

Author: SubSense AI Team
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from reportlab.pdfgen import canvas

# Configure system path to import FINANCIAL modules without prefix errors
PROJECT_ROOT = Path(__file__).resolve().parents[3]
FINANCIAL_DIR = PROJECT_ROOT / "backend" / "FINANCIAL"
if str(FINANCIAL_DIR) not in sys.path:
    sys.path.insert(0, str(FINANCIAL_DIR))

# Now we can import the pipeline modules safely
from backend.app import create_app
from backend.input_intelligence.parser import parse_input
from backend.FINANCIAL.intelligence_engine import run_financial_intelligence
from backend.ai.financial_advisor import FinancialAdvisor
from backend.routes.upload_routes import _build_financial_analysis, _build_ai_response, _build_dashboard


class TestIntegrationPipeline(unittest.TestCase):
    """Integration test suite to verify CSV, JSON, and PDF parsed data

    interoperability with Financial Intelligence, AI Intelligence, and Dashboard.
    """

    def setUp(self) -> None:
        # Establish Flask application context
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Standard CSV content
        self.csv_content = (
            "transaction_id,merchant,amount,date,category,description,tags\n"
            "TXN101,Netflix India,649.00,2026-07-15,Video Streaming,Netflix Monthly,subscription,streaming\n"
            "TXN102,Spotify,119.00,16/07/2026,Music,Spotify Premium,music,streaming\n"
            "TXN103,Amazon,2499.00,2026-07-20,Shopping,Amazon Order,shopping\n"
        )
        # Standard JSON content
        self.json_content = json.dumps({
            "transactions": [
                {
                    "transaction_id": "TXN201",
                    "merchant": "Netflix India",
                    "amount": 649.00,
                    "date": "2026-07-15",
                    "description": "Netflix monthly subscription",
                    "currency": "INR",
                    "transaction_type": "Debit",
                    "tags": ["subscription"]
                },
                {
                    "transaction_id": "TXN202",
                    "merchant": "Spotify",
                    "amount": 119.00,
                    "date": "2026-07-18",
                    "description": "Spotify Premium",
                    "currency": "INR",
                    "transaction_type": "Debit",
                    "tags": ["subscription"]
                }
            ]
        })
        # Standard PDF statement lines
        self.pdf_lines = [
            "2026-07-15   Netflix India   INR 649.00 Debit   Netflix Monthly",
            "16/07/2026   Starbucks Coffee   250.00 Debit   Coffee Purchase",
        ]

    def create_temp_pdf(self, lines: list[str]) -> str:
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".pdf") as f:
            path = f.name
        c = canvas.Canvas(path)
        y = 750
        for line in lines:
            c.drawString(50, y, line)
            y -= 30
        c.save()
        return path

    @patch("backend.ai.gemini_client.GeminiClient")
    def test_e2e_pipeline_components(self, mock_gemini_client) -> None:
        # 1. Mock Gemini Client Response matching target ResponseSchema
        mock_instance = MagicMock()
        mock_instance.generate.return_value = json.dumps({
            "report_metadata": {
                "generated_at": "2026-07-25T12:00:00Z",
                "ai_model": "Gemini",
                "version": "1.0"
            },
            "financial_summary": {
                "overall_health": "Medium Risk (Grade B)",
                "summary": "Analysis completed successfully."
            },
            "financial_health_score_explanation": {
                "score": 78,
                "grade": "B",
                "reason": "Moderate spending on streaming and coffee subscriptions."
            },
            "monthly_summary": {
                "total_spent": 8450,
                "subscriptions": 1767,
                "potential_savings": 897
            },
            "yearly_summary": {
                "total_spent": 101400,
                "subscription_cost": 21204,
                "potential_savings": 10764
            },
            "duplicate_subscription_explanations": [],
            "price_hike_explanations": [],
            "recurring_subscription_explanations": [],
            "savings_suggestions": [],
            "action_items": ["Review recurring items"],
            "dashboard_recommendations": ["Review streaming options"]
        })
        mock_gemini_client.return_value = mock_instance

        # 2. Test Ingestion Parser - CSV File Ingestion
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv", encoding="utf-8") as f:
            f.write(self.csv_content)
            csv_path = f.name
        try:
            csv_txs = parse_input(csv_path, "csv")
            self.assertGreater(len(csv_txs), 0)
        finally:
            os.remove(csv_path)

        # 3. Test Ingestion Parser - JSON File Ingestion
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as f:
            f.write(self.json_content)
            json_path = f.name
        try:
            json_txs = parse_input(json_path, "json")
            self.assertGreater(len(json_txs), 0)
        finally:
            os.remove(json_path)

        # 4. Test Ingestion Parser - PDF Ingestion
        pdf_path = self.create_temp_pdf(self.pdf_lines)
        try:
            pdf_txs = parse_input(pdf_path, "pdf")
            self.assertGreater(len(pdf_txs), 0)
        finally:
            os.remove(pdf_path)

        # 5. Execute Financial Intelligence Layer
        tx_dicts = [tx.to_dict() for tx in csv_txs]
        fin_res = run_financial_intelligence(tx_dicts)
        self.assertIsInstance(fin_res, dict)
        self.assertIn("financial_health_score", fin_res)
        self.assertIn("recurring_subscriptions", fin_res)

        # 6. Execute AI Intelligence layer
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as f:
            json.dump(fin_res, f)
            temp_analysis_path = f.name

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as f:
            temp_ai_output_path = f.name

        try:
            advisor = FinancialAdvisor(client=mock_instance)
            ai_res = advisor.generate_ai_response(temp_analysis_path, temp_ai_output_path)
            self.assertIsInstance(ai_res, dict)
            self.assertIn("financial_summary", ai_res)
            self.assertIn("action_items", ai_res)
        finally:
            os.remove(temp_analysis_path)
            os.remove(temp_ai_output_path)

        # 7. Execute Dashboard Builder contract steps
        fin_analysis_dashboard = _build_financial_analysis(csv_txs)
        ai_resp_dashboard = _build_ai_response(fin_analysis_dashboard)
        dashboard = _build_dashboard(fin_analysis_dashboard, ai_resp_dashboard)
        self.assertIsInstance(dashboard, dict)
        self.assertIn("cards", dashboard)
        self.assertIn("subscriptions", dashboard)


if __name__ == "__main__":
    unittest.main()
