import unittest

from core.client_proposal import ClientProposal
from core.approval_decision import ApprovalDecision, ApprovalStatus
from core.chief_of_staff import ChiefOfStaff
from core.project_registry import ProjectRegistry
from core.worker_registry import WorkerRegistry
from core.project import ProjectStatus
from core.project_initialization_engine import ProjectInitializationEngine
from core.project_initialization_report import ProjectInitializationReport


class TestProjectInitializationEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.worker_registry = WorkerRegistry()
        self.project_registry = ProjectRegistry()
        self.chief_of_staff = ChiefOfStaff(
            worker_registry=self.worker_registry,
            project_registry=self.project_registry,
        )
        self.engine = ProjectInitializationEngine()
        
        # Setup valid approved proposal and decision
        self.proposal_approved = ClientProposal(
            proposal_id="PRP-0010",
            proposal_version="1.0",
            proposal_date="2026-07-13",
            client_name="Charlie",
            client_organization="Cyberdyne",
            proposal_title="Cyberdyne Project Setup",
            executive_summary="Executive summary description",
            understanding_of_client_needs="Needs",
            current_business_challenges="Challenges",
            proposed_solution="Solution",
            solution_benefits="Benefits",
            project_objectives="Objectives",
            scope_of_work={},
            deliverables=[],
            project_timeline="",
            commercial_investment=50000.0,
            payment_terms="50/50 Split",
            optional_services=[],
            client_responsibilities=[],
            assumptions=[],
            exclusions=[],
            warranty="Warranty",
            support_options="Support",
            acceptance_process="Acceptance",
            next_steps="Next steps",
            proposal_valid_until="2026-08-12",
            contact_information="Contact info",
            executive_signature_block="Signature block",
        )
        
        # Link dynamic IDs for upstream validation test
        setattr(self.proposal_approved, "estimate_id", "EST-0010")
        setattr(self.proposal_approved, "blueprint_id", "BLP-0010")
        setattr(self.proposal_approved, "discovery_plan_id", "DSC-0010")
        setattr(self.proposal_approved, "opportunity_id", "OPP-0010")

        self.decision_approved = ApprovalDecision(
            decision_id="DEC-0010",
            proposal_id="PRP-0010",
            status=ApprovalStatus.APPROVED,
        )

        self.proposal_pending = ClientProposal(
            proposal_id="PRP-0020",
            proposal_version="1.0",
            proposal_date="2026-07-13",
            client_name="Bob",
            client_organization="Initech",
            proposal_title="Initech Setup",
            executive_summary="Summary",
            understanding_of_client_needs="Needs",
            current_business_challenges="Challenges",
            proposed_solution="Solution",
            solution_benefits="Benefits",
            project_objectives="Objectives",
            scope_of_work={},
            deliverables=[],
            project_timeline="",
            commercial_investment=10000.0,
            payment_terms="50/50 Split",
            optional_services=[],
            client_responsibilities=[],
            assumptions=[],
            exclusions=[],
            warranty="Warranty",
            support_options="Support",
            acceptance_process="Acceptance",
            next_steps="Next steps",
            proposal_valid_until="2026-08-12",
            contact_information="Contact info",
            executive_signature_block="Signature block",
        )
        
        self.decision_pending = ApprovalDecision(
            decision_id="DEC-0020",
            proposal_id="PRP-0020",
            status=ApprovalStatus.PENDING_REVIEW,
        )

    def test_invalid_initialize_inputs(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.initialize_project(None, self.decision_approved, self.chief_of_staff)  # type: ignore
        with self.assertRaises(ValueError):
            self.engine.initialize_project(self.proposal_approved, None, self.chief_of_staff)  # type: ignore
        with self.assertRaises(ValueError):
            self.engine.initialize_project(self.proposal_approved, self.decision_approved, None)  # type: ignore

    def test_unapproved_proposal_raises_error(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.initialize_project(self.proposal_pending, self.decision_pending, self.chief_of_staff)

    def test_initialize_success(self) -> None:
        report = self.engine.initialize_project(self.proposal_approved, self.decision_approved, self.chief_of_staff)
        self.assertIsInstance(report, ProjectInitializationReport)
        self.assertEqual(report.status, "INITIALIZED")
        self.assertEqual(report.proposal_id, "PRP-0010")
        self.assertEqual(report.decision_id, "DEC-0010")
        self.assertEqual(report.estimate_id, "EST-0010")
        self.assertEqual(report.blueprint_id, "BLP-0010")
        self.assertEqual(report.discovery_plan_id, "DSC-0010")
        self.assertEqual(report.opportunity_id, "OPP-0010")
        self.assertEqual(report.coordinator_id, "chief_of_staff")
        
        # Verify project exists in registry
        project = self.project_registry.find_by_id(report.project_id)
        self.assertIsNotNone(project)
        self.assertEqual(project.status, ProjectStatus.ACTIVE)
        self.assertEqual(getattr(project, "proposal_id", None), "PRP-0010")
        self.assertEqual(getattr(project, "coordinator_id", None), "chief_of_staff")
        
        # Verify 3 standard initial Work Orders exist on project
        self.assertEqual(len(project.work_orders), 3)
        wo_titles = [wo.title for wo in project.work_orders]
        self.assertIn("Project Kickoff", wo_titles)
        self.assertIn("Architecture Blueprint Review", wo_titles)
        self.assertIn("Environment Setup", wo_titles)
        
        # Verify decision was recorded
        self.assertEqual(len(project.decisions), 1)
        self.assertEqual(project.decisions[0].decision_id, "DEC-0010")

    def test_single_initialization_rule(self) -> None:
        # First initialization succeeds
        self.engine.initialize_project(self.proposal_approved, self.decision_approved, self.chief_of_staff)
        
        # Second initialization with same proposal ID (either in engine state or registry) fails
        with self.assertRaises(ValueError):
            self.engine.initialize_project(self.proposal_approved, self.decision_approved, self.chief_of_staff)

    def test_serialization(self) -> None:
        report = self.engine.initialize_project(self.proposal_approved, self.decision_approved, self.chief_of_staff)
        summary = report.summary()
        self.assertEqual(summary["report_id"], report.report_id)
        self.assertEqual(summary["status"], "INITIALIZED")
        
        to_dict_out = report.to_dict()
        self.assertEqual(to_dict_out["report_id"], report.report_id)
        self.assertEqual(to_dict_out["project_id"], report.project_id)
        self.assertEqual(len(to_dict_out["initial_work_orders"]), 3)
