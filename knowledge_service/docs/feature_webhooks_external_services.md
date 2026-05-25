# Feature: webhooks_external_services

## Migration Meaning
External service calls and webhooks connect Jira automation to systems such as CI/CD, ITSM, CRM, Slack, Teams, or custom business services.

## Data Center Behavior
- Scripts can call external URLs using Java or Groovy HTTP clients.
- Authentication may be stored locally or read from files.
- Network access may rely on internal infrastructure.

## Cloud Compatibility
- HTTP calls can be supported, but authentication, allowlists, rate limits, and network accessibility must be reviewed.
- Internal-only services may not be reachable from Atlassian Cloud.
- Webhooks and Forge/Automation can replace many server-side integrations.

## Compatibility Assessment
- Public HTTP calls with supported authentication: COMPATIBLE or MINOR.
- Internal network calls: PARTIAL or MAJOR.
- Calls depending on local files, server trust stores, or database secrets: MAJOR or BLOCKER.

## Recommended Migration
- Replace local credentials with secure app configuration or external secret management.
- Validate endpoint reachability from Cloud.
- Add timeout, retry, and idempotency.
- Prefer Jira Automation web requests, Forge functions, or external integration middleware.

## Detection Patterns
- `webhook_call`
- `incoming_webhook`
- `outgoing_webhook`
- `external_service_call`
- `third_party_api_call`
- `HttpURLConnection`
- `RESTClient`

## Source Notes
- Cloud integrations should be designed for internet-reachable endpoints and explicit authentication.
