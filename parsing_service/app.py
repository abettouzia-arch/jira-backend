"""Flask entry point for the Jira parsing service."""

import logging
import os
import sys
import uuid
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=wrong-import-position
from parsing_service.parsers import dump_parser, groovy_parser, xml_parser, zip_handler
from shared.repositories.analysis_repository import AnalysisRepository
from shared.schemas.parsed_data_schema import ParsedJiraData

app = Flask(__name__)
app.config["TRUSTED_HOSTS"] = None
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "temp_uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for the parsing service."""
    return jsonify({"status": "healthy", "service": "parsing_service"}), 200


@app.route("/parse", methods=["POST"])
def parse_jira_export():
    """
    Parse a Jira ZIP export and return structured entities and components.
    """
    print("DEBUG: file in request.files:", "file" in request.files)
    if "file" not in request.files:
        print("DEBUG: No file part")
        return jsonify({"error": "No file part"}), 400

    uploaded_file = request.files["file"]
    print("DEBUG: filename:", repr(uploaded_file.filename))
    print("DEBUG: content_type:", uploaded_file.content_type)

    if uploaded_file.filename == "":
        print("DEBUG: No selected file")
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(uploaded_file.filename)
    zip_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{filename}")
    extract_dir = None

    try:
        uploaded_file.save(zip_path)
        print("DEBUG: Saved uploaded file to", zip_path)
        logger.info("Received file saved to %s", zip_path)

        extract_dir, routed_files = zip_handler.extract_and_route(zip_path)
        final_data = ParsedJiraData()
        users = []
        projects = []
        issues = []
        components = []

        for xml_file in routed_files.get("xml", []):
            logger.info("Parsing XML content: %s", xml_file["filename"])
            xml_results = xml_parser.parse_xml_streaming(xml_file["full_path"])

            users.extend(xml_results.users)
            projects.extend(xml_results.projects)
            issues.extend(xml_results.issues)
            components.extend(xml_results.components)

        if routed_files.get("groovy"):
            logger.info("Parsing %s Groovy scripts...", len(routed_files["groovy"]))
            groovy_components = groovy_parser.parse_groovy_files(routed_files["groovy"])
            components.extend(groovy_components)

        if routed_files.get("dump"):
            logger.info("Parsing %s dump files...", len(routed_files["dump"]))
            dump_components = dump_parser.parse_dump_files(routed_files["dump"])
            components.extend(dump_components)

        final_data.users = users
        final_data.projects = projects
        final_data.issues = issues
        final_data.components = components

        analysis_id = str(uuid.uuid4())

        analysis_payload = {
            "analysis_id": analysis_id,
            "source_environment": "Jira Data Center",
            "target_environment": "Jira Cloud",
            "analysis_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "components": [
                _to_dict(component)
                for component in final_data.components
            ],
            "raw_stats": {
                "user_count": len(final_data.users),
                "project_count": len(final_data.projects),
                "issue_count": len(final_data.issues),
            },
        }

        analysis_repo = AnalysisRepository()
        analysis_repo.insert_analysis(analysis_payload)
        logger.info("Analysis %s saved to database.", analysis_id)

        analysis_payload.pop("_id", None)
        return jsonify(analysis_payload), 200

    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.exception("Critical error during parsing phase: %s", error)
        return jsonify({"error": str(error)}), 500

    finally:
        if extract_dir:
            try:
                zip_handler.cleanup(extract_dir)
            except Exception as cleanup_error:  # pylint: disable=broad-exception-caught
                logger.warning("Could not clean extraction directory: %s", cleanup_error)

        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except OSError as cleanup_error:
                logger.warning("Could not remove uploaded file: %s", cleanup_error)


def _to_dict(value):
    """Convert Pydantic models or dict-like values to plain dictionaries."""
    if hasattr(value, "model_dump"):
        return value.model_dump()

    if hasattr(value, "dict"):
        return value.dict()

    if isinstance(value, dict):
        return value

    return value


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
