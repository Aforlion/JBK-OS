from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

from core.execution_engine import ExecutionEngine, ExecutionStatus, ExecutionResult


class AntigravityExecutionEngine(ExecutionEngine):
    def __init__(self) -> None:
        self.executions: dict[str, ExecutionResult] = {}
        self._next_id = 1
        self.fail_next = False

    def execute(self, work_order: Any) -> ExecutionResult:
        if work_order is None:
            raise ValueError("Work order is required.")
        
        work_order_id = getattr(work_order, "id", None)
        if not work_order_id:
            raise ValueError("Work order must have a valid ID.")

        execution_id = f"EXE-{self._next_id:04d}"
        self._next_id += 1

        started_at = datetime.now(timezone.utc).isoformat()

        # Handle simulated failure
        status = ExecutionStatus.COMPLETED
        output = f"Simulated successful execution of work order: {work_order_id}"
        
        if self.fail_next or "fail" in getattr(work_order, "title", "").lower():
            status = ExecutionStatus.FAILED
            output = f"Simulated execution failure for work order: {work_order_id}"
            self.fail_next = False

        completed_at = datetime.now(timezone.utc).isoformat()

        result = ExecutionResult(
            execution_id=execution_id,
            work_order_id=work_order_id,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            output=output,
            metadata={"engine": "AntigravityExecutionEngine", "version": "1.0"},
        )

        self.executions[execution_id] = result
        return result

    def supports(self, capability: str) -> bool:
        if not capability:
            return False
        return capability.lower() in {"antigravity", "mock", "python"}

    def status(self, execution_id: str) -> ExecutionStatus:
        if not execution_id:
            raise ValueError("Execution ID is required.")
        if execution_id not in self.executions:
            raise ValueError(f"Execution not found: {execution_id}.")
        return self.executions[execution_id].status

    def cancel(self, execution_id: str) -> bool:
        if not execution_id:
            raise ValueError("Execution ID is required.")
        if execution_id not in self.executions:
            return False

        result = self.executions[execution_id]
        if result.status in {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
        }:
            return False

        result.status = ExecutionStatus.CANCELLED
        result.completed_at = datetime.now(timezone.utc).isoformat()
        return True

    def result(self, execution_id: str) -> ExecutionResult | None:
        if not execution_id:
            raise ValueError("Execution ID is required.")
        return self.executions.get(execution_id)
