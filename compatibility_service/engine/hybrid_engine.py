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
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from compatibility_service.engine.ai_reasoner import reason_with_ai
from compatibility_service.engine.component_signature import build_component_signature
from compatibility_service.engine.rag_client import (
    search_component_evidence,
    summarize_evidence,
)
from compatibility_service.engine.result_merger import merge_results
from compatibility_service.engine.rule_engine import analyze_component
from shared.repositories.component_analysis_cache_repository import (
    ComponentAnalysisCacheRepository,
)

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5
CACHE_ENABLED = os.getenv("COMPONENT_ANALYSIS_CACHE_ENABLED", "true").lower() != "false"
MAX_WORKERS = max(1, int(os.getenv("COMPATIBILITY_ANALYSIS_MAX_WORKERS", "3")))
AI_SKIP_SIMPLE_CASES = os.getenv("AI_SKIP_SIMPLE_CASES_ENABLED", "true").lower() != "false"
LEARNED_SIMILARITY_REUSE_ENABLED = (
    os.getenv("LEARNED_SIMILARITY_REUSE_ENABLED", "true").lower() != "false"
)
LEARNED_SIMILARITY_MAX_DISTANCE = float(os.getenv("LEARNED_SIMILARITY_MAX_DISTANCE", "0.28"))
AI_REQUIRED_RISKS = {"BLOCKER", "MAJOR"}
AI_REQUIRED_STATUSES = {
    "INCOMPATIBLE",
    "REWRITE_REQUIRED",
    "NEEDS_RECREATION",
    "NEEDS_REVIEW",
}


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
    signature_data = build_component_signature(component)
    cached_result = _get_cached_result(signature_data, component)

    if cached_result:
        return cached_result

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
    if _should_skip_ai(baseline_result, summarized_evidence):
        final_result = _build_rule_based_final_result(baseline_result, summarized_evidence)
        _store_cached_result(signature_data, final_result, component)
        logger.info(
            "Hybrid analysis completed without AI for component %s | final_status=%s",
            component.get("component_id", "unknown"),
            final_result.get("final_status", "NEEDS_REVIEW"),
        )
        return final_result

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

    _store_cached_result(signature_data, final_result, component)

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
    if MAX_WORKERS <= 1 or len(components) <= 1:
        return _analyze_components_sequential(components, top_k=top_k)

    return _analyze_components_parallel(components, top_k=top_k)


def _analyze_components_sequential(
    components: list[dict],
    top_k: int = DEFAULT_TOP_K,
) -> list[dict]:
    """Analyze components one by one."""
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


