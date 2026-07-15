from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone, timedelta

from core.system_event import SystemEvent
from core.performance_metric import PerformanceMetric
from core.audit_record import AuditRecord
from core.system_health_report import SystemHealthReport

LOGGER = logging.getLogger(__name__)


class MonitoringEngine:
    """Centralized Observability layer tracking JBK OS operational health.

    BR-050-001: Passive observation.
    BR-050-002: Never changes business objects or core system state.
    BR-050-005: Telemetry capture must never block execution.
    """

    def __init__(self, init_time: str | None = None) -> None:
        self._events: list[SystemEvent] = []
        self._metrics: list[PerformanceMetric] = []
        self._audit_log: list[AuditRecord] = []
        self._alerts: list[dict[str, Any]] = []
        
        self._event_counter = 1
        self._audit_counter = 1
        self._report_counter = 1
        
        self.init_time = init_time or datetime.now(timezone.utc).isoformat()
        
        # Track engine statuses manually or via recorded events
        self._engine_health_override: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Telemetry Gathers (Safe & Non-blocking, BR-050-005)
    # ------------------------------------------------------------------

    def record_event(
        self,
        engine: str,
        category: str,
        severity: str,
        message: str,
        project_id: str | None = None,
        client_id: str | None = None,
        executive_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SystemEvent | None:
        """Record operational event. BR-050-007: engine failures trigger alerts."""
        try:
            event_id = f"EVT-{self._event_counter:04d}"
            self._event_counter += 1

            event = SystemEvent(
                event_id=event_id,
                engine=engine,
                category=category,
                severity=severity,
                message=message,
                project_id=project_id,
                client_id=client_id,
                executive_id=executive_id,
                metadata=metadata,
            )
            self._events.append(event)

            # BR-050-007: Detect failed severity and issue advisory alert
            if severity == "CRITICAL" or "fail" in message.lower():
                self._trigger_advisory_alert(
                    title=f"Subsystem Health Alert: {engine}",
                    description=f"Critical event detected in {engine}. Message: {message}",
                    source_engine=engine,
                    evidence=f"Event ID: {event_id}",
                )

            return event
        except Exception as e:
            # Enforce non-blocking principle (BR-050-005)
            LOGGER.error("Observability failure in record_event: %s", e)
            return None

    def record_metric(
        self,
        engine_name: str,
        execution_time_ms: float,
        cpu_time: float = 0.0,
        memory_usage: float = 0.0,
        ai_tokens: int = 0,
        ai_cost: float = 0.0,
        success: bool = True,
        retries: int = 0,
    ) -> PerformanceMetric | None:
        """Capture runtime execution metric (non-blocking)."""
        try:
            metric = PerformanceMetric(
                engine_name=engine_name,
                execution_time_ms=execution_time_ms,
                cpu_time=cpu_time,
                memory_usage=memory_usage,
                ai_tokens=ai_tokens,
                ai_cost=ai_cost,
                success=success,
                retries=retries,
            )
            self._metrics.append(metric)

            # Performance check (anomaly alert generation)
            if execution_time_ms > 5000.0:  # Latency anomaly threshold: 5 seconds
                self._trigger_advisory_alert(
                    title=f"Performance Anomaly: {engine_name}",
                    description=f"Engine latency exceeded 5s threshold (Value: {execution_time_ms:.1f}ms)",
                    source_engine=engine_name,
                    evidence=f"Execution Time: {execution_time_ms}ms",
                )

            if ai_cost > 50.0:  # Excessive AI cost alert threshold: $50
                self._trigger_advisory_alert(
                    title=f"Budget Alert: {engine_name}",
                    description=f"Estimated AI cost exceeded limit (Value: ${ai_cost:.2f})",
                    source_engine=engine_name,
                    evidence=f"AI Cost: ${ai_cost:.2f}",
                )

            return metric
        except Exception as e:
            LOGGER.error("Observability failure in record_metric: %s", e)
            return None

    def record_audit(
        self,
        actor: str,
        action: str,
        target: str,
        outcome: str = "SUCCESS",
        explanation: str = "",
    ) -> AuditRecord | None:
        """Append an immutable audit entry (non-blocking)."""
        try:
            audit_id = f"AUD-{self._audit_counter:04d}"
            self._audit_counter += 1

            record = AuditRecord(
                audit_id=audit_id,
                actor=actor,
                action=action,
                target=target,
                outcome=outcome,
                explanation=explanation,
            )
            self._audit_log.append(record)
            return record
        except Exception as e:
            LOGGER.error("Observability failure in record_audit: %s", e)
            return None

    # ------------------------------------------------------------------
    # Telemetry Analysis (BR-050-008, BR-050-009)
    # ------------------------------------------------------------------

    def query_metrics(self, engine_name: str | None = None, window_hours: int = 24) -> dict[str, Any]:
        """Aggregate performance metrics over specified rolling window (BR-050-008, BR-050-009)."""
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=window_hours)

        relevant = []
        for m in self._metrics:
            try:
                t = datetime.fromisoformat(m.timestamp)
                if hasattr(t, "tzinfo") and t.tzinfo is None:
                    t = t.replace(tzinfo=timezone.utc)
                if t >= start_time:
                    if engine_name is None or m.engine_name == engine_name:
                        relevant.append(m)
            except Exception:
                pass

        if not relevant:
            return {
                "average_execution_time_ms": 0.0,
                "peak_execution_time_ms": 0.0,
                "total_runs": 0,
                "success_rate_pct": 100.0,
                "total_ai_tokens": 0,
                "total_ai_cost": 0.0,
            }

        exec_times = [m.execution_time_ms for m in relevant]
        successes = sum(1 for m in relevant if m.success)
        total_tokens = sum(m.ai_tokens for m in relevant)
        total_cost = sum(m.ai_cost for m in relevant)

        return {
            "average_execution_time_ms": round(sum(exec_times) / len(exec_times), 1),
            "peak_execution_time_ms": round(max(exec_times), 1),
            "total_runs": len(relevant),
            "success_rate_pct": round((successes / len(relevant)) * 100, 1),
            "total_ai_tokens": total_tokens,
            "total_ai_cost": round(total_cost, 4),
        }

    # ------------------------------------------------------------------
    # Health Assessment & Reports (BR-050-007, BR-050-010)
    # ------------------------------------------------------------------

    def get_subsystem_health(self, engine_name: str) -> str:
        """Determines subsystem health (HEALTHY, DEGRADED, WARNING, FAILED, OFFLINE)."""
        if engine_name in self._engine_health_override:
            return self._engine_health_override[engine_name]

        # Analyze events to detect failures
        engine_events = [e for e in self._events if e.engine == engine_name]
        critical_count = sum(1 for e in engine_events if e.severity == "CRITICAL")
        high_count = sum(1 for e in engine_events if e.severity == "HIGH")

        # Analyze recent performance metrics
        metrics = [m for m in self._metrics if m.engine_name == engine_name][-5:]
        failures_count = sum(1 for m in metrics if not m.success)

        if critical_count > 0 or failures_count >= 3:
            return "FAILED"
        if high_count > 0 or failures_count > 0:
            return "WARNING"
        if len(metrics) > 0 and sum(m.execution_time_ms for m in metrics)/len(metrics) > 3000.0:
            return "DEGRADED"
        if not engine_events and not metrics:
            return "OFFLINE"
        return "HEALTHY"

    def generate_health_report(self) -> SystemHealthReport:
        """Compile a complete health report carrying explainability (BR-050-010)."""
        engines = (
            "AIGateway", "AIExecutiveAssistant", "CRMEngine",
            "DeliverySupervisionEngine", "PortfolioEngine",
            "StrategicIntelligenceEngine", "CommunicationsEngine",
            "ExecutiveDashboardEngine", "AutonomousOperationsEngine",
            "ClientPortalController"
        )

        subsystem_health = {eng: self.get_subsystem_health(eng) for eng in engines}

        warnings = []
        failures = []
        recommendations = []

        for eng, status in subsystem_health.items():
            if status == "FAILED":
                failures.append(f"Subsystem {eng} is FAILED.")
                recommendations.append({
                    "action": f"Restart / Debug {eng}",
                    "evidence": f"Subsystem status computed as {status}.",
                    "source_engine": eng,
                    "corrective_actions": "Verify server connections, trace failed runtime logs.",
                })
            elif status in ("WARNING", "DEGRADED"):
                warnings.append(f"Subsystem {eng} status is {status}.")
                recommendations.append({
                    "action": f"Investigate latency/errors on {eng}",
                    "evidence": f"Subsystem status resolved to Warning/Degraded.",
                    "source_engine": eng,
                    "corrective_actions": "Review metric trace history for anomalies.",
                })

        # Uptime calculation
        try:
            init = datetime.fromisoformat(self.init_time)
            if hasattr(init, "tzinfo") and init.tzinfo is None:
                init = init.replace(tzinfo=timezone.utc)
            uptime = int((datetime.now(timezone.utc) - init).total_seconds())
        except Exception:
            uptime = 0

        # Calculate general availability
        total_runs = len(self._metrics)
        successes = sum(1 for m in self._metrics if m.success)
        availability = round((successes / total_runs) * 100, 1) if total_runs > 0 else 100.0

        report_id = f"HLT-{self._report_counter:04d}"
        self._report_counter += 1

        return SystemHealthReport(
            report_id=report_id,
            subsystem_health=subsystem_health,
            warnings=warnings,
            failures=failures,
            recommendations=recommendations,
            telemetry_summary={
                "total_events": len(self._events),
                "total_metrics": len(self._metrics),
                "total_audit_records": len(self._audit_log),
                "total_alerts": len(self._alerts),
            },
            uptime_seconds=uptime,
            availability_pct=availability,
        )

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _trigger_advisory_alert(self, title: str, description: str, source_engine: str, evidence: str) -> None:
        """Create an advisory health alert."""
        self._alerts.append({
            "title": title,
            "description": description,
            "source_engine": source_engine,
            "evidence": evidence,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def set_engine_health_override(self, engine_name: str, status: str) -> None:
        """Helper to force engine health for testing overrides."""
        self._engine_health_override[engine_name] = status

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def list_events(self) -> list[SystemEvent]:
        return list(self._events)

    def list_metrics(self) -> list[PerformanceMetric]:
        return list(self._metrics)

    def list_audit_log(self) -> list[AuditRecord]:
        return list(self._audit_log)

    def list_alerts(self) -> list[dict[str, Any]]:
        return list(self._alerts)
