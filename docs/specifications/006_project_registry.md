# Specification: 006

## Name

Project Registry

## Status

Approved

## Owner

Chief AI Architect

## Related Work Order

WO-0006

## Depends On

002 - Project

## Required By

007 - ChiefOfStaff

## Version

1.0

---

# Purpose

The Project Registry is the central directory of all Projects managed by JBK Operating System.

It provides discovery and lookup services for Projects.

It is not responsible for creating, modifying, executing, or completing Projects.

---

# Responsibilities

The Project Registry must:

* Register Projects.
* Remove Projects.
* Find Projects by ID.
* List all Projects.
* List Projects by status.
* Generate registry summary.

---

# Identity

The Project Registry is a singleton-style business service.

It has no business identifier.

---

# Stored Objects

Version 1 stores:

* Project objects only.

---

# Required Methods

register(project)

unregister(project_id)

find_by_id(project_id)

list_projects()

list_by_status(status)

summary()

to_dict()

---

# Behaviour

A Project may only be registered once.

Duplicate Project IDs must be rejected.

Removing a Project removes only the registry reference.

The Registry never creates Projects.

The Registry never updates Project state.

The Registry returns references to registered Project objects.

---

# Summary Output

summary() returns:

* Total Projects
* Projects by status
* Active Projects
* Completed Projects
* On Hold Projects

---

# Acceptance Criteria

A Project Registry can be instantiated.

Projects can be registered.

Duplicate registrations are rejected.

Projects can be removed.

Projects can be found by ID.

Projects can be listed.

Projects can be filtered by status.

summary() returns structured information.

to_dict() returns a serializable representation.

All tests pass.

---

# Non Goals

No AI.

No Project creation.

No WorkOrder management.

No Deliverable management.

No scheduling.

No orchestration.

No persistence.

---

# Architectural Constraints

The Project Registry is a directory only.

It must never:

* create Projects
* modify Projects
* assign WorkOrders
* manage Executives
* coordinate workflows

It stores and retrieves Project references only.

---

# Definition of Done

Implementation complete.

Unit tests pass.

Implementation follows DEVELOPMENT_GUIDE.md.

Ready for Specification 007 (Chief of Staff).
