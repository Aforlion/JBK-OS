import unittest
from datetime import datetime, timezone
from typing import Any
from fastapi.testclient import TestClient

from core.dashboard_view_model import (
    DashboardViewModel,
    ProjectCard,
    AlertCard,
    KPIWidget,
    ActivityFeedItem,
)
from core.executive_console_controller import ExecutiveConsoleController
from web.app import create_app
from web.websocket_manager import WebSocketManager


class MockBriefing:
    def get_briefing_summary(self) -> dict:
        return {"summary": "Brief summary", "metrics": {"items": 5}}


class MockDashboardEngine:
    def generate_dashboard(self) -> Any:
        class MockKPI:
            def __init__(self) -> None:
                self.name = "Company Health Score"
                self.value = 95.0
                self.trend = "STABLE"
                self.status = "ON_TRACK"
                self.target = None
        class MockAlert:
            def __init__(self) -> None:
                self.alert_id = "ALT-001"
                self.severity = "HIGH"
                self.title = "Risk Detected"
                self.description = "Dec"
                self.source_engine = "Eng"
                self.recommended_action = "Action"
        class MockDB:
            def __init__(self) -> None:
                self.company_status = "HEALTHY"
                self.kpis = [MockKPI()]
                self.alerts = [MockAlert()]
        return MockDB()


class MockCRM:
    def list_clients(self) -> list:
        class MockClient:
            def __init__(self) -> None:
                self.client_id = "CLT-0001"
                self.company = "Healthcare Corp"
                self.industry = "Healthcare"
                self.relationship_status = "Excellent"
                self.satisfaction_score = 4.8
        return [MockClient()]

    def register_client(self, company: str, industry: str) -> Any:
        class MockClient:
            def __init__(self) -> None:
                self.company = company
                self.client_id = "CLT-9999"
        return MockClient()


class MockAI:
    def converse(self, msg: str) -> str:
        return f"AI response to: {msg}"


class MockDelivery:
    def generate_delivery_status_report(self) -> dict:
        return {
            "status": "HEALTHY",
            "projects": [
                {
                    "project_id": "PROJ-0001",
                    "name": "Alpha Build",
                    "completion_pct": 80.0,
                    "status": "IN_PROGRESS",
                    "owner": "Dev Owner",
                    "risk_level": "LOW",
                }
            ],
            "at_risk_count": 0,
        }


class MockCommEngine:
    def get_audit_log(self) -> Any:
        class MockLog:
            def all_entries(self) -> list:
                class Entry:
                    def __init__(self) -> None:
                        self.communication_id = "001"
                        self.action = "Proposal Approved"
                        self.timestamp = "2026-07-14T09:00:00Z"
                        self.details = "Proposal was approved."
                return [Entry()]
        return MockLog()

    def generate_report(self) -> Any:
        class MockRep:
            def __init__(self) -> None:
                self.unread_notifications = 1
                self.failures = []
            def to_dict(self) -> dict:
                return {"unread_notifications": 1}
        return MockRep()


class TestDashboardViewModels(unittest.TestCase):

    def test_view_models_serialization(self) -> None:
        """Dashboard serialization test."""
        kpi = KPIWidget("Rev", 1000.0, "UP", "ON_TRACK")
        alert = AlertCard("A1", "INFO", "Title", "Desc", "Eng")
        proj = ProjectCard("P1", "Alpha", 60.0, "ACTIVE", "Dev", "LOW")
        feed = ActivityFeedItem("F1", "Proposal Approved", "Log", "2026-07-14T00:00:00Z")

        vm = DashboardViewModel(
            company_status="HEALTHY",
            kpis=[kpi],
            alerts=[alert],
            projects=[proj],
            activity_feed=[feed],
        )

        d = vm.to_dict()
        self.assertEqual(d["company_status"], "HEALTHY")
        self.assertEqual(d["kpis"][0]["name"], "Rev")
        self.assertEqual(d["alerts"][0]["title"], "Title")
        self.assertEqual(d["projects"][0]["name"], "Alpha")
        self.assertEqual(d["activity_feed"][0]["title"], "Proposal Approved")


