"""
Deterministic compatibility rules for ScriptRunner DC → Cloud migration.
Each rule maps a detected feature to its cloud compatibility status.
"""

SCRIPTRUNNER_RULES = {
    # ── BLOCKER ──────────────────────────────────────────────────────
    "direct_database_query": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": (
            "Sql.newInstance() is not supported in Cloud. "
            "Rewrite using Jira REST API v3 endpoints."
        ),
    },
    "jdbc_connection_usage": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": (
            "Direct JDBC connections are blocked in Cloud. "
            "Use Forge Storage API or REST API instead."
        ),
    },
    "active_objects_access": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": (
            "ActiveObjects ORM is not available in ScriptRunner Cloud. "
            "Migrate to Forge Storage API."
        ),
    },
    "filesystem_access": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": (
            "Local filesystem access is blocked in Cloud. "
            "Use external storage (S3, Forge Storage) instead."
        ),
    },
    "file_read": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": "File read not supported. Use Forge Storage API.",
    },
    "file_write": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": "File write not supported. Use Forge Storage API.",
    },
    "java_api": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": (
            "Raw Java API access is not available in ScriptRunner Cloud. "
            "Rewrite using ScriptRunner Cloud SDK or REST API v3."
        ),
    },
    "authentication_context_access": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "BLOCKER",
        "recommended_action": (
            "JiraAuthenticationContext is not available in Cloud. "
            "Use REST API Bearer token authentication."
        ),
    },

    # ── MAJOR ────────────────────────────────────────────────────────
    "component_accessor": {
        "cloud_status": "PARTIAL",
        "risk_level": "MAJOR",
        "recommended_action": (
            "ComponentAccessor has 40-60% coverage in ScriptRunner Cloud. "
            "Review each manager call and replace unsupported ones with REST API v3."
        ),
    },
    "issue_manager_access": {
        "cloud_status": "PARTIAL",
        "risk_level": "MAJOR",
        "recommended_action": (
            "IssueManager is partially supported. "
            "Replace with REST API v3 /rest/api/3/issue endpoints."
        ),
    },
    "user_manager_access": {
        "cloud_status": "PARTIAL",
        "risk_level": "MAJOR",
        "recommended_action": (
            "UserManager is partially supported. "
            "Replace username/userkey lookups with accountId (GDPR requirement)."
        ),
    },
    "username_identifier": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "MAJOR",
        "recommended_action": (
            "Username-based user identification is not supported in Cloud. "
            "Migrate to accountId as per GDPR requirements."
        ),
    },
    "userkey_identifier": {
        "cloud_status": "INCOMPATIBLE",
        "risk_level": "MAJOR",
        "recommended_action": (
            "Userkey identification is not supported in Cloud. "
            "Migrate to accountId."
        ),
    },
    "custom_field_manager_access": {
        "cloud_status": "PARTIAL",
        "risk_level": "MAJOR",
        "recommended_action": (
            "CustomFieldManager has limited support. "
            "Use REST API v3 /rest/api/3/field endpoints."
        ),
    },
    "workflow_manager_access": {
        "cloud_status": "PARTIAL",
        "risk_level": "MAJOR",
        "recommended_action": (
            "WorkflowManager scripting is limited in Cloud. "
            "Use ScriptRunner Cloud workflow functions."
        ),
    },

    # ── MINOR ────────────────────────────────────────────────────────
    "rest_api_v1": {
        "cloud_status": "DEPRECATED",
        "risk_level": "MINOR",
        "recommended_action": "REST API v1 is deprecated. Migrate to REST API v3.",
    },
    "rest_api_v2": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "MINOR",
        "recommended_action": "REST API v2 is supported. Consider migrating to v3.",
    },
    "workflow_post_function": {
        "cloud_status": "PARTIAL",
        "risk_level": "MINOR",
        "recommended_action": (
            "Post-functions are supported in ScriptRunner Cloud "
            "but with limited Groovy API surface."
        ),
    },
    "workflow_condition": {
        "cloud_status": "PARTIAL",
        "risk_level": "MINOR",
        "recommended_action": "Conditions supported in ScriptRunner Cloud with limitations.",
    },
    "workflow_validator": {
        "cloud_status": "PARTIAL",
        "risk_level": "MINOR",
        "recommended_action": "Validators supported in ScriptRunner Cloud with limitations.",
    },
    "scheduled_job": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "MINOR",
        "recommended_action": "Use ScriptRunner Cloud scheduled jobs.",
    },
    "http_request_execution": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "MINOR",
        "recommended_action": "External HTTP calls supported. Verify allowlist configuration.",
    },

    # ── INFO ─────────────────────────────────────────────────────────
    "rest_api_v3": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "INFO",
        "recommended_action": "REST API v3 is fully supported in Cloud. No action needed.",
    },
    "accountid_identifier": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "INFO",
        "recommended_action": "accountId is the standard identifier in Cloud. No action needed.",
    },
    "issue_creation": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "INFO",
        "recommended_action": "Issue creation via REST API v3 is fully supported.",
    },
    "issue_update": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "INFO",
        "recommended_action": "Issue update via REST API v3 is fully supported.",
    },
    "issue_transition": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "INFO",
        "recommended_action": "Issue transition via REST API v3 is fully supported.",
    },
    "issue_commenting": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "INFO",
        "recommended_action": "Issue commenting via REST API v3 is fully supported.",
    },
    "custom_field_read": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "INFO",
        "recommended_action": "Custom field read via REST API v3 is supported.",
    },
    "email_notification": {
        "cloud_status": "COMPATIBLE",
        "risk_level": "INFO",
        "recommended_action": "Email notifications are supported in Cloud.",
    },
}
