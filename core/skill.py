from __future__ import annotations

from enum import Enum
from typing import Any
import logging

LOGGER = logging.getLogger(__name__)


class SkillStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    DISABLED = "DISABLED"
    DEPRECATED = "DEPRECATED"


class Skill:
    def __init__(
        self,
        skill_id: str,
        name: str,
        description: str,
        owner_id: str,
        department: str,
        execution_engine: str,
        capabilities: list[str],
        inputs: list[str],
        outputs: list[str],
        version: str,
        status: SkillStatus | str = SkillStatus.AVAILABLE,
    ) -> None:
        if not skill_id:
            raise ValueError("Skill ID is required.")
        if not name:
            raise ValueError("Skill name is required.")
        if not owner_id:
            raise ValueError("Skill owner ID is required.")
        if not department:
            raise ValueError("Skill department is required.")
        if not execution_engine:
            raise ValueError("Skill execution engine is required.")
        if not version:
            raise ValueError("Skill version is required.")
        if status is None:
            raise ValueError("Skill status is required.")

        self._skill_id = skill_id
        self._name = name
        self._description = description
        self._owner_id = owner_id
        self._department = department
        self._execution_engine = execution_engine
        self._capabilities = [cap.strip().lower() for cap in capabilities] if capabilities else []
        self._inputs = list(inputs) if inputs else []
        self._outputs = list(outputs) if outputs else []
        self._version = version
        self._status = (
            status if isinstance(status, SkillStatus) else self._normalize_status(status)
        )

    @property
    def id(self) -> str:
        return self._skill_id

    @property
    def skill_id(self) -> str:
        return self._skill_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def owner_id(self) -> str:
        return self._owner_id

    @property
    def department(self) -> str:
        return self._department

    @property
    def execution_engine(self) -> str:
        return self._execution_engine

    @property
    def capabilities(self) -> list[str]:
        return list(self._capabilities)

    @property
    def inputs(self) -> list[str]:
        return list(self._inputs)

    @property
    def outputs(self) -> list[str]:
        return list(self._outputs)

    @property
    def version(self) -> str:
        return self._version

    @property
    def status(self) -> SkillStatus:
        return self._status

    def supports(self, capability: str) -> bool:
        if not capability:
            return False
        return capability.strip().lower() in self._capabilities

    def update_status(self, status: SkillStatus | str, actor: str = "system") -> SkillStatus:
        old_status = self._status
        self._status = (
            status if isinstance(status, SkillStatus) else self._normalize_status(status)
        )
        LOGGER.info(
            "object_id=%s action=update_status actor=%s old_status=%s new_status=%s",
            self.id,
            actor,
            old_status.value,
            self._status.value,
        )
        return self._status

    def summary(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "department": self.department,
            "status": self.status.value,
            "version": self.version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "department": self.department,
            "execution_engine": self.execution_engine,
            "capabilities": list(self._capabilities),
            "inputs": list(self._inputs),
            "outputs": list(self._outputs),
            "version": self.version,
            "status": self.status.value,
        }

    @staticmethod
    def _normalize_status(status: SkillStatus | str) -> SkillStatus:
        try:
            return SkillStatus(status)
        except ValueError as exc:
            allowed_statuses = ", ".join(s.value for s in SkillStatus)
            raise ValueError(
                f"Invalid skill status. Allowed values: {allowed_statuses}."
            ) from exc
