# Specification: 008

## Name

Client Request

## Status

Approved

## Owner

Chief AI Architect

## Related Work Order

WO-0008

## Depends On

None

## Required By

009 - Client Engagement Workflow

## Version

1.0

---

# Purpose

A Client Request represents an opportunity presented to JBK by a prospective or existing client.

It captures the client's business need from first contact until a decision is made.

An approved Client Request becomes a Project.

---

# Responsibilities

The Client Request must:

* Record who made the request.
* Capture the business problem.
* Track request status.
* Store business priority.
* Record important dates.
* Link to a Project after approval.
* Provide summary information.

---

# Identity

Every Client Request has an immutable identifier.

Format:

CR-0001

CR-0002

CR-0003

...

---

# Required Attributes

id

client_name

organization

contact_person

contact_email

contact_phone

industry

title

problem_statement

desired_outcome

priority

status

created_at

updated_at

approved_at

project_id

notes

---

# Enumerations

## Status

NEW

UNDER_REVIEW

QUALIFIED

PROPOSAL_SENT

APPROVED

PROJECT_CREATED

REJECTED

WITHDRAWN

---

## Priority

LOW

MEDIUM

HIGH

CRITICAL

---

# Ownership Rules

A Client Request belongs to one client organization.

A Client Request may produce one Project.

A Project originates from exactly one approved Client Request.

---

# Required Methods

approve()

reject()

withdraw()

link_project()

update_priority()

add_note()

summary()

to_dict()

---

# Behaviour

IDs are immutable.

A Client Request begins in NEW status.

approve() records approved_at.

link_project() stores the created Project ID and changes status to PROJECT_CREATED.

Only approved requests may be linked to Projects.

Notes are appended chronologically.

Updating significant fields updates updated_at.

---

# Summary Output

summary() returns:

* Request ID
* Client Name
* Organization
* Title
* Status
* Priority
* Industry
* Project ID (if linked)
* Creation Date
* Last Updated

---

# Acceptance Criteria

Client Request can be instantiated.

Immutable IDs are generated.

Status transitions function correctly.

Priority updates correctly.

Project linking is restricted to approved requests.

Notes are stored chronologically.

summary() returns structured information.

to_dict() returns a serializable representation.

Unit tests pass.

---

# Non Goals

No CRM.

No proposal generation.

No email integration.

No scheduling.

No notifications.

No AI qualification.

No persistence.

---

# Architectural Constraints

The Client Request is a business object.

It never creates Projects.

It never creates WorkOrders.

It never creates Deliverables.

Project creation belongs to the Chief of Staff.

---

# Business Rules

BR-0004

Only APPROVED Client Requests may become Projects.

BR-0005

A Client Request can be linked to only one Project.

BR-0006

REJECTED and WITHDRAWN requests are read-only except for notes.

---

# Future Evolution

Future versions may include:

* Proposal documents
* Estimated project value
* Sales pipeline stages
* Multiple contacts
* File attachments
* Meeting history
* AI qualification scoring
* Lead source tracking

---

# Definition of Done

Implementation complete.

Unit tests pass.

Implementation follows DEVELOPMENT_GUIDE.md.

Ready for Specification 009 (Client Engagement Workflow).
