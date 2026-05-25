# Feature: custom_field_management

## Migration Meaning
Custom field logic is common in Jira Data Center scripts and workflow functions. It can include reading values, updating values, validating values, discovering field metadata, or creating fields.

## Data Center Behavior
- Scripts often use `CustomFieldManager`.
- Field values can be accessed through Jira Java objects.
- Some scripts rely on field names, field IDs, contexts, options, or direct database tables.

## Cloud Limitation
- Jira Cloud custom fields must be accessed through REST API v3 or app-supported APIs.
- Field context, option handling, and screen behavior can differ from Data Center.
- Direct Java manager access is not available.

## Compatibility Assessment
- Custom field read through REST: COMPATIBLE or INFO.
- Custom field update through supported APIs: PARTIAL or MINOR.
- CustomFieldManager usage: PARTIAL or MAJOR.
- Direct database field access: INCOMPATIBLE or BLOCKER.

## Recommended Migration
- Replace `CustomFieldManager` with `/rest/api/3/field` and issue field APIs.
- Use custom field IDs rather than display names when possible.
- Validate field contexts and option IDs after migration.
- Re-test workflow screens and transition screens in Cloud.

## Detection Patterns
- `custom_field_manager_access`
- `custom_field_read`
- `custom_field_update`
- `custom_field_validation`
- `custom_field_creation`
- `getCustomFieldObject`

## Source Notes
- Jira Cloud field metadata and issue field operations are API-driven.
