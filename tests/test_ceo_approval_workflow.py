import unittest
from datetime import datetime, timezone

from core.client_proposal import ClientProposal
from core.approval_decision import ApprovalDecision, ApprovalStatus
from core.ceo_approval_workflow import CEOApprovalWorkflow


class TestCEOApprovalWorkflow(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = CEOApprovalWorkflow()
        self.proposal = ClientProposal(
            proposal_id="PRP-0001",
            proposal_version="1.0",
            proposal_date="2026-07-13",
            client_name="Bob",
            client_organization="Acme",
            proposal_title="Proposal Title",
            executive_summary="Summary",
            understanding_of_client_needs="Needs",
            current_business_challenges="Challenges",
            proposed_solution="Solution",
            solution_benefits="Benefits",
            project_objectives="Objectives",
            scope_of_work={},
            deliverables=[],
            project_timeline="",
            commercial_investment=25000.0,
            payment_terms="50/50 Split",
            optional_services=[],
            client_responsibilities=[],
            assumptions=[],
            exclusions=[],
            warranty="Warranty",
            support_options="Support",
            acceptance_process="Accept",
            next_steps="Next",
            proposal_valid_until="2026-08-12",
            contact_information="Contact",
            executive_signature_block="Signature",
        )

    def test_invalid_submit_inputs(self) -> None:
        with self.assertRaises(ValueError):
            self.workflow.submit_for_review(None)  # type: ignore

    def test_submit_initial_state(self) -> None:
        decision = self.workflow.submit_for_review(self.proposal)
        self.assertIsInstance(decision, ApprovalDecision)
        self.assertEqual(decision.status, ApprovalStatus.PENDING_REVIEW)
        self.assertEqual(decision.proposal_id, "PRP-0001")
        self.assertEqual(len(decision.audit_trail), 1)
        self.assertEqual(decision.audit_trail[0]["new_status"], "Pending Review")

    def test_approve_workflow(self) -> None:
        decision = self.workflow.submit_for_review(self.proposal)
        self.workflow.approve(
            decision=decision,
            decision_maker="CEO-John",
            comments="Looks great, approve after finance checks",
            conditions=["Finance verification needed"],
            reason="Aligned with Q3 goals"
        )
        self.assertEqual(decision.status, ApprovalStatus.APPROVED)
        self.assertEqual(decision.decision_maker, "CEO-John")
        self.assertEqual(decision.next_action, "Project Initialization")
        self.assertEqual(len(decision.audit_trail), 2)
        self.assertEqual(decision.audit_trail[-1]["new_status"], "Approved")

    def test_reject_workflow(self) -> None:
        decision = self.workflow.submit_for_review(self.proposal)
        self.workflow.reject(decision, "CEO-John", "Pricing is too low")
        self.assertEqual(decision.status, ApprovalStatus.REJECTED)
        self.assertEqual(decision.next_action, "Archived")

    def test_revision_workflow(self) -> None:
        decision = self.workflow.submit_for_review(self.proposal)
        requests = [{"change": "Increase price", "reason": "Low margin", "priority": "High", "department": "Commercial"}]
        self.workflow.return_for_revision(decision, "CEO-John", "Requires margin checks", requests)
        self.assertEqual(decision.status, ApprovalStatus.RETURNED_FOR_REVISION)
        self.assertEqual(decision.next_action, "Revise Proposal")
        self.assertEqual(decision.revision_requests, requests)

    def test_escalate_and_withdraw(self) -> None:
        decision = self.workflow.submit_for_review(self.proposal)
        self.workflow.escalate(decision, "CEO-John", "Escalate to board")
        self.assertEqual(decision.status, ApprovalStatus.ESCALATED)
        self.assertEqual(decision.next_action, "Board Review")
        
        self.workflow.withdraw(decision, "CEO-John", "Client retract request")
        self.assertEqual(decision.status, ApprovalStatus.WITHDRAWN)
        self.assertEqual(decision.next_action, "Retract Proposal")

    def test_expire_workflow(self) -> None:
        decision = self.workflow.submit_for_review(self.proposal)
        self.workflow.expire(decision)
        self.assertEqual(decision.status, ApprovalStatus.EXPIRED)
        self.assertEqual(decision.next_action, "Re-submit for Review")

    def test_serialization(self) -> None:
        decision = self.workflow.submit_for_review(self.proposal)
        self.workflow.approve(decision, "CEO-John", "Approve comments", ["Condition"], "Reason")
        summary = decision.summary()
        self.assertEqual(summary["decision_id"], decision.decision_id)
        self.assertEqual(summary["status"], "Approved")
        
        to_dict_out = decision.to_dict()
        self.assertEqual(to_dict_out["decision_id"], decision.decision_id)
        self.assertEqual(to_dict_out["proposal_id"], "PRP-0001")
        self.assertEqual(len(to_dict_out["audit_trail"]), 2)
