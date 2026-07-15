# Specification: 005

## Name

Worker Registry

## Status

Approved

## Owner

Chief AI Architect

## Related Work Order

WO-0005

## Depends On

001 - Executive

## Required By

006 - ChiefOfStaff

## Version

1.0

---

# Purpose

The Worker Registry is the central directory of all workers available to JBK Operating System.

In Version 1, the registry stores Executive objects only.

Future versions will support additional worker types such as Staff, Contractors, AI Agents, Partner Organizations, and External Services without changing the registry interface.

The registry is responsible for discovery, not orchestration.

---

# Responsibilities

The Worker Registry must:

* Register workers.
* Remove workers.
* Find workers by ID.
* Find workers by role.
* List all workers.
* List available workers.
* Generate a directory summary.

The registry does not assign work or manage projects.

---

# Identity

The Worker Registry is a singleton-style business service.

It does not require its own persistent ID.

---

# Stored Objects

Version 1 stores:

* Executive

Future versions may store:

* Staff
* Contractors
* AI Agents
* Partners
* External Services

All stored objects must satisfy the Worker Contract when that specification is introduced.

---

# Required Methods

register(worker)

unregister(worker_id)

find_by_id(worker_id)

find_by_role(role)

list_workers()

list_available()

summary()

---

# Behaviour

A worker may only be registered once.

Duplicate worker IDs must be rejected.

Removing a worker removes only the registry reference.

The registry never creates workers.

The registry never destroys workers.

The registry never changes worker state.

The registry returns references to registered workers.

---

# Summary Output

summary() returns:

* Total registered workers
* Workers by role
* Available workers
* Busy workers
* Offline workers
* Suspended workers

---

# Acceptance Criteria

A Worker Registry can be instantiated.

Workers can be registered.

Duplicate registrations are rejected.

Workers can be removed.

Workers can be found by ID.

Workers can be found by role.

Available workers can be listed.

summary() returns structured information.

to_dict() returns a serializable representation if implemented.

All unit tests pass.

---

# Non Goals

No AI.

No scheduling.

No assignment.

No workload balancing.

No project management.

No orchestration.

No persistence.

No database.

---

# Architectural Constraints

The Worker Registry is a directory only.

It must not:

* create workers
* assign WorkOrders
* update worker status
* know about Projects
* know about Deliverables
* know about WorkOrders

It only stores and retrieves worker references.

Version 1 assumes all registered workers are Executive objects.

---

# Definition of Done

Implementation complete.

Unit tests pass.

Implementation follows DEVELOPMENT_GUIDE.md.

Ready for Specification 006 (Chief of Staff).
