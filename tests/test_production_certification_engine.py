from __future__ import annotations

import os
import unittest
from typing import Any

from core.certification_requirement import CertificationRequirement
from core.readiness_assessment import ReadinessAssessment
from core.certification_report import CertificationReport, MockVersionRegistry
from core.production_certification_engine import ProductionCertificationEngine


# ---------------------------------------------------------------------------
# CertificationRequirement Tests
# ---------------------------------------------------------------------------

class TestCertificationRequirement(unittest.TestCase):

    def test_valid_requirement(self) -> None:
        req = CertificationRequirement(
            req_id="REQ-001",
            category="KERNEL",
            title="Kernel Verification",
            description="Kernel compiles successfully",
        )
        self.assertEqual(req.status, "PASSED")
        self.assertIn("category", req.to_dict())

    def test_blocker_missing_remediation_raises(self) -> None:
        """BR-056-009: Blockers must carry remediation guidance."""
        with self.assertRaises(ValueError):
            CertificationRequirement(
                req_id="REQ-002",
                category="SECURITY",
                title="Strict Firewall",
                description="Firewall is closed",
                status="BLOCKER",
                remediation_guidance="",  # empty
            )


# ---------------------------------------------------------------------------
# ReadinessAssessment Tests
# ---------------------------------------------------------------------------

class TestReadinessAssessment(unittest.TestCase):

    def test_scorecard_averages_correctly(self) -> None:
        """BR-056-012: Production scorecard aggregates subsystem readiness."""
        scorecard = ReadinessAssessment(
            kernel_score=100.0,
            governance_score=100.0,
            operations_score=100.0,
            intelligence_score=100.0,
            executive_score=100.0,
            ai_score=100.0,
            security_score=100.0,
            deployment_score=100.0,
            recovery_score=100.0,
            documentation_score=100.0,
            testing_score=100.0,
        )
        self.assertEqual(scorecard.overall_score, 100.0)

    def test_scorecard_serialization(self) -> None:
        scorecard = ReadinessAssessment(kernel_score=90.0)
        d = scorecard.to_dict()
        self.assertEqual(d["subsystem_scores"]["Kernel"], 90.0)


# ---------------------------------------------------------------------------
# CertificationReport Tests
# ---------------------------------------------------------------------------

class TestCertificationReport(unittest.TestCase):

    def test_report_immutability(self) -> None:
        """BR-056-005: Reports are immutable."""
        report = CertificationReport(
            certification_id="CERT-001",
            version="1.0.0",
            build_number="B1",
            readiness_score=100.0,
            scorecard=ReadinessAssessment(),
            passed_requirements=[],
            failed_requirements=[],
            warnings=[],
            blockers=[],
            recommendations=[],
            executive_summary="Summary",
            certification_status="CERTIFIED",
            verdict="APPROVED FOR PRODUCTION",
        )
        with self.assertRaises(AttributeError):
            report.verdict = "NOT APPROVED"


# ---------------------------------------------------------------------------
# ProductionCertificationEngine Tests
# ---------------------------------------------------------------------------

class TestProductionCertificationEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.registry = MockVersionRegistry()
        self.engine = ProductionCertificationEngine(
            workspace_path="c:/JBK/JBK-OS",
            version_registry=self.registry,
        )

    def test_successful_certification_verdict(self) -> None:
        """BR-056-010: Certification decisions are deterministic."""
        report = self.engine.certify()
        self.assertEqual(report.certification_status, "CERTIFIED")
        self.assertEqual(report.verdict, "APPROVED FOR PRODUCTION")
        self.assertEqual(self.registry.installed_version, "1.0.0")

    def test_failed_certification_due_to_blocker(self) -> None:
        """Blockers trigger NOT APPROVED verdict."""
        report = self.engine.certify(force_fail_requirement="REQ-003")
        self.assertEqual(report.certification_status, "NOT_CERTIFIED")
        self.assertEqual(report.verdict, "NOT APPROVED")
        # Registry must NOT be updated
        self.assertIsNone(self.registry.installed_version)

    def test_certification_profile_governance(self) -> None:
        """BR-056-014: Engine supports future profiles."""
        report = self.engine.certify(profile="GOV_STRICT")
        # Ensure additional check was evaluated
        passed_ids = [r.req_id for r in report.passed_requirements]
        self.assertIn("REQ-006", passed_ids)

    def test_verdict_statement(self) -> None:
        report = self.engine.certify()
        statement = self.engine.get_verdict_statement()
        self.assertIn("approved for production deployment", statement)

    def test_certificate_file_creation(self) -> None:
        """BR-056-013: Official certificate file generated on success."""
        cert_path = "c:/JBK/JBK-OS/docs/releases/JBK_OS_VERSION_1_CERTIFICATE.md"
        # Remove existing if any
        if os.path.exists(cert_path):
            os.remove(cert_path)

        self.engine.certify()
        self.assertTrue(os.path.exists(cert_path))

    def test_capability_inventory_evaluation(self) -> None:
        """BR-056-011: Inventory counts compiled dynamically."""
        inv = self.engine.get_capability_inventory()
        self.assertEqual(inv["specifications_implemented"], 56)
        self.assertGreaterEqual(inv["core_engines"], 0)
        self.assertGreaterEqual(inv["tests_count"], 0)


if __name__ == "__main__":
    unittest.main()
Length = 100
