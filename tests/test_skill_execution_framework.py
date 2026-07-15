import unittest
from typing import Any

from core.skill_manifest import SkillManifest
from core.output_validator import OutputValidator, ValidationResult
from core.context_builder import ContextBuilder
from core.skill_runtime import (
    BaseSkill,
    ExecutionMetrics,
    SkillExecutionResult,
    SoftwareEngineerSkill,
)
from core.skill_execution_framework import SkillExecutionFramework
from core.ai_gateway import AIGateway, AIRequest
from core.ai_provider import (
    AICapability,
    AIProvider,
    AIProviderAdapter,
    AIProviderStatus,
    GeminiAdapter,
)
from core.work_order import WorkOrder
from core.project import Project
from core.knowledge_registry import KnowledgeRegistry


# ---------------------------------------------------------------------------
# Test Doubles
# ---------------------------------------------------------------------------

class _AlwaysFailGatewayAdapter(AIProviderAdapter):
    """Adapter that always fails to simulate retry exhaustion."""

    def provider_id(self) -> str:
        return "always-fail"

    def supports(self, capability: AICapability) -> bool:
        return True

    def generate(self, request) -> dict:
        return {"content": "Provider error", "model": "fail", "token_usage": {}, "latency_ms": 0, "success": False}

    def health(self) -> AIProviderStatus:
        return AIProviderStatus.AVAILABLE

    def models(self) -> list[str]:
        return ["fail"]


class _ShortOutputAdapter(AIProviderAdapter):
    """Adapter that returns output too short to pass validation."""

    def provider_id(self) -> str:
        return "short"

    def supports(self, capability: AICapability) -> bool:
        return True

    def generate(self, request) -> dict:
        return {"content": "tiny", "model": "short-model", "token_usage": {"input": 5, "output": 2}, "latency_ms": 1, "success": True}

    def health(self) -> AIProviderStatus:
        return AIProviderStatus.AVAILABLE

    def models(self) -> list[str]:
        return ["short-model"]


