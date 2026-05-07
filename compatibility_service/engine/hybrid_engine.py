"""
Hybrid compatibility engine for Jira DC → Cloud migration analysis.

Pipeline:
- run deterministic compatibility rules
- retrieve RAG evidence from the Knowledge Service
- build an enriched baseline result
- run AI reasoning on top of the baseline
- merge baseline + AI into a final compatibility result
"""

import logging

from compatibility_service.engine.ai_reasoner import reason_with_ai
from compatibility_service.engine.rag_client import (
    search_component_evidence,
    summarize_evidence,
)
from compatibility_service.engine.result_merger import merge_results
from compatibility_service.engine.rule_engine import analyze_component

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5


def analyze_component_hybrid(component: dict, top_k: int = DEFAULT_TOP_K) -> dict:
    """
    Analyze a single Jira component using a hybrid pipeline:
    deterministic rules + RAG evidence + AI reasoning + result merge.

    Args:
        component: Jira component dict from parsing_service
        top_k: number of RAG chunks to retrieve

    Returns:
        final merged compatibility result dict
    """
    logger.info(
        "Hybrid analysis started for component %s",
        component.get("component_id", "unknown"),
    )

    # Step 1 — Deterministic baseline
    rule_result = analyze_component(component)

    # Step 2 — Retrieve RAG evidence
    rag_component = {
        **component,
        **rule_result,
        "features_detected": component.get("features_detected", []),
        "final_status": rule_result.get("overall_status", "NEEDS_REVIEW"),
    }

    evidence_chunks = search_component_evidence(rag_component, top_k=top_k)
    summarized_evidence = summarize_evidence(evidence_chunks)

    # Step 3 — Build enriched baseline
    baseline_result = {
        **rule_result,
        "rule_based_status": rule_result.get("overall_status", "NEEDS_REVIEW"),
        "rule_based_risk": rule_result.get("risk_level", "MINOR"),
        "final_status": rule_result.get("overall_status", "NEEDS_REVIEW"),
        "final_risk": rule_result.get("risk_level", "MINOR"),
        "confidence": _compute_initial_confidence(rule_result, summarized_evidence),
        "reasoning_summary": _build_reasoning_summary(rule_result, summarized_evidence),
        "evidence": summarized_evidence,
        "evidence_count": len(summarized_evidence),
        "analysis_mode": "hybrid_rules_rag",
    }

    # Step 4 — AI reasoning
    ai_result = reason_with_ai(
        component=component,
        rule_result=baseline_result,
        evidence_chunks=summarized_evidence,
    )

    # Step 5 — Merge baseline + AI
    final_result = merge_results(
        rule_result=baseline_result,
        ai_result=ai_result,
        evidence_chunks=summarized_evidence,
    )

    logger.info(
        "Hybrid analysis completed for component %s | "
        "final_status=%s | evidence=%d | confidence=%.2f",
        component.get("component_id", "unknown"),
        final_result.get("final_status", "NEEDS_REVIEW"),
        final_result.get("evidence_count", 0),
        float(final_result.get("confidence", 0.0) or 0.0),
    )

    return final_result


def analyze_components_hybrid(
    components: list[dict],
    top_k: int = DEFAULT_TOP_K,
) -> list[dict]:
    """
    Analyze a list of Jira components using the hybrid pipeline.

    Args:
        components: list of Jira component dicts
        top_k: number of RAG chunks per component

    Returns:
        list of final merged compatibility results
    """
    results = []

    for component in components:
        try:
            result = analyze_component_hybrid(component, top_k=top_k)
            results.append(result)
        except (KeyError, TypeError, ValueError) as error:
            logger.error(
                "Hybrid analysis failed for component %s: %s",
                component.get("component_id", "unknown"),
                error,
            )

    logger.info(
        "Hybrid analysis complete: %d components processed.",
        len(results),
    )
    return results


def _compute_initial_confidence(rule_result: dict, evidence: list[dict]) -> float:
    """
    Compute an initial confidence score before AI reasoning.

    Current heuristic:
    - base confidence depends on deterministic rule result
    - slightly increased if relevant RAG evidence exists

    Returns:
        float between 0.0 and 1.0
    """
    status = rule_result.get("overall_status", "NEEDS_REVIEW")
    evidence_count = len(evidence)

    if status == "INCOMPATIBLE":
        base_confidence = 0.95
    elif status in ("REWRITE_REQUIRED", "NEEDS_RECREATION"):
        base_confidence = 0.90
    elif status == "PARTIAL":
        base_confidence = 0.80
    elif status == "COMPATIBLE":
        base_confidence = 0.85
    elif status == "DEPRECATED":
        base_confidence = 0.75
    else:
        base_confidence = 0.65

    if evidence_count >= 3:
        base_confidence += 0.03
    elif evidence_count > 0:
        base_confidence += 0.01

    return round(min(base_confidence, 0.99), 2)


def _build_reasoning_summary(rule_result: dict, evidence: list[dict]) -> str:
    """
    Build a concise reasoning summary from the rule-based result and RAG evidence.

    Returns:
        human-readable summary
    """
    status = rule_result.get("overall_status", "NEEDS_REVIEW")
    risk = rule_result.get("risk_level", "MINOR")
    component_id = rule_result.get("component_id", "unknown")
    feature_count = len(rule_result.get("features_analyzed", []))
    evidence_count = len(evidence)

    if evidence_count > 0:
        return (
            f"Component {component_id} was analyzed using deterministic compatibility "
            f"rules and enriched with {evidence_count} documentation evidence chunk(s). "
            f"The current baseline assessment is {status} with {risk} risk, based on "
            f"{feature_count} analyzed feature(s)."
        )

    return (
        f"Component {component_id} was analyzed using deterministic compatibility rules. "
        f"No additional RAG evidence was retrieved. The current baseline assessment is "
        f"{status} with {risk} risk, based on {feature_count} analyzed feature(s)."
    )
