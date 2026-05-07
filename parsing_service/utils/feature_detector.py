"""
Shared Feature Detection logic for all Jira parsers.
Provides both deterministic keyword scanning and AI-powered semantic analysis.
"""

import json
import logging

from parsing_service.ollama_client import generate_text, OllamaConnectionError

logger = logging.getLogger(__name__)

ALL_DETECTABLE_FEATURES = [
    "java_api", "component_accessor", "issue_manager_access",
    "custom_field_manager_access", "workflow_manager_access",
    "user_manager_access", "project_manager_access", "search_service_access",
    "authentication_context_access", "event_dispatcher_access",
    "db_access", "direct_database_query", "sql_query_execution",
    "active_objects_access", "jdbc_connection_usage",
    "filesystem_access", "file_read", "file_write", "file_delete",
    "local_storage_usage", "temporary_file_creation",
    "rest_api_v1", "rest_api_v2", "rest_api_v3",
    "rest_issue_api", "rest_project_api", "rest_user_api",
    "http_request_execution", "external_rest_call",
    "username_identifier", "userkey_identifier", "accountid_identifier", "user_lookup",
    "workflow_transition_logic", "workflow_condition", "workflow_validator",
    "workflow_post_function", "custom_workflow_script", "workflow_script_execution",
    "event_listener", "issue_event_listener", "custom_event_handler", "event_dispatching",
    "issue_creation", "issue_update", "issue_transition", "issue_commenting",
    "issue_linking", "issue_assignment", "issue_deletion",
    "jql_query_execution", "advanced_jql_search", "custom_jql_function",
    "plugin_api_usage", "scriptrunner_api_usage", "jsu_extension_usage",
    "misc_workflow_extension_usage",
    "external_service_call", "third_party_api_call", "webhook_call",
    "incoming_webhook", "outgoing_webhook",
    "scheduled_job", "cron_job_execution", "background_task", "asynchronous_task",
    "permission_check", "group_membership_check", "role_check", "security_level_check",
    "custom_field_read", "custom_field_update", "custom_field_validation", "custom_field_creation",
    "project_creation", "project_update", "project_configuration_access",
    "email_notification", "custom_notification_logic",
]

QUICK_SCAN_HINTS = {
    "ComponentAccessor": "component_accessor",
    "IssueManager": "issue_manager_access",
    "CustomFieldManager": "custom_field_manager_access",
    "WorkflowManager": "workflow_manager_access",
    "UserManager": "user_manager_access",
    "ProjectManager": "project_manager_access",
    "SearchService": "search_service_access",
    "JiraAuthenticationContext": "authentication_context_access",
    "EventDispatcher": "event_dispatcher_access",
    "ActiveObjects": "active_objects_access",
    "Connection": "jdbc_connection_usage",
    "File": "filesystem_access",
    "new File": "file_write",
    "HttpURLConnection": "http_request_execution",
    "import com.atlassian.jira": "java_api",
    "import com.onresolve": "scriptrunner_api_usage",
    "restClient": "external_rest_call",
    "ScheduledJob": "scheduled_job",
}


def quick_scan_features(code: str) -> list[str]:
    """Fast, deterministic keyword scan."""
    detected = set()
    for keyword, feature in QUICK_SCAN_HINTS.items():
        if keyword in code:
            detected.add(feature)
    return list(detected)


def ai_detect_features(code: str, context_name: str) -> list[str]:
    """Deep semantic analysis using Ollama."""
    prompt = f"""
You are an expert Jira Data Center to Jira Cloud migration analyst.

Your task is to inspect the following code snippet from "{context_name}"
and identify which migration-relevant features are ACTUALLY USED.

You must detect only features that are clearly present in the code logic,
imports, API usage, database usage, filesystem usage, workflow behavior,
event handling, REST calls, JQL, permissions, notifications, scheduling,
or plugin-specific APIs.

IMPORTANT RULES:
1. Return ONLY valid JSON.
2. Do NOT return markdown.
3. Do NOT add explanations.
4. Use this exact JSON format:
   {{"features": ["feature_name_1", "feature_name_2"]}}
5. Use ONLY feature names from the allowed list below.
6. Do NOT invent new feature names.
7. If no feature is confidently detected, return:
   {{"features": []}}
8. Do not include duplicates.
9. Detect only features that are actually used, not merely mentioned in comments or strings.
10. Prefer precision over recall.

ALLOWED FEATURES:
{json.dumps(ALL_DETECTABLE_FEATURES, indent=2)}

EXAMPLES:

Example 1:
Code:
import com.atlassian.jira.component.ComponentAccessor
def issueManager = ComponentAccessor.getIssueManager()
Output:
{{"features": ["java_api", "component_accessor", "issue_manager_access"]}}

Example 2:
Code:
def text = "ComponentAccessor"
Output:
{{"features": []}}

Example 3:
Code:
new URL("https://api.example.com").openConnection()
Output:
{{"features": ["external_service_call", "http_request_execution", "third_party_api_call"]}}

Now analyze this code:

{code[:4000]}
"""
    try:
        raw_response = generate_text(prompt=prompt, model="llama3", format_json=True)
        parsed = json.loads(raw_response)
        features = parsed.get("features", [])

        if not isinstance(features, list):
            return []

        cleaned_features = []
        for feature in features:
            if isinstance(feature, str) and feature in ALL_DETECTABLE_FEATURES:
                cleaned_features.append(feature)

        return list(dict.fromkeys(cleaned_features))

    except (json.JSONDecodeError, OllamaConnectionError, RuntimeError, TypeError) as e:
        logger.warning("AI Detection failed for %s: %s", context_name, e)
        return []
