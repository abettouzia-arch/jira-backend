"""
Deterministic rule engine for Jira DC → Cloud compatibility analysis.
Maps detected features to compatibility status using plugin-specific rules.
"""

import logging

from compatibility_service.engine.rules.jsu_rules import JSU_RULES
from compatibility_service.engine.rules.misc_rules import MISC_RULES
from compatibility_service.engine.rules.scriptrunner_rules import SCRIPTRUNNER_RULES

logger = logging.getLogger(__name__)

# Risk level priority for sorting and scoring
RISK_PRIORITY = {
    "BLOCKER": 4,
    "MAJOR": 3,
    "MINOR": 2,
    "INFO": 1,
}

# Default rule when a feature is detected but has no specific rule
DEFAULT_RULE = {
    "cloud_status": "NEEDS_REVIEW",
    "risk_level": "MINOR",
    "recommended_action": (
        "Feature detected but no specific compatibility rule found. "
        "Manual review recommended."
    ),
}


def get_rules_for_plugin(plugin: str) -> dict:
    """
    Return the appropriate rules dictionary based on plugin name.
    Falls back to ScriptRunner rules for unknown plugins.
    """
    plugin_lower = plugin.lower()

    if "jsu" in plugin_lower:
        return JSU_RULES
    if "misc" in plugin_lower or "jmwe" in plugin_lower:
        return MISC_RULES
    if "scriptrunner" in plugin_lower or "native" in plugin_lower:
        return SCRIPTRUNNER_RULES

    # Default to ScriptRunner rules for unknown plugins
    logger.warning("Unknown plugin '%s' — using ScriptRunner rules as fallback.", plugin)
    return SCRIPTRUNNER_RULES


def analyze_component(component: dict) -> dict:
    """
    Analyze a single JiraComponent and return its compatibility result.

    Args:
        component: dict with keys: component_id, plugin, features_detected, ...

    Returns:
        dict with compatibility fields filled in
    """
    component_id = component.get("component_id", "unknown")
    plugin = component.get("plugin", "native")
    features = component.get("features_detected", [])

    logger.info(
        "Analyzing component %s (plugin: %s, features: %d)",
        component_id, plugin, len(features)
    )

    rules = get_rules_for_plugin(plugin)
    feature_results = []
    highest_risk = "INFO"

    for feature in features:
        rule = rules.get(feature, DEFAULT_RULE)

        feature_results.append({
            "feature": feature,
            "cloud_status": rule["cloud_status"],
            "risk_level": rule["risk_level"],
            "recommended_action": rule["recommended_action"],
        })

        # Track the highest risk level
        if RISK_PRIORITY.get(rule["risk_level"], 0) > RISK_PRIORITY.get(highest_risk, 0):
            highest_risk = rule["risk_level"]

    # Determine overall component cloud status
    overall_status = _compute_overall_status(feature_results)

    return {
        "component_id": component_id,
        "component_type": component.get("component_type", ""),
        "plugin": plugin,
        "location": component.get("location", {}),
        "features_analyzed": feature_results,
        "overall_status": overall_status,
        "risk_level": highest_risk,
        "is_blocker": highest_risk == "BLOCKER",
        "recommended_action": _compute_recommended_action(feature_results),
        "source_code": component.get("source_code", ""),
    }


def _compute_overall_status(feature_results: list[dict]) -> str:
    """
    Compute the overall cloud status for a component
    based on its worst feature result.
    """
    if not feature_results:
        return "COMPATIBLE"

    priority_order = [
        "INCOMPATIBLE",
        "REWRITE_REQUIRED",
        "NEEDS_RECREATION",
        "NEEDS_REVIEW",
        "PARTIAL",
        "DEPRECATED",
        "COMPATIBLE",
    ]

    statuses = {r["cloud_status"] for r in feature_results}

    for status in priority_order:
        if status in statuses:
            return status

    return "COMPATIBLE"


def _compute_recommended_action(feature_results: list[dict]) -> str:
    """
    Build a concise recommended action summary for the component.
    Prioritizes BLOCKER and MAJOR actions.
    """
    if not feature_results:
        return "No issues detected. Component is likely compatible."

    priority_actions = [
        r["recommended_action"]
        for r in feature_results
        if r["risk_level"] in ("BLOCKER", "MAJOR")
    ]

    if priority_actions:
        return " | ".join(priority_actions[:3])

    return feature_results[0]["recommended_action"]


def analyze_components(components: list[dict]) -> list[dict]:
    """
    Analyze a list of JiraComponents.
    Returns a list of compatibility results.
    """
    results = []
    for component in components:
        try:
            result = analyze_component(component)
            results.append(result)
        except (KeyError, TypeError, ValueError) as e:
            logger.error(
                "Failed to analyze component %s: %s",
                component.get("component_id", "unknown"), e
            )

    logger.info(
        "Analysis complete: %d components analyzed, %d blockers found.",
        len(results),
        sum(1 for r in results if r["is_blocker"])
    )

    return results
