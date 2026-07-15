# Specification: 002

## Name

Project

## Status

Approved

## Owner

Chief AI Architect

## Related Work Order

WO-0002

## Depends On

001 - Executive

## Required By

003 - WorkOrder

## Version

1.0

---

# Purpose

The Project is the root business object of JBK Operating System.

Every client engagement, internal initiative, research effort, or product development activity exists as a Project.

A Project owns all work performed within its boundary.

---

# Responsibilities

A Project must:

* Represent a single business initiative.
* Track its current status.
* Own Work Orders.
* Own Deliverables.
* Own Decisions.
* Provide summary information.
* Maintain its own lifecycle.

The Project coordinates work but performs none itself.

---

# Identity

Every Project must have:

* id
* title
* client
* description

The ID format shall be:

PROJ-0001

Project IDs are immutable.

---

# Required Attributes

id

title

client

description

status

work_orders

deliverables

decisions

created_at

updated_at

---

# Project Status Values

PLANNED

ACTIVE

ON_HOLD

COMPLETED

ARCHIVED

---

# Ownership Rules

A Project owns:

* Work Orders
* Deliverables
* Decisions

Executives never own these objects.

Executives only create or update them.

---

# Required Methods

add_work_order()

add_deliverable()

record_decision()

update_status()

summary()

to_dict()

---

# Behaviour

A Project may exist before any Work Orders are created.

A Project may contain zero or many Work Orders.

A Project may contain zero or many Deliverables.

A Project may contain zero or many Decisions.

Updating the Project status must update the updated_at timestamp.

---

# Summary Output

summary() should return structured information including:

Project ID

Title

Client

Status

Number of Work Orders

Number of Deliverables

Number of Decisions

Creation Date

Last Updated

---

# Acceptance Criteria

A Project can be instantiated.

A Project receives a generated Project ID if one is not supplied.

Work Orders can be added.

Deliverables can be added.

Decisions can be recorded.

Status changes correctly.

summary() returns structured data.

to_dict() returns a serializable representation.

All tests pass.

---

# Non Goals

No AI.

No Executive orchestration.

No database.

No filesystem persistence.

No API.

No user interface.

No automatic Work Order creation.

---

# Definition of Done

Implementation complete.

Tests pass.

Implementation follows DEVELOPMENT_GUIDE.md.

Ready for Specification 003 (WorkOrder).
