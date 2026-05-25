# Feature: jql_search

## Migration Meaning
JQL search logic is used to find issues, drive reports, update batches, validate transitions, or trigger automation.

## Data Center Behavior
- Scripts may use `SearchService`, Java issue search APIs, or direct Lucene/Jira internals.
- Large JQL searches may be executed server-side without Cloud API rate limits.
- Scripts may rely on usernames, project keys, custom fields, or app-specific JQL functions.

## Cloud Compatibility
- JQL is supported in Jira Cloud through REST API v3.
- Custom JQL functions may depend on app availability and feature parity.
- Search APIs require pagination and rate-limit handling.

## Compatibility Assessment
- Standard JQL through REST API v3: COMPATIBLE or INFO.
- Data Center Java `SearchService` usage: PARTIAL or MAJOR.
- Custom JQL functions: PARTIAL or NEEDS_REVIEW.
- Direct database/Lucene access: INCOMPATIBLE or BLOCKER.

## Recommended Migration
- Replace Java `SearchService` calls with `/rest/api/3/search/jql` or the current Cloud search endpoint.
- Implement pagination and field selection.
- Review custom JQL functions and app dependencies.
- Replace username references with accountId-compatible JQL where applicable.

## Detection Patterns
- `jql_query_execution`
- `advanced_jql_search`
- `custom_jql_function`
- `SearchService`
- `parseQuery`
- `searchProvider`

## Source Notes
- Jira Cloud supports JQL, but script execution and search access patterns must be Cloud-safe.
