# DEVELOPMENT_GUIDE.md

## JBK Operating System

Version: 1.0

Status: Active

Owner: Chief AI Architect

---

# Purpose

This guide defines the engineering standards used to build JBK Operating System.

Every contributor—human or AI—must follow these standards.

The goal is consistency, maintainability, traceability, and long-term evolution.

---

# Engineering Philosophy

We optimize for:

* Simplicity before sophistication.
* Working software before optimization.
* Composition over inheritance (except where a shared base class is intentional).
* Explicit behavior over hidden magic.
* Human-readable data.
* Testability.
* Deterministic workflows.
* Small, reviewable changes.

---

# Architectural Principles

1. Architecture is stable; implementation evolves.
2. Every major business concept is represented by a first-class object.
3. Executives own outcomes.
4. Skills perform specialized tasks.
5. Work moves through Work Orders.
6. Deliverables—not conversations—are the primary outputs.
7. The Chief of Staff orchestrates work.
8. The CEO assigns outcomes, not tasks.

---

# Core Objects

Version 1 supports only:

* Executive
* Project
* WorkOrder
* Deliverable
* Skill
* Memory
* Knowledge
* Decision
* Action
* Meeting

No additional core objects may be introduced without architectural review.

---

# Repository Structure

Each top-level directory has a single responsibility.

Core business logic must never depend on UI frameworks.

Business rules belong in `core/`.

Executive implementations belong in `executives/`.

---

# Naming Standards

Classes:
PascalCase

Functions:
snake_case

Variables:
snake_case

Constants:
UPPER_CASE

Files:
snake_case.py

Folders:
lowercase

---

# Object IDs

Every persistent object receives a unique identifier.

Examples:

EXEC-0001

PROJ-0001

WO-0001

DEL-0001

DEC-0001

ACT-0001

Identifiers are immutable.

---

# Logging

Every significant state change must be logged.

At minimum:

Timestamp

Object ID

Action

Actor

Result

---

# Error Handling

Fail clearly.

Never swallow exceptions silently.

Errors should contain enough information for diagnosis without exposing sensitive information.

---

# Testing Philosophy

Every business object must have automated tests.

Focus on behavior rather than implementation details.

Prefer many small tests over a few large tests.

---

# Git Workflow

Each feature is developed independently.

Every commit should represent one logical change.

Commit messages should describe intent, not implementation.

---

# AI Contribution Rules

AI-generated code must be:

Readable

Documented

Testable

Consistent with this guide

AI must not invent architecture.

When uncertain, follow existing patterns.

---

# Definition of Done

A component is complete when:

* Acceptance criteria are met.
* Tests pass.
* Documentation is updated if required.
* Code follows this guide.
* The component integrates without breaking existing behavior.

---

# Guiding Principle

JBK Operating System is built to operate a real company.

Every design decision should make the organization easier to understand, easier to evolve, and easier to trust.
