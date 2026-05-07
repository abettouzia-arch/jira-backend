"""
Result merger for the Compatibility Service.

Combines:
- deterministic rule-based result
- RAG-enriched baseline
- AI reasoning result

The merger ensures that obvious blocker situations remain conservative,
while still allowing AI to refine nuanced compatibility assessments.
"""

import logging

logger = logging.getLogger(__name__)

RISK_PRIORITY = {
    "INFO": 1,
    "MINOR": 2,
    "MAJOR": 3,
    "BLOCKER": 4,
}

STATUS_PRIORITY = {
    "COMPATIBLE": 1,
    "PARTIAL": 2,
    "DEPRECATED": 3,
    "NEEDS_REVIEW": 4,
    "REWRITE_REQUIRED": 5,
    "NEEDS_RECREATION": 6,
    "INCOMPATIBLE": 7,
}

HARD_BLOCKER_FEATURES = {
    "java_api",
    "direct_database_query",
    "filesystem_access",
    "file_read",
    "file_write",
    "jdbc_connection_usage",
    "active_objects_access",
}


def merge_results(
    rule_result: dict,
    ai_result: dict,
    evidence_chunks: list[dict],
) -> dict:
    """
    Merge rule-based and AI-based results into a final compatibility result.

    Args:
        rule_result: enriched baseline result from hybrid_engine
        ai_result: reasoning result from ai_reasoner
        evidence_chunks: RAG evidence used during reasoning

    Returns:
        merged final result dict
    """
    features = _extract_features(rule_result)
    has_hard_blocker = any(feature in HARD_BLOCKER_FEATURES for feature in features)

    rule_status = rule_result.get("final_status", rule_result.get("overall_status", "NEEDS_REVIEW"))
    rule_risk = rule_result.get("final_risk", rule_result.get("risk_level", "MINOR"))

    ai_status = ai_result.get("final_status", rule_status)
    ai_risk = ai_result.get("risk_level", rule_risk)
    ai_confidence = float(ai_result.get("confidence", 0.0) or 0.0)

    evidence_count = len(evidence_chunks)

    final_status = rule_status
    final_risk = rule_risk
    final_confidence = rule_result.get("confidence", 0.0)
    reasoning_summary = rule_result.get("reasoning_summary", "")
    recommended_action = rule_result.get("recommended_action", "")

    # Rule 1 — Hard blockers always dominate
    if has_hard_blocker:
        final_status = _most_conservative_status(rule_status, ai_status)
        final_risk = _most_conservative_risk(rule_risk, ai_risk)
        final_confidence = max(float(final_confidence or 0.0), ai_confidence, 0.95)

        reasoning_summary = (
            ai_result.get("reasoning_summary")
            or reasoning_summary
            or "Hard blocker features were detected. Conservative rule-based result retained."
        )
        recommended_action = (
            ai_result.get("recommended_action")
            or recommended_action
        )

        logger.info(
            "Result merger kept conservative blocker result for component %s",
            rule_result.get("component_id", "unknown"),
        )

    # Rule 2 — If AI confidence is high and evidence exists, AI may refine the result
    elif ai_confidence >= 0.80 and evidence_count > 0:
        final_status = _most_conservative_status(rule_status, ai_status)
        final_risk = _most_conservative_risk(rule_risk, ai_risk)
        final_confidence = round(max(float(final_confidence or 0.0), ai_confidence), 2)

        reasoning_summary = (
            ai_result.get("reasoning_summary")
            or reasoning_summary
        )
        recommended_action = (
            ai_result.get("recommended_action")
            or recommended_action
        )

        logger.info(
            "Result merger accepted AI refinement for component %s",
            rule_result.get("component_id", "unknown"),
        )

    # Rule 3 — If AI confidence is medium, prefer rule baseline but keep AI explanation if useful
    elif ai_confidence >= 0.60:
        final_status = rule_status
        final_risk = _most_conservative_risk(rule_risk, ai_risk)
        final_confidence = round(max(float(final_confidence or 0.0), ai_confidence - 0.10), 2)

        if ai_result.get("reasoning_summary"):
            reasoning_summary = ai_result["reasoning_summary"]

        if ai_result.get("recommended_action"):
            recommended_action = ai_result["recommended_action"]

        logger.info(
            "Result merger kept rule status but enriched explanation for component %s",
            rule_result.get("component_id", "unknown"),
        )

    # Rule 4 — Low confidence AI: ignore AI verdict
    else:
        final_status = rule_status
        final_risk = rule_risk
        final_confidence = round(float(final_confidence or 0.0), 2)

        logger.info(
            "Result merger ignored low-confidence AI output for component %s",
            rule_result.get("component_id", "unknown"),
        )

    merged = {
        **rule_result,
        "final_status": final_status,
        "final_risk": final_risk,
        "confidence": round(min(max(final_confidence, 0.0), 1.0), 2),
        "reasoning_summary": reasoning_summary,
        "recommended_action": recommended_action,
        "ai_reasoning": {
            "used": True,
            "ai_status": ai_status,
            "ai_risk": ai_risk,
            "ai_confidence": round(ai_confidence, 2),
        },
        "evidence": evidence_chunks,
        "evidence_count": evidence_count,
        "analysis_mode": "hybrid_rules_rag_ai",
    }

    return merged


def _extract_features(rule_result: dict) -> list[str]:
    """Extract feature names from a rule result or parsed component format."""
    features_detected = rule_result.get("features_detected", [])

    if features_detected:
        return [
            feature
            for feature in features_detected
            if isinstance(feature, str) and feature.strip()
        ]

    return [
        item.get("feature", "")
        for item in rule_result.get("features_analyzed", [])
        if item.get("feature")
    ]


def _most_conservative_status(left: str, right: str) -> str:
    """Return the more conservative compatibility status."""
    left_score = STATUS_PRIORITY.get(left, 0)
    right_score = STATUS_PRIORITY.get(right, 0)
    return left if left_score >= right_score else right


def _most_conservative_risk(left: str, right: str) -> str:
    """Return the higher risk level."""
    left_score = RISK_PRIORITY.get(left, 0)
    right_score = RISK_PRIORITY.get(right, 0)
    return left if left_score >= right_score else right
