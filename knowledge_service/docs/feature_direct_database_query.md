# Feature: direct_database_query

## Migration Meaning
Direct SQL or JDBC access means the Jira customization reads or writes Jira data through the database rather than supported application APIs.

## Data Center Behavior
- Scripts may open JDBC connections.
- Scripts may use `Sql.newInstance`, `Connection`, `PreparedStatement`, or direct SQL queries.
- Some custom reports, validators, listeners, and scheduled jobs depend on database tables.

## Cloud Limitation
- Jira Cloud does not provide database access.
- Atlassian Cloud data must be accessed through supported REST APIs, app APIs, exports, or approved data pipelines.
- Direct table assumptions are not portable to Cloud.

## Compatibility Assessment
- Cloud Status: INCOMPATIBLE.
- Risk: BLOCKER.
- Confidence should be high when SQL/JDBC patterns are present.

## Recommended Migration
- Replace database reads with REST API v3 calls or Atlassian Data Lake where appropriate.
- Replace database writes with supported Jira Cloud REST operations.
- For reporting use cases, rebuild as dashboards, BI exports, or Forge/Connect app logic.
- Validate performance and rate limits because API-based access differs from SQL access.

## Detection Patterns
- `Sql.newInstance`
- `groovy.sql.Sql`
- `DriverManager.getConnection`
- `PreparedStatement`
- `SELECT ... FROM jiraissue`
- `AO_` table names

## Source Notes
- Atlassian Cloud does not expose the underlying product database to customers or apps.
