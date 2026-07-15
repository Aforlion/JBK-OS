# Specification: 004

## Name

Deliverable

## Status

Approved

## Owner

Chief AI Architect

## Related Work Order

WO-0004

## Depends On

002 - Project

003 - WorkOrder

## Required By

005 - ChiefOfStaff

## Version

1.0

---

# Purpose

A Deliverable represents the tangible output produced by an Executive in response to a WorkOrder.

Examples include:

* Research Report
* Product Requirements Document (PRD)
* Technical Architecture
* Financial Analysis
* Proposal
* Marketing Strategy

A Deliverable exists to create business value.

---

# Responsibilities

A Deliverable must:

* Belong to exactly one Project.
* Belong to exactly one WorkOrder.
* Record its creator.
* Track versions.
* Track its lifecycle.
* Expose structured metadata.

---

# Identity

Every Deliverable must have:

* id
* project_id
* work_order_id
* title

ID format:

DEL-0001

IDs are immutable.

---

# Required Attributes

id

project_id

work_order_id

title

author

version

status

content

created_at

updated_at

---

# Status Values

DRAFT

IN_REVIEW

APPROVED

REJECTED

ARCHIVED

---

# Ownership Rules

A Deliverable:

* Belongs to one Project.
* Belongs to one WorkOrder.
* Is authored by one Executive.
* Never owns WorkOrders or Projects.

---

# Required Methods

update_content()

submit_for_review()

approve()

reject()

archive()

increment_version()

summary()

to_dict()

---

# Behaviour

A new Deliverable begins as:

Version = 1

Status = DRAFT

Updating content updates updated_at.

increment_version() increases the version number by one.

submit_for_review() changes status to IN_REVIEW.

approve() changes status to APPROVED.

reject() changes status to REJECTED.

archive() changes status to ARCHIVED.

Only APPROVED Deliverables should satisfy WorkOrder completion requirements.

---

# Summary Output

summary() returns:

* Deliverable ID
* Project ID
* WorkOrder ID
* Title
* Author
* Version
* Status
* Created At
* Updated At

---

# Acceptance Criteria

A Deliverable can be instantiated.

IDs are immutable.

Version starts at 1.

Version increments correctly.

Content updates correctly.

Status transitions work.

summary() returns structured data.

to_dict() returns a serializable representation.

All tests pass.

---

# Non Goals

No AI.

No file storage.

No document rendering.

No database.

No API.

No workflow orchestration.

---

# Architectural Constraints

A Deliverable references:

* Project by project_id
* WorkOrder by work_order_id
* Executive by author

Never embed business objects.

Business objects reference identities only.

---

# Definition of Done

Implementation complete.

Tests pass.

Implementation follows DEVELOPMENT_GUIDE.md.

Ready for Specification 005 (ChiefOfStaff).
