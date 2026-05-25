# Plugin: JSU Cloud Migration

## Migration Meaning
JSU Data Center workflow customizations often need recreation in Cloud using JSU Cloud capabilities, Jira Automation, or native workflow configuration.

## Data Center Behavior
- JSU can provide post-functions, conditions, validators, field updates, issue actions, and workflow helpers.
- Some instances combine JSU behavior with Groovy or custom scripts.

## Cloud Considerations
- JSU Cloud does not always have feature parity with JSU Data Center.
- Complex workflow functions may need Jira Automation or a custom app.
- Java API, database, filesystem, and ActiveObjects usage are not portable.

## Compatibility Assessment
- JSU extension usage with unsupported Groovy: INCOMPATIBLE, BLOCKER.
- Workflow post-functions, conditions, validators: NEEDS_RECREATION, MAJOR.
- Simple comments, assignment, issue creation, and email actions can often be recreated.

## Recommended Migration
- Export an inventory of JSU workflow functions.
- Map each function to JSU Cloud, Jira Automation, or native Jira Cloud workflow configuration.
- Recreate and test transitions in a sandbox.
- Pay special attention to user identity, custom fields, and transition ordering.

## Detection Patterns
- `jsu_extension_usage`
- `workflow_post_function`
- `workflow_condition`
- `workflow_validator`
- `custom_field_update`
- `issue_transition`

## Source Notes
- Atlassian app assessment should be used to validate whether a Marketplace app has a Cloud migration path.
