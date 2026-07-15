from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any
from datetime import datetime, timezone


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ExecutionResult:
    def __init__(
        self,
        execution_id: str,
        work_order_id: str,
        status: ExecutionStatus | str,
        started_at: str | None = None,
        completed_at: str | None = None,
        output: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not execution_id:
            raise ValueError("Execution ID is required.")
        if not work_order_id:
            raise ValueError("Work order ID is required.")
        if not status:
            raise ValueError("Execution status is required.")

        self.execution_id = execution_id
        self.work_order_id = work_order_id
        self.status = (
            status if isinstance(status, ExecutionStatus) else ExecutionStatus(status)
        )
        self.started_at = started_at
        self.completed_at = completed_at
        self.output = output
        self.metadata = metadata or {}

    def summary(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "work_order_id": self.work_order_id,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "work_order_id": self.work_order_id,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "output": self.output,
            "metadata": dict(self.metadata),
        }


class ExecutionEngine(ABC):
    @abstractmethod
    def execute(self, work_order: Any) -> ExecutionResult:
        """
        Starts execution of a work order.
        """
        pass

    @abstractmethod
    def supports(self, capability: str) -> bool:
        """
        Checks if the engine supports a given capability.
        """
        pass

    @abstractmethod
    def status(self, execution_id: str) -> ExecutionStatus:
        """
        Checks current status of an execution.
        """
        pass

    @abstractmethod
    def cancel(self, execution_id: str) -> bool:
        """
        Attempts to cancel a running execution.
        """
        pass

    @abstractmethod
    def result(self, execution_id: str) -> ExecutionResult | None:
        """
        Retrieves the execution result if available.
        """
        pass
