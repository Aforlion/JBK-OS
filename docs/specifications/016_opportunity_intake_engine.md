# Specification 016

## Opportunity Intake Engine

Version: 1.0

Status: Approved

---

# Purpose

The Opportunity Intake Engine is the first business intelligence component of JBK OS.

Its responsibility is to transform an unstructured client conversation into a structured Opportunity Brief.

Clients rarely communicate their requirements in a structured way. They often describe symptoms, desired outcomes, or incomplete ideas. The Opportunity Intake Engine analyzes these conversations and produces a standardized representation that downstream systems can understand.

It is the entry point into the Client Delivery Pipeline.

---

# Business Goal

Transform natural-language client requests into structured business opportunities that can be reviewed, clarified, and developed into executable projects.

---

# Inputs

Natural-language client conversation.

Examples:

* Email
* Chat message
* Meeting notes
* Voice transcription
* Executive notes

---

# Outputs

OpportunityBrief

---

# Opportunity Brief

The Opportunity Brief shall contain:

* Brief ID
* Date Created
* Client Name (if known)
* Organization (if known)
* Business Domain
* Industry
* Business Problems
* Desired Outcomes
* Known Constraints
* Assumptions
* Missing Information
* Opportunity Complexity
* Confidence Score
* Recommended Next Step

---

# Business Domain Detection

The engine shall identify the client's business domain whenever possible.

Examples include:

* Education
* Healthcare
* Finance
* Legal
* Manufacturing
* Retail
* Government
* Non-profit
* Technology
* Professional Services

If the domain cannot be determined, the value shall be "Unknown."

---

# Information Extraction

The engine shall identify:

Business Problems

Desired Outcomes

Existing Processes

Known Constraints

Technology References

Budget Mentions

Timeline Mentions

Decision Makers

Success Criteria

---

# Missing Information Detection

The engine shall identify information required before a proposal can be prepared.

Typical examples:

* Budget
* Timeline
* Number of users
* Existing systems
* Decision maker
* Project objectives
* Success criteria

Each missing information item should generate a corresponding clarification recommendation.

---

# Opportunity Complexity

The engine shall classify opportunities as:

* Low
* Medium
* High
* Enterprise

The classification should be based on available information only.

---

# Confidence Score

The engine shall calculate a confidence score representing the completeness of the intake.

Range:

0.0 – 1.0

Higher scores indicate better understanding of the opportunity.

---

# Recommended Next Step

Possible recommendations include:

* Begin Discovery Conversation
* Request Missing Information
* Schedule Client Meeting
* Reject Opportunity
* Escalate for Executive Review

---

# Public Interface

The engine should expose methods similar to:

analyze()

generate_brief()

calculate_confidence()

identify_missing_information()

recommend_next_step()

summary()

to_dict()

---

# Architectural Constraints

The engine:

* shall not create Projects.
* shall not create Client Requests.
* shall not assign Work Orders.
* shall not estimate pricing.
* shall not recommend solutions.
* shall remain advisory only.

---

# Testing Requirements

Unit tests shall verify:

* Empty conversations
* Short conversations
* Long conversations
* Multiple industries
* Unknown industries
* Confidence calculations
* Complexity calculations
* Serialization
* Missing information detection

All existing tests must continue to pass.

---

# Future Evolution (Version 2+)

* Opportunity entity replacing standalone briefs.
* CRM integration.
* Voice conversation support.
* Multi-language intake.
* Semantic language models.
* Historical opportunity scoring.
* Industry-specific intake templates.
* Learning from won and lost opportunities.

---

# Related Specifications

017 – Discovery Conversation Engine

018 – Solution Architect

019 – Estimation Engine

020 – Pricing Engine

021 – Proposal Generator
