# Feature: user_identity_accountid

## Migration Meaning
Jira Cloud uses `accountId` as the primary user identifier. Legacy username and userKey logic from Data Center needs review.

## Data Center Behavior
- Scripts may reference users by username, userKey, email, or display name.
- UserManager and authentication context APIs often return Data Center user objects.
- Older scripts may store usernames in custom fields, comments, or configuration.

## Cloud Limitation
- Username and userKey are not reliable Cloud identifiers.
- Cloud APIs use accountId for user references.
- Privacy controls can restrict access to email and display name.

## Compatibility Assessment
- Cloud Status: PARTIAL or INCOMPATIBLE depending on usage.
- Risk: MAJOR when username/userKey drives assignment, permissions, approvals, or notifications.
- Risk can be INFO when the code already uses accountId.

## Recommended Migration
- Replace username and userKey references with accountId.
- Build a user mapping step before migration.
- Validate inactive users, app users, and external accounts.
- Avoid matching users by display name.

## Detection Patterns
- `getUserByName`
- `getUserByKey`
- `user.name`
- `userKey`
- `username`
- `accountId`

## Source Notes
- Atlassian Cloud user identity is privacy-oriented and accountId-based.
