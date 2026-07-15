# Specification 017

## Discovery Conversation Engine

Version: 1.0

Status: Approved for Implementation

---

# Purpose

Clients rarely describe their real problem accurately.

They usually describe symptoms, assumptions, or desired solutions rather than the underlying business problem.

The Discovery Conversation Engine exists to help JBK OS uncover the true business need through a structured, intelligent conversation.

It transforms an Opportunity Brief into a repeatable discovery process that any JBK executive—human or AI—can follow.

---

# Business Goal

Produce a complete understanding of the client's business problem before any solution, estimate, pricing, or proposal is generated.

---

# Inputs

OpportunityBrief

---

# Outputs

DiscoveryPlan

---

# Discovery Plan

The Discovery Plan shall contain:

* Discovery ID
* Opportunity ID (optional)
* Conversation Objective
* Information Already Known
* Information Still Required
* Recommended Question Sequence
* Conversation Categories
* Discovery Completeness
* Confidence Score
* Recommended Next Step

---

# Conversation Categories

The engine shall organize questions into categories.

Minimum categories:

Business

Current Process

Technology

People

Operations

Budget

Timeline

Success Criteria

Risks

Compliance

Future Growth

---

# Dynamic Question Generation

Questions shall never be hardcoded to one industry.

Instead they shall be generated using:

Business Domain

Opportunity Complexity

Detected Pain Points

Missing Information

Desired Outcomes

Known Constraints

---

# Prioritization

Questions shall be ordered by importance.

Critical business questions appear before technical questions.

The engine should avoid asking questions whose answers are already known.

---

# Conversation Rules

Questions shall:

* be clear
* avoid jargon
* ask one thing at a time
* progressively narrow uncertainty
* reduce ambiguity

---

# Non-Goals

The engine shall not:

* estimate pricing
* recommend products
* create projects
* create client requests
* create work orders

---

# Architectural Constraints

The engine is advisory only.

No business state may be modified.

No registries may be updated.

No workflows may be executed.

---

# Public Interface

The engine should expose methods similar to:

generate_plan()

prioritize_questions()

calculate_completeness()

recommend_next_step()

summary()

to_dict()

---

# Success Criteria

A user providing an Opportunity Brief should receive a structured Discovery Plan that:

* identifies missing information
* prioritizes clarification
* supports executive conversations
* is reusable across industries

---

# Testing Requirements

Unit tests shall verify:

* empty briefs
* complete briefs
* multiple industries
* varying complexity
* prioritization
* serialization
* confidence calculations

All previous tests must continue to pass.

---

# Future Evolution (Version 2+)

* Adaptive questioning based on previous answers.
* Voice conversations.
* Live meeting transcription.
* Industry-specific discovery playbooks.
* Integration with CRM systems.
* AI-generated discovery summaries.
* Opportunity entity integration (replace standalone briefs with Opportunity objects).
* Learning from successful client engagements to improve future discovery plans.

---

# Related Specifications

016 – Opportunity Intake Engine

018 – Solution Architect

019 – Estimation Engine

020 – Pricing Engine
