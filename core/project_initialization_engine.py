from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

from core.client_proposal import ClientProposal
from core.approval_decision import ApprovalDecision, ApprovalStatus
from core.chief_of_staff import ChiefOfStaff
from core.project import Project, ProjectStatus
from core.work_order import WorkOrder, WorkOrderPriority
from core.project_initialization_report import ProjectInitializationReport

LOGGER = logging.getLogger(__name__)


class ProjectInitializationEngine:
    def __init__(self) -> None:
        self._initialized_proposals: set[str] = set()
        self._next_report_id = 1

    def _generate_report_id(self) -> str:
        rep_id = f"IR-{self._next_report_id:04d}"
        self._next_report_id += 1
        return rep_id

    def initialize_project(
        self,
        client_proposal: ClientProposal,
        approval_decision: ApprovalDecision,
        chief_of_staff: ChiefOfStaff,
    ) -> ProjectInitializationReport:
        if client_proposal is None:
            raise ValueError("Client proposal is required.")
        if approval_decision is None:
            raise ValueError("Approval decision is required.")
        if chief_of_staff is None:
            raise ValueError("Chief of Staff is required.")

        proposal_id = getattr(client_proposal, "proposal_id", "UNKNOWN")
        decision_id = getattr(approval_decision, "decision_id", "UNKNOWN")

        # 1. Enforce Single Initialization Rule
        if proposal_id in self._initialized_proposals:
            raise ValueError(f"Proposal {proposal_id} has already been initialized.")

        # Check registry for any existing projects with same proposal ID
        for proj in chief_of_staff.project_registry.list_projects():
            if getattr(proj, "proposal_id", None) == proposal_id:
                raise ValueError(f"Proposal {proposal_id} has already been initialized (project exists).")

        # 2. Enforce Approval validation
        status_val = getattr(approval_decision.status, "value", approval_decision.status)
        if status_val != "Approved" and status_val != ApprovalStatus.APPROVED.value:
            raise ValueError(f"Cannot initialize project. Status must be Approved, got: {status_val}.")

        LOGGER.info(
            "object_id=%s action=initialize_project actor=system status=DRAFT proposal_id=%s",
            decision_id,
            proposal_id,
        )

        # 3. Extract upstream IDs
        estimate_id = getattr(client_proposal, "estimate_id", None) or getattr(approval_decision, "estimate_id", "UNKNOWN")
        blueprint_id = getattr(client_proposal, "blueprint_id", None) or getattr(approval_decision, "blueprint_id", "UNKNOWN")
        discovery_plan_id = getattr(client_proposal, "discovery_plan_id", None) or getattr(approval_decision, "discovery_plan_id", "UNKNOWN")
        opportunity_id = getattr(client_proposal, "opportunity_id", None) or getattr(approval_decision, "opportunity_id", "UNKNOWN")

        project_title = client_proposal.proposal_title or f"Project for {client_proposal.client_organization}"
        client_label = f"{client_proposal.client_name} ({client_proposal.client_organization})"
        project_description = client_proposal.executive_summary or "Initialized JBK Project."

        # 4. Instantiate & Register project
        project = chief_of_staff.create_project(
            title=project_title,
            client=client_label,
            description=project_description,
            status=ProjectStatus.ACTIVE,
        )

        # Attach link properties to Project dynamically
        setattr(project, "proposal_id", proposal_id)
        setattr(project, "decision_id", decision_id)
        setattr(project, "estimate_id", estimate_id)
        setattr(project, "blueprint_id", blueprint_id)
        setattr(project, "discovery_plan_id", discovery_plan_id)
        setattr(project, "opportunity_id", opportunity_id)
        setattr(project, "coordinator_id", "chief_of_staff")

        # Record decision
        project.record_decision(approval_decision, actor="project_initialization_engine")

        # Register project
        chief_of_staff.register_project(project)

        # 5. Create standard initial Work Orders
        initial_work_orders_data = [
            {
                "title": "Project Kickoff",
                "objective": "Execute project kickoff meeting and align deliverables checklist.",
                "priority": WorkOrderPriority.HIGH,
            },
            {
                "title": "Architecture Blueprint Review",
                "objective": "Review and approve solution design blueprints.",
                "priority": WorkOrderPriority.MEDIUM,
            },
            {
                "title": "Environment Setup",
                "objective": "Provision sandbox development and testing environments.",
                "priority": WorkOrderPriority.MEDIUM,
            },
        ]

        created_wos = []
        for wo_data in initial_work_orders_data:
            wo = chief_of_staff.create_work_order(
                project_id=project.id,
                title=wo_data["title"],
                objective=wo_data["objective"],
                priority=wo_data["priority"],
            )
            created_wos.append(wo.to_dict())

        # Update set
        self._initialized_proposals.add(proposal_id)

        report_id = self._generate_report_id()
        report = ProjectInitializationReport(
            report_id=report_id,
            project_id=project.id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            estimate_id=estimate_id,
            blueprint_id=blueprint_id,
            discovery_plan_id=discovery_plan_id,
            opportunity_id=opportunity_id,
            client_name=client_proposal.client_name,
            client_organization=client_proposal.client_organization,
            project_title=project_title,
            project_description=project_description,
            coordinator_id="chief_of_staff",
            initial_work_orders=created_wos,
            status="INITIALIZED",
        )

        LOGGER.info(
            "object_id=%s action=initialize_project actor=system status=READY project_id=%s",
            report_id,
            project.id,
        )
        return report
