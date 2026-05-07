"""Flask entry point for the Jira parsing service."""

import logging
import os
import sys
import uuid
from datetime import datetime

from dotenv import load_dotenv

from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename

# pylint: disable=wrong-import-position
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsing_service.parsers import dump_parser, groovy_parser, xml_parser, zip_handler
from shared.repositories.analysis_repository import AnalysisRepository
from shared.schemas.parsed_data_schema import ParsedJiraData

load_dotenv()
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "temp_uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for the parsing service."""
    return jsonify({"status": "healthy", "service": "parsing_service"})


@app.route("/parse", methods=["POST"])
def parse_jira_export():
    """
    Parse a Jira ZIP export and return structured entities and components.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    zip_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{filename}")

    try:
        file.save(zip_path)
        logger.info("Received file saved to %s", zip_path)

        extract_dir, routed_files = zip_handler.extract_and_route(zip_path)

        final_data = ParsedJiraData()

        for xml_file in routed_files.get("xml", []):
            logger.info("Parsing XML content: %s", xml_file["filename"])
            xml_results = xml_parser.parse_xml_streaming(xml_file["full_path"])

            # pylint: disable=no-member
            final_data.users.extend(xml_results.users)
            final_data.projects.extend(xml_results.projects)
            final_data.issues.extend(xml_results.issues)
            final_data.components.extend(xml_results.components)

        if routed_files.get("groovy"):
            logger.info("Parsing %s Groovy scripts...", len(routed_files["groovy"]))
            groovy_components = groovy_parser.parse_groovy_files(routed_files["groovy"])
            # pylint: disable=no-member
            final_data.components.extend(groovy_components)

        if routed_files.get("dump"):
            logger.info("Parsing %s dump files...", len(routed_files["dump"]))
            dump_components = dump_parser.parse_dump_files(routed_files["dump"])
            # pylint: disable=no-member
            final_data.components.extend(dump_components)

        analysis_id = str(uuid.uuid4())

        analysis_payload = {
            "analysis_id": analysis_id,
            "source_environment": "Jira Data Center",
            "target_environment": "Jira Cloud",
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "components": [component.model_dump() for component in final_data.components],
            "raw_stats": {
                "user_count": len(final_data.users),
                "project_count": len(final_data.projects),
                "issue_count": len(final_data.issues),
            },
        }

        analysis_repo = AnalysisRepository()
        analysis_repo.insert_analysis(analysis_payload)
        logger.info("Analysis %s saved to database.", analysis_id)

        zip_handler.cleanup(extract_dir)
        os.remove(zip_path)

        analysis_payload.pop("_id", None)
        return jsonify(analysis_payload)

    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.exception("Critical error during parsing phase: %s", error)
        if os.path.exists(zip_path):
            os.remove(zip_path)
        return jsonify({"error": str(error)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
