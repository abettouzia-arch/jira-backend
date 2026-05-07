"""
Deterministic compatibility rules for JSU (JIRA Suite Utilities) DC → Cloud migration.
"""

JSU_RULES = {
    # ── BLOCKER ──────────────────────────────────────────────────────
    "jsu_extension_usage": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": (
            "JSU Groovy expressions are not supported in Cloud. "
            "Rewrite using Jira Automation rules or JSU Cloud (limited feature set)."
        ),
    },
    "direct_database_query": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": (
            "Database access in JSU scripts is not possible in Cloud. "
            "Use REST API v3 instead."
        ),
    },
    "java_api": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": (
            "Java API usage in JSU is not supported in Cloud. "
            "Use Jira Automation native actions."
        ),
    },
    "filesystem_access": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": (
            "File system access in JSU is not possible in Cloud. "
            "Use external storage solutions."
        ),
    },
    "active_objects_access": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": (
            "ActiveObjects is not available in JSU Cloud. "
            "Use Forge Storage API."
        ),
    },

    # ── MAJOR ────────────────────────────────────────────────────────
    "workflow_post_function": {
        "cloud_status": "NEEDS_RECREATION",
        "risk_level": "MAJOR",
        "recommended_action": (
            "JSU post-functions must be recreated using Jira Automation rules. "
            "Map each post-function to an equivalent Automation action."
        ),
    },
    "workflow_condition": {
        "cloud_status": "NEEDS_RECREATION",
        "risk_level": "MAJOR",
        "recommended_action": (
            "JSU conditions must be recreated using Jira Automation conditions. "
            "Review each condition and find the Automation equivalent."
        ),
    },
    "workflow_validator": {
        "cloud_status": "NEEDS_RECREATION",
        "risk_level": "MAJOR",
        "recommended_action": (
            "JSU validators must be recreated using Jira Automation validators. "
            "Some complex validators may require custom Forge apps."
        ),
    },
    "custom_field_update": {
        "cloud_status": "PARTIAL",
        "risk_level": "MAJOR",
        "recommended_action": (
            "Field updates in JSU must be recreated using "
            "Jira Automation 'Set field value' action."
        ),
    },
    "issue_transition": {
        "cloud_status": "PARTIAL",
        "risk_level": "MAJOR",
        "recommended_action": (
            "JSU transition triggers are partially supported. "
            "Use Jira Automation 'Transition issue' action."
        ),
    },
    "component_accessor": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "MAJOR",
        "recommended_action": (
            "ComponentAccessor is not available in JSU Cloud. "
            "Use Jira Automation field references instead."
        ),
    },
    "user_manager_access": {
        "cloud_status": "PARTIAL",
        "risk_level": "MAJOR",
        "recommended_action": (
            "User lookups in JSU must use accountId in Cloud. "
            "Replace username/userkey references."
        ),
    },

    # ── MINOR ────────────────────────────────────────────────────────
    "email_notification": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "MINOR",
        "recommended_action": (
            "JSU email actions are supported. "
            "Use Jira Automation 'Send email' action."
        ),
    },
    "issue_commenting": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "MINOR",
        "recommended_action": (
            "JSU comment actions are supported. "
            "Use Jira Automation 'Add comment' action."
        ),
    },
    "issue_assignment": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "MINOR",
        "recommended_action": (
            "JSU assign actions are supported. "
            "Use Jira Automation 'Assign issue' action."
        ),
    },
    "issue_creation": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "MINOR",
        "recommended_action": (
            "Issue creation is supported via Jira Automation "
            "'Create issue' action."
        ),
    },

    # ── INFO ─────────────────────────────────────────────────────────
    "rest_api_v3": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "INFO",
        "recommended_action": "REST API v3 calls are fully supported. No action needed.",
    },
    "accountid_identifier": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "INFO",
        "recommended_action": "accountId is the standard identifier in Cloud. No action needed.",
    },
}
