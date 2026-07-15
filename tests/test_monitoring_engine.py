import unittest
from datetime import datetime, timezone, timedelta

from core.system_event import SystemEvent
from core.performance_metric import PerformanceMetric
from core.audit_record import AuditRecord
from core.system_health_report import SystemHealthReport
from core.monitoring_engine import MonitoringEngine


class TestSystemEventModel(unittest.TestCase):

    def test_valid_event(self) -> None:
        event = SystemEvent(
            event_id="EVT-0001",
            engine="AIGateway",
            category="SECURITY",
            severity="HIGH",
            message="Unauthorized access blocked",
        )
        self.assertEqual(event.severity, "HIGH")
        self.assertIsNotNone(event.timestamp)

    def test_invalid_category_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SystemEvent("E1", "Eng", "DATABASE", "LOW", "Msg")

    def test_invalid_severity_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SystemEvent("E1", "Eng", "SYSTEM", "WARNING", "Msg")

    def test_serialization(self) -> None:
        event = SystemEvent("E1", "Eng", "SYSTEM", "LOW", "Msg")
        d = event.to_dict()
        self.assertEqual(d["event_id"], "E1")
        self.assertEqual(d["category"], "SYSTEM")


class TestPerformanceMetricModel(unittest.TestCase):

    def test_metric_defaults(self) -> None:
        m = PerformanceMetric(
            engine_name="CRMEngine",
            execution_time_ms=120.5,
            ai_tokens=150,
            ai_cost=0.003,
        )
        self.assertEqual(m.execution_time_ms, 120.5)
        self.assertEqual(m.ai_tokens, 150)
        self.assertEqual(m.ai_cost, 0.003)
        self.assertTrue(m.success)

    def test_serialization(self) -> None:
        m = PerformanceMetric("Eng", 50.0)
        d = m.to_dict()
        self.assertEqual(d["engine_name"], "Eng")
        self.assertEqual(d["execution_time_ms"], 50.0)


class TestAuditRecordModel(unittest.TestCase):

    def test_immutable_audit_record(self) -> None:
        """BR-050-004: Audit records are strictly immutable."""
        record = AuditRecord(
            audit_id="AUD-0001",
            actor="CEO",
            action="APPROVE_PROPOSAL",
            target="PROP-0001",
        )
        self.assertEqual(record.actor, "CEO")
        
        with self.assertRaises(AttributeError):
            # Attempting to mutate locked attribute raises exception
            record._actor = "ChiefOfStaff"

    def test_serialization(self) -> None:
        record = AuditRecord("AUD-0001", "CEO", "ACTION", "TARGET")
        d = record.to_dict()
        self.assertEqual(d["audit_id"], "AUD-0001")


class TestMonitoringEngine(unittest.TestCase):

    def test_record_event_triggers_failures_alert(self) -> None:
        """BR-050-007: Engine failures trigger alerts."""
        engine = MonitoringEngine()
        event = engine.record_event(
            engine="DeliverySupervisionEngine",
            category="SYSTEM",
            severity="CRITICAL",
            message="Database connection failure.",
        )
        self.assertIsNotNone(event)
        self.assertEqual(len(engine.list_events()), 1)

        # Check alert generation
        alerts = engine.list_alerts()
        self.assertEqual(len(alerts), 1)
        self.assertIn("Subsystem Health Alert", alerts[0]["title"])

    def test_record_metric_anomaly_alerts(self) -> None:
        """Advisory alerts generated for performance issues."""
        engine = MonitoringEngine()
        
        # Latency anomaly
        engine.record_metric("AIGateway", execution_time_ms=6000.0)
        # Cost anomaly
        engine.record_metric("AIGateway", execution_time_ms=100.0, ai_cost=60.0)

        alerts = engine.list_alerts()
        self.assertEqual(len(alerts), 2)
        self.assertIn("Performance Anomaly", alerts[0]["title"])
        self.assertIn("Budget Alert", alerts[1]["title"])

    def test_record_audit_log(self) -> None:
        engine = MonitoringEngine()
        audit = engine.record_audit("CEO", "APPROVE", "PROP-0001")
        self.assertIsNotNone(audit)
        self.assertEqual(len(engine.list_audit_log()), 1)

    def test_passive_non_blocking_behavior(self) -> None:
        """BR-050-001 & BR-050-005: Gathers are passive/non-blocking."""
        engine = MonitoringEngine()
        # Ensure invalid inputs do not raise and crash, instead returns None gracefully
        res_event = engine.record_event(engine="", category="DATABASE", severity="LOW", message="")
        self.assertIsNone(res_event)

        res_metric = engine.record_metric(engine_name="", execution_time_ms=-1.0)
        self.assertIsNotNone(res_metric)  # Negative metrics logged but do not crash

    def test_historical_metrics_aggregation(self) -> None:
        """BR-050-008: Performance metrics are aggregated. BR-050-009: Queryable."""
        engine = MonitoringEngine()
        engine.record_metric("CRMEngine", execution_time_ms=100.0, ai_tokens=10, ai_cost=0.1, success=True)
        engine.record_metric("CRMEngine", execution_time_ms=200.0, ai_tokens=20, ai_cost=0.2, success=True)
        engine.record_metric("CRMEngine", execution_time_ms=300.0, ai_tokens=30, ai_cost=0.3, success=False)

        stats = engine.query_metrics("CRMEngine", window_hours=1)
        self.assertEqual(stats["total_runs"], 3)
        self.assertEqual(stats["average_execution_time_ms"], 200.0)
        self.assertEqual(stats["peak_execution_time_ms"], 300.0)
        self.assertEqual(stats["success_rate_pct"], 66.7)
        self.assertEqual(stats["total_ai_tokens"], 60)
        self.assertEqual(stats["total_ai_cost"], 0.6)

    def test_engine_health_calculation(self) -> None:
        engine = MonitoringEngine()
        self.assertEqual(engine.get_subsystem_health("AIGateway"), "OFFLINE")

        # Log some healthy runs
        engine.record_metric("AIGateway", execution_time_ms=50.0)
        self.assertEqual(engine.get_subsystem_health("AIGateway"), "HEALTHY")

        # Log repeated failures
        engine.record_metric("AIGateway", execution_time_ms=50.0, success=False)
        engine.record_metric("AIGateway", execution_time_ms=50.0, success=False)
        engine.record_metric("AIGateway", execution_time_ms=50.0, success=False)
        self.assertEqual(engine.get_subsystem_health("AIGateway"), "FAILED")

    def test_health_report_explainability(self) -> None:
        """BR-050-010: Health reports carry explainability and recommendations."""
        engine = MonitoringEngine()
        engine.record_event("AIGateway", "SYSTEM", "CRITICAL", "Crashed.")
        
        report = engine.generate_health_report()
        self.assertEqual(report.subsystem_health["AIGateway"], "FAILED")
        self.assertEqual(len(report.failures), 1)
        self.assertEqual(len(report.recommendations), 1)
        self.assertEqual(report.recommendations[0]["source_engine"], "AIGateway")
        self.assertIn("corrective_actions", report.recommendations[0])


if __name__ == "__main__":
    unittest.main()
