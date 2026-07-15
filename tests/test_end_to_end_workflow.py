import unittest
from typing import Any
from datetime import datetime, timezone

# Layer 1: Client Pipeline
from core.opportunity_intake_engine import OpportunityIntakeEngine
from core.opportunity_brief import OpportunityBrief
from core.discovery_conversation_engine import DiscoveryConversationEngine
from core.discovery_plan import DiscoveryPlan
from core.solution_architect import SolutionArchitect
from core.solution_blueprint import SolutionBlueprint
from core.estimation_engine import EstimationEngine
from core.project_estimate import ProjectEstimate
from core.pricing_engine import PricingEngine
from core.commercial_proposal import CommercialProposal
from core.proposal_generator import ProposalGenerator
from core.client_proposal import ClientProposal
from core.ceo_approval_workflow import CEOApprovalWorkflow
from core.approval_decision import ApprovalDecision, ApprovalStatus

# Layer 2: Company Layer & Registries
from core.chief_of_staff import ChiefOfStaff
from core.project_registry import ProjectRegistry
from core.worker_registry import WorkerRegistry
from core.skill_registry import SkillRegistry
from core.knowledge_registry import KnowledgeRegistry
from core.executive import Executive
from core.skill import Skill
from core.project import Project, ProjectStatus
from core.project_initialization_engine import ProjectInitializationEngine
from core.project_initialization_report import ProjectInitializationReport

# Layer 3: Delivery Pipeline
from core.delivery_planning_engine import DeliveryPlanningEngine
from core.delivery_plan import DeliveryPlan
from core.work_breakdown_engine import WorkBreakdownEngine
from core.work_breakdown_structure import WorkBreakdownStructure
from core.resource_allocation_engine import ResourceAllocationEngine
from core.resource_allocation_plan import ResourceAllocationPlan
from core.work_order_generation_engine import WorkOrderGenerationEngine
from core.work_order_generation_report import WorkOrderGenerationReport
from core.work_execution_orchestrator import WorkExecutionOrchestrator
from core.execution_report import ExecutionReport
from core.delivery_supervision_engine import DeliverySupervisionEngine
from core.delivery_status_report import DeliveryStatusReport

# Layer 4: Learning Pipeline
from core.organizational_memory_engine import OrganizationalMemoryEngine
from core.organizational_memory_report import OrganizationalMemoryReport
from core.continuous_improvement_engine import ContinuousImprovementEngine
from core.continuous_improvement_report import ContinuousImprovementReport

# Layer 5: Business Transformation & Portfolio Layer
from core.business_transformation_engine import BusinessTransformationEngine
from core.business_transformation_plan import BusinessTransformationPlan
from core.portfolio_management_engine import PortfolioManagementEngine
from core.portfolio_report import PortfolioReport
from core.strategic_intelligence_engine import StrategicIntelligenceEngine
from core.strategic_intelligence_report import StrategicIntelligenceReport


class MockExecutionPlanner:
    def __init__(self, skill_id: str, engine_name: str) -> None:
        self.skill_id = skill_id
        self.engine_name = engine_name

    def get_recommendation(self, work_order: Any) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "engine_name": self.engine_name,
        }


