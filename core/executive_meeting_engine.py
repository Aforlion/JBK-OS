from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from core.chief_of_staff import ChiefOfStaff
from core.portfolio_report import PortfolioReport
from core.strategic_intelligence_report import StrategicIntelligenceReport
from core.executive_meeting import (
    ExecutiveMeeting,
    AgendaItem,
    ExecutiveDecision,
    ExecutiveActionItem,
)
from core.executive_meeting_report import ExecutiveMeetingReport
from core.agenda_generator import AgendaGenerator
from core.organizational_knowledge import OrganizationalKnowledge

LOGGER = logging.getLogger(__name__)


class ExecutiveMeetingEngine:
    """Coordinates meeting minutes, decisions, and alignments across roles (Spec 040)."""

    def __init__(self) -> None:
        self._meeting_counter = 1
        self._decision_counter = 1
        self._agenda_generator = AgendaGenerator()

    def conduct_meeting(
        self,
        meeting_type: str,
        participants: list[str],
        chief_of_staff: ChiefOfStaff,
        portfolio_report: PortfolioReport | None = None,
        strategic_intel: StrategicIntelligenceReport | None = None,
        executive_briefings: dict[str, str] | None = None,
        ceo_override_decisions: dict[str, str] | None = None,
    ) -> ExecutiveMeetingReport:
        """Runs the meeting lifecycle and aggregates all updates and consensus checks."""
        if not meeting_type:
            raise ValueError("Meeting Type is required.")
        if not participants:
            raise ValueError("At least one participant is required.")
        if chief_of_staff is None:
            raise ValueError("Chief of Staff is required.")

        meeting_id = f"MTG-{self._meeting_counter:04d}"
        self._meeting_counter += 1

        LOGGER.info("object_id=%s action=conduct_meeting actor=system status=ACTIVE type=%s", meeting_id, meeting_type)

        # 1. Agenda Generation (BR-040-004)
        agenda = self._agenda_generator.generate(
            project_registry=chief_of_staff.project_registry,
            strategic_intel=strategic_intel,
            chief_of_staff=chief_of_staff,
        )

        meeting = ExecutiveMeeting(
            meeting_id=meeting_id,
            meeting_type=meeting_type,
            participants=participants,
            agenda=agenda,
            status="IN_PROGRESS",
        )

        # 2. Executive Briefings Aggregation (BR-040-005)
        briefings = dict(executive_briefings or {})

        # 3. Discussion Management, Consensus & Conflict Detection (BR-040-006, BR-040-009, BR-040-010)
        decisions: list[ExecutiveDecision] = []
        action_items: list[ExecutiveActionItem] = []
        unresolved_items: list[dict[str, Any]] = []
        consensus_achieved = True

        # Process each agenda item and check for arguments in briefings
        for item in agenda:
            owner = item.owner
            discussion_points = briefings.get(owner, f"Standard update regarding {item.title}.")
            item.discussion = discussion_points

            # Simple simulated conflict: if another executive key argues differently in briefings
            # e.g., CTO: "Build internally" vs CFO: "Buy existing software"
            has_conflict = False
            conflict_details = {}

            if "CTO" in briefings and "CFO" in briefings:
                cto_brief = briefings["CTO"].lower()
                cfo_brief = briefings["CFO"].lower()
                if "build" in cto_brief and "buy" in cfo_brief:
                    has_conflict = True
                    conflict_details = {
                        "agenda_item": item.title,
                        "conflict": "CTO recommends 'Build' while CFO recommends 'Buy'.",
                    }

            # CEO Override (BR-040-011)
            overridden = False
            override_val = None
            if has_conflict and ceo_override_decisions:
                # CEO decision resolves the conflict
                override_val = ceo_override_decisions.get(item.title)
                if override_val:
                    overridden = True

            dec_id = f"DEC-{self._decision_counter:04d}"
            self._decision_counter += 1

            if has_conflict and not overridden:
                consensus_achieved = False
                unresolved_items.append(conflict_details)
                # Decision outcome records deadlock status
                dec = ExecutiveDecision(
                    decision_id=dec_id,
                    proposal=f"Resolve build/buy choice for {item.title}",
                    outcome="POSTPONED",
                    rationale="Executive disagreement between CTO and CFO. Decision postponed.",
                    confidence=0.5,
                    proposer=owner,
                )
            else:
                outcome_str = "APPROVED" if not overridden else f"APPROVED (CEO OVERRIDE: {override_val})"
                rationale_str = f"Consensus achieved under {owner} proposal." if not overridden else f"Resolved via CEO directive: {override_val}."
                
                dec = ExecutiveDecision(
                    decision_id=dec_id,
                    proposal=f"Approve action plan for {item.title}",
                    outcome=outcome_str,
                    rationale=rationale_str,
                    confidence=0.9,
                    proposer=owner,
                )

                # BR-040-008: Auto-assign action item for approved items
                action_items.append(
                    ExecutiveActionItem(
                        owner=owner,
                        description=f"Implement resolution for: {item.title}",
                        priority=item.priority,
                        due_date="Next governance cycle",
                        originating_decision=dec_id,
                    )
                )

            item.decisions.append(dec)
            decisions.append(dec)

        # 4. Knowledge Capture (BR-040-013)
        knowledge_candidates = []
        if chief_of_staff.knowledge_registry and consensus_achieved:
            ok = OrganizationalKnowledge(
                knowledge_id=f"KN-MTG-{meeting_id}",
                title=f"Executive Meeting Minutes: {meeting_type} ({meeting_id})",
                category="GENERAL",
                source_project_ids=["PROJ-SYSTEM"],
                future_recommendations=[f"Meeting resolved with {len(decisions)} formal decisions."],
            )
            chief_of_staff.register_knowledge(ok)
            knowledge_candidates.append(ok.id)

        meeting.end_time = datetime.now(timezone.utc).isoformat()
        meeting.status = "CONCLUDED"

        return ExecutiveMeetingReport(
            meeting_id=meeting.meeting_id,
            meeting_type=meeting.meeting_type,
            attendance=participants,
            agenda=[i.to_dict() for i in agenda],
            discussions={i.owner: i.discussion for i in agenda},
            decisions=[d.to_dict() for d in decisions],
            action_items=[a.to_dict() for a in action_items],
            unresolved_items=unresolved_items,
            knowledge_candidates=knowledge_candidates,
            consensus_achieved=consensus_achieved,
        )
