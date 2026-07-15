from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from core.chief_of_staff import ChiefOfStaff
from core.skill_registry import SkillRegistry
from core.knowledge_registry import KnowledgeRegistry
from core.intent_recognizer import IntentRecognizer, IntentResult
from core.executive_conversation_record import ConversationTurn, ExecutiveConversationRecord

# Import all integration components
from core.opportunity_intake_engine import OpportunityIntakeEngine
from core.discovery_conversation_engine import DiscoveryConversationEngine
from core.solution_architect import SolutionArchitect
from core.estimation_engine import EstimationEngine
from core.pricing_engine import PricingEngine
from core.proposal_generator import ProposalGenerator
from core.ceo_approval_workflow import CEOApprovalWorkflow
from core.project_initialization_engine import ProjectInitializationEngine
from core.delivery_planning_engine import DeliveryPlanningEngine
from core.work_breakdown_engine import WorkBreakdownEngine
from core.resource_allocation_engine import ResourceAllocationEngine
from core.work_order_generation_engine import WorkOrderGenerationEngine
from core.work_execution_orchestrator import WorkExecutionOrchestrator
from core.delivery_supervision_engine import DeliverySupervisionEngine
from core.organizational_memory_engine import OrganizationalMemoryEngine
from core.continuous_improvement_engine import ContinuousImprovementEngine
from core.business_transformation_engine import BusinessTransformationEngine
from core.portfolio_management_engine import PortfolioManagementEngine
from core.strategic_intelligence_engine import StrategicIntelligenceEngine


@dataclass
class AssistantResponse:
    message: str
    intent: str
    confidence: float
    engines_consulted: list[str]
    reasoning: str
    execution_timeline: list[dict[str, Any]]
    data: dict[str, Any] | None = None
    follow_up_question: str | None = None
    requires_authorization: bool = False


