from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from core.client_proposal import ClientProposal
from core.approval_decision import ApprovalDecision, ApprovalStatus

LOGGER = logging.getLogger(__name__)


class CEOApprovalWorkflow:
    def __init__(self) -> None:
        self._next_id = 1
        self.default_expiration_days = 7

    def _generate_decision_id(self) -> str:
        dec_id = f"DEC-{self._next_id:04d}"
        self._next_id += 1
        return dec_id

    def submit_for_review(self, client_proposal: ClientProposal) -> ApprovalDecision:
        if client_proposal is None:
            raise ValueError("Client proposal is required for submission.")
            
        proposal_id = getattr(client_proposal, "proposal_id", "UNKNOWN")
        decision_id = self._generate_decision_id()
        
        LOGGER.info("object_id=%s action=submit_for_review actor=system status=PENDING_REVIEW", decision_id)

        # Set standard expiration
        today = datetime.now(timezone.utc)
        exp_date = today + timedelta(days=self.default_expiration_days)
        expiration_str = exp_date.strftime("%Y-%m-%d")

        decision = ApprovalDecision(
            decision_id=decision_id,
            proposal_id=proposal_id,
            status=ApprovalStatus.PENDING_REVIEW,
            expiration_date=expiration_str,
            next_action="Awaiting Executive Action"
        )
        
        # Log initial submission in audit
        decision.add_audit_record(
            previous_status=ApprovalStatus.PENDING_REVIEW,
            new_status=ApprovalStatus.PENDING_REVIEW,
            decision_maker="System",
            comments=f"Proposal submitted for review. Expiration set to {expiration_str}."
        )
        return decision

    def approve(
        self,
        decision: ApprovalDecision,
        decision_maker: str,
        comments: str,
        conditions: list[str] | None = None,
        reason: str | None = None,
    ) -> None:
        if decision is None:
            raise ValueError("Decision reference is required.")
        if not decision_maker:
            raise ValueError("Decision maker is required.")

        prev_status = decision.status
        decision.status = ApprovalStatus.APPROVED
        decision.decision_maker = decision_maker
        decision.decision_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        decision.executive_comments = comments
        decision.conditions = conditions or []
        decision.approval_reason = reason or "Proposal meets commercial and strategic criteria."
        decision.next_action = "Project Initialization"

        decision.add_audit_record(
            previous_status=prev_status,
            new_status=ApprovalStatus.APPROVED,
            decision_maker=decision_maker,
            comments=comments,
            conditions=conditions,
            revision_requests=None
        )
        LOGGER.info("object_id=%s action=approve actor=%s status=APPROVED", decision.decision_id, decision_maker)

    def reject(self, decision: ApprovalDecision, decision_maker: str, comments: str) -> None:
        if decision is None:
            raise ValueError("Decision reference is required.")
        if not decision_maker:
            raise ValueError("Decision maker is required.")

        prev_status = decision.status
        decision.status = ApprovalStatus.REJECTED
        decision.decision_maker = decision_maker
        decision.decision_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        decision.executive_comments = comments
        decision.next_action = "Archived"

        decision.add_audit_record(
            previous_status=prev_status,
            new_status=ApprovalStatus.REJECTED,
            decision_maker=decision_maker,
            comments=comments,
            conditions=None,
            revision_requests=None
        )
        LOGGER.info("object_id=%s action=reject actor=%s status=REJECTED", decision.decision_id, decision_maker)

    def return_for_revision(
        self,
        decision: ApprovalDecision,
        decision_maker: str,
        comments: str,
        revision_requests: list[dict[str, Any]],
    ) -> None:
        if decision is None:
            raise ValueError("Decision reference is required.")
        if not decision_maker:
            raise ValueError("Decision maker is required.")
        if not revision_requests:
            raise ValueError("Revision requests list cannot be empty when returning for revision.")

        prev_status = decision.status
        decision.status = ApprovalStatus.RETURNED_FOR_REVISION
        decision.decision_maker = decision_maker
        decision.decision_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        decision.executive_comments = comments
        decision.revision_requests = revision_requests
        decision.next_action = "Revise Proposal"

        decision.add_audit_record(
            previous_status=prev_status,
            new_status=ApprovalStatus.RETURNED_FOR_REVISION,
            decision_maker=decision_maker,
            comments=comments,
            conditions=None,
            revision_requests=revision_requests
        )
        LOGGER.info(
            "object_id=%s action=return_for_revision actor=%s status=RETURNED_FOR_REVISION",
            decision.decision_id,
            decision_maker,
        )

    def escalate(self, decision: ApprovalDecision, decision_maker: str, comments: str) -> None:
        if decision is None:
            raise ValueError("Decision reference is required.")
        if not decision_maker:
            raise ValueError("Decision maker is required.")

        prev_status = decision.status
        decision.status = ApprovalStatus.ESCALATED
        decision.decision_maker = decision_maker
        decision.decision_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        decision.executive_comments = comments
        decision.next_action = "Board Review"

        decision.add_audit_record(
            previous_status=prev_status,
            new_status=ApprovalStatus.ESCALATED,
            decision_maker=decision_maker,
            comments=comments,
            conditions=None,
            revision_requests=None
        )
        LOGGER.info("object_id=%s action=escalate actor=%s status=ESCALATED", decision.decision_id, decision_maker)

    def withdraw(self, decision: ApprovalDecision, decision_maker: str, comments: str) -> None:
        if decision is None:
            raise ValueError("Decision reference is required.")
        if not decision_maker:
            raise ValueError("Decision maker is required.")

        prev_status = decision.status
        decision.status = ApprovalStatus.WITHDRAWN
        decision.decision_maker = decision_maker
        decision.decision_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        decision.executive_comments = comments
        decision.next_action = "Retract Proposal"

        decision.add_audit_record(
            previous_status=prev_status,
            new_status=ApprovalStatus.WITHDRAWN,
            decision_maker=decision_maker,
            comments=comments,
            conditions=None,
            revision_requests=None
        )
        LOGGER.info("object_id=%s action=withdraw actor=%s status=WITHDRAWN", decision.decision_id, decision_maker)

    def expire(self, decision: ApprovalDecision) -> None:
        if decision is None:
            raise ValueError("Decision reference is required.")

        prev_status = decision.status
        decision.status = ApprovalStatus.EXPIRED
        decision.decision_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        decision.next_action = "Re-submit for Review"

        decision.add_audit_record(
            previous_status=prev_status,
            new_status=ApprovalStatus.EXPIRED,
            decision_maker="System",
            comments="Proposal review timeline expired.",
            conditions=None,
            revision_requests=None
        )
        LOGGER.info("object_id=%s action=expire actor=system status=EXPIRED", decision.decision_id)
