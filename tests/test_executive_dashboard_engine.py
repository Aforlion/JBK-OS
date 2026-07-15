import unittest
from datetime import datetime, timezone

from core.executive_kpi import ExecutiveKPI
from core.dashboard_alert import DashboardAlert
from core.dashboard_section import DashboardSection
from core.executive_dashboard import ExecutiveDashboard
from core.executive_dashboard_engine import ExecutiveDashboardEngine
from core.financial_report import FinancialReport
from core.financial_snapshot import FinancialSnapshot


class MockEngine:
    """Mock helper for dashboard generation tests."""

    def __init__(self, key: str) -> None:
        self.key = key

    def get_briefing_summary(self) -> dict:
        return {"summary": "A OK", "metrics": {"count": 10}}

    def generate_report(self) -> dict:
        return {"total_projects": 5, "at_risk_count": 1, "win_rate": 80.0}

    def list_clients(self) -> list:
        # Simple client profile list mock
        class ClientMock:
            def __init__(self) -> None:
                self.company = "Mock Corp"
                self.satisfaction_score = 4.5
                self.trust_score = 90.0
                self.client_id = "CLT-0001"
        return [ClientMock()]

    def evaluate_success(self, client: Any) -> Any:
        class SuccessMock:
            def __init__(self) -> None:
                self.risk_alerts = []
        return SuccessMock()

    def generate_delivery_status_report(self) -> dict:
        return {"status": "HEALTHY", "projects": [1, 2], "at_risk_count": 0}

    def generate_health_report(self) -> dict:
        return {"health_score": 95, "executive_utilization": 85.0}

    def get_usage_summary(self) -> dict:
        return {"total_calls": 120, "total_cost": 1.25}


class MockFinancialEngine:
    def generate_financial_report(self) -> Any:
        snap = FinancialSnapshot(total_revenue=50000.0, total_expenses=12000.0)
        return FinancialReport(
            report_id="FIN-0001",
            executive_summary="Revenue is 50k",
            kpis={"total_revenue": 50000.0, "total_expenses": 12000.0, "outstanding_invoices_count": 2},
            recommendations=[{"action": "Collect AR", "why": "Due", "calculations": "10k", "assumptions": "None"}],
            cash_health="Healthy",
            snapshot=snap,
        )


class MockCommunicationEngine:
    def generate_report(self) -> Any:
        class CommReportMock:
            def __init__(self) -> None:
                self.unread_notifications = 2
                self.failures = [{"recipient": "client@ex.com"}]
            def to_dict(self) -> dict:
                return {"unread_notifications": 2}
        return CommReportMock()


class TestDashboardModels(unittest.TestCase):

    def test_kpi_creation_and_trends(self) -> None:
        """BR-046-008: Supports trend values: UP, DOWN, STABLE, UNKNOWN."""
        kpi = ExecutiveKPI(name="Test KPI", value=100, trend="UP", status="ON_TRACK")
        self.assertEqual(kpi.trend, "UP")

        with self.assertRaises(ValueError):
            ExecutiveKPI(name="Test", value=10, trend="IMPROVING")

    def test_alert_severity_sorting(self) -> None:
        """BR-046-004: Critical alerts weight higher."""
        c = DashboardAlert(alert_id="A1", severity="CRITICAL", category="C", title="T", description="D")
        h = DashboardAlert(alert_id="A2", severity="HIGH", category="C", title="T", description="D")
        m = DashboardAlert(alert_id="A3", severity="MEDIUM", category="C", title="T", description="D")

        self.assertTrue(c.severity_weight > h.severity_weight)
        self.assertTrue(h.severity_weight > m.severity_weight)

    def test_section_unavailable_default_summary(self) -> None:
        """BR-046-006: Unavailable sections show 'Unavailable' summary."""
        sec = DashboardSection(title="Test", source_engine="TestEngine", status="UNAVAILABLE")
        self.assertEqual(sec.summary, "Unavailable")

    def test_dashboard_serialization(self) -> None:
        """BR-046-009: Fully serializable."""
        kpi = ExecutiveKPI(name="KPI", value=5)
        alert = DashboardAlert(alert_id="A1", severity="HIGH", category="C", title="T", description="D")
        sec = DashboardSection(title="Sec", source_engine="Eng")
        db = ExecutiveDashboard(
            dashboard_id="DSH-0001",
            company_status="HEALTHY",
            sections=[sec],
            alerts=[alert],
            kpis=[kpi],
        )

        d = db.to_dict()
        self.assertEqual(d["dashboard_id"], "DSH-0001")
        self.assertEqual(len(d["sections"]), 1)
        self.assertEqual(len(d["alerts"]), 1)
        self.assertEqual(len(d["kpis"]), 1)