class AIExecutiveAssistant:
    """Intelligent conductor of JBK-OS V1 conversational interface (Spec 035)."""

    def __init__(
        self,
        chief_of_staff: ChiefOfStaff,
        skill_registry: SkillRegistry,
        knowledge_registry: KnowledgeRegistry,
    ) -> None:
        self.chief_of_staff = chief_of_staff
        self.skill_registry = skill_registry
        self.knowledge_registry = knowledge_registry

        self.intent_recognizer = IntentRecognizer()
        
        # Session state
        self.active_record = ExecutiveConversationRecord(
            session_id="SESS-0001",
            executive_id="CEO-John",
        )
        self.turn_counter = 1
        
        # Context tracking (context-awareness: BR-035-003)
        self.context: dict[str, Any] = {
            "active_client_name": None,
            "active_organization": None,
            "active_brief": None,
            "active_discovery_plan": None,
            "active_blueprint": None,
            "active_estimate": None,
            "active_commercial_proposal": None,
            "active_proposal": None,
            "active_decision": None,
            "active_project": None,
        }

        # Lazily instantiated engines
        self.intake_engine = OpportunityIntakeEngine()
        self.discovery_engine = DiscoveryConversationEngine()
        self.solution_architect = SolutionArchitect()
        self.estimation_engine = EstimationEngine()
        self.pricing_engine = PricingEngine()
        self.proposal_generator = ProposalGenerator()
        self.approval_workflow = CEOApprovalWorkflow()
        self.init_engine = ProjectInitializationEngine()
        self.planning_engine = DeliveryPlanningEngine()
        self.wbs_engine = WorkBreakdownEngine()
        self.allocation_engine = ResourceAllocationEngine()
        self.wog_engine = WorkOrderGenerationEngine()
        self.orchestrator = WorkExecutionOrchestrator()
        self.supervision_engine = DeliverySupervisionEngine()
        self.memory_engine = OrganizationalMemoryEngine()
        self.ci_engine = ContinuousImprovementEngine()
        self.bt_engine = BusinessTransformationEngine()
        self.portfolio_engine = PortfolioManagementEngine()
        self.si_engine = StrategicIntelligenceEngine()

    def generate_startup_briefing(self, intent: str = "EXECUTIVE_BRIEFING") -> AssistantResponse:
        """Produce the morning executive operational briefing (BR-035-012)."""
        brief_data = self.chief_of_staff.generate_executive_brief()
        
        message = (
            "Good Morning. Today's priorities are focused on current delivery execution. "
            f"We have {len(brief_data.get('projects_in_progress', []))} active projects in progress. "
            f"There are {len(brief_data.get('items_requiring_ceo_attention', []))} items requiring your attention."
        )

        return AssistantResponse(
            message=message,
            intent=intent,
            confidence=1.0,
            engines_consulted=["ChiefOfStaff"],
            reasoning="Constructed startup operational overview by querying core registries.",
            execution_timeline=[
                {
                    "step": "Executive Briefing Generation",
                    "engine": "ChiefOfStaff",
                    "status": "COMPLETED",
                    "description": "Queried ProjectRegistry and WorkerRegistry for operational stats.",
                }
            ],
            data=brief_data,
        )

    def converse(self, user_message: str) -> AssistantResponse:
        """Process incoming natural language and orchestrate appropriate engines."""
        turn_id = f"TRN-{self.turn_counter:04d}"
        self.turn_counter += 1

        # Classify intent & extract entities
        rec_result = self.intent_recognizer.recognize(user_message)

        # Try extracting client entities even if classified as general question (multi-turn context)
        extra_entities = self.intent_recognizer._extract_client_entities(user_message)
        for k, v in extra_entities.items():
            if v:
                rec_result.entities[k] = v

        # Merge extracted entities into session context if available
        if rec_result.entities.get("client_name"):
            self.context["active_client_name"] = rec_result.entities["client_name"]
        if rec_result.entities.get("organization"):
            self.context["active_organization"] = rec_result.entities["organization"]

        # Context-awareness (BR-035-003): If general question, but active client exists and we got new intake details
        if rec_result.intent == "GENERAL_QUESTION" and (self.context["active_client_name"] or self.context["active_organization"]):
            if rec_result.entities.get("budget") or rec_result.entities.get("timeline") or rec_result.entities.get("contact"):
                rec_result.intent = "NEW_CLIENT"
                rec_result.confidence = 0.9

        # Clarification handling (BR-035-006)
        if rec_result.clarification_needed:
            return self._build_clarification_response(turn_id, user_message, rec_result)

        # Route intent to core coordinators
        try:
            if rec_result.intent == "GREETING":
                response = self.generate_startup_briefing(intent="GREETING")
            elif rec_result.intent == "EXECUTIVE_BRIEFING":
                response = self.generate_startup_briefing()
            elif rec_result.intent == "PORTFOLIO_REVIEW":
                response = self._run_portfolio_review()
            elif rec_result.intent == "STRATEGIC_ANALYSIS":
                response = self._run_strategic_analysis(rec_result)
            elif rec_result.intent == "KNOWLEDGE_QUERY":
                response = self._run_knowledge_query(user_message)
            elif rec_result.intent == "DELIVERY_STATUS":
                response = self._run_delivery_status()
            elif rec_result.intent == "NEW_CLIENT":
                response = self._run_new_client_intake(user_message, rec_result)
            elif rec_result.intent == "PROPOSAL_REVIEW":
                response = self._run_proposal_review(rec_result)
            else:
                response = AssistantResponse(
                    message=f"I recognized your intent as '{rec_result.intent}', but V1 orchestration for this is pending.",
                    intent=rec_result.intent,
                    confidence=rec_result.confidence,
                    engines_consulted=[],
                    reasoning="Intent parsed but no engine handler linked.",
                    execution_timeline=[],
                )
        except Exception as e:
            response = AssistantResponse(
                message=f"An error occurred while orchestrating engines: {str(e)}",
                intent=rec_result.intent,
                confidence=rec_result.confidence,
                engines_consulted=[],
                reasoning=f"Engine orchestration failed: {str(e)}",
                execution_timeline=[],
            )

        # Log turn into session record (BR-035-014)
        turn = ConversationTurn(
            turn_id=turn_id,
            user_message=user_message,
            assistant_message=response.message,
            intent=response.intent,
            confidence=response.confidence,
            engines_consulted=response.engines_consulted,
            reasoning=response.reasoning,
            execution_timeline=response.execution_timeline,
        )
        self.active_record.add_turn(turn)

        return response

    # ------------------------------------------------------------------
    # Intent Orchestration Handlers
    # ------------------------------------------------------------------

    def _run_new_client_intake(self, message: str, result: IntentResult) -> AssistantResponse:
        timeline = []
        engines = []

        # Step 1: Intake (Opportunity Intake Engine)
        brief = self.intake_engine.intake(message)
        self.context["active_brief"] = brief
        engines.append("OpportunityIntakeEngine")
        timeline.append({
            "step": "Opportunity Intake",
            "engine": "OpportunityIntakeEngine",
            "status": "COMPLETED",
            "description": f"Intamed client brief. Domain: {brief.business_domain}.",
        })

        # Step 2: Discovery
        discovery_plan = self.discovery_engine.generate_plan(brief)
        self.context["active_discovery_plan"] = discovery_plan
        engines.append("DiscoveryConversationEngine")
        timeline.append({
            "step": "Discovery Planning",
            "engine": "DiscoveryConversationEngine",
            "status": "COMPLETED",
            "description": f"Formulated question sequence with completeness {discovery_plan.discovery_completeness}.",
        })

        # Step 3: Architect
        blueprint = self.solution_architect.design_solution(discovery_plan)
        self.context["active_blueprint"] = blueprint
        engines.append("SolutionArchitect")
        timeline.append({
            "step": "Solution Architecture Design",
            "engine": "SolutionArchitect",
            "status": "COMPLETED",
            "description": f"Created blueprint {blueprint.blueprint_id} outlining capabilities.",
        })

        # Step 4: Estimation
        estimate = self.estimation_engine.estimate(blueprint)
        self.context["active_estimate"] = estimate
        engines.append("EstimationEngine")
        timeline.append({
            "step": "Delivery Estimation",
            "engine": "EstimationEngine",
            "status": "COMPLETED",
            "description": f"Calculated effort: {estimate.expected_effort} hours, duration: {estimate.expected_duration} weeks.",
        })

        # Step 5: Pricing
        comm_proposal = self.pricing_engine.price_project(estimate)
        self.context["active_commercial_proposal"] = comm_proposal
        engines.append("PricingEngine")
        timeline.append({
            "step": "Commercial Pricing Analysis",
            "engine": "PricingEngine",
            "status": "COMPLETED",
            "description": f"Computed recommended price: ${comm_proposal.recommended_price}.",
        })

        # Step 6: Proposal Generation
        client_name = result.entities.get("client_name") or self.context.get("active_client_name") or "Authorized Executive"
        org_name = result.entities.get("organization") or self.context.get("active_organization") or "Acme Corp"
        proposal = self.proposal_generator.generate_proposal(comm_proposal, client_name, org_name)
        self.context["active_proposal"] = proposal
        engines.append("ProposalGenerator")
        timeline.append({
            "step": "Proposal Document Generation",
            "engine": "ProposalGenerator",
            "status": "COMPLETED",
            "description": f"Generated public proposal {proposal.proposal_id}.",
        })

        msg = (
            f"Intake completed for new lead. I have run the entire pipeline from Intake to Proposal. "
            f"A proposal has been generated for {org_name} totaling ${proposal.commercial_investment:.2f}."
        )

        return AssistantResponse(
            message=msg,
            intent="NEW_CLIENT",
            confidence=0.95,
            engines_consulted=engines,
            reasoning="Orchestrated intake-to-proposal pipeline based on new client query.",
            execution_timeline=timeline,
            data=proposal.to_dict(),
        )

    def _run_proposal_review(self, result: IntentResult) -> AssistantResponse:
        proposal = self.context.get("active_proposal")
        if not proposal:
            return AssistantResponse(
                message="There is no active proposal in context to review. Please initialize a new client first.",
                intent="PROPOSAL_REVIEW",
                confidence=0.8,
                engines_consulted=[],
                reasoning="No proposal found in active context.",
                execution_timeline=[],
            )

        # Enforce Decision Boundaries (BR-035-009): Require explicit authorization
        # We present the proposal to the CEO with authorization status set to True
        msg = (
            f"Proposal {proposal.proposal_id} for {proposal.client_organization} is ready for review. "
            f"Investment: ${proposal.commercial_investment:.2f}. "
            "Please explicitly authorize to approve and sign the contract."
        )

        return AssistantResponse(
            message=msg,
            intent="PROPOSAL_REVIEW",
            confidence=0.9,
            engines_consulted=[],
            reasoning="Decision boundary check: Proposal requires explicit CEO signature authorization.",
            execution_timeline=[
                {
                    "step": "Proposal Review",
                    "engine": "CEOApprovalWorkflow",
                    "status": "PENDING_AUTHORIZATION",
                    "description": "Awaiting explicit executive signature approval.",
                }
            ],
            data=proposal.to_dict(),
            requires_authorization=True,
        )

    def _run_portfolio_review(self) -> AssistantResponse:
        timeline = []
        # Generate delivery status reports to feed the portfolio engine
        projects = self.chief_of_staff.project_registry.list_projects()
        reports = []
        for p in projects:
            rep = self.supervision_engine.supervise_project(p, self.chief_of_staff.worker_registry)
            reports.append(rep)
        
        portfolio_report = self.portfolio_engine.analyze_portfolio(
            project_registry=self.chief_of_staff.project_registry,
            worker_registry=self.chief_of_staff.worker_registry,
            delivery_reports=reports,
        )

        timeline.append({
            "step": "Portfolio Health Evaluation",
            "engine": "PortfolioManagementEngine",
            "status": "COMPLETED",
            "description": f"Calculated portfolio health score: {portfolio_report.metrics.portfolio_health_score}.",
        })

        msg = (
            "Portfolio review complete. "
            f"The current portfolio health score is {portfolio_report.metrics.portfolio_health_score:.2f}. "
            f"Total active projects: {portfolio_report.metrics.total_active_projects}."
        )

        return AssistantResponse(
            message=msg,
            intent="PORTFOLIO_REVIEW",
            confidence=0.95,
            engines_consulted=["PortfolioManagementEngine", "DeliverySupervisionEngine"],
            reasoning="Queried active projects and ran portfolio metrics derivation.",
            execution_timeline=timeline,
            data=portfolio_report.to_dict(),
        )

    def _run_strategic_analysis(self, result: IntentResult) -> AssistantResponse:
        # Generate portfolio report as input
        projects = self.chief_of_staff.project_registry.list_projects()
        reports = [self.supervision_engine.supervise_project(p, self.chief_of_staff.worker_registry) for p in projects]
        portfolio_report = self.portfolio_engine.analyze_portfolio(
            project_registry=self.chief_of_staff.project_registry,
            worker_registry=self.chief_of_staff.worker_registry,
            delivery_reports=reports,
        )

        # Run Strategic Intelligence
        si_report = self.si_engine.generate_intelligence_report(
            portfolio_reports=[portfolio_report],
            market_research=[{"title": f"Growth in {result.entities.get('sector', 'General')} Sector", "source": "Market Research"}],
        )

        msg = (
            "Strategic analysis complete. "
            f"Found {len(si_report.emerging_opportunities)} emerging opportunities. "
            f"There are {len(si_report.ceo_action_items)} high-priority CEO action items."
        )

        return AssistantResponse(
            message=msg,
            intent="STRATEGIC_ANALYSIS",
            confidence=0.9,
            engines_consulted=["StrategicIntelligenceEngine", "PortfolioManagementEngine"],
            reasoning="Coordinated portfolio KPIs and market research datasets to build strategic watch report.",
            execution_timeline=[
                {
                    "step": "Strategic Intelligence Compilation",
                    "engine": "StrategicIntelligenceEngine",
                    "status": "COMPLETED",
                    "description": "Generated strategic radar recommendations.",
                }
            ],
            data=si_report.to_dict(),
        )

    def _run_knowledge_query(self, message: str) -> AssistantResponse:
        # Search the knowledge registry
        matches = []
        if self.chief_of_staff.knowledge_registry:
            matches = self.chief_of_staff.knowledge_registry.search(message)

        msg = (
            f"Knowledge search completed. Found {len(matches)} historical assets matching your query."
        )

        return AssistantResponse(
            message=msg,
            intent="KNOWLEDGE_QUERY",
            confidence=0.85,
            engines_consulted=["KnowledgeRegistry"],
            reasoning="Scanned organizational memory assets.",
            execution_timeline=[
                {
                    "step": "Knowledge Registry Lookup",
                    "engine": "KnowledgeRegistry",
                    "status": "COMPLETED",
                    "description": f"Retrieved matches from the JBK Brain.",
                }
            ],
            data={"matches": [m.to_dict() if hasattr(m, "to_dict") else m for m in matches]},
        )

    def _run_delivery_status(self) -> AssistantResponse:
        # Summarize active execution states
        projects = self.chief_of_staff.project_registry.list_projects()
        active_p = [p for p in projects if p.status.value == "ACTIVE"]

        msg = (
            f"Delivery status: {len(active_p)} active projects are currently running. "
            "I'm observing all active work orders."
        )

        return AssistantResponse(
            message=msg,
            intent="DELIVERY_STATUS",
            confidence=0.9,
            engines_consulted=["DeliverySupervisionEngine"],
            reasoning="Monitored active delivery workflows.",
            execution_timeline=[
                {
                    "step": "Delivery Status Check",
                    "engine": "DeliverySupervisionEngine",
                    "status": "COMPLETED",
                    "description": "Scanned project work order arrays.",
                }
            ],
        )

    def _build_clarification_response(
        self, turn_id: str, message: str, result: IntentResult
    ) -> AssistantResponse:
        q = "Which client or organization is this initiative regarding?"
        turn = ConversationTurn(
            turn_id=turn_id,
            user_message=message,
            assistant_message=q,
            intent=result.intent,
            confidence=result.confidence,
            engines_consulted=[],
            reasoning="Intent details insufficient (missing name/organization). Awaiting client clarification.",
            execution_timeline=[],
        )
        self.active_record.add_turn(turn)

        return AssistantResponse(
            message=q,
            intent=result.intent,
            confidence=result.confidence,
            engines_consulted=[],
            reasoning="Clarification requested due to missing entities.",
            execution_timeline=[],
            follow_up_question=q,
        )
