# Jira Cloud Architecture

## Key Limitations

- No direct database access
- No filesystem access
- REST API is the primary integration method
- Uses accountId instead of username/userKey

## Authentication

- OAuth 2.0
- API tokens

## Automation

- Jira Automation replaces most scripting use cases
- Rule-based triggers and actions

## REST API

- v3 is recommended
- v2 supported
- v1 deprecated

## App Frameworks

- Forge (recommended)
- Connect (legacy)

---

## Feature: java_api

### Cloud Status
INCOMPATIBLE

### Risk
BLOCKER

### Why
Jira Cloud does not allow execution of Java code.

### Recommended Migration
- Use REST API v3
- Use Forge backend functions

### Keywords
java_api, cloud limitation, jira cloud

---

## Feature: direct_database_query

### Cloud Status
INCOMPATIBLE

### Risk
BLOCKER

### Why
Cloud does not allow database access.

### Recommended Migration
- Replace with REST API calls

### Keywords
database, sql, jira cloud limitation