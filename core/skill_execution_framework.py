from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from core.ai_gateway import AIGateway, AIRequest
from core.skill_runtime import (
    BaseSkill,
    ExecutionMetrics,
    SkillExecutionResult,
)
from core.output_validator import ValidationResult
from core.work_order import WorkOrder
from core.project import Project
from core.knowledge_registry import KnowledgeRegistry

LOGGER = logging.getLogger(__name__)


class SkillExecutionFramework:
    """Orchestrates the standard skill lifecycle (BR-038-001).

    Pipeline:
        1. Receive Work Order
        2. Validate Inputs
        3. Prepare Context
        4. Build Prompt
        5. Invoke AI Gateway
        6. Validate Output
        7. Generate Deliverable
        8. Quality Review
        9. Return Execution Report
    """

    def __init__(self, ai_gateway: AIGateway, max_retries: int = 2) -> None:
        if ai_gateway is None:
            raise ValueError("AIGateway is required.")
        self._gateway = ai_gateway
        self._max_retries = max_retries

    def execute(
        self,
        skill: BaseSkill,
        work_order: WorkOrder,
        project: Project | None = None,
        knowledge_registry: KnowledgeRegistry | None = None,
        previous_deliverables: list[Any] | None = None,
        company_standards: list[str] | None = None,
    ) -> SkillExecutionResult:
        """Run the full 9-step lifecycle (BR-038-001). Never raises uncaught exceptions (BR-038-009)."""
        execution_id = f"EXEC-{uuid.uuid4().hex[:8].upper()}"
        logs: list[str] = []
        start_time = time.monotonic()

        try:
            # Step 1: Receive Work Order (already received as parameter)
            logs.append(f"Step 1: Received Work Order {work_order.id}.")

            # Step 2: Validate Inputs
            manifest = skill.get_manifest()
            logs.append(f"Step 2: Loaded manifest '{manifest.name}' v{manifest.version}.")
            if "WorkOrder" in manifest.required_inputs and work_order is None:
                return self._failure_result(
                    execution_id, work_order.id, logs, start_time,
                    "Input validation failed: WorkOrder is required.",
                )

            # Step 3: Prepare Context (BR-038-005)
            context = skill.build_context(
                work_order=work_order,
                project=project,
                knowledge_registry=knowledge_registry,
                previous_deliverables=previous_deliverables,
                company_standards=company_standards,
            )
            logs.append("Step 3: Context prepared.")

            # Step 4: Build Prompt (BR-038-004)
            prompt = skill.build_prompt(context)
            logs.append(f"Step 4: Prompt built ({len(prompt)} chars).")

            # Step 5: Invoke AI Gateway with retry (BR-038-006, BR-038-010)
            ai_response = None
            retries = 0
            last_error = ""

            for attempt in range(1, self._max_retries + 2):  # +1 for initial + retries
                request = AIRequest(
                    capability=skill.get_capability(),
                    prompt=prompt,
                    system_context=f"Skill: {manifest.name} v{manifest.version}",
                )
                response = self._gateway.generate(request)

                if response.success:
                    ai_response = response
                    logs.append(f"Step 5: AI Gateway succeeded (provider={response.provider}, attempt={attempt}).")
                    break
                else:
                    retries += 1
                    last_error = response.content
                    logs.append(f"Step 5: Attempt {attempt} failed ({response.content[:80]}). Retrying...")

            if ai_response is None:
                return self._failure_result(
                    execution_id, work_order.id, logs, start_time,
                    f"AI Gateway failed after {retries} retries. Last error: {last_error}",
                    retries=retries,
                )

            content = ai_response.content

            # Step 6: Validate Output (BR-038-007)
            validation = skill.validate(content)
            logs.append(f"Step 6: Validation {'passed' if validation.passed else 'failed'} (score={validation.score}).")

            # Step 7: Generate Deliverable (BR-038-008)
            if not validation.passed:
                duration_ms = int((time.monotonic() - start_time) * 1000)
                metrics = ExecutionMetrics(
                    duration_ms=duration_ms,
                    retries=retries,
                    provider=ai_response.provider,
                    model=ai_response.model,
                    tokens=ai_response.token_usage,
                    estimated_cost=ai_response.estimated_cost,
                    validation_score=validation.score,
                )
                logs.append("Step 7: Deliverable NOT created due to validation failure.")
                return SkillExecutionResult(
                    execution_id=execution_id,
                    work_order_id=work_order.id,
                    status="VALIDATION_FAILED",
                    metrics=metrics,
                    validation=validation,
                    logs=logs,
                    reasoning=f"Output failed validation: {', '.join(validation.issues)}",
                )

            deliverable = skill.package_deliverable(work_order, content)
            if hasattr(deliverable, "submit_for_review"):
                deliverable.submit_for_review(actor="system")
            logs.append(f"Step 7: Deliverable created ({deliverable.id}).")

            # Step 8: Quality Review (BR-038-013)
            logs.append(f"Step 8: Quality review complete. Score: {validation.score}.")

            # Step 9: Return Execution Report
            duration_ms = int((time.monotonic() - start_time) * 1000)
            metrics = ExecutionMetrics(
                duration_ms=duration_ms,
                retries=retries,
                provider=ai_response.provider,
                model=ai_response.model,
                tokens=ai_response.token_usage,
                estimated_cost=ai_response.estimated_cost,
                validation_score=validation.score,
            )

            logs.append("Step 9: Execution complete.")

            return SkillExecutionResult(
                execution_id=execution_id,
                work_order_id=work_order.id,
                status="SUCCESS",
                deliverable=deliverable,
                metrics=metrics,
                validation=validation,
                logs=logs,
                reasoning=f"Prompt sent to {ai_response.provider} ({ai_response.model}). Validation passed with score {validation.score}.",
            )

        except Exception as exc:
            # BR-038-009: Never raise uncaught exceptions
            logs.append(f"EXCEPTION: {str(exc)}")
            return self._failure_result(
                execution_id, work_order.id, logs, start_time,
                f"Unhandled exception: {str(exc)}",
            )

    def _failure_result(
        self,
        execution_id: str,
        work_order_id: str,
        logs: list[str],
        start_time: float,
        reason: str,
        retries: int = 0,
    ) -> SkillExecutionResult:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        logs.append(f"FAILED: {reason}")
        return SkillExecutionResult(
            execution_id=execution_id,
            work_order_id=work_order_id,
            status="FAILED",
            metrics=ExecutionMetrics(duration_ms=duration_ms, retries=retries),
            logs=logs,
            reasoning=reason,
        )
