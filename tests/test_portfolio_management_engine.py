import unittest
from typing import Any
from enum import Enum

from core.project_registry import ProjectRegistry
from core.worker_registry import WorkerRegistry
from core.delivery_status_report import DeliveryStatusReport
from core.resource_allocation_plan import ResourceAllocationPlan
from core.business_transformation_plan import BusinessTransformationPlan
from core.portfolio_report import (
    PortfolioMetrics,
    PortfolioRecommendation,
    PortfolioRisk,
    CapacityForecast,
    PortfolioReport,
)
from core.portfolio_management_engine import PortfolioManagementEngine


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

class MockStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    PLANNED = "PLANNED"
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"


class MockProject:
    def __init__(self, project_id: str, status: MockStatus, title: str = "Test Proj") -> None:
        self.id = project_id
        self.status = status
        self.title = title

    def summary(self) -> dict[str, Any]:
        return {"id": self.id, "title": self.title, "status": self.status.value}


class MockWorker:
    def __init__(self, worker_id: str, status: MockStatus) -> None:
        self.id = worker_id
        self.status = status


def _make_delivery_report(project_id: str, health: str) -> DeliveryStatusReport:
    # Minimal fields for testing
    return DeliveryStatusReport(
        report_id=f"DSR-{project_id}",
        project_id=project_id,
        health_status=health,
        active_work=[],
        waiting_work=[],
        completed_work=[],
        failed_work=[],
        risk_register=[],
        worker_utilization={},
        blockers=[],
        ceo_attention_items=[],
        corrective_recommendations=[],
    )


def _make_allocation_plan(project_id: str, unassigned_count: int) -> ResourceAllocationPlan:
    return ResourceAllocationPlan(
        allocation_id=f"RAP-{project_id}",
        project_id=project_id,
        assignments=[],
        unassigned_tasks=[{"task_id": str(i)} for i in range(unassigned_count)],
        workload_summary={},
        utilization={},
        warnings=[],
    )


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------

class TestPortfolioManagementEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = PortfolioManagementEngine()
        self.project_reg = ProjectRegistry()
        self.worker_reg = WorkerRegistry()

    # ------------------------------------------------------------------
    # Input Validation
    # ------------------------------------------------------------------

    def test_rejects_missing_project_registry(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.analyze_portfolio(None, self.worker_reg)  # type: ignore

    def test_rejects_missing_worker_registry(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.analyze_portfolio(self.project_reg, None)  # type: ignore

    # ------------------------------------------------------------------
    # Portfolio Health Score Calculation
    # ------------------------------------------------------------------

    def test_health_score_perfect(self) -> None:
        self.project_reg.register(MockProject("P1", MockStatus.ACTIVE))
        self.project_reg.register(MockProject("P2", MockStatus.ACTIVE))
        
        rep1 = _make_delivery_report("P1", "HEALTHY")
        rep2 = _make_delivery_report("P2", "HEALTHY")
        
        report = self.engine.analyze_portfolio(self.project_reg, self.worker_reg, delivery_reports=[rep1, rep2])
        self.assertEqual(report.metrics.portfolio_health_score, 1.0)
        self.assertEqual(len(report.active_projects), 2)
        self.assertEqual(len(report.at_risk_projects), 0)

    def test_health_score_averages(self) -> None:
        self.project_reg.register(MockProject("P1", MockStatus.ACTIVE))
        self.project_reg.register(MockProject("P2", MockStatus.ACTIVE))
        
        rep1 = _make_delivery_report("P1", "HEALTHY")  # 1.0
        rep2 = _make_delivery_report("P2", "CRITICAL") # 0.0
        
        report = self.engine.analyze_portfolio(self.project_reg, self.worker_reg, delivery_reports=[rep1, rep2])
        self.assertAlmostEqual(report.metrics.portfolio_health_score, 0.5)

    def test_default_health_is_healthy_without_report(self) -> None:
        self.project_reg.register(MockProject("P1", MockStatus.ACTIVE))
        
        report = self.engine.analyze_portfolio(self.project_reg, self.worker_reg)
        self.assertEqual(report.metrics.portfolio_health_score, 1.0)

    # ------------------------------------------------------------------
    # Identifies At-Risk and Critical Projects
    # ------------------------------------------------------------------

    def test_identifies_at_risk_projects(self) -> None:
        self.project_reg.register(MockProject("P1", MockStatus.ACTIVE))
        rep1 = _make_delivery_report("P1", "WARNING")
        
        report = self.engine.analyze_portfolio(self.project_reg, self.worker_reg, delivery_reports=[rep1])
        self.assertEqual(len(report.at_risk_projects), 1)
        self.assertEqual(report.at_risk_projects[0]["id"], "P1")

    def test_identifies_critical_projects(self) -> None:
        self.project_reg.register(MockProject("P1", MockStatus.ACTIVE))
        rep1 = _make_delivery_report("P1", "CRITICAL")
        
        report = self.engine.analyze_portfolio(self.project_reg, self.worker_reg, delivery_reports=[rep1])
        self.assertEqual(len(report.critical_projects), 1)
        self.assertEqual(len(report.at_risk_projects), 1) # Critical is also at-risk

    # ------------------------------------------------------------------
    # Capacity Forecast Derivation
    # ------------------------------------------------------------------

    def test_capacity_forecast_healthy(self) -> None:
        self.worker_reg.register(MockWorker("W1", MockStatus.AVAILABLE))
        self.worker_reg.register(MockWorker("W2", MockStatus.AVAILABLE))
        
        report = self.engine.analyze_portfolio(self.project_reg, self.worker_reg)
        self.assertEqual(report.capacity_forecast.capacity_status, "HEALTHY")
        self.assertEqual(report.capacity_forecast.available_workers, 2)
        self.assertEqual(report.metrics.resource_utilization_percent, 0.0)

    def test_capacity_forecast_warning_due_to_unassigned_tasks(self) -> None:
        self.worker_reg.register(MockWorker("W1", MockStatus.AVAILABLE))
        alloc = _make_allocation_plan("P1", unassigned_count=1)
        
        report = self.engine.analyze_portfolio(self.project_reg, self.worker_reg, allocation_plans=[alloc])
        # Unassigned <= available, so warning
        self.assertEqual(report.capacity_forecast.capacity_status, "WARNING")

    def test_capacity_forecast_critical_due_to_high_utilization(self) -> None:
        for i in range(10):
            self.worker_reg.register(MockWorker(f"W{i}", MockStatus.BUSY))
            
        report = self.engine.analyze_portfolio(self.project_reg, self.worker_reg)
        self.assertEqual(report.capacity_forecast.capacity_status, "CRITICAL")
        self.assertEqual(report.metrics.resource_utilization_percent, 100.0)

    # ------------------------------------------------------------------
    # Recommendation Evidence and Rules
    # ------------------------------------------------------------------

    def test_recommendation_evidence(self) -> None:
        self.project_reg.register(MockProject("P1", MockStatus.ACTIVE))
        report = self.engine.analyze_portfolio(self.project_reg, self.worker_reg)
        
        self.assertGreater(len(report.recommendations), 0)
        for rec in report.recommendations:
            self.assertGreater(len(rec.evidence), 0, f"Recommendation '{rec.title}' lacks evidence")

    def test_recommendation_object_validation(self) -> None:
        with self.assertRaises(ValueError):
            PortfolioRecommendation(
                recommendation_id="R1", title="T", description="D", priority="LOW",
                evidence=[],  # Empty evidence must raise
                recommended_action="Do nothing"
            )

    # ------------------------------------------------------------------
    # Risks and Priorities
    # ------------------------------------------------------------------

    def test_high_proportion_of_at_risk_projects_creates_risk(self) -> None:
        self.project_reg.register(MockProject("P1", MockStatus.ACTIVE))
        self.project_reg.register(MockProject("P2", MockStatus.ACTIVE))
        self.project_reg.register(MockProject("P3", MockStatus.ACTIVE))
        
        # 2 out of 3 are at risk (>30%)
        rep1 = _make_delivery_report("P1", "WARNING")
        rep2 = _make_delivery_report("P2", "AT_RISK")
        rep3 = _make_delivery_report("P3", "HEALTHY")
        
        report = self.engine.analyze_portfolio(self.project_reg, self.worker_reg, delivery_reports=[rep1, rep2, rep3])
        
        risk_titles = [r.title for r in report.risks]
        self.assertIn("High Proportion of At-Risk Projects", risk_titles)

    def test_ceo_priority_list_includes_critical_items(self) -> None:
        # Create critical capacity scenario
        for i in range(10):
            self.worker_reg.register(MockWorker(f"W{i}", MockStatus.BUSY))
            
        report = self.engine.analyze_portfolio(self.project_reg, self.worker_reg)
        self.assertGreater(len(report.ceo_priority_list), 0)
        
        priorities = [
            getattr(item, "priority", getattr(item, "severity", "")) 
            for item in report.ceo_priority_list
        ]
        self.assertTrue(any(p in ("CRITICAL", "HIGH") for p in priorities))

    # ------------------------------------------------------------------
    # Advisory Boundaries
    # ------------------------------------------------------------------

    def test_advisory_boundaries_respected(self) -> None:
        self.project_reg.register(MockProject("P1", MockStatus.ACTIVE))
        p_count = len(self.project_reg.list_projects())
        
        self.engine.analyze_portfolio(self.project_reg, self.worker_reg)
        
        self.assertEqual(len(self.project_reg.list_projects()), p_count)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def test_report_serialization(self) -> None:
        self.project_reg.register(MockProject("P1", MockStatus.ACTIVE))
        report = self.engine.analyze_portfolio(self.project_reg, self.worker_reg)
        
        d = report.to_dict()
        self.assertIn("report_id", d)
        self.assertIn("metrics", d)
        self.assertIn("capacity_forecast", d)
        self.assertIn("active_projects", d)
        self.assertIn("summary", d)
        
    def test_summary_structure(self) -> None:
        self.project_reg.register(MockProject("P1", MockStatus.ACTIVE))
        report = self.engine.analyze_portfolio(self.project_reg, self.worker_reg)
        
        s = report.summary()
        self.assertIn("portfolio_health_score", s)
        self.assertIn("active_project_count", s)
        self.assertEqual(s["active_project_count"], 1)

    def test_report_id_format(self) -> None:
        report = self.engine.analyze_portfolio(self.project_reg, self.worker_reg)
        self.assertTrue(report.report_id.startswith("PRT-"))


if __name__ == "__main__":
    unittest.main()