def _analyze_components_parallel(
    components: list[dict],
    top_k: int = DEFAULT_TOP_K,
) -> list[dict]:
    """Analyze components concurrently while preserving input order."""
    worker_count = min(MAX_WORKERS, len(components))
    ordered_results: list[dict | None] = [None] * len(components)

    logger.info(
        "Hybrid analysis running in parallel: components=%d workers=%d",
        len(components),
        worker_count,
    )

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_to_index = {
            executor.submit(analyze_component_hybrid, component, top_k): index
            for index, component in enumerate(components)
        }

        for future in as_completed(future_to_index):
            index = future_to_index[future]
            component = components[index]

            try:
                ordered_results[index] = future.result()
            except (KeyError, TypeError, ValueError) as error:
                logger.error(
                    "Hybrid analysis failed for component %s: %s",
                    component.get("component_id", "unknown"),
                    error,
                )

    results = [result for result in ordered_results if result is not None]
    logger.info(
        "Hybrid parallel analysis complete: %d/%d components processed.",
        len(results),
        len(components),
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


def _should_skip_ai(baseline_result: dict, evidence: list[dict]) -> bool:
    """
    Decide whether the deterministic + RAG result is strong enough without AI.

    This is intentionally conservative. AI is still required for blocker, major,
    incompatible, rewrite, recreation and review cases.
    """
    if not AI_SKIP_SIMPLE_CASES:
        return False

    risk = baseline_result.get("final_risk", "MINOR")
    status = baseline_result.get("final_status", "NEEDS_REVIEW")
    confidence = float(baseline_result.get("confidence", 0.0) or 0.0)

    if risk in AI_REQUIRED_RISKS:
        return False

    if status in AI_REQUIRED_STATUSES:
        return False

    if _has_confirming_learned_evidence(baseline_result, evidence):
        return confidence >= 0.75

    if confidence < 0.80:
        return False

    if not evidence:
        return False

    return True


def _has_confirming_learned_evidence(baseline_result: dict, evidence: list[dict]) -> bool:
    """Return True when a close learned analysis confirms the current verdict."""
    if not LEARNED_SIMILARITY_REUSE_ENABLED:
        return False

    learned = _best_learned_evidence(evidence)
    if not learned:
        return False

    return (
        learned.get("final_status") == baseline_result.get("final_status")
        and learned.get("final_risk") == baseline_result.get("final_risk")
    )


def _best_learned_evidence(evidence: list[dict]) -> dict | None:
    """Return the closest learned-analysis evidence chunk under the distance threshold."""
    learned_chunks = [
        chunk
        for chunk in evidence
        if chunk.get("source_type") == "learned_component_analysis"
        and _distance_is_close(chunk.get("distance"))
    ]

    if not learned_chunks:
        return None

    return sorted(learned_chunks, key=lambda chunk: float(chunk.get("distance") or 0.0))[0]


def _distance_is_close(distance: object) -> bool:
    """Return True when a Chroma distance is close enough for learned reuse."""
    try:
        return float(distance) <= LEARNED_SIMILARITY_MAX_DISTANCE
    except (TypeError, ValueError):
        return False


def _build_rule_based_final_result(
    baseline_result: dict,
    evidence: list[dict],
) -> dict:
    """Build a complete professional result without calling the LLM."""
    status = baseline_result.get("final_status", "NEEDS_REVIEW")
    risk = baseline_result.get("final_risk", "MINOR")
    component_label = _component_label(baseline_result)
    feature_count = len(baseline_result.get("features_analyzed", []))
    evidence_count = len(evidence)
    learned_evidence = _best_learned_evidence(evidence)
    learned_context = ""

    if learned_evidence:
        learned_context = (
            f" A similar previously analyzed component "
            f"('{learned_evidence.get('component_name', 'unknown')}') confirmed the same "
            f"{status}/{risk} assessment."
        )

    reasoning_summary = (
        f"Component {component_label} was assessed using deterministic Jira Cloud "
        f"migration rules and validated with {evidence_count} relevant knowledge "
        f"chunk(s). The rule-based result is {status} with {risk} risk across "
        f"{feature_count} analyzed feature(s). No AI escalation was required because "
        f"the finding is non-critical, evidence-backed, and high-confidence.{learned_context}"
    )

    return {
        **baseline_result,
        "final_status": status,
        "final_risk": risk,
        "confidence": round(float(baseline_result.get("confidence", 0.0) or 0.0), 2),
        "reasoning_summary": reasoning_summary,
        "recommended_action": _professionalize_recommended_action(baseline_result),
        "ai_reasoning": {
            "used": False,
            "reason": "Skipped for high-confidence non-critical rule-based finding.",
        },
        "evidence": evidence,
        "evidence_count": evidence_count,
        "analysis_mode": "hybrid_rules_rag_no_ai",
    }


def _professionalize_recommended_action(baseline_result: dict) -> str:
    """Return a polished action for high-confidence non-critical results."""
    action = baseline_result.get("recommended_action", "")

    if action:
        return (
            f"{action} Confirm this component during migration rehearsal and keep "
            "the finding in the migration checklist for traceability."
        )

    return (
        "No blocking remediation is required. Validate the component during migration "
        "rehearsal and keep it in the migration checklist for traceability."
    )


def _build_reasoning_summary(rule_result: dict, evidence: list[dict]) -> str:
    """
    Build a concise reasoning summary from the rule-based result and RAG evidence.

    Returns:
        human-readable summary
    """
    status = rule_result.get("overall_status", "NEEDS_REVIEW")
    risk = rule_result.get("risk_level", "MINOR")
    component_label = _component_label(rule_result)
    feature_count = len(rule_result.get("features_analyzed", []))
    evidence_count = len(evidence)

    if evidence_count > 0:
        return (
            f"Component {component_label} was analyzed using deterministic compatibility "
            f"rules and enriched with {evidence_count} documentation evidence chunk(s). "
            f"The current baseline assessment is {status} with {risk} risk, based on "
            f"{feature_count} analyzed feature(s)."
        )

    return (
        f"Component {component_label} was analyzed using deterministic compatibility rules. "
        f"No additional RAG evidence was retrieved. The current baseline assessment is "
        f"{status} with {risk} risk, based on {feature_count} analyzed feature(s)."
    )


def _component_label(component: dict) -> str:
    """Return the report-friendly component label, falling back to the technical ID."""
    return component.get("component_name") or component.get("component_id", "unknown")


def _get_cached_result(signature_data: dict, component: dict) -> dict | None:
    """Return a hydrated cached result when available."""
    if not CACHE_ENABLED:
        return None

    signature = signature_data.get("signature", "")

    try:
        cache_repo = ComponentAnalysisCacheRepository()
        cached = cache_repo.get_by_signature(signature)

        if not cached or not cached.get("result"):
            return None

        cache_repo.mark_used(signature)
        logger.info(
            "Component analysis cache hit for %s",
            component.get("component_id", "unknown"),
        )

        return _hydrate_cached_result(cached["result"], component)

    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.warning(
            "Component analysis cache lookup failed for %s: %s",
            component.get("component_id", "unknown"),
            error,
        )
        return None


def _store_cached_result(signature_data: dict, result: dict, component: dict) -> None:
    """Persist a successful component analysis result for future reuse."""
    if not CACHE_ENABLED:
        return

    try:
        cache_repo = ComponentAnalysisCacheRepository()
        cache_repo.upsert_result(signature_data, result, component)
    except Exception as error:  # pylint: disable=broad-exception-caught
        logger.warning(
            "Component analysis cache write failed for %s: %s",
            component.get("component_id", "unknown"),
            error,
        )


def _hydrate_cached_result(cached_result: dict, component: dict) -> dict:
    """
    Reuse a cached verdict while preserving the current component identity.

    The same script can be uploaded from a different file or workflow. The cached
    compatibility result remains useful, but the report must still show the
    current component name, location and ID.
    """
    result = {**cached_result}
    previous_id = str(result.get("component_id", ""))
    previous_name = str(result.get("component_name", ""))
    current_id = component.get("component_id", previous_id)
    current_name = component.get("component_name", previous_name)

    result.update({
        "component_id": current_id,
        "component_name": current_name,
        "component_type": component.get("component_type", result.get("component_type", "")),
        "plugin": component.get("plugin", result.get("plugin", "")),
        "location": component.get("location", result.get("location", {})),
        "source_code": component.get("source_code", result.get("source_code", "")),
        "cache_hit": True,
        "analysis_mode": f"{result.get('analysis_mode', 'hybrid_rules_rag_ai')}_cache",
    })

    for field in ("reasoning_summary", "recommended_action"):
        result[field] = _replace_cached_component_label(
            result.get(field, ""),
            previous_id,
            previous_name,
            current_name or current_id,
        )

    return result


def _replace_cached_component_label(
    text: object,
    previous_id: str,
    previous_name: str,
    current_label: str,
) -> str:
    """Replace stale component labels inside cached human-readable text."""
    cleaned = str(text or "")

    for old_value in (previous_id, previous_name):
        if old_value and current_label:
            cleaned = cleaned.replace(old_value, current_label)

    return cleaned
