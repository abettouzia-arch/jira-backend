"""
Knowledge Service — RAG indexing and search API.
Indexes Atlassian documentation and serves relevant chunks
to the report_service for LLM-grounded report generation.
"""

import logging
import os
import sys

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=wrong-import-position
from knowledge_service.indexer.document_loader import (
    get_collection_stats,
    index_documents,
)
from knowledge_service.retriever.search import search, search_for_component

load_dotenv()
app = Flask(__name__)
app.config["TRUSTED_HOSTS"] = None
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    collection_stats = get_collection_stats()
    return jsonify({
        "status": "healthy",
        "service": "knowledge_service",
        "indexed_chunks": collection_stats["total_chunks"],
    })


@app.route("/knowledge/stats", methods=["GET"])
def knowledge_stats():
    """Return stats about the ChromaDB collection."""
    return jsonify(get_collection_stats()), 200


@app.route("/knowledge/index", methods=["POST"])
def index():
    """
    Index all documents from docs/ into ChromaDB.
    Accepts optional { "force_reindex": true } to rebuild from scratch.
    """
    data = request.get_json() or {}
    force = data.get("force_reindex", False)

    try:
        count = index_documents(force_reindex=force)
        return jsonify({
            "status": "success",
            "chunks_indexed": count,
            "force_reindex": force,
        }), 200
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Indexing failed: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/knowledge/search", methods=["POST"])
def search_endpoint():
    """
    Search for relevant documentation chunks.
    Body: { "query": "...", "top_k": 5 }
    """
    data = request.get_json()

    if not data or "query" not in data:
        return jsonify({"error": "'query' field is required."}), 400

    query = data["query"]
    top_k = data.get("top_k", 5)

    try:
        results = search(query=query, top_k=top_k)
        return jsonify({
            "query": query,
            "results": results,
            "count": len(results),
        }), 200
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Search failed: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/knowledge/search/component", methods=["POST"])
def search_component():
    """
    Search for docs relevant to a specific compatibility result.
    Body: { "component": { ...compatibility result dict... } }
    Used internally by report_service.
    """
    data = request.get_json()

    if not data or "component" not in data:
        return jsonify({"error": "'component' field is required."}), 400

    try:
        top_k = data.get("top_k", 5)
        results = search_for_component(data["component"], top_k=top_k)
        return jsonify({
            "results": results,
            "count": len(results),
        }), 200
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Component search failed: %s", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Auto-index on startup if collection is empty
    logger.info("Starting Knowledge Service — checking index...")
    index_documents(force_reindex=False)

    port = int(os.environ.get("PORT", 5003))
    app.run(host="0.0.0.0", port=port, debug=True)
