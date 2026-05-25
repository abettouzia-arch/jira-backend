# Feature: workflow_functions

## Migration Meaning
Workflow validators, conditions, and post-functions often contain custom logic that must be reviewed during Jira Data Center to Cloud migration.

## Data Center Behavior
- ScriptRunner, JSU, JMWE, and native workflows can run server-side custom logic.
- Groovy workflow logic may use issue managers, custom field managers, users, groups, permissions, or external services.
- Post-functions can mutate issues during transitions.

## Cloud Limitation
- Cloud workflow extensibility is different from Data Center.
- Some marketplace apps provide Cloud equivalents, but feature parity is not guaranteed.
- Complex Groovy scripts usually need rewriting or recreation.

## Compatibility Assessment
- Simple workflow functions: PARTIAL or NEEDS_RECREATION.
- Workflow functions with Java API, database, filesystem, or unsupported managers: REWRITE_REQUIRED or INCOMPATIBLE.
- Risk: MINOR to MAJOR depending on complexity.

## Recommended Migration
- Classify each workflow rule as validator, condition, or post-function.
- Map simple cases to Jira Automation or the Cloud app equivalent.
- Rewrite complex scripts with REST API v3, Forge, or ScriptRunner Cloud features.
- Test transitions in a sandbox because workflow behavior is user-facing and business-critical.

## Detection Patterns
- `workflow_post_function`
- `workflow_condition`
- `workflow_validator`
- `transition`
- `PostFunction`
- `Validator`
- `Condition`

## Source Notes
- Atlassian recommends assessing apps and workflow customizations before migration.
