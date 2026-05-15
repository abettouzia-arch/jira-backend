"""
API Gateway service for Jira Migration backend.
Provides authentication and routing to backend microservices.
"""

import logging
import os
import sys
from datetime import timedelta

from dotenv import load_dotenv
from flasgger import Swagger
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import create_access_token, jwt_required
import requests

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=wrong-import-position
from shared.core.config import Config
from shared.core.errors import register_error_handlers
from shared.core.extensions import jwt, mongo
from shared.core.logger import setup_logger

logger = logging.getLogger(__name__)

WORKER_URL = os.getenv("WORKER_URL", "http://worker:5005")
REPORT_SERVICE_URL = os.getenv("REPORT_SERVICE_URL", "http://report_service:5004")
REQUEST_TIMEOUT = 180


def create_app():
    """Create and configure the API Gateway Flask application."""
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}}) #, supports_credentials=True

    app.config["MONGO_URI"] = Config.MONGO_URI
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=8)

    mongo.init_app(app)
    jwt.init_app(app)

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "JiraMigration API Gateway",
            "description": "API Gateway with JWT Authentication",
            "version": "1.0.0",
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Enter token with Bearer prefix: Bearer <token>",
            }
        },
    }
    Swagger(app, template=swagger_template)

    setup_logger(app)
    register_error_handlers(app)

    user_credentials = {
        "email": "admin@test.com",
        "password": "1234",
    }

    @app.route("/api/health", methods=["GET"])
    def health():
        """Gateway health check."""
        return jsonify({"status": "ok", "service": "gateway"}), 200

    @app.route("/api/login", methods=["POST"])
    def login():
        """
        User login endpoint.
        """
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        if (
            data.get("email") == user_credentials["email"]
            and data.get("password") == user_credentials["password"]
        ):
            token = create_access_token(identity=data["email"])
            return jsonify({"token": token}), 200

        return jsonify({"error": "Invalid credentials"}), 401

    @app.route("/api/analyze", methods=["POST"])
    @jwt_required()
    def analyze():
        """
        Trigger full analysis pipeline through Worker.

        Expects multipart/form-data:
          file=<zip/xml/json/sql>
        """
        if "file" not in request.files:
            return jsonify({"error": "File is required."}), 400

        uploaded_file = request.files["file"]

        if not uploaded_file.filename:
            return jsonify({"error": "Uploaded file must have a filename."}), 400

        try:
            url = f"{WORKER_URL.rstrip('/')}/worker/jobs/run"

            data = uploaded_file.read()
            logger.info(
                "Forwarding file to worker: filename=%s size=%s content_type=%s",
                uploaded_file.filename,
                len(data),
                uploaded_file.content_type,
            )
            files = {
                "file": (
                    uploaded_file.filename,
                    data,
                    uploaded_file.content_type,
                )
            }

            response = requests.post(
                url,
                files=files,
                timeout=REQUEST_TIMEOUT,
            )

            return jsonify(response.json()), response.status_code

        except requests.exceptions.RequestException as error:
            logger.error("Worker request failed: %s", error)
            return jsonify({"error": f"Worker request failed: {error}"}), 502

        except ValueError as error:
            logger.error("Invalid Worker response: %s", error)
            return jsonify({"error": "Invalid response from Worker service."}), 502

    @app.route("/api/jobs/<job_id>", methods=["GET"])
    @jwt_required()
    def get_job(job_id):
        """Get worker job status."""
        try:
            url = f"{WORKER_URL.rstrip('/')}/worker/jobs/{job_id}"
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            return jsonify(response.json()), response.status_code

        except requests.exceptions.RequestException as error:
            logger.error("Worker job status request failed: %s", error)
            return jsonify({"error": f"Worker request failed: {error}"}), 502

    @app.route("/api/jobs", methods=["GET"])
    @jwt_required()
    def list_jobs():
        """List worker jobs."""
        try:
            limit = request.args.get("limit", 50)
            url = f"{WORKER_URL.rstrip('/')}/worker/jobs?limit={limit}"
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            return jsonify(response.json()), response.status_code

        except requests.exceptions.RequestException as error:
            logger.error("Worker jobs request failed: %s", error)
            return jsonify({"error": f"Worker request failed: {error}"}), 502

    @app.route("/api/reports/<report_id>", methods=["GET"])
    @jwt_required()
    def get_report(report_id):
        """Proxy report retrieval."""
        try:
            url = f"{REPORT_SERVICE_URL.rstrip('/')}/reports/{report_id}"
            response = requests.get(url, timeout=REQUEST_TIMEOUT)

            # Vérifier si la requête a réussi avant de parser le JSON
            if response.status_code != 200:
                try:
                    return jsonify(response.json()), response.status_code
                except ValueError:
                    error_message = "Rapport non trouvé ou erreur du service"
                    return jsonify({"error": error_message}), response.status_code

            return jsonify(response.json()), response.status_code

        except requests.exceptions.RequestException as error:
            logger.error("Report request failed: %s", error)
            return jsonify({"error": f"Report request failed: {error}"}), 502

    @app.route("/api/reports", methods=["GET"])
    @jwt_required()
    def list_reports():
        """List all generated reports."""
        try:
            url = f"{REPORT_SERVICE_URL.rstrip('/')}/reports"
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            return jsonify(response.json()), response.status_code
        except requests.exceptions.RequestException as error:
            logger.error("List reports failed: %s", error)
            return jsonify({"error": f"Report request failed: {error}"}), 502

    @app.route("/api/reports/generate", methods=["POST"])
    @jwt_required()
    def generate_report():
        """Generate a report from matrix_id or analysis_id."""
        try:
            url = f"{REPORT_SERVICE_URL.rstrip('/')}/reports/generate"
            # Forward the JSON body to the report service
            response = requests.post(url, json=request.get_json(), timeout=REQUEST_TIMEOUT)
            return jsonify(response.json()), response.status_code
        except requests.exceptions.RequestException as error:
            logger.error("Generate report failed: %s", error)
            return jsonify({"error": f"Report request failed: {error}"}), 502

    @app.route("/api/reports/<report_id>/json", methods=["GET"])
    @jwt_required()
    def export_report_json(report_id):
        """Export report as JSON file."""
        try:
            url = f"{REPORT_SERVICE_URL.rstrip('/')}/reports/{report_id}/json"
            response = requests.get(url, timeout=REQUEST_TIMEOUT)

            # If error (e.g. 404), return json error message
            if response.status_code != 200:
                return jsonify(response.json()), response.status_code

            # Pass the file content and headers back to the client
            filename = f'report_{report_id}.json'
            headers = {
                'Content-Disposition': response.headers.get(
                    'Content-Disposition', f'attachment; filename={filename}'
                ),
                'Content-Type': response.headers.get('Content-Type', 'application/json')
            }
            return response.content, 200, headers

        except requests.exceptions.RequestException as error:
            logger.error("Report JSON export failed: %s", error)
            return jsonify({"error": f"Report request failed: {error}"}), 502

    @app.route("/api/reports/<report_id>/pdf", methods=["GET"])
    @jwt_required()
    def export_report_pdf(report_id):
        """Export report as PDF file."""
        try:
            url = f"{REPORT_SERVICE_URL.rstrip('/')}/reports/{report_id}/pdf"
            response = requests.get(url, timeout=REQUEST_TIMEOUT)

            # If error (e.g. 404), return json error message
            if response.status_code != 200:
                try:
                    return jsonify(response.json()), response.status_code
                except ValueError:
                    return jsonify({"error": "Failed to retrieve PDF"}), response.status_code

            # Pass the PDF file content and headers back to the client
            filename = f'report_{report_id}.pdf'
            headers = {
                'Content-Disposition': response.headers.get(
                    'Content-Disposition', f'attachment; filename={filename}'
                ),
                'Content-Type': response.headers.get('Content-Type', 'application/pdf')
            }
            return response.content, 200, headers

        except requests.exceptions.RequestException as error:
            logger.error("Report PDF export failed: %s", error)
            return jsonify({"error": f"Report request failed: {error}"}), 502

    return app


if __name__ == "__main__":
    gateway_app = create_app()
    port = int(os.environ.get("PORT", 5000))
    gateway_app.run(host="0.0.0.0", port=port, debug=True)
