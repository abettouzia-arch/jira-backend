"""Index learned component analysis results from MongoDB into ChromaDB."""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# pylint: disable=wrong-import-position
from shared.repositories.component_analysis_cache_repository import (
    ComponentAnalysisCacheRepository,
)

logger = logging.getLogger(__name__)

SOURCE_TYPE = "learned_component_analysis"
SOURCE_NAME = "mongo_component_analysis_cache"


def index_learned_component_knowledge(limit: int = 500) -> dict:
    """
    Index cached component analysis results as reusable RAG knowledge.

    This does not train the LLM. It makes historical verified analysis results
    searchable by the Knowledge Service so future analyses can retrieve them as
    context before calling the AI model.
    """
    cache_repo = ComponentAnalysisCacheRepository()
    records = cache_repo.list_recent(limit=limit)
    chunks = [_record_to_chunk(record) for record in records if record.get("result")]
    chunks = [chunk for chunk in chunks if chunk["text"].strip()]

    if not chunks:
        return {
            "status": "success",
            "source_type": SOURCE_TYPE,
            "records_found": len(records),
            "chunks_indexed": 0,
        }

    from knowledge_service.indexer.document_loader import get_chroma_collection
    from knowledge_service.indexer.embedder import embed_texts

    embeddings = embed_texts([chunk["text"] for chunk in chunks])
    collection = get_chroma_collection()

    collection.upsert(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["text"] for chunk in chunks],
        embeddings=embeddings,
        metadatas=[chunk["metadata"] for chunk in chunks],
    )

    logger.info("Indexed %d learned component analysis chunks.", len(chunks))
    return {
        "status": "success",
        "source_type": SOURCE_TYPE,
        "records_found": len(records),
        "chunks_indexed": len(chunks),
    }


def _record_to_chunk(record: dict) -> dict:
    """Convert one cached analysis record into a ChromaDB document chunk."""
    signature = record.get("signature", "")
    result = record.get("result", {})
    component_name = (
        record.get("component_name")
        or result.get("component_name")
        or result.get("component_id")
        or "Unknown component"
    )
    plugin = record.get("plugin_label") or result.get("plugin") or record.get("plugin", "")
    component_type = (
        record.get("component_type_label")
        or result.get("component_type")
        or record.get("component_type", "")
    )
    features = record.get("features", [])
    feature_text = ", ".join(features)
    final_status = result.get("final_status", result.get("overall_status", ""))
    final_risk = result.get("final_risk", result.get("risk_level", ""))
    reasoning_summary = result.get("reasoning_summary", "")
    recommended_action = result.get("recommended_action", "")

    text = (
        f"Learned Jira migration analysis for component '{component_name}'.\n"
        f"Plugin: {plugin}.\n"
        f"Component type: {component_type}.\n"
        f"Detected features: {feature_text}.\n"
        f"Final compatibility status: {final_status}.\n"
        f"Final migration risk: {final_risk}.\n"
        f"Reasoning: {reasoning_summary}\n"
        f"Recommended action: {recommended_action}"
    )

    return {
        "id": f"learned_component__{signature}",
        "text": text,
        "metadata": {
            "source": SOURCE_NAME,
            "source_type": SOURCE_TYPE,
            "chunk_index": 0,
            "signature": signature,
            "component_name": component_name,
            "plugin": plugin,
            "component_type": component_type,
            "features": feature_text,
            "final_status": final_status,
            "final_risk": final_risk,
        },
    }