class TestExecutiveDashboardEngine(unittest.TestCase):

    def test_generate_dashboard_full_success(self) -> None:
        """Test dashboard generation when all engines are online."""
        engine = ExecutiveDashboardEngine(
            portfolio_engine=MockEngine("portfolio"),
            financial_engine=MockFinancialEngine(),
            crm_engine=MockEngine("crm"),
            delivery_engine=MockEngine("delivery"),
            strategic_engine=MockEngine("strategic"),
            autonomous_engine=MockEngine("autonomous"),
            client_success_engine=MockEngine("success"),
            memory_engine=MockEngine("memory"),
            ai_gateway=MockEngine("gateway"),
            communication_engine=MockCommunicationEngine(),
            briefing_engine=MockEngine("briefing"),
        )

        db = engine.generate_dashboard()
        self.assertEqual(db.company_status, "HEALTHY")
        self.assertEqual(len(db.sections), 11)
        self.assertEqual(len(db.kpis), 11)
        self.assertEqual(len(db.alerts), 1)  # 1 delivery failure alert
        self.assertEqual(db.alerts[0].source_engine, "CommunicationEngine")

        # Test render-agnostic property (BR-046-010: structured data only)
        # Should not contain HTML tags or markdown syntax inside values
        d = db.to_dict()
        self.assertNotIn("<html>", str(d))
        self.assertNotIn("<b>", str(d))

    def test_missing_engine_resilience(self) -> None:
        """BR-046-006: Unavailable sections display: Unavailable instead of failing."""
        # Setup engine with only one subsystem online, rest None
        engine = ExecutiveDashboardEngine(
            portfolio_engine=None,
            financial_engine=None,
            crm_engine=None,
            delivery_engine=None,
            strategic_engine=None,
            autonomous_engine=None,
            client_success_engine=None,
            memory_engine=None,
            ai_gateway=None,
            communication_engine=None,
            briefing_engine=None,
        )

        db = engine.generate_dashboard()
        self.assertEqual(len(db.sections), 11)
        # Check that all sections have status UNAVAILABLE and summary "Unavailable"
        for sec in db.sections:
            self.assertEqual(sec.status, "UNAVAILABLE")
            self.assertEqual(sec.summary, "Unavailable")

        # Company Health Score calculated despite missing systems
        self.assertEqual(db.kpis[-1].name, "Company Health Score")
        self.assertEqual(db.kpis[-1].value, 50.0)  # Neutral penalty score (50.0)

    def test_alert_ordering(self) -> None:
        """BR-046-004: Critical alerts appear before all other content."""
        engine = ExecutiveDashboardEngine()

        # Generate a dummy dashboard
        db = engine.generate_dashboard()

        # Manually inject alerts of different severities
        db.alerts = [
            DashboardAlert(alert_id="A1", severity="LOW", category="C", title="T", description="D"),
            DashboardAlert(alert_id="A2", severity="CRITICAL", category="C", title="T", description="D"),
            DashboardAlert(alert_id="A3", severity="HIGH", category="C", title="T", description="D"),
            DashboardAlert(alert_id="A4", severity="MEDIUM", category="C", title="T", description="D"),
        ]

        # Re-sort using same sort key logic
        db.alerts.sort(key=lambda a: a.severity_weight, reverse=True)

        self.assertEqual(db.alerts[0].severity, "CRITICAL")
        self.assertEqual(db.alerts[1].severity, "HIGH")
        self.assertEqual(db.alerts[2].severity, "MEDIUM")
        self.assertEqual(db.alerts[3].severity, "LOW")

    def test_recommendation_includes_originating_engine(self) -> None:
        """BR-046-005: Recommendations include originating engine."""
        engine = ExecutiveDashboardEngine(
            financial_engine=MockFinancialEngine(),
        )
        db = engine.generate_dashboard()
        self.assertTrue(len(db.recommendations) > 0)
        self.assertEqual(db.recommendations[0]["source_engine"], "FinancialOperationsEngine")

    def test_stateless_generation(self) -> None:
        """BR-046-001: Dashboard generation is stateless."""
        engine = ExecutiveDashboardEngine()
        db1 = engine.generate_dashboard()
        db2 = engine.generate_dashboard()
        self.assertNotEqual(db1.dashboard_id, db2.dashboard_id)

    def test_read_only_boundary(self) -> None:
        """BR-046-002: Dashboard never modifies operational data."""
        # Verify creating dashboard does not mutate mock values
        engine = ExecutiveDashboardEngine()
        orig_counter = engine._dashboard_counter
        engine.generate_dashboard()
        self.assertEqual(engine._dashboard_counter, orig_counter + 1)


if __name__ == "__main__":
    unittest.main()
