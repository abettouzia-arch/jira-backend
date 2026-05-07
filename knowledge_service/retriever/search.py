"""
Retriever for the Knowledge Service.
Searches ChromaDB for the most relevant documentation chunks
given a compatibility analysis query.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# pylint: disable=wrong-import-position
from knowledge_service.indexer.document_loader import get_chroma_collection
from knowledge_service.indexer.embedder import embed_texts

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5


def search(query: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """Search for the most relevant documentation chunks for a given query."""
    if not query or not query.strip():
        return []

    collection = get_chroma_collection()

    if collection.count() == 0:
        logger.warning("ChromaDB collection is empty. Run indexing first.")
        return []

    query_embedding = embed_texts([query])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, metadata, distance in zip(documents, metadatas, distances):
        chunks.append({
            "text": doc,
            "source": metadata.get("source", ""),
            "chunk_index": metadata.get("chunk_index", 0),
            "distance": round(distance, 4),
        })

    logger.info(
        "Search for '%s' returned %d results.",
        query[:50],
        len(chunks),
    )

    return chunks


def _extract_features(component: dict) -> list[str]:
    """
    Extract feature names from different component/result formats.

    Supports:
    - parsed component format: features_detected = ["java_api", ...]
    - compatibility format: features_analyzed = [{"feature": "...", "risk_level": "..."}]
    """
    features_detected = component.get("features_detected", [])
    if features_detected:
        return [
            feature
            for feature in features_detected
            if isinstance(feature, str) and feature.strip()
        ]

    features_analyzed = component.get("features_analyzed", [])
    extracted = []

    for feature_result in features_analyzed:
        if not isinstance(feature_result, dict):
            continue

        feature_name = feature_result.get("feature", "")
        risk_level = feature_result.get("risk_level", "")

        if feature_name and risk_level in ("BLOCKER", "MAJOR"):
            extracted.append(feature_name)

    return extracted


def search_for_component(component: dict, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """
    Build a query from a component or compatibility result and search for relevant docs.
    Used by compatibility_service and report_service.
    """
    plugin = component.get("plugin", "")
    overall_status = component.get(
        "final_status",
        component.get("overall_status", ""),
    )

    features = _extract_features(component)

    if not features:
        logger.warning(
            "No features found for RAG search on component %s",
            component.get("component_id", "unknown"),
        )
        return []

    query = (
        f"{plugin} plugin Jira Cloud compatibility migration: "
        f"{', '.join(features[:6])} "
        f"status {overall_status}"
    )

    logger.info(
        "RAG query for component %s: %s",
        component.get("component_id", "unknown"),
        query,
    )

    return search(query, top_k=top_k)
