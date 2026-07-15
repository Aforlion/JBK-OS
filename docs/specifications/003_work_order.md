# Specification: 003

## Name

WorkOrder

## Status

Approved

## Owner

Chief AI Architect

## Related Work Order

WO-0003

## Depends On

001 - Executive

002 - Project

## Required By

004 - Deliverable

005 - ChiefOfStaff

## Version

1.0

---

# Purpose

A WorkOrder represents a single unit of business work.

It is created by an orchestrator (normally the Chief of Staff), assigned to an Executive, and completed by producing a Deliverable.

A WorkOrder never exists outside a Project.

---

# Responsibilities

A WorkOrder must:

* Belong to exactly one Project.
* Be assigned to one Executive.
* Track its own lifecycle.
* Reference its Deliverable.
* Record assignment and completion timestamps.
* Produce structured status information.

---

# Identity

Every WorkOrder must have:

* id
* project_id
* title
* objective

ID format:

WO-0001

IDs are immutable.

---

# Required Attributes

id

project_id

title

objective

assigned_by

assigned_to

priority

status

deliverable_id

created_at

assigned_at

completed_at

updated_at

---

# Priority Values

LOW

MEDIUM

HIGH

CRITICAL

---

# Status Values

CREATED

ASSIGNED

ACCEPTED

IN_PROGRESS

COMPLETED

CANCELLED

---

# Ownership Rules

A WorkOrder:

* Belongs to one Project.
* Is assigned to one Executive.
* May reference one Deliverable.
* Never creates sibling business objects.

---

# Required Methods

assign()

accept()

start()

complete()

cancel()

attach_deliverable()

update_priority()

summary()

to_dict()

---

# Behaviour

A WorkOrder is created in CREATED status.

assign() moves it to ASSIGNED.

accept() moves it to ACCEPTED.

start() moves it to IN_PROGRESS.

complete() moves it to COMPLETED.

cancel() moves it to CANCELLED.

Completing a WorkOrder records completed_at.

Attaching a Deliverable stores only its identifier.

---

# Summary Output

summary() returns:

* WorkOrder ID
* Project ID
* Title
* Priority
* Status
* Assigned By
* Assigned To
* Deliverable ID
* Created At
* Updated At

---

# Acceptance Criteria

A WorkOrder can be instantiated.

A WorkOrder belongs to exactly one Project.

Status transitions work correctly.

Priority updates correctly.

Deliverable IDs can be attached.

summary() returns structured information.

to_dict() returns a serializable representation.

All unit tests pass.

---

# Non Goals

No AI.

No Project creation.

No Executive creation.

No filesystem.

No API.

No database.

No orchestration logic.

---

# Architectural Constraints

A WorkOrder references its Project using project_id only.

A WorkOrder references its Executive using assigned_to only.

A WorkOrder references its Deliverable using deliverable_id only.

Business objects reference identities, not embedded objects.

Business objects never create sibling business objects.

---

# Definition of Done

Implementation complete.

Unit tests pass.

Implementation follows DEVELOPMENT_GUIDE.md.

Ready for Specification 004 (Deliverable).
