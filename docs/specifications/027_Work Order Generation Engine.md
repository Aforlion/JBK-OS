Specification 027 — Work Order Generation Engine
Purpose

The Work Order Generation Engine transforms the advisory Resource Allocation Plan into executable Work Orders.

This is the point where planning becomes operations.

Unlike previous planning engines, this component creates real WorkOrder objects and registers them with the Chief of Staff for execution.

Objectives

The engine shall:

Read a ResourceAllocationPlan.
Create executable WorkOrders.
Link every WorkOrder to its Project.
Link assigned Worker.
Preserve dependency chains.
Generate execution priorities.
Register all WorkOrders through the Chief of Staff.
Produce a WorkOrderGenerationReport.
Inputs
Project
ResourceAllocationPlan
ChiefOfStaff
WorkerRegistry
Outputs

Creates:

WorkOrderGenerationReport

containing:

generation_id
project_id
created_work_orders
skipped_tasks
dependency_graph
warnings
summary
Business Rules
BR-027-001

Every allocated task becomes exactly one WorkOrder.

BR-027-002

Tasks marked UNASSIGNED shall not become executable WorkOrders.

Instead:

PENDING_RESOURCE
BR-027-003

Dependencies from the WBS must be copied into WorkOrders.

BR-027-004

Generated WorkOrders begin with status

PLANNED

not ACTIVE.

BR-027-005

Every WorkOrder must contain

Project ID
Assigned Worker
Required Capabilities
Estimated Hours
Priority
Dependencies
BR-027-006

The engine must register all WorkOrders through the Chief of Staff.

Direct registry manipulation is prohibited.

BR-027-007

Generation must be atomic.

If one WorkOrder cannot be created, no partial generation occurs.

BR-027-008

The engine shall generate dependency metadata for downstream scheduling engines.

BR-027-009

The engine shall never start execution.

Execution belongs to later engines.

Components
core/
    work_order_generation_report.py
    work_order_generation_engine.py

Tests

tests/
    test_work_order_generation_engine.py
Deliverables
WorkOrderGenerationReport

Stores:

created work orders
skipped tasks
dependency tree
warnings
statistics
Generation Metrics

Includes

Total Tasks
Generated
Pending Resources
Failed
Average Effort
Critical Path Count
Design Principles

The engine must remain:

Deterministic
Atomic
Traceable
Chief-of-Staff Driven
Future Evolution (Version 2+)
Automatic Reallocation

Retry unassigned tasks whenever new workers or skills become available.

Parallel Generation

Generate very large project work orders concurrently while preserving transactional integrity.

Smart Dependency Optimization

Automatically simplify dependency graphs where safe to increase parallel execution.

Work Order Templates

Generate standardized work orders from reusable project and industry templates.

Critical Path Analysis

Automatically identify and highlight the critical execution path.

Execution Readiness Score

Compute a percentage indicating how ready a project is for execution based on resources, dependencies, and approvals.

External Workforce Support

Generate work orders for partner companies, freelancers, or third-party AI services while maintaining unified tracking.

Digital Twin Simulation

Run a simulated execution to predict bottlenecks before activating work orders.

Candidate Brain Entry

Work Order Generation Standards

# Work Order Generation Architectural Standards

All work order generation engines in JBK OS must satisfy:

1. **Atomic Generation**
   Work Orders are generated as a single transaction. Partial generation is prohibited.

2. **Chief of Staff Authority**
   All Work Orders must be created and registered through the Chief of Staff.

3. **Execution Separation**
   Generated Work Orders remain in the PLANNED state until activated by the Execution Orchestrator.

4. **Dependency Preservation**
   All upstream task dependencies must be retained to ensure correct execution sequencing.

5. **Full Traceability**
   Every Work Order must maintain links to its originating WBS task, project, resource allocation, and upstream planning artifacts.