class _MarketingAnalystSkill(BaseSkill):
    """A second skill to demonstrate framework extensibility (BR-038-015)."""

    def load_manifest(self) -> SkillManifest:
        return SkillManifest(
            skill_id="SKILL-099",
            name="Marketing Analyst",
            version="1.0",
            owner="CMO",
            description="Analyzes market data and produces campaign reports.",
            capabilities=["marketing", "analytics"],
            required_inputs=["WorkOrder"],
            generated_outputs=["Deliverable"],
            supported_models=["Gemini"],
        )

    def build_prompt(self, context: dict[str, Any]) -> str:
        wo = context.get("work_order", {})
        return f"You are a marketing analyst. Objective: {wo.get('objective', 'N/A')}"

    def get_capability(self) -> AICapability:
        return AICapability.RESEARCH

    def package_deliverable(self, work_order: WorkOrder, content: str) -> Any:
        from core.deliverable import Deliverable
        return Deliverable(
            project_id=work_order.project_id,
            work_order_id=work_order.id,
            title=f"Analysis: {work_order.title}",
            author="MarketingAnalystSkill",
            content=content,
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSkillExecutionFramework(unittest.TestCase):

    def setUp(self) -> None:
        # Set up a gateway with a working Gemini adapter
        self.gateway = AIGateway()
        provider = AIProvider(
            provider_id="gemini", name="Gemini",
            capabilities=[AICapability.CHAT, AICapability.CODING, AICapability.RESEARCH],
            priority=10,
        )
        self.gateway.register_provider(provider, GeminiAdapter())

        self.framework = SkillExecutionFramework(ai_gateway=self.gateway)
        self.skill = SoftwareEngineerSkill()

        self.work_order = WorkOrder(
            project_id="PROJ-TEST",
            title="Build Authentication Module",
            objective="Implement JWT-based authentication with refresh tokens.",
            work_order_id="WO-TEST",
        )

    # ------------------------------------------------------------------
    # Manifest Loading (BR-038-002)
    # ------------------------------------------------------------------

    def test_manifest_loading(self) -> None:
        manifest = self.skill.get_manifest()
        self.assertIsInstance(manifest, SkillManifest)
        self.assertEqual(manifest.skill_id, "SKILL-001")
        self.assertEqual(manifest.name, "Software Engineer")
        self.assertIn("python", manifest.capabilities)

        d = manifest.to_dict()
        self.assertEqual(d["version"], "1.0")
        self.assertEqual(d["owner"], "CTO")

        s = manifest.summary()
        self.assertIn("skill_id", s)

    # ------------------------------------------------------------------
    # Context Building (BR-038-005)
    # ------------------------------------------------------------------

    def test_context_building(self) -> None:
        context = self.skill.build_context(
            work_order=self.work_order,
            company_standards=["PEP 8", "Type hints required"],
        )
        self.assertIn("work_order", context)
        self.assertEqual(context["work_order"]["id"], "WO-TEST")
        self.assertIn("company_standards", context)
        self.assertEqual(len(context["company_standards"]), 2)

    # ------------------------------------------------------------------
    # Prompt Generation (BR-038-004)
    # ------------------------------------------------------------------

    def test_prompt_generation(self) -> None:
        context = self.skill.build_context(work_order=self.work_order)
        prompt = self.skill.build_prompt(context)
        self.assertIsInstance(prompt, str)
        self.assertIn("JWT-based authentication", prompt)
        self.assertIn("JBK Technologies", prompt)

    # ------------------------------------------------------------------
    # Successful Execution (BR-038-001)
    # ------------------------------------------------------------------

    def test_successful_execution(self) -> None:
        result = self.framework.execute(
            skill=self.skill,
            work_order=self.work_order,
        )
        self.assertIsInstance(result, SkillExecutionResult)
        self.assertEqual(result.status, "SUCCESS")
        self.assertIsNotNone(result.deliverable)
        self.assertGreater(len(result.logs), 0)
        self.assertIn("Step 9: Execution complete.", result.logs)

    # ------------------------------------------------------------------
    # Validation Failure (BR-038-007)
    # ------------------------------------------------------------------

    def test_validation_failure(self) -> None:
        # Use a gateway adapter that returns very short output
        gw = AIGateway()
        provider = AIProvider(
            provider_id="short", name="Short",
            capabilities=[AICapability.CODING],
            priority=1,
        )
        gw.register_provider(provider, _ShortOutputAdapter())
        framework = SkillExecutionFramework(ai_gateway=gw)

        result = framework.execute(skill=self.skill, work_order=self.work_order)
        self.assertEqual(result.status, "VALIDATION_FAILED")
        self.assertIsNone(result.deliverable)
        self.assertIsNotNone(result.validation)
        self.assertFalse(result.validation.passed)

    # ------------------------------------------------------------------
    # AI Gateway Failure with Retry (BR-038-010)
    # ------------------------------------------------------------------

    def test_all_retries_exhausted(self) -> None:
        gw = AIGateway()
        provider = AIProvider(
            provider_id="always-fail", name="AlwaysFail",
            capabilities=[AICapability.CODING],
            priority=1,
        )
        gw.register_provider(provider, _AlwaysFailGatewayAdapter())
        framework = SkillExecutionFramework(ai_gateway=gw, max_retries=2)

        result = framework.execute(skill=self.skill, work_order=self.work_order)
        self.assertEqual(result.status, "FAILED")
        self.assertIn("retries", result.reasoning.lower())

    # ------------------------------------------------------------------
    # Deliverable Creation (BR-038-008)
    # ------------------------------------------------------------------

    def test_deliverable_creation(self) -> None:
        result = self.framework.execute(skill=self.skill, work_order=self.work_order)
        self.assertEqual(result.status, "SUCCESS")
        self.assertIsNotNone(result.deliverable)
        self.assertEqual(result.deliverable.project_id, "PROJ-TEST")
        self.assertIn("Authentication Module", result.deliverable.title)

    # ------------------------------------------------------------------
    # Metrics Recording (BR-038-011)
    # ------------------------------------------------------------------

    def test_metrics_recording(self) -> None:
        result = self.framework.execute(skill=self.skill, work_order=self.work_order)
        m = result.metrics
        self.assertIsInstance(m, ExecutionMetrics)
        self.assertGreaterEqual(m.duration_ms, 0)
        self.assertEqual(m.provider, "gemini")
        self.assertIn("input", m.tokens)
        self.assertGreaterEqual(m.estimated_cost, 0.0)
        self.assertGreater(m.validation_score, 0.0)

        d = m.to_dict()
        self.assertIn("provider", d)
        self.assertIn("estimated_cost", d)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def test_serialization(self) -> None:
        result = self.framework.execute(skill=self.skill, work_order=self.work_order)

        s = result.summary()
        self.assertEqual(s["status"], "SUCCESS")
        self.assertIn("execution_id", s)

        d = result.to_dict()
        self.assertIn("metrics", d)
        self.assertIn("validation", d)
        self.assertIn("logs", d)
        self.assertIn("reasoning", d)

    # ------------------------------------------------------------------
    # New Skill Registration / Extensibility (BR-038-015)
    # ------------------------------------------------------------------

    def test_new_skill_registration(self) -> None:
        # Register Gemini with RESEARCH capability (already done in setUp)
        marketing_skill = _MarketingAnalystSkill()
        manifest = marketing_skill.get_manifest()
        self.assertEqual(manifest.name, "Marketing Analyst")

        result = self.framework.execute(
            skill=marketing_skill,
            work_order=self.work_order,
        )
        self.assertEqual(result.status, "SUCCESS")
        self.assertIsNotNone(result.deliverable)
        self.assertIn("Analysis", result.deliverable.title)

    # ------------------------------------------------------------------
    # Output Validator
    # ------------------------------------------------------------------

    def test_output_validator_passing(self) -> None:
        v = OutputValidator()
        result = v.validate("This is a long enough piece of content for validation.", min_length=10)
        self.assertTrue(result.passed)
        self.assertEqual(result.score, 1.0)
        self.assertEqual(len(result.issues), 0)

    def test_output_validator_empty(self) -> None:
        v = OutputValidator()
        result = v.validate("", min_length=10)
        self.assertFalse(result.passed)
        self.assertEqual(result.score, 0.0)
        self.assertIn("Output is empty.", result.issues)

    def test_output_validator_missing_sections(self) -> None:
        v = OutputValidator()
        result = v.validate(
            "Some content here but missing important sections.",
            required_sections=["Introduction", "Conclusion"],
        )
        self.assertFalse(result.passed)
        self.assertEqual(len(result.issues), 2)


if __name__ == "__main__":
    unittest.main()
