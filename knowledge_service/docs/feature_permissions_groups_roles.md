# Feature: permissions_groups_roles

## Migration Meaning
Permission checks, group membership checks, role checks, and security level logic control who can see or act on Jira data.

## Data Center Behavior
- Scripts may use Jira permission managers, group managers, project roles, or issue security APIs.
- Data Center logic often assumes local user objects and group names.
- Permission logic may run inside validators, conditions, listeners, or scheduled jobs.

## Cloud Limitation
- Jira Cloud permissions must be checked through supported APIs and Cloud permission models.
- User identity is accountId-based.
- Group and role names may differ after migration.
- Some permission checks may require app scopes or admin privileges.

## Compatibility Assessment
- Simple permission checks: PARTIAL.
- Username/userKey-based checks: MAJOR.
- Direct Java permission manager usage: MAJOR or REWRITE_REQUIRED.
- Security-sensitive workflow logic should be reviewed carefully.

## Recommended Migration
- Map groups and project roles before migration.
- Replace username and userKey with accountId.
- Validate permission schemes and issue security schemes in Cloud.
- Rebuild workflow validators/conditions with Jira Automation, Cloud app functions, or Forge.

## Detection Patterns
- `permission_check`
- `group_membership_check`
- `role_check`
- `security_level_check`
- `PermissionManager`
- `GroupManager`
- `ProjectRoleManager`

## Source Notes
- Permission behavior must be validated in a Cloud sandbox because it affects access control and compliance.
