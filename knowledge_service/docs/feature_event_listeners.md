# Feature: event_listeners

## Migration Meaning
Event listeners react to Jira issue or system events and often perform automation, notifications, synchronization, or field updates.

## Data Center Behavior
- Listeners can use ScriptRunner or custom Java/Groovy logic.
- They may access event objects, issue managers, users, groups, permissions, or external APIs.
- Some listeners run synchronously and may affect user workflows.

## Cloud Limitation
- Cloud listener models are different and may depend on marketplace app capabilities, webhooks, Jira Automation, Forge triggers, or external integration workers.
- Event payloads and identity fields differ from Data Center.

## Compatibility Assessment
- Simple notification or update listener: PARTIAL.
- Listener using Java API, database, filesystem, or unsupported managers: MAJOR or BLOCKER.
- External webhooks can often be rebuilt with Jira Automation or Forge.

## Recommended Migration
- Identify trigger event, target action, and side effects.
- Rebuild simple listeners with Jira Automation.
- Use Forge triggers or webhooks for complex integrations.
- Add retry and idempotency for external calls.
- Validate permissions and actor identity in Cloud.

## Detection Patterns
- `event_listener`
- `issue_event_listener`
- `custom_event_handler`
- `EventDispatcher`
- `IssueEvent`
- `webhook_call`

## Source Notes
- Jira Cloud automation and app event models should replace server-side listener assumptions.
