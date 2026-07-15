from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any


LOGGER = logging.getLogger(__name__)


class WorkerRegistry:
    def __init__(self) -> None:
        self._workers: dict[str, Any] = {}

    def register(self, worker: Any) -> Any:
        worker_id = self._get_worker_id(worker)
        if worker_id in self._workers:
            raise ValueError(f"Worker ID already registered: {worker_id}.")

        self._workers[worker_id] = worker
        self._log_state_change(worker_id, "register", "system", "registered")
        return worker

    def unregister(self, worker_id: str) -> Any:
        if not worker_id:
            raise ValueError("Worker ID is required.")
        if worker_id not in self._workers:
            raise ValueError(f"Worker ID is not registered: {worker_id}.")

        worker = self._workers.pop(worker_id)
        self._log_state_change(worker_id, "unregister", "system", "unregistered")
        return worker

    def find_by_id(self, worker_id: str) -> Any | None:
        if not worker_id:
            raise ValueError("Worker ID is required.")
        return self._workers.get(worker_id)

    def find_by_role(self, role: str) -> list[Any]:
        if not role:
            raise ValueError("Role is required.")
        return [
            worker
            for worker in self._workers.values()
            if getattr(worker, "title", None) == role
        ]

    def list_workers(self) -> list[Any]:
        return list(self._workers.values())

    def list_available(self) -> list[Any]:
        return [
            worker
            for worker in self._workers.values()
            if self._status_value(worker) == "AVAILABLE"
        ]

    def summary(self) -> dict[str, Any]:
        workers_by_role: dict[str, int] = {}
        available_workers = 0
        busy_workers = 0
        offline_workers = 0
        suspended_workers = 0

        for worker in self._workers.values():
            role = getattr(worker, "title", "UNKNOWN")
            workers_by_role[role] = workers_by_role.get(role, 0) + 1

            status = self._status_value(worker)
            if status == "AVAILABLE":
                available_workers += 1
            elif status == "BUSY":
                busy_workers += 1
            elif status == "OFFLINE":
                offline_workers += 1
            elif status == "SUSPENDED":
                suspended_workers += 1

        return {
            "total_registered_workers": len(self._workers),
            "workers_by_role": workers_by_role,
            "available_workers": available_workers,
            "busy_workers": busy_workers,
            "offline_workers": offline_workers,
            "suspended_workers": suspended_workers,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "workers": [
                self._serialize_worker(worker)
                for worker in self._workers.values()
            ],
            "summary": self.summary(),
        }

    @staticmethod
    def _get_worker_id(worker: Any) -> str:
        if worker is None:
            raise ValueError("Worker is required.")

        worker_id = getattr(worker, "id", None)
        if not worker_id:
            raise ValueError("Worker must have an ID.")
        return worker_id

    @staticmethod
    def _status_value(worker: Any) -> str | None:
        status = getattr(worker, "status", None)
        return getattr(status, "value", status)

    @staticmethod
    def _serialize_worker(worker: Any) -> Any:
        if hasattr(worker, "to_dict") and callable(worker.to_dict):
            return worker.to_dict()
        if hasattr(worker, "__dict__"):
            return dict(worker.__dict__)
        return worker

    @staticmethod
    def _log_state_change(
        worker_id: str,
        action: str,
        actor: str,
        result: str,
    ) -> None:
        LOGGER.info(
            "timestamp=%s object_id=%s action=%s actor=%s result=%s",
            datetime.now(timezone.utc).isoformat(),
            worker_id,
            action,
            actor,
            result,
        )
