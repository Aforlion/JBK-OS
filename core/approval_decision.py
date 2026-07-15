from __future__ import annotations

from enum import Enum
from typing import Any
from datetime import datetime, timezone


class ApprovalStatus(Enum):
    PENDING_REVIEW = "Pending Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    RETURNED_FOR_REVISION = "Returned for Revision"
    ESCALATED = "Escalated"
    WITHDRAWN = "Withdrawn"
    EXPIRED = "Expired"


class ApprovalDecision:
    def __init__(
        self,
        decision_id: str,
        proposal_id: str,
        status: ApprovalStatus = ApprovalStatus.PENDING_REVIEW,
        decision_date: str | None = None,
        decision_maker: str | None = None,
        executive_comments: str | None = None,
        conditions: list[str] | None = None,
        revision_requests: list[dict[str, Any]] | None = None,
        approval_reason: str | None = None,
        expiration_date: str | None = None,
        audit_reference: str | None = None,
        next_action: str | None = None,
        audit_trail: list[dict[str, Any]] | None = None,
        created_at: str | None = None,
    ) -> None:
        self.decision_id = decision_id
        self.proposal_id = proposal_id
        self.status = status
        self.decision_date = decision_date
        self.decision_maker = decision_maker
        self.executive_comments = executive_comments
        self.conditions = conditions or []
        self.revision_requests = revision_requests or []
        self.approval_reason = approval_reason
        self.expiration_date = expiration_date
        self.audit_reference = audit_reference or f"AUD-{decision_id}"
        self.next_action = next_action
        self.audit_trail = audit_trail or []
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def add_audit_record(
        self,
        previous_status: ApprovalStatus,
        new_status: ApprovalStatus,
        decision_maker: str,
        comments: str | None = None,
        conditions: list[str] | None = None,
        revision_requests: list[dict[str, Any]] | None = None,
    ) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_status": previous_status.value,
            "new_status": new_status.value,
            "decision_maker": decision_maker,
            "comments": comments or "",
            "conditions": list(conditions) if conditions else [],
            "revision_requests": [dict(r) for r in revision_requests] if revision_requests else [],
        }
        self.audit_trail.append(record)

    def summary(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "proposal_id": self.proposal_id,
            "status": self.status.value,
            "decision_maker": self.decision_maker,
            "decision_date": self.decision_date,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "proposal_id": self.proposal_id,
            "status": self.status.value,
            "decision_date": self.decision_date,
            "decision_maker": self.decision_maker,
            "executive_comments": self.executive_comments,
            "conditions": list(self.conditions),
            "revision_requests": [dict(r) for r in self.revision_requests],
            "approval_reason": self.approval_reason,
            "expiration_date": self.expiration_date,
            "audit_reference": self.audit_reference,
            "next_action": self.next_action,
            "audit_trail": [dict(rec) for rec in self.audit_trail],
            "created_at": self.created_at,
        }
