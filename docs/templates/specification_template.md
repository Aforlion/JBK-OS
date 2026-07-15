# Specification: XXX

## Name

<Component Name>

## Status

Draft | Approved | Deprecated

## Owner

Chief AI Architect

## Related Work Order

WO-XXXX

## Depends On

List all prerequisite specifications.

Example:

001 - Executive

002 - Project

## Required By

List specifications that depend on this component.

Example:

006 - ChiefOfStaff

## Version

1.0

## Last Updated

YYYY-MM-DD

---

# Purpose

Describe why this component exists.

Focus on the business purpose, not the implementation.

---

# Responsibilities

List everything this component is responsible for.

Keep each responsibility concise.

Example:

* Register workers.
* Track lifecycle.
* Generate reports.

---

# Identity

Describe the identity of the object.

If applicable specify:

* ID format
* Immutability
* Required identifiers

If the component does not require an ID, explain why.

---

# Required Attributes

List every required attribute.

Example:

id

title

status

created_at

updated_at

---

# Enumerations

Document all allowed values.

Example:

Status

ACTIVE

INACTIVE

ARCHIVED

Priority

LOW

MEDIUM

HIGH

CRITICAL

If no enumerations exist, write:

None.

---

# Ownership Rules

Define ownership explicitly.

Examples:

A WorkOrder belongs to exactly one Project.

A Deliverable belongs to exactly one WorkOrder.

A Registry owns no business objects.

---

# Required Methods

List every public method.

Example:

create()

update()

summary()

to_dict()

---

# Behaviour

Describe expected behaviour.

Use business language.

Avoid implementation details.

Examples:

Updating status updates updated_at.

IDs are immutable.

Version numbers increase sequentially.

---

# Summary Output

Describe the expected structure returned by summary().

List all required fields.

---

# Acceptance Criteria

List measurable completion criteria.

Example:

* Component can be instantiated.
* IDs are immutable.
* Required methods function correctly.
* Summary returns structured information.
* Unit tests pass.

---

# Non Goals

Explicitly state what this specification does NOT include.

This prevents scope creep.

Example:

* No AI.
* No database.
* No API.
* No orchestration.

---

# Architectural Constraints

List architecture rules that engineering must follow.

Examples:

* Reference business objects by ID only.
* Do not create sibling business objects.
* Use only the Python standard library.
* Do not anticipate future specifications.

---

# Dependencies

List runtime dependencies.

Example:

Executive

Project

Worker Registry

If none:

None.

---

# Risks

Describe known architectural risks or trade-offs.

Example:

Future persistence may require ID generation changes.

---

# Future Evolution

List improvements intentionally deferred to later versions.

These should also be recorded in the Architecture Evolution Log.

Example:

* Replace embedded assignment with Assignment Value Object.
* Introduce lifecycle state machine.

---

# Definition of Done

Implementation is complete when:

* Acceptance criteria are satisfied.
* Unit tests pass.
* DEVELOPMENT_GUIDE.md has been followed.
* No architectural constraints are violated.
* Documentation is complete.
* Component is ready for the next dependent specification.

---

# Notes

Optional.

Use this section to capture implementation guidance, rationale, or references that may help future contributors.

Do not place mandatory requirements here. Mandatory requirements belong in the sections above.
