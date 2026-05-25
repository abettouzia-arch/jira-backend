# Feature: component_accessor

## Migration Meaning
`ComponentAccessor` is a Jira Data Center Java API entry point commonly used by ScriptRunner and Groovy scripts to reach Jira managers and services.

## Data Center Behavior
- Scripts can access internal Jira managers directly.
- Common calls include `getIssueManager`, `getCustomFieldManager`, `getUserManager`, `getWorkflowManager`, and `getProjectManager`.
- Scripts often combine `ComponentAccessor` with other Java APIs.

## Cloud Limitation
- Jira Cloud does not expose the Jira server-side Java API.
- Scripts must use supported Cloud APIs, ScriptRunner Cloud capabilities, Jira Automation, Forge, or REST API v3.
- Each manager call must be reviewed separately because some behaviors can be recreated while others need a full rewrite.

## Compatibility Assessment
- Cloud Status: PARTIAL or REWRITE_REQUIRED depending on the called manager.
- Risk: MAJOR by default.
- Escalate to BLOCKER when the script also uses filesystem, database, ActiveObjects, or unsupported Java execution.

## Recommended Migration
- Inventory each `ComponentAccessor` call.
- Replace issue operations with `/rest/api/3/issue`.
- Replace custom field discovery with `/rest/api/3/field`.
- Replace user lookups with accountId-based Cloud APIs.
- Rebuild workflow behavior using ScriptRunner Cloud workflow functions, Jira Automation, or Forge.

## Detection Patterns
- `ComponentAccessor`
- `ComponentAccessor.getIssueManager()`
- `ComponentAccessor.getCustomFieldManager()`
- `ComponentAccessor.getUserManager()`
- `ComponentAccessor.getWorkflowManager()`

## Source Notes
- Atlassian Cloud apps do not run inside the Jira Data Center JVM.
- ScriptRunner Cloud has a different execution and API model from ScriptRunner Data Center.
