"""
Deterministic compatibility rules for MISC/JMWE DC → Cloud migration.
"""

MISC_RULES = {
    # ── BLOCKER ──────────────────────────────────────────────────────
    "misc_workflow_extension_usage": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": (
            "MISC/JMWE Groovy expressions are not supported in Cloud. "
            "Rewrite using JMWE Cloud with Nunjucks templates."
        ),
    },
    "direct_database_query": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": (
            "Database access is not possible in JMWE Cloud. "
            "Use REST API v3 instead."
        ),
    },
    "java_api": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": (
            "Java API is not available in JMWE Cloud. "
            "Use JMWE Cloud REST-based actions."
        ),
    },
    "component_accessor": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": (
            "ComponentAccessor is not available in JMWE Cloud. "
            "Use JMWE Cloud field references with Nunjucks syntax."
        ),
    },
    "active_objects_access": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": (
            "ActiveObjects is not available in JMWE Cloud. "
            "Use Forge Storage API."
        ),
    },
    "filesystem_access": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": (
            "Filesystem access is not possible in JMWE Cloud. "
            "Use external storage solutions."
        ),
    },

    # ── MAJOR ────────────────────────────────────────────────────────
    "workflow_post_function": {
        "cloud_status": "REWRITE_REQUIRED",
        "risk_level": "MAJOR",
        "recommended_action": (
            "Groovy post-functions must be rewritten using "
            "JMWE Cloud Nunjucks-based post-functions."
        ),
    },
    "workflow_condition": {
        "cloud_status": "REWRITE_REQUIRED",
        "risk_level": "MAJOR",
        "recommended_action": (
            "Groovy conditions must be rewritten using "
            "JMWE Cloud condition syntax."
        ),
    },
    "workflow_validator": {
        "cloud_status": "REWRITE_REQUIRED",
        "risk_level": "MAJOR",
        "recommended_action": (
            "Groovy validators must be rewritten using "
            "JMWE Cloud validator syntax."
        ),
    },
    "custom_field_update": {
        "cloud_status": "PARTIAL",
        "risk_level": "MAJOR",
        "recommended_action": (
            "Field updates must use JMWE Cloud 'Set Field Value' "
            "with Nunjucks expressions instead of Groovy."
        ),
    },
    "user_manager_access": {
        "cloud_status": "PARTIAL",
        "risk_level": "MAJOR",
        "recommended_action": (
            "User lookups must use accountId in JMWE Cloud. "
            "Replace all username/userkey references."
        ),
    },
    "issue_transition": {
        "cloud_status": "PARTIAL",
        "risk_level": "MAJOR",
        "recommended_action": (
            "Transition logic must be rewritten using "
            "JMWE Cloud 'Transition Issue' action."
        ),
    },

    # ── MINOR ────────────────────────────────────────────────────────
    "issue_commenting": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "MINOR",
        "recommended_action": (
            "Comment actions are supported. "
            "Use JMWE Cloud 'Add Comment' action."
        ),
    },
    "email_notification": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "MINOR",
        "recommended_action": (
            "Email notifications are supported. "
            "Use JMWE Cloud 'Send Email' action."
        ),
    },
    "issue_assignment": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "MINOR",
        "recommended_action": (
            "Assignment actions are supported. "
            "Use JMWE Cloud 'Assign Issue' action."
        ),
    },

    # ── INFO ─────────────────────────────────────────────────────────
    "rest_api_v3": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "INFO",
        "recommended_action": "REST API v3 is fully supported. No action needed.",
    },
    "accountid_identifier": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "INFO",
        "recommended_action": "accountId is the standard identifier. No action needed.",
    },
    "issue_creation": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "INFO",
        "recommended_action": "Issue creation is supported via JMWE Cloud actions.",
    },
}