class TestExecutiveConsoleController(unittest.TestCase):

    def test_controller_dashboard_compilation(self) -> None:
        """Dashboard loads completely."""
        controller = ExecutiveConsoleController(
            dashboard_engine=MockDashboardEngine(),
            crm_engine=MockCRM(),
            delivery_engine=MockDelivery(),
            communication_engine=MockCommEngine(),
        )

        vm = controller.load_dashboard()
        self.assertEqual(vm.company_status, "HEALTHY")
        self.assertEqual(len(vm.kpis), 1)
        self.assertEqual(vm.kpis[0].name, "Company Health Score")
        self.assertEqual(len(vm.projects), 1)
        self.assertEqual(vm.projects[0].project_id, "PROJ-0001")
        self.assertEqual(len(vm.activity_feed), 1)
        self.assertEqual(vm.activity_feed[0].title, "Proposal Approved")

    def test_graceful_degradation_missing_engines(self) -> None:
        """Widget degradation when engines are offline."""
        controller = ExecutiveConsoleController()
        vm = controller.load_dashboard()
        # Should not raise exception; loads fallback items
        self.assertEqual(vm.company_status, "CRITICAL")
        self.assertTrue(len(vm.kpis) > 0)
        self.assertEqual(len(vm.projects), 0)

    def test_global_search(self) -> None:
        """Search functionality filters and returns correct structures."""
        controller = ExecutiveConsoleController(crm_engine=MockCRM())
        res = controller.search("Health")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["title"], "Healthcare Corp")

        empty_res = controller.search("")
        self.assertEqual(len(empty_res), 0)

    def test_quick_action_crm(self) -> None:
        """Quick action triggers crm client registration."""
        controller = ExecutiveConsoleController(crm_engine=MockCRM())
        res = controller.quick_action("new-client", {"company": "Acme Inc", "industry": "AI"})
        self.assertTrue(res["success"])
        self.assertIn("Acme Inc", res["details"])

    def test_quick_action_briefing(self) -> None:
        """Quick action triggers assistant startup briefing."""
        controller = ExecutiveConsoleController(ai_assistant=MockAI())
        res = controller.quick_action("briefing")
        self.assertTrue(res["success"])
        self.assertIn("startup briefing", res["response"])


class TestWebConsoleAPI(unittest.TestCase):

    def setUp(self) -> None:
        self.controller = ExecutiveConsoleController(
            dashboard_engine=MockDashboardEngine(),
            crm_engine=MockCRM(),
            delivery_engine=MockDelivery(),
            ai_assistant=MockAI(),
        )
        self.app = create_app(self.controller)
        self.client = TestClient(self.app)

    def test_health_check(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    def test_get_dashboard_api(self) -> None:
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("company_status", response.json())
        self.assertEqual(response.json()["company_status"], "HEALTHY")

    def test_refresh_dashboard_api(self) -> None:
        """Refresh updates dashboard widgets."""
        response = self.client.post("/api/dashboard/refresh")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

    def test_get_projects_api(self) -> None:
        """Project loading works."""
        response = self.client.get("/api/dashboard/projects")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["name"], "Alpha Build")

    def test_execute_action_api(self) -> None:
        """Quick actions trigger correct engines."""
        response = self.client.post(
            "/api/dashboard/actions/new-client",
            json={"company": "Test Co", "industry": "Tech"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    def test_global_search_api(self) -> None:
        response = self.client.get("/api/dashboard/search?q=Health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_converse_with_assistant_api(self) -> None:
        """Assistant routing and command bar conversations."""
        response = self.client.post("/api/converse?message=Show+company+health")
        self.assertEqual(response.status_code, 200)
        self.assertIn("AI response to: Show company health", response.json()["response"])


class TestWebSocketUpdates(unittest.TestCase):

    def test_connection_management(self) -> None:
        manager = WebSocketManager()
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
        asyncio.run(manager.connect(ws))
        self.assertTrue(ws.accepted)
        self.assertEqual(len(manager.active_connections), 1)

        # Broadcast update (websocket updates emitted correctly)
        asyncio.run(manager.broadcast({"event": "status_update", "status": "HEALTHY"}))
        self.assertEqual(len(ws.sent_texts), 1)
        self.assertIn("status_update", ws.sent_texts[0])

        manager.disconnect(ws)
        self.assertEqual(len(manager.active_connections), 0)


if __name__ == "__main__":
    unittest.main()
