"""
Compatibility Matrix builder for Jira DC → Cloud migration analysis.
Aggregates individual component results into a summary matrix.
"""

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

RISK_PRIORITY = {
    "BLOCKER": 4,
    "MAJOR": 3,
    "MINOR": 2,
    "INFO": 1,
}


def build_matrix(analysis_id: str, component_results: list[dict]) -> dict:
    """
    Build a CompatibilityMatrix from a list of analyzed component results.

    Args:
        analysis_id: the ID from the parsing service
        component_results: list of dicts returned by the hybrid engine

    Returns:
        dict representing the full CompatibilityMatrix
    """
    matrix_id = str(uuid.uuid4())
    total = len(component_results)

    if total == 0:
        logger.warning("No components to build matrix from.")
        return _empty_matrix(matrix_id, analysis_id)

    blockers = [
        result for result in component_results
        if _get_risk(result) == "BLOCKER"
    ]
    majors = [
        result for result in component_results
        if _get_risk(result) == "MAJOR"
    ]
    minors = [
        result for result in component_results
        if _get_risk(result) == "MINOR"
    ]
    infos = [
        result for result in component_results
        if _get_risk(result) == "INFO"
    ]

    incompatible = [
        result for result in component_results
        if _get_status(result) == "INCOMPATIBLE"
    ]
    partial = [
        result for result in component_results
        if _get_status(result) == "PARTIAL"
    ]
    compatible = [
        result for result in component_results
        if _get_status(result) == "COMPATIBLE"
    ]
    needs_review = [
        result for result in component_results
        if _get_status(result) in (
            "NEEDS_REVIEW",
            "NEEDS_RECREATION",
            "REWRITE_REQUIRED",
            "DEPRECATED",
        )
    ]

    score = _compute_migration_score(total, blockers, majors, minors)
    recommendation = _compute_migration_recommendation(score, len(blockers))

    matrix = {
        "matrix_id": matrix_id,
        "analysis_id": analysis_id,
        "analyzed_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_components": total,
            "blocker_count": len(blockers),
            "major_count": len(majors),
            "minor_count": len(minors),
            "info_count": len(infos),
            "compatible_count": len(compatible),
            "partial_count": len(partial),
            "incompatible_count": len(incompatible),
            "needs_review_count": len(needs_review),
            "migration_score": score,
            "migration_recommendation": recommendation,
        },
        "components": component_results,
        "blockers": [
            {
                "component_id": result.get("component_id", "unknown"),
                "plugin": result.get("plugin", ""),
                "risk_level": _get_risk(result),
                "overall_status": _get_status(result),
                "recommended_action": result.get("recommended_action", ""),
                "confidence": result.get("confidence"),
            }
            for result in blockers
        ],
    }

    logger.info(
        "Matrix built — score: %d/100 | blockers: %d | majors: %d | total: %d",
        score,
        len(blockers),
        len(majors),
        total,
    )

    return matrix


def _get_status(component_result: dict) -> str:
    """
    Return the final compatibility status if present,
    otherwise fall back to the legacy overall_status.
    """
    return component_result.get(
        "final_status",
        component_result.get("overall_status", "NEEDS_REVIEW"),
    )


def _get_risk(component_result: dict) -> str:
    """
    Return the final compatibility risk if present,
    otherwise fall back to the legacy risk_level.
    """
    return component_result.get(
        "final_risk",
        component_result.get("risk_level", "MINOR"),
    )


def _compute_migration_score(
    total: int,
    blockers: list,
    majors: list,
    minors: list,
) -> int:
    """
    Compute a migration readiness score from 0 to 100.
    100 = fully ready, 0 = not ready at all.

    Scoring logic:
    - Each BLOCKER removes 20 points (max -60)
    - Each MAJOR removes 10 points (max -30)
    - Each MINOR removes 2 points (max -10)
    """
    if total == 0:
        return 100

    score = 100
    score -= min(len(blockers) * 20, 60)
    score -= min(len(majors) * 10, 30)
    score -= min(len(minors) * 2, 10)

    return max(0, score)


def _compute_migration_recommendation(score: int, blocker_count: int) -> str:
    """
    Return a human-readable migration recommendation based on score and blockers.
    """
    if blocker_count > 0:
        return (
            f"Migration blocked — {blocker_count} blocker(s) must be resolved before migration. "
            "Address all BLOCKER items and re-analyze."
        )
    if score >= 80:
        return (
            "Migration ready — minor adjustments required. "
            "Review MAJOR items and proceed with migration plan."
        )
    if score >= 50:
        return (
            "Migration possible with significant effort. "
            "Multiple components require rewriting or adaptation."
        )
    return (
        "Migration not recommended at this stage. "
        "Major architectural changes required before migrating to Cloud."
    )


def _empty_matrix(matrix_id: str, analysis_id: str) -> dict:
    """Return an empty matrix when no components are provided."""
    return {
        "matrix_id": matrix_id,
        "analysis_id": analysis_id,
        "analyzed_at": datetime.utcnow().isoformat(),
        "summary": {
            "total_components": 0,
            "blocker_count": 0,
            "major_count": 0,
            "minor_count": 0,
            "info_count": 0,
            "compatible_count": 0,
            "partial_count": 0,
            "incompatible_count": 0,
            "needs_review_count": 0,
            "migration_score": 100,
            "migration_recommendation": "No components found to analyze.",
        },
        "components": [],
        "blockers": [],
    }


def get_summary(matrix: dict) -> dict:
    """Return only the summary section of a matrix."""
    return matrix.get("summary", {})


def get_blockers(matrix: dict) -> list:
    """Return only the blocker components from a matrix."""
    return matrix.get("blockers", [])
