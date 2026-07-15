import unittest

from core.solution_blueprint import SolutionBlueprint
from core.project_estimate import ProjectEstimate
from core.estimation_engine import EstimationEngine


class TestEstimationEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = EstimationEngine()
        
        # Mock solution blueprints
        self.bp_small = SolutionBlueprint(
            blueprint_id="BLP-0001",
            opportunity_id="OPP-0001",
            discovery_plan_id="DSC-0001",
            client_summary="Client summary small",
            business_problem="crashes",
            root_cause_analysis={
                "symptoms": ["crashes"],
                "business_constraints": [],
                "technical_constraints": [],
                "operational_constraints": []
            },
            business_objectives=[],
            proposed_solution_options=[],
            recommended_solution={"title": "Small fix", "description": "Quick fix description"},
            business_benefits=[],
            technical_considerations=[],
            required_capabilities=["API Integration"], # 1 cap + 1 symptom = 2 score (Low complexity)
            required_skills=[],
            required_departments=["Technology"],
            estimated_complexity="Low",
            risks=[],
            assumptions=[],
            dependencies=[],
            success_metrics=[],
            executive_recommendation="Recommendation",
            confidence_score=0.8,
        )

        self.bp_enterprise = SolutionBlueprint(
            blueprint_id="BLP-0002",
            opportunity_id="OPP-0002",
            discovery_plan_id="DSC-0002",
            client_summary="Client summary large",
            business_problem="Multiple errors and slow throughput across systems",
            root_cause_analysis={
                "symptoms": ["slow throughput", "errors", "data leakage"],
                "business_constraints": ["Budget is tight", "Tax compliance requirements"],
                "technical_constraints": ["Must use Python", "Must host on AWS"],
                "operational_constraints": ["Must complete in Q3"]
            },
            business_objectives=[],
            proposed_solution_options=[],
            recommended_solution={"title": "Enterprise Solution", "description": "Large platform description"},
            business_benefits=[],
            technical_considerations=[],
            required_capabilities=["API Integration", "AI Automation", "Data Migration", "UX Design"], # 3 symptoms + 5 constraints + 4 caps = 12 score (Enterprise complexity)
            required_skills=[],
            required_departments=["Technology", "Operations"],
            estimated_complexity="High",
            risks=[],
            assumptions=[],
            dependencies=[],
            success_metrics=[],
            executive_recommendation="Recommendation",
            confidence_score=1.0,
        )

    def test_invalid_estimate_inputs(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.estimate(None)  # type: ignore

    def test_estimate_small_project(self) -> None:
        est = self.engine.estimate(self.bp_small)
        self.assertIsInstance(est, ProjectEstimate)
        self.assertEqual(est.delivery_complexity, "Low")
        self.assertEqual(est.expected_duration, 2.0)  # Low expected duration is 2.0 weeks
        self.assertEqual(est.expected_effort, 80.0)  # Low expected effort is 80.0 hours
        self.assertEqual(est.best_case_duration, 1.5)  # 2.0 * 0.75
        self.assertEqual(est.worst_case_duration, 3.0)  # 2.0 * 1.5
        self.assertEqual(est.delivery_strategy, "Kanban (Justification: Low complexity is best suited for visual task boards.)")
        
        # Risk buffer: Low -> 10%
        self.assertEqual(est.risk_buffer["percentage"], 10.0)
        self.assertEqual(est.risk_buffer["additional_duration_weeks"], 0.2)
        
        # Milestones: No Prototype Approved for Low complexity
        self.assertNotIn("Prototype Approved", est.major_milestones)

    def test_estimate_enterprise_project(self) -> None:
        est = self.engine.estimate(self.bp_enterprise)
        self.assertEqual(est.delivery_complexity, "Enterprise")
        self.assertEqual(est.expected_duration, 24.0)  # Enterprise expected duration is 24.0 weeks
        self.assertEqual(est.expected_effort, 960.0)  # Enterprise expected effort is 960.0 hours
        self.assertEqual(est.delivery_strategy, "Waterfall (Justification: Strict compliance and vast deployment bounds require phase-gated execution.)")
        
        # Risk buffer: Enterprise -> 30%
        self.assertEqual(est.risk_buffer["percentage"], 30.0)
        self.assertEqual(est.risk_buffer["additional_duration_weeks"], 7.2)
        
        # Milestones: Includes Prototype Approved
        self.assertIn("Prototype Approved", est.major_milestones)

    def test_serialization(self) -> None:
        est = self.engine.estimate(self.bp_small)
        summary = est.summary()
        self.assertEqual(summary["estimate_id"], est.estimate_id)
        self.assertEqual(summary["delivery_complexity"], "Low")
        
        to_dict_out = est.to_dict()
        self.assertEqual(to_dict_out["estimate_id"], est.estimate_id)
        self.assertEqual(to_dict_out["blueprint_id"], "BLP-0001")
        self.assertIsNotNone(to_dict_out["risk_buffer"])
