# Feature: issue_operations

## Migration Meaning
Issue operations include creating, updating, transitioning, commenting, linking, assigning, or deleting issues.

## Data Center Behavior
- Scripts often use `IssueManager`, `IssueService`, or mutable issue objects.
- Workflow post-functions and listeners frequently modify issues.
- Some scripts assume synchronous server-side mutation.

## Cloud Compatibility
- Most issue operations are supported through Jira Cloud REST API v3.
- Workflow and permission context must be validated.
- Some operations require transition IDs, field IDs, accountIds, and explicit permissions.

## Compatibility Assessment
- REST API v3 issue creation/update/comment/transition: COMPATIBLE or INFO.
- Java `IssueManager` or mutable issue object usage: PARTIAL or MAJOR.
- Issue deletion or bulk operations: NEEDS_REVIEW due to risk and permissions.

## Recommended Migration
- Replace `IssueManager` with `/rest/api/3/issue` operations.
- Use transition APIs for workflow transitions.
- Use accountId for assignee and reporter.
- Add error handling for permissions, field screens, required fields, and rate limits.
- Validate behavior in a migration rehearsal.

## Detection Patterns
- `issue_manager_access`
- `issue_creation`
- `issue_update`
- `issue_transition`
- `issue_commenting`
- `issue_linking`
- `issue_assignment`
- `issue_deletion`

## Source Notes
- Jira Cloud issue operations are API-supported, but scripts must be rewritten away from Java object mutation.
