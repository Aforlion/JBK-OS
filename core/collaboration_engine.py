from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from core.work_order import WorkOrder, WorkOrderStatus
from core.chief_of_staff import ChiefOfStaff
from core.skill_runtime import BaseSkill
from core.skill_execution_framework import SkillExecutionFramework
from core.organizational_knowledge import OrganizationalKnowledge
from core.collaboration_session import (
    CollaborationSession,
    CollaborationParticipant,
    CollaborationRole,
    CollaborationParticipantStatus,
    CollaborationMessage,
    SessionStatus,
)
from core.collaboration_report import CollaborationReport

LOGGER = logging.getLogger(__name__)


class MultiAgentCollaborationEngine:
    """Coordinates multiple AI employee skills working collaboratively on a Work Order (Spec 039)."""

    def __init__(self, framework: SkillExecutionFramework) -> None:
        if framework is None:
            raise ValueError("SkillExecutionFramework is required.")
        self._framework = framework
        self._session_counter = 1

    def coordinate(
        self,
        work_order: WorkOrder,
        skills: list[BaseSkill],
        chief_of_staff: ChiefOfStaff,
    ) -> CollaborationReport:
        """Decomposes, assigns, executes, reviews, and closes collaboration session."""
        if work_order is None:
            raise ValueError("Work order is required.")
        if not skills:
            raise ValueError("At least one skill participant is required.")
        if chief_of_staff is None:
            raise ValueError("Chief of Staff is required.")

        session_id = f"COL-{self._session_counter:04d}"
        self._session_counter += 1

        session = CollaborationSession(session_id, work_order.id)
        LOGGER.info("object_id=%s action=coordinate actor=system status=ACTIVE work_order=%s", session_id, work_order.id)

        # 1. Selection & Registration (BR-039-002)
        contributors: list[BaseSkill] = []
        reviewers: list[BaseSkill] = []

        for skill in skills:
            manifest = skill.get_manifest()
            # If skill name or capabilities contain review/audit/security, assign REVIEWER
            is_reviewer = any(
                term in manifest.name.lower() or any(term in cap.lower() for cap in manifest.capabilities)
                for term in ["reviewer", "review", "audit", "security", "qa"]
            )
            role = CollaborationRole.REVIEWER if is_reviewer else CollaborationRole.CONTRIBUTOR
            
            p = CollaborationParticipant(
                skill_id=manifest.skill_id,
                role=role,
                status=CollaborationParticipantStatus.IDLE,
            )
            session.register_participant(p)

            if role == CollaborationRole.REVIEWER:
                reviewers.append(skill)
            else:
                contributors.append(skill)

            session.log_message(
                CollaborationMessage(
                    sender="system",
                    receiver=manifest.skill_id,
                    message_type="PARTICIPANT_REGISTRATION",
                    content=f"Registered in role {role.value}.",
                )
            )

        # If no reviewer exists, fallback the last contributor or assign one as reviewer
        if not reviewers and len(contributors) > 1:
            fallback_rev = contributors.pop()
            manifest = fallback_rev.get_manifest()
            session.participants[manifest.skill_id].role = CollaborationRole.REVIEWER
            reviewers.append(fallback_rev)

        # 2. Task Decomposition (BR-039-003)
        # Create sub-tasks for contributors
        for skill in contributors:
            manifest = skill.get_manifest()
            sub_task_title = f"Build Contribution: {manifest.name}"
            p_record = session.participants[manifest.skill_id]
            p_record.assigned_tasks.append(sub_task_title)
            session.log_message(
                CollaborationMessage(
                    sender="system",
                    receiver=manifest.skill_id,
                    message_type="TASK_ASSIGNMENT",
                    content=sub_task_title,
                )
            )

        # 3. Parallel Execution & Shared Workspace Exchange (BR-039-004, BR-039-005, BR-039-006)
        last_artifact_content = ""
        last_artifact_id = None

        for skill in contributors:
            manifest = skill.get_manifest()
            p_record = session.participants[manifest.skill_id]
            p_record.status = CollaborationParticipantStatus.ACTIVE

            # Execute Skill
            exec_result = self._framework.execute(
                skill=skill,
                work_order=work_order,
                project=None,
                knowledge_registry=chief_of_staff.knowledge_registry,
            )
            p_record.status = CollaborationParticipantStatus.COMPLETED
            if exec_result.status == "SUCCESS" and exec_result.deliverable:
                last_artifact_content = getattr(exec_result.deliverable, "content", "")
                last_artifact_id = exec_result.deliverable.id
                p_record.deliverables.append(exec_result.deliverable.id)

                # Store in Shared Workspace (BR-039-005)
                workspace_key = f"{manifest.skill_id}_output"
                session.workspace.put(workspace_key, exec_result.deliverable)

                session.log_message(
                    CollaborationMessage(
                        sender=manifest.skill_id,
                        receiver="workspace",
                        message_type="ARTIFACT_SUBMISSION",
                        artifact_reference=exec_result.deliverable.id,
                        content=f"Submitted deliverable from {manifest.name}.",
                    )
                )
            else:
                # Execution failure handles gracefully
                session.status = SessionStatus.ESCALATED
                session.log_message(
                    CollaborationMessage(
                        sender=manifest.skill_id,
                        receiver="system",
                        message_type="EXECUTION_FAILURE",
                        content=exec_result.reasoning,
                    )
                )
                return self._compile_report(session, consensus_reached=False, reasoning="Execution failure in contributor.")

        # 4. Review Cycle & Conflict Resolution (BR-039-007, BR-039-008, BR-039-009)
        session.status = SessionStatus.REVIEW
        reviews_logged = []
        conflicts_logged = []
        consensus_reached = True

        for reviewer_skill in reviewers:
            rev_manifest = reviewer_skill.get_manifest()
            rev_record = session.participants[rev_manifest.skill_id]
            rev_record.status = CollaborationParticipantStatus.ACTIVE

            # Create review request work order
            review_wo = WorkOrder(
                project_id=work_order.project_id,
                title=f"Review Deliverable for {work_order.title}",
                objective=f"Review this output: {last_artifact_content[:100]}",
                work_order_id=f"WO-REV-{rev_manifest.skill_id}",
            )

            # Reviewer validates content
            val_res = reviewer_skill.validate(last_artifact_content)
            rev_record.status = CollaborationParticipantStatus.COMPLETED

            if not val_res.passed:
                consensus_reached = False

            review_record = {
                "reviewer": rev_manifest.name,
                "passed": val_res.passed,
                "score": val_res.score,
                "issues": val_res.issues,
            }
            reviews_logged.append(review_record)

            if not val_res.passed:
                consensus_reached = False
                conflicts_logged.append({
                    "skill_id": rev_manifest.skill_id,
                    "issues": val_res.issues,
                    "recommendations": val_res.recommendations,
                })
                session.status = SessionStatus.ESCALATED
                session.log_message(
                    CollaborationMessage(
                        sender=rev_manifest.skill_id,
                        receiver="workspace",
                        message_type="REVIEW_FEEDBACK",
                        content=f"Review failed. Issues: {', '.join(val_res.issues)}",
                    )
                )
                session.log_message(
                    CollaborationMessage(
                        sender="system",
                        receiver="CEO",
                        message_type="CONFLICT_RECORD",
                        content=f"Conflict detected. Reviewer {rev_manifest.name} rejected output.",
                    )
                )
            else:
                session.log_message(
                    CollaborationMessage(
                        sender=rev_manifest.skill_id,
                        receiver="workspace",
                        message_type="REVIEW_FEEDBACK",
                        content=f"Review passed with score {val_res.score}.",
                    )
                )

        if consensus_reached:
            session.status = SessionStatus.CONSENSUS_REACHED
            session.log_message(
                CollaborationMessage(
                    sender="system",
                    receiver="all",
                    message_type="CONSENSUS_REACHED",
                    content="Consensus detected. All reviews passed.",
                )
            )

            # BR-039-012: Knowledge Capture
            if chief_of_staff.knowledge_registry:
                ok = OrganizationalKnowledge(
                    knowledge_id=f"KN-COL-{session_id}",
                    title=f"Collaboration Outcome: {work_order.title}",
                    category="GENERAL",
                    source_project_ids=[work_order.project_id],
                    future_recommendations=[f"Successful collaboration on {work_order.title} by {[p.skill_id for p in session.participants.values()]}."],
                )
                chief_of_staff.register_knowledge(ok)
                session.log_message(
                    CollaborationMessage(
                        sender="system",
                        receiver="knowledge_registry",
                        message_type="KNOWLEDGE_CAPTURE",
                        content=f"Registered knowledge asset {ok.id}.",
                    )
                )

        return self._compile_report(
            session=session,
            consensus_reached=consensus_reached,
            reviews=reviews_logged,
            conflicts=conflicts_logged,
            final_artifact_id=last_artifact_id,
            reasoning="Multi-agent cycle finished. Consensus reached: " + str(consensus_reached),
        )

    def _compile_report(
        self,
        session: CollaborationSession,
        consensus_reached: bool,
        reviews: list[dict[str, Any]] | None = None,
        conflicts: list[dict[str, Any]] | None = None,
        final_artifact_id: str | None = None,
        reasoning: str = "",
    ) -> CollaborationReport:
        timeline = [msg.to_dict() for msg in session.audit_trail]
        participants = [p.to_dict() for p in session.participants.values()]

        recs = []
        if not consensus_reached:
            recs.append("Trigger executive override or revision cycle to resolve outstanding review conflicts.")
        else:
            recs.append("Deliverable is ready for client-facing deployment and sign-off.")

        return CollaborationReport(
            session_id=session.session_id,
            participants=participants,
            timeline=timeline,
            reviews=reviews or [],
            conflicts=conflicts or [],
            consensus_reached=consensus_reached,
            recommendations=recs,
            final_artifact_id=final_artifact_id,
            reasoning=reasoning,
        )
