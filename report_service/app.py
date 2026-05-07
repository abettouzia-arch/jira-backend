"""
Report Service for Jira DC → Cloud migration analysis.

Generates structured migration reports from compatibility matrices.
"""

import logging
import os
import sys

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=wrong-import-position
from report_service.generators.json_export import export_report_to_json
from report_service.generators.pdf_export import export_report_to_pdf
from report_service.generators.report_builder import build_report
from shared.repositories.compatibility_repository import CompatibilityRepository
from shared.repositories.report_repository import ReportRepository

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "report_service"}), 200


@app.route("/reports/generate", methods=["POST"])
def generate_report():
    """
    Generate a report from a compatibility matrix.

    Body:
      { "matrix_id": "xxx" }
    or
      { "analysis_id": "xxx" }
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    matrix = _load_matrix(data)

    if not matrix:
        return jsonify({
            "error": "No compatibility matrix found for provided identifier."
        }), 404

    try:
        report = build_report(matrix)
    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.error("Report generation failed: %s", error)
        return jsonify({"error": f"Report generation failed: {error}"}), 500

    try:
        report_repo = ReportRepository()
        report_repo.insert_report({**report})
        logger.info("Report %s saved to MongoDB.", report["report_id"])
    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.warning("Could not save report to MongoDB: %s", error)

    report.pop("_id", None)
    return jsonify(report), 200


@app.route("/reports/<report_id>", methods=["GET"])
def get_report(report_id):
    """Retrieve a generated report by report_id."""
    try:
        report_repo = ReportRepository()
        report = report_repo.get_report_by_id(report_id)

        if not report:
            return jsonify({"error": f"Report '{report_id}' not found."}), 404

        report.pop("_id", None)
        return jsonify(report), 200

    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.error("Error retrieving report: %s", error)
        return jsonify({"error": str(error)}), 500


@app.route("/reports", methods=["GET"])
def list_reports():
    """List generated reports with summary only."""
    try:
        report_repo = ReportRepository()
        reports = report_repo.list_reports()

        return jsonify({"reports": reports, "count": len(reports)}), 200

    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.error("Error listing reports: %s", error)
        return jsonify({"error": str(error)}), 500


@app.route("/reports/<report_id>/json", methods=["GET"])
def export_json(report_id):
    """Export a report as JSON file."""
    report_repo = ReportRepository()
    report = report_repo.get_report_by_id(report_id)

    if not report:
        return jsonify({"error": f"Report '{report_id}' not found."}), 404

    report.pop("_id", None)
    file_path = export_report_to_json(report)
    return send_file(file_path, as_attachment=True)


@app.route("/reports/<report_id>/pdf", methods=["GET"])
def export_pdf(report_id):
    """Export a report as PDF file."""
    report_repo = ReportRepository()
    report = report_repo.get_report_by_id(report_id)

    if not report:
        return jsonify({"error": f"Report '{report_id}' not found."}), 404

    report.pop("_id", None)
    file_path = export_report_to_pdf(report)
    return send_file(file_path, as_attachment=True)


def _load_matrix(data: dict) -> dict | None:
    """
    Load a compatibility matrix by matrix_id or latest matrix for analysis_id.
    """
    compatibility_repo = CompatibilityRepository()

    if data.get("matrix_id"):
        return compatibility_repo.get_matrix_by_id(data["matrix_id"])

    if data.get("analysis_id"):
        return compatibility_repo.get_latest_matrix_by_analysis_id(data["analysis_id"])

    return None


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5004))
    app.run(host="0.0.0.0", port=port, debug=True)
