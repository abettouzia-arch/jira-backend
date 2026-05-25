# Feature: filesystem_access

## Migration Meaning
Filesystem access means a script reads or writes local files on the Jira Data Center node.

## Data Center Behavior
- Groovy scripts can often use Java file APIs.
- Typical use cases include temporary exports, attachments processing, audit files, CSV generation, and local configuration files.
- In clustered Data Center, local filesystem behavior may already be node-dependent.

## Cloud Limitation
- Jira Cloud scripts do not have access to the server filesystem.
- Cloud execution is sandboxed.
- Persistent data must use supported Cloud storage, external object storage, app storage, or Jira APIs.

## Compatibility Assessment
- Cloud Status: INCOMPATIBLE.
- Risk: BLOCKER.
- Treat file read, file write, local storage, and temporary file creation as non-portable unless rewritten.

## Recommended Migration
- Replace local files with Forge Storage, external storage such as S3, or managed app storage.
- Replace generated exports with REST-generated attachments or reports.
- Avoid storing secrets in files; move secrets to approved secure configuration.
- Rehearse cleanup and retention rules in Cloud.

## Detection Patterns
- `new File`
- `FileInputStream`
- `FileOutputStream`
- `.readLines()`
- `.write(`
- `java.nio.file`

## Source Notes
- Cloud apps execute in a managed environment and cannot rely on local Jira server paths.
