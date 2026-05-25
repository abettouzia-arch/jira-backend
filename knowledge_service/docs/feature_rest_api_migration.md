# Feature: rest_api_migration

## Migration Meaning
REST API usage is generally the preferred migration target for Jira Cloud custom logic.

## Data Center Behavior
- Scripts may call Jira internal Java APIs or REST API v2.
- Some scripts call external systems using HTTP clients.
- Authentication may rely on server-side context.

## Cloud Compatibility
- Jira Cloud REST API v3 is the recommended API surface.
- REST API v2 can work for some endpoints but v3 is preferred.
- API authentication, scopes, permissions, rate limits, and pagination must be reviewed.

## Compatibility Assessment
- REST API v3: COMPATIBLE, INFO.
- REST API v2: COMPATIBLE or DEPRECATED, MINOR.
- External REST calls: COMPATIBLE or PARTIAL depending on authentication and network constraints.

## Recommended Migration
- Prefer `/rest/api/3`.
- Use accountId for users.
- Implement pagination and rate-limit handling.
- Replace direct Java manager calls with REST endpoints.
- Validate OAuth/API token or app authentication model.

## Detection Patterns
- `/rest/api/3`
- `/rest/api/2`
- `HttpURLConnection`
- `RESTClient`
- `http_request_execution`
- `external_rest_call`

## Source Notes
- Jira Cloud integrations should use supported Cloud APIs rather than internal Java APIs.
