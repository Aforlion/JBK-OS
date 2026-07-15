import unittest
from datetime import datetime, timezone

from core.project import Project, ProjectStatus
from core.chief_of_staff import ChiefOfStaff
from core.project_registry import ProjectRegistry
from core.worker_registry import WorkerRegistry
from core.knowledge_registry import KnowledgeRegistry
from core.deliverable import Deliverable, DeliverableStatus
from core.work_order import WorkOrder, WorkOrderStatus
from core.approval_decision import ApprovalDecision, ApprovalStatus
from core.client_delivery_handover_report import ClientAcceptance, ProjectClosureReport
from core.client_delivery_handover_engine import ClientDeliveryHandoverEngine


class TestClientDeliveryHandoverEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.project_registry = ProjectRegistry()
        self.worker_registry = WorkerRegistry()
        self.knowledge_registry = KnowledgeRegistry()
        
        self.chief_of_staff = ChiefOfStaff(
            worker_registry=self.worker_registry,
            project_registry=self.project_registry,
            knowledge_registry=self.knowledge_registry,
        )

        self.engine = ClientDeliveryHandoverEngine()

        # Create active project
        self.project = self.chief_of_staff.create_project(
            project_id="PROJ-9999",
            title="Database Rollout",
            client="Acme Corp",
            description="Production rollout of PostgreSQL on AWS.",
        )
        self.chief_of_staff.register_project(self.project)

        # Create a work order that is completed
        self.wo = self.chief_of_staff.create_work_order(
            project_id="PROJ-9999",
            title="Deploy Postgres",
            objective="Deploy PG instances",
            work_order_id="WO-9999",
        )
        self.wo.status = WorkOrderStatus.COMPLETED

        # Create deliverables (one main, one documentation)
        self.deliv_main = Deliverable(
            project_id="PROJ-9999",
            work_order_id="WO-9999",
            title="Database instances configured",
            author="EXEC-0001",
            content="PostgreSQL is live.",
            deliverable_id="DEL-101",
        )
        self.deliv_main.status = DeliverableStatus.APPROVED

        self.deliv_doc = Deliverable(
            project_id="PROJ-9999",
            work_order_id="WO-9999",
            title="Operations Manual",
            author="EXEC-0001",
            content="System documentation guide.",
            deliverable_id="DEL-102",
        )
        self.deliv_doc.status = DeliverableStatus.APPROVED

        # Default acceptance
        self.acceptance = ClientAcceptance(
            status="Accepted",
            reviewer="Alice Smith",
            comments="Everything works perfectly.",
            approval_date="2026-07-13",
        )

        # Default CEO approval
        self.approval = ApprovalDecision(
            decision_id="DEC-8888",
            proposal_id="PRP-9999",
            status=ApprovalStatus.APPROVED,
        )

    # ------------------------------------------------------------------
    # Completion Validations (BR-036-001)
    # ------------------------------------------------------------------

    def test_unfinished_work_orders_prevent_handover(self) -> None:
        self.wo.status = WorkOrderStatus.IN_PROGRESS  # In progress
        with self.assertRaises(ValueError):
            self.engine.complete_project(
                self.project,
                self.chief_of_staff,
                [self.deliv_main, self.deliv_doc],
                self.acceptance,
                self.approval,
            )

    def test_unapproved_deliverables_prevent_handover(self) -> None:
        self.deliv_main.status = DeliverableStatus.IN_REVIEW
        with self.assertRaises(ValueError):
            self.engine.complete_project(
                self.project,
                self.chief_of_staff,
                [self.deliv_main, self.deliv_doc],
                self.acceptance,
                self.approval,
            )

    def test_missing_documentation_prevents_handover(self) -> None:
        # Deliverables only contain main configured db, no doc/guide/manual
        with self.assertRaises(ValueError):
            self.engine.complete_project(
                self.project,
                self.chief_of_staff,
                [self.deliv_main],
                self.acceptance,
                self.approval,
            )

    # ------------------------------------------------------------------
    # Executive Sign-Off Requirement (BR-036-010)
    # ------------------------------------------------------------------

    def test_executive_approval_mandatory(self) -> None:
        # No approval object
        with self.assertRaises(ValueError):
            self.engine.complete_project(
                self.project,
                self.chief_of_staff,
                [self.deliv_main, self.deliv_doc],
                self.acceptance,
                executive_approval_decision=None,
            )

        # Pending approval
        self.approval.status = ApprovalStatus.PENDING_REVIEW
        with self.assertRaises(ValueError):
            self.engine.complete_project(
                self.project,
                self.chief_of_staff,
                [self.deliv_main, self.deliv_doc],
                self.acceptance,
                self.approval,
            )

    # ------------------------------------------------------------------
    # Client Acceptance Workflows
    # ------------------------------------------------------------------

    def test_conditional_acceptance_spawns_work_orders(self) -> None:
        cond_acceptance = ClientAcceptance(
            status="Accepted with Conditions",
            reviewer="Alice Smith",
            conditions=["Fix slow AWS IOPS backup", "Update admin password policy"],
        )

        report = self.engine.complete_project(
            self.project,
            self.chief_of_staff,
            [self.deliv_main, self.deliv_doc],
            cond_acceptance,
            self.approval,
        )

        self.assertIsInstance(report, ProjectClosureReport)
        self.assertEqual(report.acceptance_result["status"], "Accepted with Conditions")

        # Verify that follow-up work orders were spawned under the project
        # In this test, project has 1 original work order + 2 new conditional work orders
        self.assertEqual(len(self.project.work_orders), 3)
        self.assertEqual(self.project.work_orders[1].title, "Resolve Condition: Fix slow AWS IOPS backup")
        self.assertEqual(self.project.work_orders[2].title, "Resolve Condition: Update admin password policy")

    def test_client_rejection_workflow(self) -> None:
        rejected_acceptance = ClientAcceptance(
            status="Rejected",
            reviewer="Alice Smith",
            comments="Performance is far below baseline requirements.",
        )
        # Rejection should generate report but project stays in completed/active state
        report = self.engine.complete_project(
            self.project,
            self.chief_of_staff,
            [self.deliv_main, self.deliv_doc],
            rejected_acceptance,
            self.approval,
        )
        self.assertEqual(report.acceptance_result["status"], "Rejected")

    # ------------------------------------------------------------------
    # Full Happy Path Project Closure (BR-036-011)
    # ------------------------------------------------------------------

    def test_serialization_and_happy_path(self) -> None:
        report = self.engine.complete_project(
            self.project,
            self.chief_of_staff,
            [self.deliv_main, self.deliv_doc],
            self.acceptance,
            self.approval,
        )

        # 1. Output Validation
        self.assertIsInstance(report, ProjectClosureReport)
        self.assertEqual(report.project_id, "PROJ-9999")
        self.assertEqual(str(report.executive_approval["status"]).upper(), "APPROVED")
        self.assertEqual(self.project.status, ProjectStatus.COMPLETED)

        # 2. Service activations
        self.assertIn("start_date", report.warranty_activated)
        self.assertEqual(report.support_activated["support_level"], "Standard Tier")

        # 3. Knowledge registration
        self.assertEqual(len(report.knowledge_registered), 1)

        # 4. Serialization checks
        s = report.summary()
        self.assertEqual(s["report_id"], report.report_id)
        self.assertEqual(s["project_id"], "PROJ-9999")
        self.assertEqual(s["acceptance_status"], "Accepted")

        d = report.to_dict()
        self.assertEqual(d["report_id"], report.report_id)
        self.assertEqual(str(d["executive_approval"]["status"]).upper(), "APPROVED")
        self.assertEqual(len(d["archived_assets"]), 5)  # Blueprint + Estimate + Proposal + 2 Deliverables
