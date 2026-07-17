# JBK-OS Pilot Demo Script

This script walks a salesperson or operator through showing a prospective client the full automated lifecycle of JBK-OS V1.

## 1. Setup & Introduction
Explain the core value proposition: JBK-OS acts as the digital nervous system of the organization, coordinating business intake, estimation, approvals, work delivery, and learning capture automatically.

---

## 2. Step-by-Step Walkthrough

### Step 2.1: Client Opportunity Intake
**Action**: Submit an unstructured project request into JBK-OS.
- **Sample Request Input**:
  > "We need a new PostgreSQL database migrated to AWS. Budget is $50,000. Timeline is 6 weeks. Contact: alice@jbk.tech"
- **Visual Outcome**: JBK-OS parses the unstructured text, classifies it as a `Technology` project, and registers the contact info.

### Step 2.2: Automated Discovery & Scoping
**Action**: Observe the system formulate context-aware discovery questions.
- **Visual Outcome**: The system automatically generates a list of required questions regarding database size, target AWS region, and source environment details.

### Step 2.3: Solution Architecture Blueprinting
**Action**: The system generates the `SolutionBlueprint`.
- **Visual Outcome**: The system identifies that an `API & Backend Development` capability is required and estimates that the scope requires 80 engineering hours.

### Step 2.4: Estimation & Pricing Calculation
**Action**: Open the generated estimation and commercial model.
- **Visual Outcome**: The pricing engine calculates developer cost, adds the target margin, and proposes a client price of `$24,000` with a 50/50 payment split structure.

### Step 2.5: CEO Approval
**Action**: Run the CEO approval simulation.
- **Visual Outcome**: The system submits the proposal to the CEO Approval Workflow. The CEO approves the margins, signing off with: "Looks great. Proceeding with database setup."

### Step 2.6: Delivery Automation
**Action**: Observe the system spawn the project and allocate tasks.
- **Visual Outcome**:
  - The project transitions to `ACTIVE`.
  - The system creates tasks (`TSK-01-01`, etc.) and automatically assigns them to active workers based on matching skills.
  - Work orders are generated and executed.

### Step 2.7: Project Archiving & Learning Capture
**Action**: Run project closure and check the Knowledge Registry.
- **Visual Outcome**: The project closes successfully. The Organizational Memory Engine immediately extracts lessons learned and updates the database-migration estimate models to refine future estimates.
