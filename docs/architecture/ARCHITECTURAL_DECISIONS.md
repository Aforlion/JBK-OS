# JBK OS Architectural Decisions

Version: 1.0

Status: Active

Owner: Chief AI Architect

---

# Purpose

This document records all architectural decisions that are immediately effective.

Unlike the Architecture Evolution Log, decisions recorded here are part of the current engineering standard and must be followed by all contributors.

Every decision receives a permanent identifier.

Architectural decisions are immutable.

If a decision changes, create a new decision that supersedes the previous one.

Never edit history.

---

# Decision Template

## AD-XXXX

### Title

Decision

### Status

Active

Supersedes:

(Optional)

### Context

Why this decision was necessary.

### Decision

The architectural rule.

### Consequences

Benefits

Trade-offs

Implementation impact

---

# Active Decisions

---

## AD-0001

### Title

Business Objects Reference Identity Only

### Status

Active

### Context

Embedding business objects creates tight coupling and serialization problems.

### Decision

Business objects must reference other business objects by immutable identifiers only.

Examples:

Project → project_id

Executive → executive_id

WorkOrder → work_order_id

Deliverable → deliverable_id

Never embed business objects inside one another.

### Consequences

Loose coupling.

Simpler persistence.

Cleaner APIs.

---

## AD-0002

### Title

Projects Own WorkOrders

### Status

Active

### Context

Projects define the business boundary.

### Decision

Every WorkOrder belongs to exactly one Project.

Projects own WorkOrders.

Projects do not create WorkOrders.

Creation belongs to orchestration.

### Consequences

Clear ownership.

Simple lifecycle.

---

## AD-0003

### Title

Business Objects Never Create Sibling Business Objects

### Status

Active

### Context

Creation logic causes unnecessary coupling.

### Decision

Business objects must never create sibling business objects.

Creation belongs to orchestration components.

### Consequences

Simpler domain model.

Lower coupling.

Improved testability.

---

## AD-0004

### Title

Worker Registry Is A Directory

### Status

Active

### Context

Registration and orchestration are separate responsibilities.

### Decision

The Worker Registry stores and retrieves worker references.

It never:

* assigns work
* creates workers
* manages projects
* updates worker state

### Consequences

Single Responsibility Principle.

Cleaner orchestration layer.

---

## AD-0005

### Title

Chief Of Staff Is The Workflow Engine

### Status

Active

### Context

Work coordination must be centralized.

### Decision

The Chief of Staff coordinates work.

It does not create business value.

It creates WorkOrders.

Assigns WorkOrders.

Monitors progress.

Collects Deliverables.

Reports to the CEO.

Executives create Deliverables.

### Consequences

Clear separation between execution and coordination.

---

## AD-0006

### Title

WorkOrder Completion Requires Approved Deliverable

### Status

Active

### Context

Completed work must produce business value.

### Decision

A WorkOrder cannot complete until it references an APPROVED Deliverable.

### Consequences

Guarantees quality.

Prevents false completion.

---

## AD-0007

### Title

Version 1 Prioritizes Delivery

### Status

Active

### Context

Scope growth delays customer value.

### Decision

Version 1 grows only because of verified client needs.

Ideas are recorded in the Architecture Evolution Log.

They are not implemented until explicitly approved.

### Consequences

Stable roadmap.

Reduced scope creep.

Faster delivery.

---

## AD-0008

### Title

Specification-Driven Development

### Status

Active

### Context

AI engineering requires precise implementation boundaries.

### Decision

Every implementation begins with an approved Specification.

Every implementation receives a Work Order.

Engineering implements specifications—not conversations.

### Consequences

Predictable engineering.

Repeatable development.

Better AI collaboration.

---

## AD-0009

### Title

Worker Contract

### Status

Active

### Context

JBK will eventually include AI workers, human staff, contractors, partners, and external services.

### Decision

Every worker integrated into JBK OS must comply with the Worker Contract.

The Worker Registry depends on this contract rather than on concrete worker types.

Version 1 registers Executive objects only.

Future versions will expand supported worker types without changing the registry interface.

### Consequences

Future-proof architecture.

Consistent onboarding of new worker types.

Reduced integration effort.

---

## AD-0010

### Title

Domain-Neutral Core

### Status

Active

### Context

JBK serves multiple industries and client types.

### Decision

The JBK OS core must remain domain-neutral.

Industry expertise belongs in:

* Workers
* Skills
* Knowledge
* WorkOrders
* Client Assets

The Operating System manages coordination, not business domains.

### Consequences

Reusable platform.

Supports education, legal, healthcare, finance, government, and future domains without modifying the OS.

---

# Governance

Every architectural decision must satisfy three questions before becoming Active:

1. Does it simplify the system?
2. Does it reduce coupling?
3. Will it still make sense three years from now?

If the answer to any question is "No", record the idea in the Architecture Evolution Log instead of activating it.

---

# Change Process

New decisions are added only after architectural review.

Existing decisions are never edited.

If a decision changes:

* Create a new decision.
* Reference the superseded decision.
* Explain why the change was made.

This preserves the architectural history of JBK OS.
