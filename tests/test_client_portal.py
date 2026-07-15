import unittest
from datetime import datetime, timezone
from typing import Any
from fastapi.testclient import TestClient

from core.client_workspace import (
    ClientWorkspace,
    WorkspaceSection,
    WorkspaceNotification,
    WorkspaceActivity,
    WorkspaceSummary,
    WorkspacePermission,
)
from core.client_portal_controller import ClientPortalController
from portal.app import create_portal_app
from portal.websocket_manager import PortalWebSocketManager
from core.client_profile import ClientProfile
from core.invoice import Invoice, LineItem
from core.financial_snapshot import FinancialSnapshot
from core.financial_report import FinancialReport


class MockCRMEngine:
    def __init__(self) -> None:
        self.client = ClientProfile(
            client_id="CLT-0001",
            company="Acme Corp",
            industry="EdTech",
        )
        self.client.active_projects = ["PROJ-0001"]
        self.interactions = []

    def get_client(self, client_id: str) -> Any:
        if client_id == "CLT-0001":
            return self.client
        return None

    def list_clients(self) -> list:
        return [self.client]

    def log_interaction(self, client_id: str, interaction_type: str, description: str, outcome: str = "") -> None:
        self.interactions.append({
            "client_id": client_id,
            "type": interaction_type,
            "description": description,
            "outcome": outcome,
        })

    def update_health(self, client_id: str) -> None:
        pass


class MockFinancialEngine:
    def list_invoices(self) -> list:
        inv = Invoice(
            invoice_id="INV-0001",
            client_id="CLT-0001",
            project_id="PROJ-0001",
            due_date="2026-08-30",
        )
        # Add line item so total works
        inv.line_items = [LineItem("Consulting", 1, 1000.0)]
        return [inv]

    def generate_financial_report(self) -> Any:
        snap = FinancialSnapshot(total_revenue=1000.0)
        report = FinancialReport(
            report_id="FIN-0001",
            executive_summary="Summary",
            cash_health="Healthy",
            snapshot=snap,
        )
        # Set invoice balance outstanding
        report.outstanding_invoices = [
            {"client_id": "CLT-0001", "invoice_id": "INV-0001", "balance": 1000.0, "status": "SENT"}
        ]
        return report


class MockDeliveryEngine:
    def generate_delivery_status_report(self) -> dict:
        return {
            "status": "HEALTHY",
            "projects": [
                {
                    "project_id": "PROJ-0001",
                    "client_id": "CLT-0001",
                    "name": "Alpha Build",
                    "completion_pct": 80.0,
                    "status": "IN_PROGRESS",
                }
            ]
        }


class MockCommEngine:
    def __init__(self) -> None:
        class AuditLogMock:
            def __init__(self) -> None:
                self.logs = []
            def append(self, communication_id: str, action: str, details: str) -> None:
                self.logs.append({"id": communication_id, "action": action, "details": details})
        self.audit_log = AuditLogMock()

    def get_audit_log(self) -> Any:
        return self.audit_log

    def list_notifications(self) -> list:
        class Notif:
            def __init__(self) -> None:
                self.notification_id = "NTF-0001"
                self.title = "Deliverable Ready"
                self.message = "Milestone 1 is ready."
                self.recipient_role = "CLIENT"
                self.severity = "MEDIUM"
                self.created_at = "2026-07-14T09:00:00Z"
                self.source_engine = "ClientSuccessEngine"
        return [Notif()]


class MockImprovementEngine:
    def __init__(self) -> None:
        self.learnings = []

    def register_learning_opportunity(self, source: str, description: str, severity: str) -> None:
        self.learnings.append({
            "source": source,
            "description": description,
            "severity": severity,
        })


class TestClientWorkspaceModels(unittest.TestCase):

    def test_workspace_serialization(self) -> None:
        """BR-048-010: Serialization works."""
        summary = WorkspaceSummary(active_projects_count=1, pending_approvals_count=2, balance_due=150.0)
        section = WorkspaceSection("projects", "Projects", "HEALTHY")
        notif = WorkspaceNotification("N1", "Title", "Msg", "LOW")
        act = WorkspaceActivity("A1", "Milestone Approved", "Approvals", "2026-07-14T00:00:00Z")
        perm = WorkspacePermission(read_only=False)

        ws = ClientWorkspace(
            client_id="CLT-0001",
            company="Test Client",
            summary=summary,
            sections=[section],
            notifications=[notif],
            activities=[act],
            permissions=perm,
        )

        d = ws.to_dict()
        self.assertEqual(d["client_id"], "CLT-0001")
        self.assertEqual(d["summary"]["balance_due"], 150.0)
        self.assertEqual(d["sections"][0]["title"], "Projects")
        self.assertEqual(d["notifications"][0]["title"], "Title")
        self.assertEqual(d["activities"][0]["title"], "Milestone Approved")
        self.assertEqual(d["permissions"]["can_approve"], True)