class TestEndToEndWorkflow(unittest.TestCase):

    def setUp(self) -> None:
        # Initialize Registries
        self.project_registry = ProjectRegistry()
        self.worker_registry = WorkerRegistry()
        self.skill_registry = SkillRegistry()
        self.knowledge_registry = KnowledgeRegistry()

        # Initialize Chief of Staff
        self.chief_of_staff = ChiefOfStaff(
            worker_registry=self.worker_registry,
            project_registry=self.project_registry,
            knowledge_registry=self.knowledge_registry,
        )

        # Register standard workers and their skills for allocation
        self.worker_tech = Executive(
            executive_id="EXEC-0001",
            title="Senior Developer",
            mission="Deliver high-quality software integrations.",
        )
        self.worker_ops = Executive(
            executive_id="EXEC-0002",
            title="Operations Specialist",
            mission="Optimize business processes.",
        )
        self.worker_registry.register(self.worker_tech)
        self.worker_registry.register(self.worker_ops)

        self.skill_tech = Skill(
            skill_id="SKL-0001",
            name="API & Backend Development",
            description="Integration of REST APIs and Postgres DBs.",
            owner_id="EXEC-0001",
            department="Technology",
            execution_engine="Python",
            capabilities=["Web Development", "API Integration", "Database Migration"],
            inputs=[],
            outputs=[],
            version="1.0"
        )
        self.skill_ops = Skill(
            skill_id="SKL-0002",
            name="Workflow Optimization",
            description="Process Mapping and Training.",
            owner_id="EXEC-0002",
            department="Operations",
            execution_engine="Manual",
            capabilities=["Training", "Operations Management"],
            inputs=[],
            outputs=[],
            version="1.0"
        )
        self.skill_registry.register(self.skill_tech)
        self.skill_registry.register(self.skill_ops)

        self.planner = MockExecutionPlanner(skill_id="SKL-0001", engine_name="Antigravity")

    def test_complete_client_lifecycle_integration(self) -> None:
        """Runs the entire JBK-OS lifecycle end-to-end and validates outputs flow cleanly."""
        
        # 1. Opportunity Intake
        intake_engine = OpportunityIntakeEngine()
        client_req = (
            "We need a new PostgreSQL database migrated to AWS. "
            "Timeline: under 6 weeks. "
            "Budget is $50,000. "
            "Contact: Alice (alice@jbk.tech)."
        )
        brief = intake_engine.intake(client_req)
        self.assertIsInstance(brief, OpportunityBrief)
        self.assertEqual(brief.business_domain, "Technology")
        self.assertGreaterEqual(brief.confidence_score, 0.8)

        # 2. Discovery Conversation
        discovery_engine = DiscoveryConversationEngine()
        discovery_plan = discovery_engine.generate_plan(brief)
        self.assertIsInstance(discovery_plan, DiscoveryPlan)
        self.assertEqual(discovery_plan.opportunity_id, brief.opportunity_id)
        # Ensure questions were generated
        self.assertGreater(len(discovery_plan.recommended_question_sequence), 0)

        # 3. Solution Architecture
        solution_architect = SolutionArchitect()
        blueprint = solution_architect.design_solution(discovery_plan)
        self.assertIsInstance(blueprint, SolutionBlueprint)
        self.assertEqual(blueprint.opportunity_id, brief.opportunity_id)
        self.assertIn("Data Migration", blueprint.required_capabilities)

        # 4. Project Estimation
        estimation_engine = EstimationEngine()
        estimate = estimation_engine.estimate(blueprint)
        self.assertIsInstance(estimate, ProjectEstimate)
        self.assertEqual(estimate.blueprint_id, blueprint.blueprint_id)
        self.assertGreater(estimate.expected_effort, 0)

        # 5. Pricing
        pricing_engine = PricingEngine()
        comm_proposal = pricing_engine.price_project(estimate)
        self.assertIsInstance(comm_proposal, CommercialProposal)
        self.assertEqual(comm_proposal.estimate_id, estimate.estimate_id)
        self.assertGreater(comm_proposal.recommended_price, 0)

        # 6. Proposal Generation
        proposal_generator = ProposalGenerator()
        client_proposal = proposal_generator.generate_proposal(
            comm_proposal, client_name="Alice", client_organization="Acme Corp"
        )
        self.assertIsInstance(client_proposal, ClientProposal)
        self.assertEqual(client_proposal.proposal_id, comm_proposal.proposal_id)

        # Inject references needed for downstream initialization report matching
        setattr(client_proposal, "estimate_id", estimate.estimate_id)
        setattr(client_proposal, "blueprint_id", blueprint.blueprint_id)
        setattr(client_proposal, "discovery_plan_id", discovery_plan.discovery_id)
        setattr(client_proposal, "opportunity_id", brief.opportunity_id)

        # 7. CEO Approval
        approval_workflow = CEOApprovalWorkflow()
        decision = approval_workflow.submit_for_review(client_proposal)
        self.assertIsInstance(decision, ApprovalDecision)
        self.assertEqual(decision.status, ApprovalStatus.PENDING_REVIEW)

        approval_workflow.approve(
            decision=decision,
            decision_maker="CEO-John",
            comments="Looks great. Proceeding with database setup.",
        )
        self.assertEqual(decision.status, ApprovalStatus.APPROVED)

        # 8. Project Initialization
        init_engine = ProjectInitializationEngine()
        init_report = init_engine.initialize_project(
            client_proposal, decision, self.chief_of_staff
        )
        self.assertEqual(init_report.status, "INITIALIZED")
        
        # Verify project registered
        project = self.project_registry.find_by_id(init_report.project_id)
        self.assertIsNotNone(project)
        self.assertEqual(project.status, ProjectStatus.ACTIVE)

        # 9. Delivery Planning
        planning_engine = DeliveryPlanningEngine()
        proj_details = {
            "title": project.title,
            "complexity": blueprint.estimated_complexity,
            "domain": brief.business_domain,
        }
        delivery_plan = planning_engine.generate_delivery_plan(project.id, proj_details)
        self.assertIsInstance(delivery_plan, DeliveryPlan)
        self.assertEqual(delivery_plan.project_id, project.id)

        # 10. Work Breakdown Structure
        wbs_engine = WorkBreakdownEngine()
        wbs = wbs_engine.generate_wbs(delivery_plan)
        self.assertIsInstance(wbs, WorkBreakdownStructure)
        self.assertEqual(wbs.project_id, project.id)

        # 11. Resource Allocation
        allocation_engine = ResourceAllocationEngine()
        allocation_plan = allocation_engine.allocate_resources(
            wbs, self.worker_registry, self.skill_registry
        )
        self.assertIsInstance(allocation_plan, ResourceAllocationPlan)
        self.assertEqual(allocation_plan.project_id, project.id)

        # 12. Work Order Generation
        wog_engine = WorkOrderGenerationEngine()
        wog_report = wog_engine.generate_work_orders(
            project, allocation_plan, self.chief_of_staff
        )
        self.assertIsInstance(wog_report, WorkOrderGenerationReport)
        self.assertEqual(wog_report.project_id, project.id)
        self.assertGreater(len(project.work_orders), 0)

        # 13. Execution Orchestration
        orchestrator = WorkExecutionOrchestrator()
        exec_reports: list[ExecutionReport] = []
        for wo in project.work_orders:
            exec_report = orchestrator.execute_work_order(
                wo, project, self.skill_registry, self.planner, self.chief_of_staff
            )
            self.assertIsInstance(exec_report, ExecutionReport)
            self.assertEqual(exec_report.status, "COMPLETED")
            exec_reports.append(exec_report)

        # 14. Delivery Supervision
        supervision_engine = DeliverySupervisionEngine()
        delivery_report = supervision_engine.supervise_project(
            project, self.worker_registry
        )
        self.assertIsInstance(delivery_report, DeliveryStatusReport)
        self.assertEqual(delivery_report.project_id, project.id)

        # 15. Knowledge Capture (Organizational Memory Engine)
        memory_engine = OrganizationalMemoryEngine()
        # Transition project to COMPLETED to meet archiving business rule BR-030-001
        project.update_status(ProjectStatus.COMPLETED, actor="chief_of_staff")
        
        memory_report = memory_engine.archive_project(
            project=project,
            chief_of_staff=self.chief_of_staff,
            delivery_report=delivery_report,
            execution_reports=exec_reports,
            blueprint=blueprint,
        )
        self.assertIsInstance(memory_report, OrganizationalMemoryReport)

        # 16. Continuous Improvement
        ci_engine = ContinuousImprovementEngine()
        ci_report = ci_engine.analyze(
            knowledge_registry=self.knowledge_registry
        )
        self.assertIsInstance(ci_report, ContinuousImprovementReport)

        # 17. Business Transformation
        bt_engine = BusinessTransformationEngine()
        bt_plan = bt_engine.transform(
            blueprint=blueprint,
            estimate=estimate,
            proposal=comm_proposal,
            discovery_plan=discovery_plan,
        )
        self.assertIsInstance(bt_plan, BusinessTransformationPlan)

        # 18. Portfolio Management
        portfolio_engine = PortfolioManagementEngine()
        portfolio_report = portfolio_engine.analyze_portfolio(
            project_registry=self.project_registry,
            worker_registry=self.worker_registry,
            delivery_reports=[delivery_report],
            allocation_plans=[allocation_plan],
            transformation_plans=[bt_plan],
        )
        self.assertIsInstance(portfolio_report, PortfolioReport)

        # 19. Strategic Intelligence
        si_engine = StrategicIntelligenceEngine()
        si_report = si_engine.generate_report=si_engine.generate_intelligence_report(
            organizational_knowledge=memory_report.knowledge_assets,
            portfolio_reports=[portfolio_report],
        )
        self.assertIsInstance(si_report, StrategicIntelligenceReport)
        self.assertEqual(si_report.report_id.startswith("SIR-"), True)

        # Serialization Verification
        self.assertIsNotNone(portfolio_report.to_dict())
        self.assertIsNotNone(si_report.to_dict())
        self.assertIsNotNone(bt_plan.to_dict())
        self.assertIsNotNone(delivery_report.to_dict())
        self.assertIsNotNone(init_report.to_dict())
