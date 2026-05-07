"""
Compatibility Service for Jira DC → Cloud migration analysis.
Receives parsed components and returns a full compatibility matrix.
"""

import logging
import os
import sys

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=wrong-import-position
from compatibility_service.engine.hybrid_engine import analyze_components_hybrid
from compatibility_service.engine.matrix import build_matrix
from shared.repositories.analysis_repository import AnalysisRepository
from shared.repositories.compatibility_repository import CompatibilityRepository


app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "compatibility_service"})


@app.route("/compatibility/analyze", methods=["POST"])
def analyze():
    """
    Analyze compatibility of parsed Jira components.

    Accepts either:
      - { "analysis_id": "xxx" }  → loads components from MongoDB
      - { "components": [...] }   → uses components sent directly in request
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    if "analysis_id" in data:
        analysis_id = data["analysis_id"]
        logger.info("Loading components from MongoDB for analysis_id: %s", analysis_id)

        try:
            analysis_repo = AnalysisRepository()
            record = analysis_repo.get_analysis_by_id(analysis_id)

            if not record:
                return jsonify({
                    "error": f"analysis_id '{analysis_id}' not found in database."
                }), 404

            components = record.get("components", [])
            logger.info("Loaded %d components from MongoDB.", len(components))

        except Exception as error:  # pylint: disable=broad-exception-caught
            logger.error("Database error: %s", error)
            return jsonify({"error": f"Database error: {error}"}), 500

    elif "components" in data:
        components = data["components"]
        analysis_id = data.get("analysis_id", "direct-input")
        logger.info("Using %d components from request body.", len(components))

    else:
        return jsonify({
            "error": "Request must contain either 'analysis_id' or 'components'."
        }), 400

    if not components:
        return jsonify({"error": "No components found to analyze."}), 400

    try:
        component_results = analyze_components_hybrid(components)
        matrix = build_matrix(analysis_id, component_results)
    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.error("Analysis engine error: %s", error)
        return jsonify({"error": f"Analysis failed: {error}"}), 500

    try:
        compatibility_repo = CompatibilityRepository()
        compatibility_repo.insert_matrix({**matrix})
        logger.info("Matrix %s saved to MongoDB.", matrix["matrix_id"])
    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.warning("Could not save matrix to MongoDB: %s", error)

    matrix.pop("_id", None)

    return jsonify(matrix), 200


@app.route("/compatibility/matrix/<matrix_id>", methods=["GET"])
def get_matrix(matrix_id):
    """Retrieve a previously computed compatibility matrix by ID."""
    try:
        compatibility_repo = CompatibilityRepository()
        matrix = compatibility_repo.get_matrix_by_id(matrix_id)

        if not matrix:
            return jsonify({"error": f"Matrix '{matrix_id}' not found."}), 404

        matrix.pop("_id", None)
        return jsonify(matrix), 200

    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.error("Error retrieving matrix: %s", error)
        return jsonify({"error": str(error)}), 500


@app.route("/compatibility/matrices", methods=["GET"])
def list_matrices():
    """List all compatibility matrices with summary only."""
    try:
        compatibility_repo = CompatibilityRepository()
        matrices = compatibility_repo.list_matrices()
        return jsonify({"matrices": matrices, "count": len(matrices)}), 200

    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.error("Error listing matrices: %s", error)
        return jsonify({"error": str(error)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=True)
