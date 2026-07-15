# Executable CEO Demonstration Script: JBK-OS V1

This document provides a step-by-step walkthrough to run a complete, end-to-end simulation of JBK-OS. This script can be run by anyone to demonstrate the unified system.

## Scenario Setup

A new prospective client, **Acme Corp**, has reached out with an unstructured request:
> "We need a new PostgreSQL database migrated to AWS. Budget is $50,000. Timeline is 6 weeks. Contact: alice@jbk.tech"

---

## Execution Guide

### Step 1: Boot JBK-OS & Display Briefing
Run the executive console. In your terminal, execute the following command:
```bash
python -m unittest tests/test_end_to_end_workflow.py -v
```

This test acts as our end-to-end integration validator. It simulates the system booting up, registering the Executive staff (`EXEC-0001` and `EXEC-0002`), registering their skills, and standing up the core registries under the Chief of Staff.

### Step 2: Client Pipeline Stages
During the execution, JBK-OS runs the following client pipeline sequentially:
1. **Opportunity Intake**: Evaluates the text input and determines the request belongs to the `Technology` domain.
2. **Discovery Conversation**: Formulates discovery questions based on the brief.
3. **Solution Architecture**: Generates a `SolutionBlueprint` indicating that a "PostgreSQL Database Migration" capability is required.
4. **Project Estimation**: Automatically calculates that a Tech-domain project of this scale requires approximately `80 hours` of developer effort.
5. **Pricing Engine**: Determines costs, applies margins, and recommends a commercial price of `$24,000` with a 50/50 payment split structure.
6. **Proposal Generator**: Generates a formal proposal block.

### Step 3: CEO Review & Approval
The generated proposal is submitted to the **CEO Approval Workflow**. The CEO reviews the margins and signs off:
- **Decision Maker**: `CEO-John`
- **Action**: `APPROVE`
- **Comment**: "Looks great. Proceeding with database setup."

### Step 4: Delivery Automation
Upon approval, the system transitions to the delivery phase:
1. **Initialization**: Creates a project (`PROJ-0001`) with status `ACTIVE`.
2. **Delivery Planning**: Generates work streams (Technology and Operations).
3. **Work Breakdown**: Deconstructs work streams into tasks (`TSK-01-01`, `TSK-01-02`, etc.).
4. **Resource Allocation**: Assigns the backend tasks to `EXEC-0001` (Dev Lead) because they own the matching `API & Backend Development` skill.
5. **Work Order Generation**: Atomically spawns executable work orders.

### Step 5: Execution & Learning Capture
1. **Execution**: The orchestrator dispatches and executes the work orders. The developer registers completed deliverables.
2. **Delivery Supervision**: Observes utilization rates, ensuring no executive was bottlenecked.
3. **Project Archiving**: The Chief of Staff transitions the project to `COMPLETED`. The **Organizational Memory Engine** immediately extracts lessons learned and reusable blueprints, registering them in the `KnowledgeRegistry`.
4. **Continuous Improvement**: The engine reviews the registry, identifying process bottlenecks to refine future estimation weights.

### Step 6: Portfolio & Strategic Report Updates
Finally, the portfolio is updated:
1. **Portfolio Management**: Analyzes the status of all projects, calculating that the active project list is empty (healthy closure) and available capacity has returned to 100%.
2. **Strategic Intelligence**: Runs analysis on the archived knowledge asset and recommends:
   - *Action required regarding: Knowledge Base Insight*
   - *Category*: `Technology`
   - *Expected Business Impact*: `Transformational`
   - *Recommended Action*: "Establish internal working group to evaluate technology adoption."

This represents a complete lifecycle run of the executive operating system!
