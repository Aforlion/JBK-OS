Specification 038 — Skill Execution Framework

Version: 1.0

Status: Approved for Implementation

Priority: Critical

Architectural Layer: Workforce Runtime

Executive Summary

The Skill Execution Framework standardizes how every AI employee within JBK Technologies performs work.

It provides a common lifecycle for executing any skill—from software engineering to marketing, legal review, finance, research, or customer success—ensuring consistency, traceability, validation, and quality regardless of the underlying AI provider.

This framework becomes the runtime environment for every AI employee.

Mission

Every AI employee shall execute work through a standardized lifecycle.

No skill shall invent its own execution process.

Business Requirements
BR-038-001 Standard Skill Lifecycle

Every skill execution shall follow the same lifecycle:

Receive Work Order
        ↓
Validate Inputs
        ↓
Prepare Context
        ↓
Build Prompt
        ↓
Invoke AI Gateway
        ↓
Validate Output
        ↓
Generate Deliverable
        ↓
Quality Review
        ↓
Return Execution Report
BR-038-002 Skill Manifest

Every executable skill shall contain a manifest.yaml.

Example:

skill_id: SKILL-001

name: Software Engineer

version: 1.0

owner: CTO

description: Develops software solutions

capabilities:
  - python
  - architecture
  - testing

required_inputs:
  - WorkOrder

generated_outputs:
  - Deliverable

supported_models:
  - Gemini
  - Claude

quality_validator:
  validator.py
BR-038-003 Skill Runtime

Every skill shall expose one standard interface:

execute(work_order) -> SkillExecutionResult
BR-038-004 Prompt Templates

Every skill shall maintain reusable prompt templates.

Example folders:

prompts/

review.md

implementation.md

analysis.md

documentation.md
BR-038-005 Context Builder

Automatically construct execution context from:

Work Order
Project
Client
Knowledge Registry
Previous Deliverables
Company Standards
BR-038-006 AI Gateway Integration

Skills shall never communicate directly with LLM providers.

All requests must pass through the AI Gateway.

BR-038-007 Output Validation

Every execution shall be validated before completion.

Validators may check:

completeness
formatting
required sections
code compilation
documentation
business rules
BR-038-008 Deliverable Packaging

Successful executions automatically create Deliverable objects.

BR-038-009 Failure Handling

Execution failures shall return structured failure reports.

Never raise uncaught exceptions.

BR-038-010 Retry Support

Allow configurable retry policies.

BR-038-011 Execution Metrics

Capture:

duration
provider
model
tokens
estimated cost
retries
validation results
BR-038-012 Stateless Runtime

Execution runtime remains stateless.

Conversation history belongs elsewhere.

BR-038-013 Explainability

Every execution shall explain:

chosen prompt
selected provider
validation outcome
quality score
BR-038-014 Versioning

Skills shall expose:

version
compatibility
changelog
BR-038-015 Extensibility

New skills shall require zero framework modification.

Adding a skill should only require:

folder
manifest
prompts
validator
Domain Models

Create:

SkillManifest

Contains:

identity
metadata
capabilities
supported providers
runtime configuration
SkillExecutionResult

Contains:

execution_id
work_order_id
status
deliverable
metrics
validation
logs
reasoning
ValidationResult

Contains:

passed
score
issues
recommendations
ExecutionMetrics

Contains:

duration
retries
provider
model
tokens
estimated_cost
New Components

Create:

core/skill_manifest.py
core/skill_runtime.py
core/skill_execution_framework.py
core/output_validator.py
core/context_builder.py
Base Abstract Class
class BaseSkill:

Standard interface:

load_manifest()

build_context()

build_prompt()

execute()

validate()

package_deliverable()

Every AI employee inherits from this class.

Standard Skill Directory
software-engineer/

    manifest.yaml

    prompts/

        implementation.md

        review.md

        testing.md

    validator.py

    runtime.py

Every skill follows exactly this structure.

Integration Points

Uses:

AI Gateway
Work Execution Orchestrator
Deliverables
Knowledge Registry
Skill Registry
Chief of Staff
Tests

Minimum coverage:

manifest loading
runtime execution
prompt generation
context building
AI Gateway invocation
validation success
validation failure
retry handling
deliverable creation
metrics recording
serialization
new skill registration
framework extensibility
Production Readiness
Operational Status

Requires Integration

Dependencies
AI Gateway
Skill Registry
Deliverables
Work Execution Orchestrator
Security Considerations
Prompt sanitization
Input validation
Output validation
Provider isolation
Performance Considerations
Stateless execution
Prompt caching
Context reuse
Validation optimization
Operational Risks
Poor prompt design
Invalid manifests
Provider outages
Validator failures
Migration Impact

Medium.

Existing skill folders should gradually adopt the new standard structure.

Backward Compatibility

Yes.

Legacy skills may continue operating until migrated.

Future Evolution (Version 2+)
Skill self-learning from completed projects.
Automatic prompt optimization based on execution success.
Multi-step internal reasoning workflows.
Human approval checkpoints for sensitive skills.
Skill benchmarking across multiple AI providers.
Marketplace for importing third-party skills.
Skill certification and quality scoring.
Runtime sandboxing for untrusted skills.
Shared prompt libraries across departments.
Dynamic capability acquisition (skills learning new capabilities over time).
Candidate Brain Entry

Skill-Execution-Framework-Standards.md

# Skill Execution Framework Architectural Standards

1. Every AI employee must inherit from the standard Skill Runtime.

2. Skills must execute through the lifecycle:
   Validate → Context → Prompt → AI Gateway → Validation → Deliverable.

3. All AI communication must occur through the AI Gateway.

4. Every skill must expose a manifest.yaml describing its capabilities and requirements.

5. Skills must validate outputs before producing deliverables.

6. Skill runtimes must remain stateless.

7. New skills must integrate without requiring framework modifications.