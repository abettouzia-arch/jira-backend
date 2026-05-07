"""
RAG client for the Compatibility Service.

Responsible for querying the Knowledge Service in order to retrieve
documentation evidence relevant to a compatibility analysis result.
"""

import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)


DEFAULT_TOP_K = 5
DEFAULT_TIMEOUT = 20


def get_knowledge_service_url() -> str:
    """Return the configured Knowledge Service base URL."""
    return os.getenv(
        "KNOWLEDGE_SERVICE_URL",
        "http://localhost:5003",
    ).rstrip("/")


def search_component_evidence(component: dict, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """
    Query the Knowledge Service for documentation evidence related to a component.

    Args:
        component: compatibility baseline result or component dict
        top_k: maximum number of chunks to retrieve

    Returns:
        list of evidence chunks, each chunk being a dict like:
        {
            "text": "...",
            "source": "scriptrunner_cloud.md",
            "chunk_index": 3,
            "distance": 0.1234
        }

        Returns an empty list if the Knowledge Service is unavailable
        or if no results are found.
    """
    url = f"{get_knowledge_service_url()}/knowledge/search/component"
    payload = {
        "component": component,
        "top_k": top_k,
    }

    try:
        logger.info(
            "Requesting RAG evidence from Knowledge Service for component %s",
            component.get("component_id", "unknown"),
        )

        response = requests.post(
            url,
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        if not isinstance(results, list):
            logger.warning(
                "Knowledge Service returned unexpected 'results' format for component %s",
                component.get("component_id", "unknown"),
            )
            return []

        logger.info(
            "Received %d evidence chunks for component %s",
            len(results),
            component.get("component_id", "unknown"),
        )
        return results

    except requests.exceptions.RequestException as error:
        logger.warning(
            "Knowledge Service request failed for component %s: %s",
            component.get("component_id", "unknown"),
            error,
        )
        return []

    except (ValueError, TypeError) as error:
        logger.warning(
            "Invalid Knowledge Service response for component %s: %s",
            component.get("component_id", "unknown"),
            error,
        )
        return []


def search_text_evidence(query: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """
    Query the Knowledge Service using a raw text query.

    Useful for direct debugging or future advanced retrieval flows.

    Args:
        query: natural-language search query
        top_k: maximum number of chunks to retrieve

    Returns:
        list of evidence chunks, or an empty list if nothing is found.
    """
    if not query or not query.strip():
        return []

    url = f"{get_knowledge_service_url()}/knowledge/search"
    payload = {
        "query": query,
        "top_k": top_k,
    }

    try:
        logger.info("Requesting text-based RAG search: %s", query[:80])

        response = requests.post(
            url,
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        if not isinstance(results, list):
            return []

        logger.info("Received %d chunks for text query.", len(results))
        return results

    except requests.exceptions.RequestException as error:
        logger.warning("Knowledge Service text search failed: %s", error)
        return []

    except (ValueError, TypeError) as error:
        logger.warning("Invalid Knowledge Service text search response: %s", error)
        return []


def summarize_evidence(evidence_chunks: list[dict]) -> list[dict[str, Any]]:
    """
    Return a lighter evidence representation suitable for logging or persistence.

    Args:
        evidence_chunks: raw chunks returned by the Knowledge Service

    Returns:
        list of simplified evidence dicts
    """
    summarized = []

    for chunk in evidence_chunks:
        summarized.append({
            "source": chunk.get("source", ""),
            "chunk_index": chunk.get("chunk_index", 0),
            "distance": chunk.get("distance"),
            "text": chunk.get("text", "")[:500],
        })

    return summarized
