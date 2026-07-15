from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class AuditRecord:
    """Immutable audit record detailing administrative or critical system actions.

    BR-050-004: Audit records are strictly immutable.
    BR-050-006: Fully serializable to dictionary format.
    """

    def __init__(
        self,
        audit_id: str,
        actor: str,
        action: str,
        target: str,
        outcome: str = "SUCCESS",
        explanation: str = "",
        timestamp: str | None = None,
    ) -> None:
        self._audit_id = audit_id
        self._actor = actor
        self._action = action
        self._target = target
        self._outcome = outcome
        self._explanation = explanation
        self._timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        # Lock attributes to enforce immutability
        self._frozen = True

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_frozen", False):
            raise AttributeError("AuditRecord is immutable and cannot be modified (BR-050-004).")
        super().__setattr__(name, value)

    @property
    def audit_id(self) -> str:
        return self._audit_id

    @property
    def actor(self) -> str:
        return self._actor

    @property
    def action(self) -> str:
        return self._action

    @property
    def target(self) -> str:
        return self._target

    @property
    def outcome(self) -> str:
        return self._outcome

    @property
    def explanation(self) -> str:
        return self._explanation

    @property
    def timestamp(self) -> str:
        return self._timestamp

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "actor": self.actor,
            "action": self.action,
            "target": self.target,
            "outcome": self.outcome,
            "explanation": self.explanation,
            "timestamp": self.timestamp,
        }
