# JMWE / MISC Compatibility Rules

## Context
JMWE DC uses Groovy. Cloud uses Nunjucks.

---

## Feature: misc_workflow_extension_usage

### Cloud Status
INCOMPATIBLE

### Risk
BLOCKER

### Recommended Migration
- Rewrite using Nunjucks

---

## Feature: component_accessor

### Cloud Status
INCOMPATIBLE

### Risk
BLOCKER

### Why
ComponentAccessor is not available in Cloud.

---

## Feature: java_api

### Cloud Status
INCOMPATIBLE

### Risk
BLOCKER

---

## Feature: active_objects_access

### Cloud Status
INCOMPATIBLE

### Risk
BLOCKER

---

## Feature: workflow_post_function

### Cloud Status
REWRITE_REQUIRED

### Risk
MAJOR

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

## Feature: user_lookup

### Cloud Status
PARTIAL

### Risk
MAJOR

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