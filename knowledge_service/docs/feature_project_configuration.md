# Feature: project_configuration

## Migration Meaning
Project configuration access includes reading or modifying project metadata, components, versions, schemes, permissions, and workflow associations.

## Data Center Behavior
- Scripts can access project managers and configuration managers directly.
- Automation may update project settings or inspect schemes.
- Some scripts assume admin-level Java API access.

## Cloud Limitation
- Jira Cloud project configuration is available through specific REST APIs and admin interfaces.
- Not every Data Center configuration API has a direct Cloud equivalent.
- Admin permissions and app scopes are required for many operations.

## Compatibility Assessment
- Simple project reads through REST: COMPATIBLE or INFO.
- Project updates through supported APIs: PARTIAL.
- Java manager access or scheme mutation: MAJOR or NEEDS_REVIEW.

## Recommended Migration
- Replace Java project manager calls with REST API v3 project endpoints.
- Validate project type, company-managed/team-managed differences, and permissions.
- Avoid direct scheme mutation unless supported by Cloud APIs.
- Document any manual configuration steps required after migration.

## Detection Patterns
- `project_manager_access`
- `project_creation`
- `project_update`
- `project_configuration_access`
- `ProjectManager`
- `project schemes`

## Source Notes
- Project configuration behavior can differ between Jira Data Center and Jira Cloud project types.
