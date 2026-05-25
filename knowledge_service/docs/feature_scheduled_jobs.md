# Feature: scheduled_job

## Migration Meaning
Scheduled jobs execute recurring logic such as cleanup, synchronization, reporting, notifications, or batch updates.

## Data Center Behavior
- ScriptRunner Data Center jobs can run Groovy on a schedule.
- Jobs may access Java APIs, database tables, files, or external services.
- Long-running jobs may depend on local server resources.

## Cloud Compatibility
- ScriptRunner Cloud supports scheduled jobs with a different execution model and API surface.
- Jira Automation can cover some scheduled use cases.
- Forge scheduled triggers can be used for app-owned workloads.

## Compatibility Assessment
- Simple scheduled REST/API logic: COMPATIBLE or PARTIAL.
- Jobs using Java API, database, filesystem, or local server state: REWRITE_REQUIRED or INCOMPATIBLE.
- Risk: MINOR to MAJOR depending on side effects and dependencies.

## Recommended Migration
- Identify schedule, data volume, and side effects.
- Replace local Jira Java APIs with REST API v3.
- Add pagination, retry, and rate-limit handling.
- Move persistent state to Forge Storage or external storage.
- Test runtime limits in Cloud.

## Detection Patterns
- `scheduled_job`
- `cron_job_execution`
- `background_task`
- `asynchronous_task`
- `ScheduledJob`
- `cron`

## Source Notes
- Cloud execution is managed and may enforce limits that do not exist in Data Center scripts.
