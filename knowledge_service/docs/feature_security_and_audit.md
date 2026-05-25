# Feature: security_and_audit

## Migration Meaning
Security-sensitive scripts handle permissions, identity, secrets, audit trails, compliance checks, or issue security levels.

## Data Center Behavior
- Scripts may access local files, environment variables, user objects, groups, roles, or audit tables.
- Secrets may be stored in files, script parameters, or plugin configuration.
- Audit behavior may depend on server logs or database records.

## Cloud Limitation
- Cloud apps must use approved authentication, scopes, and secure storage patterns.
- Local files and database audit tables are not available.
- User privacy and app scopes affect what data can be read.

## Compatibility Assessment
- Security logic should default to NEEDS_REVIEW unless clearly supported.
- Local secrets, filesystem, database, or unsupported Java APIs can become BLOCKER.
- Identity conversion to accountId is usually MAJOR when access control is involved.

## Recommended Migration
- Inventory secrets and move them to secure Cloud-compatible storage.
- Validate app scopes and permissions.
- Replace local audit files with Cloud audit logs, external logging, or app storage.
- Re-test access control with representative users.

## Detection Patterns
- `security_level_check`
- `permission_check`
- `authentication_context_access`
- `file_read`
- `file_write`
- `direct_database_query`
- `username_identifier`

## Source Notes
- Security-sensitive automation should be verified during migration rehearsal and reviewed by administrators.
