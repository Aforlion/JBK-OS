Specification 028
Work Execution Orchestrator

Version: 1.0

Purpose

Coordinate the execution of generated Work Orders by selecting the appropriate execution engine (Antigravity, Claude Code, Human Executive, future AI agents), monitoring execution, capturing outputs, handling failures, and updating project progress.

This is the operational heart of JBK-OS.

Responsibilities

The Work Execution Orchestrator shall:

Receive executable WorkOrders.
Verify dependencies are satisfied.
Consult the Execution Planner.
Select the best Skill.
Select the proper Execution Engine.
Dispatch execution.
Monitor execution.
Collect outputs.
Register Deliverables.
Update WorkOrder status.
Notify Chief of Staff.
Produce execution reports.
Inputs
WorkOrder
ExecutionPlan
SkillRegistry
ExecutionEngine
WorkerRegistry
KnowledgeRegistry (optional)
Outputs
ExecutionReport
Updated WorkOrder
Deliverables
Execution Logs
Functional Requirements
FR-028-001

Accept executable WorkOrders.

FR-028-002

Verify all dependency WorkOrders are COMPLETE.

If not:

WAIT.

FR-028-003

Retrieve Execution Plan.

FR-028-004

Locate recommended Skill.

FR-028-005

Verify Skill availability.

FR-028-006

Verify Execution Engine supports the Skill.

FR-028-007

Dispatch execution.

Example:

Antigravity

Claude Code

Human Executive

Future Agent
FR-028-008

Monitor execution lifecycle.

States:

QUEUED

RUNNING

WAITING

FAILED

COMPLETED

CANCELLED
FR-028-009

Capture:

stdout
reports
generated files
summaries
logs
FR-028-010

Create Deliverables.

FR-028-011

Attach Deliverables to WorkOrder.

FR-028-012

Mark WorkOrder COMPLETE only after successful Deliverable validation.

FR-028-013

On failure:

capture exception
retry (future)
notify Chief of Staff
FR-028-014

Produce ExecutionReport.

Including:

duration
engine
worker
outputs
status
errors
FR-028-015

Remain completely stateless.

Business Rules
BR-028-001

Never execute WorkOrders with unmet dependencies.

BR-028-002

Never bypass the Execution Planner.

BR-028-003

Never mutate Projects directly.

BR-028-004

Deliverables are mandatory before completion.

BR-028-005

Execution engines remain isolated.

BR-028-006

Failures never terminate JBK-OS.

BR-028-007

Execution Reports are immutable.

Objects

Create:

ExecutionReport

ExecutionLifecycle

WorkExecutionOrchestrator
Unit Tests

Verify:

dependency blocking
engine selection
skill lookup
execution success
execution failure
deliverable creation
report generation
unsupported skills
cancelled execution
stateless execution
Future Evolution (Version 2+)

This section will become your long-term engineering backlog.

Planned Improvements
Automatic retry policies with exponential backoff.
Parallel execution of independent Work Orders.
Distributed execution across multiple execution engines.
Live execution dashboard with streaming logs.
Human approval gates during execution for sensitive tasks.
Automatic rollback for reversible operations.
AI-assisted execution optimization based on historical performance.
Real-time progress percentage estimation.
Execution cost tracking and comparison across engines.
Plugin architecture for external execution providers (GitHub Actions, Docker, Kubernetes, cloud runners, etc.).
Candidate Brain Entry

Execution Orchestration Standards

# Work Execution Architectural Standards

1. The orchestrator coordinates execution but never performs work itself.
2. Every execution must pass through the Execution Planner before dispatch.
3. Dependencies must be satisfied before execution begins.
4. A Work Order is complete only after validated Deliverables are attached.
5. Execution Reports are immutable records of every run.
6. Execution engines must remain replaceable and isolated through the ExecutionEngine interface.