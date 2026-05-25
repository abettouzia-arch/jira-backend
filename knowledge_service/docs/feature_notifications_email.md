# Feature: notifications_email

## Migration Meaning
Notification scripts send messages to users, teams, or external systems when Jira events occur.

## Data Center Behavior
- Scripts may send email directly through Java mail APIs or Jira notification managers.
- Notifications may use usernames, emails, groups, roles, custom fields, or watchers.
- Some scripts build custom message templates.

## Cloud Compatibility
- Jira Cloud supports native notifications and Automation email actions.
- Direct server-side mail APIs are not portable.
- Email visibility can be restricted by privacy settings.

## Compatibility Assessment
- Jira Automation email action: COMPATIBLE or MINOR.
- Custom direct mail sending: PARTIAL or MAJOR.
- Email lookup by username/userKey: MAJOR.
- Notification logic requiring Java APIs: REWRITE_REQUIRED.

## Recommended Migration
- Prefer Jira Automation for standard notifications.
- Use accountId-based recipients where possible.
- Validate email visibility and privacy settings.
- For complex templates, use Forge, external integration middleware, or approved notification services.

## Detection Patterns
- `email_notification`
- `custom_notification_logic`
- `NotificationManager`
- `sendEmail`
- `javax.mail`
- `watchers`

## Source Notes
- Cloud notification behavior should be tested with real permissions and privacy settings.
