import unittest
from typing import Any

from core.work_order import WorkOrder
from core.project_registry import ProjectRegistry
from core.worker_registry import WorkerRegistry
from core.knowledge_registry import KnowledgeRegistry
from core.chief_of_staff import ChiefOfStaff
from core.ai_gateway import AIGateway
from core.ai_provider import AICapability, AIProvider, GeminiAdapter, AIProviderStatus, AIProviderAdapter
from core.skill_manifest import SkillManifest
from core.skill_runtime import BaseSkill, SoftwareEngineerSkill
from core.skill_execution_framework import SkillExecutionFramework
from core.output_validator import ValidationResult
from core.collaboration_session import CollaborationSession, CollaborationRole, CollaborationParticipantStatus
from core.collaboration_report import CollaborationReport
from core.collaboration_engine import MultiAgentCollaborationEngine


# ---------------------------------------------------------------------------
# Test Doubles
# ---------------------------------------------------------------------------

class _RejectingValidatorAdapter(AIProviderAdapter):
    """Adapter that returns output failing validator checks (e.g. too short)."""

    def provider_id(self) -> str:
        return "reject"

    def supports(self, capability: AICapability) -> bool:
        return True

    def generate(self, request) -> dict:
        return {
            "content": "Short",  # will fail software engineer's min_length validation
            "model": "reject",
            "token_usage": {},
            "latency_ms": 0,
            "success": True,
        }

    def health(self) -> AIProviderStatus:
        return AIProviderStatus.AVAILABLE

    def models(self) -> list[str]:
        return ["reject"]


class _SecurityArchitectSkill(BaseSkill):
    """Extensible skill acting as a custom Reviewer (BR-039-015)."""

    def __init__(self, pass_review: bool = True) -> None:
        super().__init__()
        self._pass_review = pass_review

    def load_manifest(self) -> SkillManifest:
        return SkillManifest(
            skill_id="SKILL-SEC",
            name="Security Architect",
            version="1.0",
            owner="CISO",
            description="Reviews deliverables for authentication leaks and CVEs.",
            capabilities=["security", "audit", "review"],
            required_inputs=["WorkOrder"],
            generated_outputs=["Deliverable"],
        )

    def build_prompt(self, context: dict[str, Any]) -> str:
        return "Review this content."

    def get_capability(self) -> AICapability:
        return AICapability.RESEARCH

    def validate(self, content: str) -> ValidationResult:
        if self._pass_review:
            return ValidationResult(passed=True, score=0.9)
        else:
            return ValidationResult(passed=False, score=0.2, issues=["OWASP Top 10 breach: Hardcoded API keys found."])

    def package_deliverable(self, work_order: WorkOrder, content: str) -> Any:
        return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestMultiAgentCollaborationEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.project_registry = ProjectRegistry()
        self.worker_registry = WorkerRegistry()
        self.knowledge_registry = KnowledgeRegistry()
        self.chief_of_staff = ChiefOfStaff(
            worker_registry=self.worker_registry,
            project_registry=self.project_registry,
            knowledge_registry=self.knowledge_registry,
        )

        self.gateway = AIGateway()
        provider = AIProvider(
            provider_id="gemini", name="Gemini",
            capabilities=[AICapability.CHAT, AICapability.CODING, AICapability.RESEARCH],
            priority=10,
        )
        self.gateway.register_provider(provider, GeminiAdapter())

        self.framework = SkillExecutionFramework(ai_gateway=self.gateway)
        self.engine = MultiAgentCollaborationEngine(framework=self.framework)

        self.work_order = WorkOrder(
            project_id="PROJ-COLLAB",
            title="Integrate Database Layer",
            objective="Develop python database wrapper with connection pooling.",
            work_order_id="WO-COLLAB",
        )

        self.developer = SoftwareEngineerSkill()
        self.security = _SecurityArchitectSkill(pass_review=True)

    # ------------------------------------------------------------------
    # Session & Participant Registration (BR-039-001, BR-039-002)
    # ------------------------------------------------------------------

    def test_session_and_participant_registration(self) -> None:
        report = self.engine.coordinate(
            work_order=self.work_order,
            skills=[self.developer, self.security],
            chief_of_staff=self.chief_of_staff,
        )

        self.assertIsInstance(report, CollaborationReport)
        self.assertTrue(report.session_id.startswith("COL-"))
        self.assertEqual(len(report.participants), 2)

        roles = {p["role"] for p in report.participants}
        self.assertIn("CONTRIBUTOR", roles)
        self.assertIn("REVIEWER", roles)

    # ------------------------------------------------------------------
    # Decompose & Parallel Execution (BR-039-003, BR-039-004)
    # ------------------------------------------------------------------

    def test_task_decomposition_and_assignment(self) -> None:
        report = self.engine.coordinate(
            work_order=self.work_order,
            skills=[self.developer, self.security],
            chief_of_staff=self.chief_of_staff,
        )
        developer_part = [p for p in report.participants if p["skill_id"] == "SKILL-001"][0]
        self.assertIn("Build Contribution: Software Engineer", developer_part["assigned_tasks"])

    # ------------------------------------------------------------------
    # Shared Workspace (BR-039-005, BR-039-006)
    # ------------------------------------------------------------------

    def test_shared_workspace_exchange(self) -> None:
        report = self.engine.coordinate(
            work_order=self.work_order,
            skills=[self.developer, self.security],
            chief_of_staff=self.chief_of_staff,
        )
        self.assertTrue(report.consensus_reached)
        self.assertIsNotNone(report.final_artifact_id)

        # Audit trail must show submission to workspace
        msg_types = [m["message_type"] for m in report.timeline]
        self.assertIn("ARTIFACT_SUBMISSION", msg_types)
        self.assertIn("REVIEW_FEEDBACK", msg_types)

    # ------------------------------------------------------------------
    # Conflict Loops & Rejections (BR-039-007, BR-039-008)
    # ------------------------------------------------------------------

    def test_reviewer_rejection_conflict_handling(self) -> None:
        failing_security = _SecurityArchitectSkill(pass_review=False)

        report = self.engine.coordinate(
            work_order=self.work_order,
            skills=[self.developer, failing_security],
            chief_of_staff=self.chief_of_staff,
        )

        self.assertFalse(report.consensus_reached)
        self.assertEqual(len(report.conflicts), 1)
        self.assertEqual(report.conflicts[0]["skill_id"], "SKILL-SEC")
        self.assertIn("Hardcoded API keys", report.conflicts[0]["issues"][0])

    # ------------------------------------------------------------------
    # Knowledge Capture & Serialization (BR-039-010, BR-039-012)
    # ------------------------------------------------------------------

    def test_knowledge_capture_and_serialization(self) -> None:
        report = self.engine.coordinate(
            work_order=self.work_order,
            skills=[self.developer, self.security],
            chief_of_staff=self.chief_of_staff,
        )

        # Verified Knowledge capture logged to Chief of Staff registry
        self.assertEqual(len(self.chief_of_staff.knowledge_registry.list_items()), 1)

        d = report.to_dict()
        self.assertIn("session_id", d)
        self.assertIn("consensus_reached", d)
        self.assertIn("timeline", d)

        s = report.summary()
        self.assertTrue(s["consensus_reached"])
        self.assertEqual(s["conflict_count"], 0)


if __name__ == "__main__":
    unittest.main()
