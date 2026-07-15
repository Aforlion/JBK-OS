from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any

from core.skill_manifest import SkillManifest
from core.output_validator import ValidationResult, OutputValidator
from core.context_builder import ContextBuilder
from core.work_order import WorkOrder
from core.project import Project
from core.knowledge_registry import KnowledgeRegistry
from core.ai_provider import AICapability
from core.ai_gateway import AIGateway, AIRequest


# ---------------------------------------------------------------------------
# Execution Metrics & Result Models
# ---------------------------------------------------------------------------


class ExecutionMetrics:
    """Captures operational telemetry for a single skill execution (BR-038-011)."""

    def __init__(
        self,
        duration_ms: int = 0,
        retries: int = 0,
        provider: str = "",
        model: str = "",
        tokens: dict[str, int] | None = None,
        estimated_cost: float = 0.0,
        validation_score: float = 0.0,
    ) -> None:
        self.duration_ms = duration_ms
        self.retries = retries
        self.provider = provider
        self.model = model
        self.tokens = dict(tokens or {})
        self.estimated_cost = estimated_cost
        self.validation_score = validation_score

    def to_dict(self) -> dict[str, Any]:
        return {
            "duration_ms": self.duration_ms,
            "retries": self.retries,
            "provider": self.provider,
            "model": self.model,
            "tokens": dict(self.tokens),
            "estimated_cost": self.estimated_cost,
            "validation_score": self.validation_score,
        }


class SkillExecutionResult:
    """Structured outcome of a skill execution (BR-038-003)."""

    def __init__(
        self,
        execution_id: str,
        work_order_id: str,
        status: str,
        deliverable: Any | None = None,
        metrics: ExecutionMetrics | None = None,
        validation: ValidationResult | None = None,
        logs: list[str] | None = None,
        reasoning: str = "",
    ) -> None:
        self.execution_id = execution_id
        self.work_order_id = work_order_id
        self.status = status  # SUCCESS, FAILED, VALIDATION_FAILED
        self.deliverable = deliverable
        self.metrics = metrics or ExecutionMetrics()
        self.validation = validation
        self.logs = list(logs or [])
        self.reasoning = reasoning

    def summary(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "work_order_id": self.work_order_id,
            "status": self.status,
            "validation_score": self.metrics.validation_score if self.metrics else 0.0,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "work_order_id": self.work_order_id,
            "status": self.status,
            "deliverable_id": getattr(self.deliverable, "id", None) if self.deliverable else None,
            "metrics": self.metrics.to_dict() if self.metrics else {},
            "validation": self.validation.to_dict() if self.validation else {},
            "logs": list(self.logs),
            "reasoning": self.reasoning,
        }


# ---------------------------------------------------------------------------
# Abstract Base Skill (BR-038-003)
# ---------------------------------------------------------------------------


class BaseSkill(ABC):
    """Abstract base class every AI employee inherits from.

    Defines the standard interface for the skill lifecycle.
    """

    def __init__(self) -> None:
        self._manifest: SkillManifest | None = None
        self._context_builder = ContextBuilder()
        self._validator = OutputValidator()

    @abstractmethod
    def load_manifest(self) -> SkillManifest:
        """Return the skill manifest describing capabilities and requirements."""
        ...

    def build_context(
        self,
        work_order: WorkOrder,
        project: Project | None = None,
        knowledge_registry: KnowledgeRegistry | None = None,
        previous_deliverables: list[Any] | None = None,
        company_standards: list[str] | None = None,
    ) -> dict[str, Any]:
        """Construct execution context from organizational sources (BR-038-005)."""
        return self._context_builder.build(
            work_order=work_order,
            project=project,
            knowledge_registry=knowledge_registry,
            previous_deliverables=previous_deliverables,
            company_standards=company_standards,
        )

    @abstractmethod
    def build_prompt(self, context: dict[str, Any]) -> str:
        """Build the prompt to send to the AI Gateway (BR-038-004)."""
        ...

    @abstractmethod
    def get_capability(self) -> AICapability:
        """Return the AI capability required for this skill."""
        ...

    def validate(self, content: str) -> ValidationResult:
        """Validate the AI output (BR-038-007). Override for custom validation."""
        return self._validator.validate(content, min_length=10)

    @abstractmethod
    def package_deliverable(self, work_order: WorkOrder, content: str) -> Any:
        """Create a Deliverable from the validated output (BR-038-008)."""
        ...

    def get_manifest(self) -> SkillManifest:
        if self._manifest is None:
            self._manifest = self.load_manifest()
        return self._manifest


# ---------------------------------------------------------------------------
# Reference Implementation: Software Engineer Skill (BR-038-015)
# ---------------------------------------------------------------------------


class SoftwareEngineerSkill(BaseSkill):
    """Concrete reference skill demonstrating framework extensibility."""

    def load_manifest(self) -> SkillManifest:
        return SkillManifest(
            skill_id="SKILL-001",
            name="Software Engineer",
            version="1.0",
            owner="CTO",
            description="Develops software solutions based on work order specifications.",
            capabilities=["python", "architecture", "testing"],
            required_inputs=["WorkOrder"],
            generated_outputs=["Deliverable"],
            supported_models=["Gemini", "Claude"],
            quality_validator="default",
        )

    def build_prompt(self, context: dict[str, Any]) -> str:
        wo = context.get("work_order", {})
        project = context.get("project", {})
        standards = context.get("company_standards", [])

        prompt = (
            f"You are a senior software engineer at JBK Technologies.\n"
            f"Project: {project.get('title', 'Unknown')}\n"
            f"Client: {project.get('client', 'Unknown')}\n"
            f"Work Order: {wo.get('title', 'Unknown')}\n"
            f"Objective: {wo.get('objective', 'No objective provided')}\n"
        )
        if standards:
            prompt += f"Company Standards: {', '.join(standards)}\n"
        prompt += "\nDeliver production-quality code with tests and documentation."
        return prompt

    def get_capability(self) -> AICapability:
        return AICapability.CODING

    def validate(self, content: str) -> ValidationResult:
        return self._validator.validate(content, min_length=20)

    def package_deliverable(self, work_order: WorkOrder, content: str) -> Any:
        from core.deliverable import Deliverable
        return Deliverable(
            project_id=work_order.project_id,
            work_order_id=work_order.id,
            title=f"Implementation: {work_order.title}",
            author="SoftwareEngineerSkill",
            content=content,
        )
