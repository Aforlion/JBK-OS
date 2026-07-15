# JBK-OS Engine Dependency Map (Version 1.0)

This document provides a comprehensive map of all 19 major engines within JBK-OS, outlining their consumers, producers, dependencies, objects, side effects, and state characteristics.

---

## 1. Client Pipeline Layer

### Opportunity Intake Engine
- **Consumes**: Raw natural language client request (`str`).
- **Produces**: `OpportunityBrief`
- **Dependencies**: None.
- **Business Objects**: `OpportunityBrief`
- **Registries Used**: None.
- **Side Effects**: None.
- **Read Only?**: Yes (Inputs are not modified).
- **Stateless?**: Yes.

### Discovery Conversation Engine
- **Consumes**: `OpportunityBrief`
- **Produces**: `DiscoveryPlan`
- **Dependencies**: None.
- **Business Objects**: `OpportunityBrief`, `DiscoveryPlan`
- **Registries Used**: None.
- **Side Effects**: None.
- **Read Only?**: Yes.
- **Stateless?**: Yes.

### Solution Architect
- **Consumes**: `DiscoveryPlan`
- **Produces**: `SolutionBlueprint`
- **Dependencies**: None.
- **Business Objects**: `DiscoveryPlan`, `SolutionBlueprint`
- **Registries Used**: None.
- **Side Effects**: None.
- **Read Only?**: Yes.
- **Stateless?**: Yes.

### Estimation Engine
- **Consumes**: `SolutionBlueprint`
- **Produces**: `ProjectEstimate`
- **Dependencies**: None.
- **Business Objects**: `SolutionBlueprint`, `ProjectEstimate`
- **Registries Used**: None.
- **Side Effects**: None.
- **Read Only?**: Yes.
- **Stateless?**: Yes.

### Pricing Engine
- **Consumes**: `ProjectEstimate`
- **Produces**: `CommercialProposal`
- **Dependencies**: None.
- **Business Objects**: `ProjectEstimate`, `CommercialProposal`
- **Registries Used**: None.
- **Side Effects**: None.
- **Read Only?**: Yes.
- **Stateless?**: Yes.

### Proposal Generator
- **Consumes**: `CommercialProposal`, Client Name (`str`), Client Organization (`str`).
- **Produces**: `ClientProposal`
- **Dependencies**: None.
- **Business Objects**: `CommercialProposal`, `ClientProposal`
- **Registries Used**: None.
- **Side Effects**: None.
- **Read Only?**: Yes.
- **Stateless?**: Yes.

### CEO Approval Workflow
- **Consumes**: `ClientProposal`, Approval Decision Maker (`str`), Decision Comments (`str`).
- **Produces**: `ApprovalDecision`
- **Dependencies**: None.
- **Business Objects**: `ClientProposal`, `ApprovalDecision`
- **Registries Used**: None.
- **Side Effects**: None (state is encapsulated in returning `ApprovalDecision` object).
- **Read Only?**: No (Mutates status of returning `ApprovalDecision` via `approve`/`reject` methods).
- **Stateless?**: Yes (methods operate purely on objects passed as parameters).

---

## 2. Company Layer & Core Registries

### Chief of Staff (Registry Manager)
- **Consumes**: Worker, Project, and Knowledge assets.
- **Produces**: Instantiated/registered entities.
- **Dependencies**: `WorkerRegistry`, `ProjectRegistry`, `KnowledgeRegistry`.
- **Business Objects**: `Project`, `WorkOrder`, `Deliverable`, `OrganizationalKnowledge`.
- **Registries Used**: `WorkerRegistry`, `ProjectRegistry`, `KnowledgeRegistry`.
- **Side Effects**: Registers and updates state inside registry dictionaries.
- **Read Only?**: No.
- **Stateless?**: No (holds references to active registries).

---

## 3. Delivery Pipeline Layer

### Project Initialization Engine
- **Consumes**: `ClientProposal`, `ApprovalDecision`, `ChiefOfStaff`.
- **Produces**: `ProjectInitializationReport`
- **Dependencies**: `ChiefOfStaff`.
- **Business Objects**: `ClientProposal`, `ApprovalDecision`, `Project`, `ProjectInitializationReport`.
- **Registries Used**: `ProjectRegistry` (via `ChiefOfStaff`).
- **Side Effects**: Registers initialized project with status `ACTIVE`.
- **Read Only?**: No.
- **Stateless?**: Yes.

### Delivery Planning Engine
- **Consumes**: Project ID (`str`), Project Details (`dict`).
- **Produces**: `DeliveryPlan`
- **Dependencies**: None.
- **Business Objects**: `DeliveryPlan`
- **Registries Used**: None.
- **Side Effects**: None.
- **Read Only?**: Yes.
- **Stateless?**: Yes.

### Work Breakdown Engine
- **Consumes**: `DeliveryPlan`
- **Produces**: `WorkBreakdownStructure`
- **Dependencies**: None.
- **Business Objects**: `DeliveryPlan`, `WorkBreakdownStructure`
- **Registries Used**: None.
- **Side Effects**: None.
- **Read Only?**: Yes.
- **Stateless?**: Yes.

