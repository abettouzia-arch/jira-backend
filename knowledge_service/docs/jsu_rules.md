# JSU (JIRA Suite Utilities) DC vs Cloud Compatibility Rules

## Context
JSU for Data Center uses Groovy expressions and internal Jira APIs.

---

## Feature: jsu_extension_usage

### Cloud Status
INCOMPATIBLE

### Risk
BLOCKER

### Why
JSU Cloud does not support Groovy scripts.

### Recommended Migration
- Use Jira Automation rules

### Keywords
jsu, groovy, automation

---

## Feature: workflow_post_function

### Cloud Status
REWRITE_REQUIRED

### Risk
MAJOR

### Recommended Migration
- Recreate using Jira Automation

---

## Feature: workflow_condition

### Cloud Status
REWRITE_REQUIRED

### Risk
MAJOR

---

## Feature: workflow_validator

### Cloud Status
REWRITE_REQUIRED

### Risk
MAJOR

---

## Feature: custom_field_update

### Cloud Status
PARTIAL

### Risk
MAJOR

---

## Feature: issue_transition

### Cloud Status
PARTIAL

### Risk
MAJOR

---

## Feature: email_notification

### Cloud Status
COMPATIBLE

### Risk
MINOR

---

## Feature: issue_commenting

### Cloud Status
COMPATIBLE

### Risk
MINOR

---

## Feature: issue_assignment

### Cloud Status
COMPATIBLE

### Risk
MINOR