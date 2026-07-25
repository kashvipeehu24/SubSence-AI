"""
End-to-End Integration Pipeline Tests.

Tests CSV, JSON, TXT, XLS, XLSX, Digital PDF, Scanned PDF, Images, screenshots
(PhonePe, GPay, Paytm, Bank), blank images, password PDFs, corrupted PDFs,
and oversized uploads, verifying the full backend pipeline to HTTP 200 / 400.

Author: SubSense AI Team
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from PIL import Image, ImageDraw

from backend.app import create_app
from backend.input_intelligence.parsers.ocr_parser import _mock_ocr_result
import backend.input_intelligence.parsers.ocr_parser as ocr_parser


class TestE2EPipeline(unittest.TestCase):
    """End-to-End test suite verifying statement ingestion to dashboard output."""

    def setUp(self) -> None:
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

        # Clean mock OCR
        ocr_parser._mock_ocr_result = None

        # Build bulletproof direct module mock injection
        self.mock_client_cls = MagicMock()
        self.mock_instance = self.mock_client_cls.return_value
        self.mock_instance.generate.side_effect = None
        self.mock_instance.generate.return_value = json.dumps({
            "transactions": [
                {
                    "date": "2026-07-15",
                    "merchant": "Netflix India",
                    "amount": 649.00,
                    "currency": "INR",
                    "category": "Entertainment",
                    "description": "Streaming Service"
                }
            ]
        })

        # Save and inject mock into all modules loaded under any gemini_client path
        self.saved_originals = {}
        for key, mod in list(sys.modules.items()):
            if "gemini_client" in key:
                if hasattr(mod, "GeminiClient"):
                    self.saved_originals[key] = mod.GeminiClient
                    mod.GeminiClient = self.mock_client_cls

    def tearDown(self) -> None:
        # Restore original classes
        for key, orig in self.saved_originals.items():
            if key in sys.modules:
                sys.modules[key].GeminiClient = orig
        ocr_parser._mock_ocr_result = None
        self.ctx.pop()

    def _create_reportlab_pdf(self, path: str, text: str) -> None:
        from reportlab.pdfgen import canvas
        c = canvas.Canvas(path)
        c.drawString(100, 750, text)
        c.save()

    def _create_password_pdf(self, path: str) -> None:
        from reportlab.pdfgen import canvas
        from PyPDF2 import PdfReader, PdfWriter
        temp_pdf = path + ".temp.pdf"
        c = canvas.Canvas(temp_pdf)
        c.drawString(100, 750, "Protected Document Content")
        c.save()

        reader = PdfReader(temp_pdf)
        writer = PdfWriter()
        writer.add_page(reader.pages[0])
        writer.encrypt("secret_pass")
        with open(path, "wb") as f:
            writer.write(f)
        try:
            os.remove(temp_pdf)
        except Exception:
            pass

    def _create_excel(self, path: str) -> None:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Date", "Merchant", "Amount"])
        ws.append(["2026-07-15", "Netflix India", 649.00])
        ws.append(["16-07-2026", "Starbucks Coffee", 250.00])
        wb.save(path)

    def _create_mock_image(self, format: str) -> io.BytesIO:
        # Create non-blank mock image with high pixel variance
        img = Image.new("RGB", (300, 300), color="white")
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 250, 250], fill="blue")
        buf = io.BytesIO()
        img.save(buf, format=format)
        buf.seek(0)
        return buf

    # --- SUCCESS CASES (HTTP 200) ---

    def test_e2e_valid_csv(self) -> None:
        self.mock_instance.generate.side_effect = None
        csv_data = (
            "date,merchant,amount\n"
            "2026-07-15,Netflix India,649.00\n"
            "2026-07-16,Starbucks,250.00\n"
        )
        response = self.client.post(
            "/api/upload",
            data={"file": (io.BytesIO(csv_data.encode("utf-8")), "statement.csv")}
        )
        self.assertEqual(response.status_code, 200)
        res_json = response.get_json()
        self.assertEqual(res_json["status"], "ok")
        self.assertIn("analysis_id", res_json)
        self.assertEqual(res_json["transaction_count"], 2)

    def test_e2e_valid_json(self) -> None:
        self.mock_instance.generate.side_effect = None
        json_data = {
            "transactions": [
                {"date": "2026-07-15", "merchant": "Netflix India", "amount": 649.00},
                {"date": "2026-07-16", "merchant": "Starbucks Coffee", "amount": 250.00}
            ]
        }
        response = self.client.post(
            "/api/upload",
            data={"file": (io.BytesIO(json.dumps(json_data).encode("utf-8")), "statement.json")}
        )
        self.assertEqual(response.status_code, 200)
        res_json = response.get_json()
        self.assertEqual(res_json["status"], "ok")

    def test_e2e_valid_txt(self) -> None:
        self.mock_instance.generate.side_effect = None
        txt_data = (
            "Dear customer, Rs. 649.00 spent at Netflix India on 2026-07-15.\n"
            "Dear customer, Rs. 250.00 spent at Starbucks on 16/07/2026.\n"
        )
        response = self.client.post(
            "/api/upload",
            data={"file": (io.BytesIO(txt_data.encode("utf-8")), "statement.txt")}
        )
        self.assertEqual(response.status_code, 200)
        res_json = response.get_json()
        self.assertEqual(res_json["status"], "ok")

    def test_e2e_valid_xlsx(self) -> None:
        self.mock_instance.generate.side_effect = None
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".xlsx") as tmp:
            self._create_excel(tmp.name)
            path = tmp.name
        try:
            with open(path, "rb") as f:
                response = self.client.post(
                    "/api/upload",
                    data={"file": (f, "statement.xlsx")}
                )
            self.assertEqual(response.status_code, 200)
            res_json = response.get_json()
            self.assertEqual(res_json["status"], "ok")
        finally:
            os.remove(path)

    def test_e2e_valid_digital_pdf(self) -> None:
        self.mock_instance.generate.side_effect = None
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".pdf") as tmp:
            self._create_reportlab_pdf(tmp.name, "2026-07-15 Netflix India 649.00")
            path = tmp.name
        try:
            with open(path, "rb") as f:
                response = self.client.post(
                    "/api/upload",
                    data={"file": (f, "statement.pdf")}
                )
            self.assertEqual(response.status_code, 200)
            res_json = response.get_json()
            self.assertEqual(res_json["status"], "ok")
        finally:
            os.remove(path)

    def test_e2e_scanned_pdf_ocr(self) -> None:
        self.mock_instance.generate.side_effect = None
        ocr_parser._mock_ocr_result = (
            "STATEMENT OF ACCOUNT\n"
            "2026-07-15 Netflix India 649.00\n"
            "16-07-2026 Starbucks 250.00\n"
        )
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".pdf") as tmp:
            self._create_reportlab_pdf(tmp.name, " ")
            path = tmp.name
        try:
            with open(path, "rb") as f:
                response = self.client.post(
                    "/api/upload",
                    data={"file": (f, "scanned.pdf")}
                )
            self.assertEqual(response.status_code, 200)
        finally:
            os.remove(path)

    def test_e2e_image_formats_png_jpeg_webp_heic(self) -> None:
        self.mock_instance.generate.side_effect = None
        ocr_parser._mock_ocr_result = (
            "PhonePe successful payment\n"
            "Paid to Netflix India\n"
            "₹649.00\n"
            "Date: 2026-07-15"
        )
        for ext in [".png", ".jpg", ".webp", ".heic"]:
            img_buf = self._create_mock_image("PNG" if ext != ".heic" else "JPEG")
            response = self.client.post(
                "/api/upload",
                data={"file": (img_buf, f"photo{ext}")}
            )
            self.assertEqual(response.status_code, 200, f"Failed for image format {ext}")
            res_json = response.get_json()
            self.assertEqual(res_json["status"], "ok")

    def test_e2e_screenshots_phonepe_gpay_paytm_bank(self) -> None:
        self.mock_instance.generate.side_effect = None
        screenshots = [
            ("PhonePe Paid to Netflix ₹649.00 Successful 2026-07-15", "phonepe.png"),
            ("Google Pay Sent ₹250.00 Completed Starbucks 2026-07-16", "gpay.png"),
            ("Paytm Received Rs. 1500.00 Credit from Employer 17-07-2026", "paytm.png"),
            ("HDFC Bank Transfer ₹2500.00 to Rent Landlord 18/07/2026", "hdfc.png")
        ]
        for mock_text, filename in screenshots:
            ocr_parser._mock_ocr_result = mock_text
            img_buf = self._create_mock_image("PNG")
            response = self.client.post(
                "/api/upload",
                data={"file": (img_buf, filename)}
            )
            self.assertEqual(response.status_code, 200, f"Failed for screenshot {filename}")
            res_json = response.get_json()
            self.assertEqual(res_json["status"], "ok")

    # --- FALLBACK GEMINI TEST CASES (HTTP 200) ---

    def test_e2e_gemini_fallback_trigger_success(self) -> None:
        self.mock_instance.generate.side_effect = None
        self.mock_instance.generate.return_value = json.dumps({
            "transactions": [
                {
                    "date": "2026-07-15",
                    "merchant": "Gemini Fallback Ltd",
                    "amount": 1250.00,
                    "currency": "INR",
                    "category": "Technology",
                    "description": "API Ingestion Fallback"
                }
            ]
        })

        unstructured_log = "Statement logs: Fallback payment made, we transfer total of Rs 1250 to Gemini Fallback Ltd on July 15."
        
        response = self.client.post(
            "/api/upload",
            data={"file": (io.BytesIO(unstructured_log.encode("utf-8")), "unstructured.txt")}
        )
        self.assertEqual(response.status_code, 200)
        res_json = response.get_json()
        self.assertEqual(res_json["status"], "ok")
        self.assertEqual(res_json["transaction_count"], 1)

    # --- ERROR CASES (HTTP 400) ---

    def test_e2e_blank_image(self) -> None:
        self.mock_instance.generate.side_effect = None
        # Solid white square = blank standard deviation 0.0
        img = Image.new("RGB", (100, 100), color="white")
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".png") as tmp:
            img.save(tmp, format="PNG")
            path = tmp.name
        try:
            with open(path, "rb") as f:
                response = self.client.post(
                    "/api/upload",
                    data={"file": (f, "blank.png")}
                )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.get_json()["error"], "Blank image.")
        finally:
            os.remove(path)

    def test_e2e_unreadable_image(self) -> None:
        self.mock_instance.generate.side_effect = None
        ocr_parser._mock_ocr_result = "   \n  \n  "  # empty text
        img_buf = self._create_mock_image("PNG")
        response = self.client.post(
            "/api/upload",
            data={"file": (img_buf, "noise.png")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Unreadable image.")

    def test_e2e_ocr_failure(self) -> None:
        # Mock OCR parser throwing library error
        with patch("backend.input_intelligence.parsers.ocr_parser.ocr_image", side_effect=ValueError("OCR failure.")):
            img_buf = self._create_mock_image("PNG")
            response = self.client.post(
                "/api/upload",
                data={"file": (img_buf, "image.png")}
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.get_json()["error"], "OCR failure.")

    def test_e2e_gemini_fallback_failure(self) -> None:
        # Mock Gemini throwing API exception during fallback
        self.mock_instance.generate.side_effect = RuntimeError("Quota exceeded.")

        # Unstructured txt log (fails deterministic SMS/Email parser)
        unstructured_log = "Unstructured log transfer Rs 1250 on July 15."

        response = self.client.post(
            "/api/upload",
            data={"file": (io.BytesIO(unstructured_log.encode("utf-8")), "fallback_fail.txt")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Gemini failure.")

    def test_e2e_password_pdf(self) -> None:
        self.mock_instance.generate.side_effect = None
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".pdf") as tmp:
            self._create_password_pdf(tmp.name)
            path = tmp.name
        try:
            with open(path, "rb") as f:
                response = self.client.post(
                    "/api/upload",
                    data={"file": (f, "protected.pdf")}
                )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.get_json()["error"], "Password-protected PDF.")
        finally:
            os.remove(path)

    def test_e2e_corrupted_pdf(self) -> None:
        self.mock_instance.generate.side_effect = None
        corrupted_data = b"Some random garbage binary data not pdf content"
        response = self.client.post(
            "/api/upload",
            data={"file": (io.BytesIO(corrupted_data), "corrupted.pdf")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Corrupted PDF.")

    def test_e2e_invalid_csv_date_missing(self) -> None:
        self.mock_instance.generate.side_effect = None
        csv_data = "merchant,amount\nNetflix,649.00\n"
        response = self.client.post(
            "/api/upload",
            data={"file": (io.BytesIO(csv_data.encode("utf-8")), "invalid.csv")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Date column missing.")

    def test_e2e_oversized_upload(self) -> None:
        self.mock_instance.generate.side_effect = None
        large_data = b"x" * (11 * 1024 * 1024)
        response = self.client.post(
            "/api/upload",
            data={"file": (io.BytesIO(large_data), "huge_statement.csv")}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("exceeds limit of 10 MB", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