### Resource Allocation Engine
- **Consumes**: `WorkBreakdownStructure`, `WorkerRegistry`, `SkillRegistry`.
- **Produces**: `ResourceAllocationPlan`
- **Dependencies**: None.
- **Business Objects**: `WorkBreakdownStructure`, `ResourceAllocationPlan`.
- **Registries Used**: `WorkerRegistry`, `SkillRegistry`.
- **Side Effects**: None (advisory allocation).
- **Read Only?**: Yes.
- **Stateless?**: Yes.

### Work Order Generation Engine
- **Consumes**: `Project`, `ResourceAllocationPlan`, `ChiefOfStaff`.
- **Produces**: `WorkOrderGenerationReport`
- **Dependencies**: `ChiefOfStaff`.
- **Business Objects**: `Project`, `ResourceAllocationPlan`, `WorkOrder`, `WorkOrderGenerationReport`.
- **Registries Used**: `ProjectRegistry` (via `ChiefOfStaff`).
- **Side Effects**: Attaches registered `WorkOrder` entities to the project record and assigns them to worker workloads.
- **Read Only?**: No.
- **Stateless?**: Yes.

### Work Execution Orchestrator
- **Consumes**: `WorkOrder`, `Project`, `SkillRegistry`, `ExecutionPlanner`, `ChiefOfStaff`.
- **Produces**: `ExecutionReport`, `Deliverable`.
- **Dependencies**: `ChiefOfStaff`.
- **Business Objects**: `WorkOrder`, `Project`, `ExecutionReport`, `Deliverable`.
- **Registries Used**: `SkillRegistry`, `ProjectRegistry` (via `ChiefOfStaff`).
- **Side Effects**: Mutates `WorkOrder` status (e.g. `COMPLETED`), registers generated deliverables.
- **Read Only?**: No.
- **Stateless?**: Yes.

### Delivery Supervision Engine
- **Consumes**: `Project`, `WorkerRegistry`, optional list of `ExecutionReport`.
- **Produces**: `DeliveryStatusReport`
- **Dependencies**: None.
- **Business Objects**: `Project`, `DeliveryStatusReport`.
- **Registries Used**: `WorkerRegistry`.
- **Side Effects**: None.
- **Read Only?**: Yes.
- **Stateless?**: Yes.

---

## 4. Learning Pipeline Layer

### Organizational Memory Engine
- **Consumes**: `Project`, `ChiefOfStaff`, `DeliveryStatusReport` (optional), list of `ExecutionReport` (optional), `SolutionBlueprint` (optional), notes (`list[str]`).
- **Produces**: `OrganizationalMemoryReport` (containing `OrganizationalKnowledge` objects).
- **Dependencies**: `ChiefOfStaff`.
- **Business Objects**: `Project`, `OrganizationalKnowledge`, `OrganizationalMemoryReport`.
- **Registries Used**: `KnowledgeRegistry` (via `ChiefOfStaff`).
- **Side Effects**: Registers knowledge assets to `KnowledgeRegistry` upon project archiving.
- **Read Only?**: No (registers output to registry).
- **Stateless?**: Yes.

### Continuous Improvement Engine
- **Consumes**: `KnowledgeRegistry`, optional notes (`list[str]`).
- **Produces**: `ContinuousImprovementReport`
- **Dependencies**: None.
- **Business Objects**: `ContinuousImprovementReport`, `ContinuousImprovementRecommendation`.
- **Registries Used**: `KnowledgeRegistry`.
- **Side Effects**: None (advisory improvements).
- **Read Only?**: Yes.
- **Stateless?**: Yes.

---

## 5. Portfolio & Strategic Layer

### Business Transformation Engine
- **Consumes**: `SolutionBlueprint`, optional `ProjectEstimate`, `CommercialProposal`, `DiscoveryPlan`.
- **Produces**: `BusinessTransformationPlan`
- **Dependencies**: None.
- **Business Objects**: `SolutionBlueprint`, `BusinessTransformationPlan`.
- **Registries Used**: None.
- **Side Effects**: None.
- **Read Only?**: Yes.
- **Stateless?**: Yes.

### Portfolio Management Engine
- **Consumes**: `ProjectRegistry`, `WorkerRegistry`, lists of reports/plans.
- **Produces**: `PortfolioReport`
- **Dependencies**: None.
- **Business Objects**: `PortfolioReport`.
- **Registries Used**: `ProjectRegistry`, `WorkerRegistry`.
- **Side Effects**: None.
- **Read Only?**: Yes.
- **Stateless?**: Yes.

### Strategic Intelligence Engine
- **Consumes**: Lists of `OrganizationalKnowledge`, `PortfolioReport`, and raw intelligence dicts.
- **Produces**: `StrategicIntelligenceReport`
- **Dependencies**: None.
- **Business Objects**: `StrategicIntelligenceReport`.
- **Registries Used**: None.
- **Side Effects**: None.
- **Read Only?**: Yes.
- **Stateless?**: Yes.