class TestClientPortalController(unittest.TestCase):

    def setUp(self) -> None:
        self.crm = MockCRMEngine()
        self.fin = MockFinancialEngine()
        self.delivery = MockDeliveryEngine()
        self.comm = MockCommEngine()
        self.imp = MockImprovementEngine()

        self.controller = ClientPortalController(
            crm_engine=self.crm,
            financial_engine=self.fin,
            delivery_engine=self.delivery,
            communication_engine=self.comm,
            improvement_engine=self.imp,
        )

    def test_load_workspace_success(self) -> None:
        """Workspace loads successfully."""
        ws = self.controller.load_workspace("CLT-0001", "CLT-0001")
        self.assertEqual(ws.company, "Acme Corp")
        self.assertEqual(ws.summary.balance_due, 1000.0)
        self.assertEqual(ws.summary.active_projects_count, 1)

    def test_client_isolation_enforced(self) -> None:
        """Client A can never see Client B's workspace."""
        with self.assertRaises(PermissionError):
            self.controller.load_workspace("CLT-0002", "CLT-0001")

    def test_internal_information_hidden(self) -> None:
        """BR-048-002: Internal information hidden (e.g. no margin, no internal costs)."""
        ws = self.controller.load_workspace("CLT-0001", "CLT-0001")
        d = ws.to_dict()
        # Ensure no internal cost metrics leaks to the view model serialization
        serialized_str = str(d).lower()
        self.assertNotIn("margin", serialized_str)
        self.assertNotIn("internal_cost", serialized_str)
        self.assertNotIn("profit", serialized_str)

    def test_document_vault_version_history(self) -> None:
        """BR-048-004: Version history works."""
        doc1 = self.controller.upload_document("CLT-0001", "Spec.pdf", "Content v1", "Client User")
        doc2 = self.controller.upload_document("CLT-0001", "Spec.pdf", "Content v2", "Client User")

        self.assertEqual(doc1["version"], 1)
        self.assertEqual(doc2["version"], 2)

        ws = self.controller.load_workspace("CLT-0001", "CLT-0001")
        doc_sec = next(s for s in ws.sections if s.section_id == "documents")
        self.assertEqual(len(doc_sec.items), 1)
        self.assertEqual(len(doc_sec.items[0]["history"]), 2)

    def test_proposal_approval_audit_trail(self) -> None:
        """BR-048-003: Auditable approval lifecycle."""
        audit = self.controller.approve_proposal("CLT-0001", "PROP-0001", "John Doe")
        self.assertEqual(audit["item_id"], "PROP-0001")
        self.assertEqual(audit["item_type"], "Proposal")
        self.assertEqual(audit["approver"], "John Doe")

        # Verify added to activities feed
        ws = self.controller.load_workspace("CLT-0001", "CLT-0001")
        self.assertEqual(len(ws.activities), 1)
        self.assertEqual(ws.activities[0].title, "Proposal Approved")

        # Verify communication engine logged
        self.assertEqual(len(self.comm.audit_log.logs), 1)
        self.assertEqual(self.comm.audit_log.logs[0]["action"], "PROPOSAL_APPROVED")

    def test_milestone_approval_audit_trail(self) -> None:
        audit = self.controller.approve_milestone("CLT-0001", "PROJ-0001", "Milestone 1", "Jane Doe")
        self.assertEqual(audit["item_type"], "Milestone")
        self.assertEqual(audit["item_id"], "PROJ-0001:Milestone 1")

    def test_support_request_creates_crm_interaction(self) -> None:
        """BR-048-007: Support request creates CRM interaction."""
        ticket = self.controller.submit_support_request("CLT-0001", "Bug", "Page crash")
        self.assertEqual(ticket["status"], "OPEN")
        self.assertEqual(len(self.crm.interactions), 1)
        self.assertEqual(self.crm.interactions[0]["type"], "support")
        self.assertIn("Bug", self.crm.interactions[0]["description"])

    def test_feedback_routes_to_crm_and_improvement(self) -> None:
        """BR-048-008: Feedback routes to CI and CRM."""
        res = self.controller.submit_feedback("CLT-0001", score=4.5, comments="Good services.")
        self.assertTrue(res["success"])

        # CRM Update check
        self.assertEqual(self.crm.client.satisfaction_score, 4.5)
        self.assertEqual(len(self.crm.interactions), 1)
        self.assertEqual(self.crm.interactions[0]["type"], "review meeting")

        # Continuous Improvement check
        self.assertEqual(len(self.imp.learnings), 1)
        self.assertEqual(self.imp.learnings[0]["description"], "Good services.")

    def test_graceful_degradation_missing_subsystems(self) -> None:
        """BR-048-009: Graceful degradation when engines are unavailable."""
        empty_controller = ClientPortalController()
        ws = empty_controller.load_workspace("CLT-0001", "CLT-0001")
        self.assertEqual(ws.company, "Client Organization")
        self.assertEqual(ws.summary.balance_due, 0.0)


