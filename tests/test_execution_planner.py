import unittest

from core.execution_planner import ExecutionPlanner, ExecutionPlan, PlanningStatus
from core.skill import Skill, SkillStatus
from core.skill_registry import SkillRegistry
from core.work_order import WorkOrder


class TestExecutionPlanner(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = SkillRegistry()
        self.planner = ExecutionPlanner(self.registry)
        
        # Register a few mock skills
        self.skill_postgres = Skill(
            skill_id="SKL-0001",
            name="Postgres Deploy",
            description="Deploys postgres db",
            owner_id="EXEC-0002",
            department="Operations",
            execution_engine="Antigravity",
            capabilities=["postgres", "database"],
            inputs=["config"],
            outputs=["connection"],
            version="1.0",
        )
        self.skill_mysql = Skill(
            skill_id="SKL-0002",
            name="MySQL Deploy",
            description="Deploys mysql db",
            owner_id="EXEC-0002",
            department="Operations",
            execution_engine="Antigravity",
            capabilities=["mysql", "database"],
            inputs=["config"],
            outputs=["connection"],
            version="1.0",
            status=SkillStatus.BUSY, # Not AVAILABLE
        )
        self.skill_generic_db = Skill(
            skill_id="SKL-0003",
            name="Generic DB Installer",
            description="Deploys general database configurations",
            owner_id="EXEC-0003",
            department="Operations",
            execution_engine="Antigravity",
            capabilities=["database"],
            inputs=["config"],
            outputs=["connection"],
            version="1.0",
        )
        
        self.registry.register(self.skill_postgres)
        self.registry.register(self.skill_mysql)
        self.registry.register(self.skill_generic_db)

    def test_instantiation_without_skill_registry(self) -> None:
        with self.assertRaises(ValueError):
            ExecutionPlanner(None)

    def test_plan_id_sequential_generation(self) -> None:
        p1 = self.planner._generate_plan_id()
        p2 = self.planner._generate_plan_id()
        self.assertEqual(p1, "PLN-0001")
        self.assertEqual(p2, "PLN-0002")

    def test_execution_plan_serialization(self) -> None:
        plan = ExecutionPlan(
            plan_id="PLN-0001",
            work_order_id="WO-0001",
            recommended_skill_id="SKL-0001",
            execution_engine="Antigravity",
            confidence_score=0.9,
            reasoning="Perfect match",
            alternative_skills=["SKL-0003"],
        )
        
        summary = plan.summary()
        self.assertEqual(summary["plan_id"], "PLN-0001")
        self.assertEqual(summary["confidence_score"], 0.9)
        self.assertNotIn("reasoning", summary)

        full_dict = plan.to_dict()
        self.assertEqual(full_dict["reasoning"], "Perfect match")
        self.assertEqual(full_dict["alternative_skills"], ["SKL-0003"])

    def test_identify_capabilities(self) -> None:
        wo = WorkOrder(
            project_id="PROJ-0001",
            title="Install postgres",
            objective="Make sure the postgres database server runs.",
            work_order_id="WO-0001",
        )
        caps = self.planner.identify_capabilities(wo)
        self.assertIn("postgres", caps)
        self.assertIn("database", caps)

    def test_successful_planning_with_ranking(self) -> None:
        # Requesting "postgres" and "database"
        wo = WorkOrder(
            project_id="PROJ-0001",
            title="Deploy Postgres Database server",
            objective="Ensure postgres runs.",
            work_order_id="WO-0001",
        )
        initial_status = wo.status
        
        plan = self.planner.generate_plan(wo)
        
        # Verify no direct mutation of business object WorkOrder
        self.assertEqual(wo.status, initial_status)
        
        self.assertEqual(self.planner.status, PlanningStatus.READY)
        self.assertEqual(plan.status, PlanningStatus.READY)
        
        # SKL-0001 (Postgres Deploy) matches both 'postgres' and 'database', so it should rank highest.
        # SKL-0002 (MySQL Deploy) is BUSY, so it cannot be recommended.
        # SKL-0003 (Generic DB Installer) matches only 'database', so it should be the alternative.
        self.assertEqual(plan.recommended_skill_id, "SKL-0001")
        self.assertEqual(plan.alternative_skills, ["SKL-0003"])
        self.assertEqual(plan.confidence_score, 1.0) # Matches all found capabilities

    def test_graceful_failure_no_matching_capabilities(self) -> None:
        wo = WorkOrder(
            project_id="PROJ-0001",
            title="Paint the wall",
            objective="Make it blue",
            work_order_id="WO-0002",
        )
        plan = self.planner.generate_plan(wo)
        self.assertEqual(plan.status, PlanningStatus.FAILED)
        self.assertEqual(self.planner.status, PlanningStatus.FAILED)
        self.assertIsNone(plan.recommended_skill_id)
        self.assertEqual(plan.confidence_score, 0.0)

    def test_graceful_failure_no_available_skills(self) -> None:
        # Request mysql database - only skill_mysql has 'mysql', but it is BUSY
        wo = WorkOrder(
            project_id="PROJ-0001",
            title="Setup mysql server",
            objective="Setup mysql db",
            work_order_id="WO-0003",
        )
        # Temporarily disable generic database skill too so only mysql matches but is unavailable
        self.skill_generic_db.update_status(SkillStatus.DISABLED)
        
        plan = self.planner.generate_plan(wo)
        self.assertEqual(plan.status, PlanningStatus.FAILED)
        self.assertEqual(self.planner.status, PlanningStatus.FAILED)
        self.assertIsNone(plan.recommended_skill_id)
        self.assertEqual(plan.confidence_score, 0.0)

    def test_planner_serialization(self) -> None:
        wo = WorkOrder(
            project_id="PROJ-0001",
            title="Deploy Postgres Database server",
            objective="Ensure postgres runs.",
            work_order_id="WO-0001",
        )
        self.planner.generate_plan(wo)
        
        summary = self.planner.summary()
        self.assertEqual(summary["status"], "READY")
        self.assertEqual(summary["last_capabilities_count"], 2)
        
        full_dict = self.planner.to_dict()
        self.assertEqual(full_dict["status"], "READY")
        self.assertEqual(full_dict["last_capabilities"], self.planner.last_capabilities)
        self.assertIsNotNone(full_dict["last_plan"])