class TestClientPortalWebAPI(unittest.TestCase):

    def setUp(self) -> None:
        self.crm = MockCRMEngine()
        self.fin = MockFinancialEngine()
        self.delivery = MockDeliveryEngine()
        self.comm = MockCommEngine()
        self.imp = MockImprovementEngine()

        self.controller = ClientPortalController(
            crm_engine=self.crm,
            financial_engine=self.fin,
            delivery_engine=self.delivery,
            communication_engine=self.comm,
            improvement_engine=self.imp,
        )
        self.app = create_portal_app(self.controller)
        self.client = TestClient(self.app)

    def test_health_check(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_read_workspace_api(self) -> None:
        response = self.client.get(
            "/api/portal/workspace/CLT-0001",
            headers={"x-authenticated-client": "CLT-0001"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["company"], "Acme Corp")

    def test_read_workspace_isolation_breach(self) -> None:
        response = self.client.get(
            "/api/portal/workspace/CLT-0001",
            headers={"x-authenticated-client": "CLT-0002"},
        )
        self.assertEqual(response.status_code, 403)

    def test_approve_proposal_api(self) -> None:
        response = self.client.post(
            "/api/portal/workspace/CLT-0001/approve/proposal/PROP-0001?approver=Jane+Doe",
            headers={"x-authenticated-client": "CLT-0001"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["item_id"], "PROP-0001")

    def test_approve_milestone_api(self) -> None:
        response = self.client.post(
            "/api/portal/workspace/CLT-0001/approve/milestone/PROJ-0001?milestone_title=Milestone+1&approver=Jane+Doe",
            headers={"x-authenticated-client": "CLT-0001"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["item_id"], "PROJ-0001:Milestone 1")

    def test_submit_support_api(self) -> None:
        response = self.client.post(
            "/api/portal/workspace/CLT-0001/support",
            json={"title": "Urgent", "description": "Crash"},
            headers={"x-authenticated-client": "CLT-0001"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "OPEN")

    def test_submit_feedback_api(self) -> None:
        response = self.client.post(
            "/api/portal/workspace/CLT-0001/feedback",
            json={"score": 4.0, "comments": "Cool"},
            headers={"x-authenticated-client": "CLT-0001"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])


class TestPortalWebSocketManager(unittest.TestCase):

    def test_portal_websocket_management(self) -> None:
        manager = PortalWebSocketManager()
        # Mock WebSocket connection
        class MockWS:
            def __init__(self) -> None:
                self.accepted = False
                self.sent_texts = []
            async def accept(self) -> None:
                self.accepted = True
            async def send_text(self, text: str) -> None:
                self.sent_texts.append(text)

        ws = MockWS()
        import asyncio
        asyncio.run(manager.connect("CLT-0001", ws))
        self.assertTrue(ws.accepted)
        self.assertEqual(len(manager.active_connections["CLT-0001"]), 1)

        # Broadcast update (websocket updates emitted correctly)
        asyncio.run(manager.send_to_client("CLT-0001", {"event": "project_progress", "pct": 85.0}))
        self.assertEqual(len(ws.sent_texts), 1)
        self.assertIn("project_progress", ws.sent_texts[0])

        manager.disconnect("CLT-0001", ws)
        self.assertNotIn("CLT-0001", manager.active_connections)


if __name__ == "__main__":
    unittest.main()
