import unittest

from core.solution_blueprint import SolutionBlueprint
from core.project_estimate import ProjectEstimate
from core.commercial_proposal import CommercialProposal
from core.discovery_plan import DiscoveryPlan
from core.organizational_knowledge import (
    KnowledgeCategory,
    KnowledgeConfidence,
    OrganizationalKnowledge,
)
from core.business_transformation_plan import (
    KPI,
    TransformationObjective,
    ChangeImpact,
    AdoptionPhase,
    BusinessTransformationPlan,
)
from core.business_transformation_engine import BusinessTransformationEngine


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

def _make_blueprint(
    blueprint_id: str = "BP-001",
    business_objectives: list[str] | None = None,
    success_metrics: list[str] | None = None,
    departments: list[str] | None = None,
    risks: list[str] | None = None,
    complexity: str = "High",
) -> SolutionBlueprint:
    _SENTINEL = object()  # not used; we use None as sentinel directly
    return SolutionBlueprint(
        blueprint_id=blueprint_id,
        opportunity_id=None,
        discovery_plan_id="DP-001",
        client_summary="Ministry of Education needs a digital platform.",
        business_problem="Manual record management is slow and error-prone.",
        root_cause_analysis={"cause": "Paper-based processes"},
        business_objectives=(
            ["Digitize all student records", "Automate reporting to reduce manual effort by 80%"]
            if business_objectives is None else business_objectives
        ),
        proposed_solution_options=[{"title": "SaaS Platform"}],
        recommended_solution={"title": "SaaS Platform", "approach": "Cloud-first"},
        business_benefits=["Efficiency gains", "Cost reduction", "Data accuracy"],
        technical_considerations=["Data migration", "System integration", "Security hardening"],
        required_capabilities=["cloud", "API", "reporting"],
        required_skills=["Python", "React", "PostgreSQL"],
        required_departments=(
            ["Engineering", "Operations", "HR"]
            if departments is None else departments
        ),
        estimated_complexity=complexity,
        risks=(
            ["Scope creep", "Data migration risk", "Change resistance"]
            if risks is None else risks
        ),
        assumptions=["Internet connectivity available", "Client IT team available"],
        dependencies=["Existing MIS data export", "Network infrastructure"],
        success_metrics=(
            [
                "Zero paper-based records by Q4",
                "99.9% system uptime",
                "80% reduction in manual reporting time",
            ]
            if success_metrics is None else success_metrics
        ),
        executive_recommendation="Proceed immediately with SaaS-first delivery.",
        confidence_score=0.88,
    )


def _make_estimate() -> ProjectEstimate:
    return ProjectEstimate(
        estimate_id="EST-001",
        blueprint_id="BP-001",
        client_summary="Ministry of Education",
        solution_summary="SaaS platform delivery",
        delivery_complexity="High",
        estimated_duration="16 weeks",
        estimated_effort="1200 hours",
        best_case_duration=12.0,
        expected_duration=16.0,
        worst_case_duration=22.0,
        best_case_effort=900.0,
        expected_effort=1200.0,
        worst_case_effort=1600.0,
        required_departments=["Engineering", "QA", "Operations"],
        required_executive_roles=["Project Manager", "Tech Lead"],
        required_skills=["Python", "React"],
        required_capabilities=["cloud", "API"],
        resource_requirements={"engineers": 3, "qa": 1},
        delivery_strategy="Agile",
        major_milestones=["Kickoff & Discovery", "Core Build", "UAT", "Go-Live"],
        critical_dependencies=["Client data export"],
        risk_buffer={"weeks": 3, "hours": 200},
        key_assumptions=["Client availability for weekly reviews"],
        known_constraints=["Fixed budget", "Q4 deadline"],
        confidence_score=0.82,
        executive_notes="Buffer recommended due to data migration complexity.",
    )


def _make_proposal() -> CommercialProposal:
    return CommercialProposal(
        proposal_id="PROP-001",
        estimate_id="EST-001",
        client_summary="Ministry of Education",
        project_summary="SaaS platform",
        commercial_strategy="Value-Based",
        conservative_price=85000.0,
        recommended_price=110000.0,
        premium_price=140000.0,
        expected_gross_margin=0.42,
        pricing_rationale="Value-based pricing aligned to digitization ROI.",
        commercial_risks=[
            {"risk": "Budget approval delay", "severity": "HIGH",
             "mitigation": "Secure provisional approval before project start."},
            {"risk": "Scope expansion", "severity": "MEDIUM"},
        ],
        payment_structure="Milestone Payments",
        payment_milestones=[{"milestone": "Kickoff", "amount": 30000}],
        maintenance_recommendation="12-month maintenance contract recommended.",
        support_recommendation="Tier 2 support SLA.",
        warranty_recommendation="90-day warranty period.",
        licensing_recommendation="Per-seat SaaS licensing.",
        optional_services=[{"service": "Training", "price": 5000}],
        commercial_assumptions=["Exchange rate stability"],
        negotiation_notes={"floor_price": 80000},
        executive_recommendation="Strong commercial case. Proceed.",
        confidence_score=0.85,
    )


def _make_discovery_plan() -> DiscoveryPlan:
    return DiscoveryPlan(
        discovery_id="DP-001",
        opportunity_id="OPP-001",
        conversation_objective="Understand digitization goals",
        information_already_known=["Client uses paper records", "Has 5000 students"],
        information_still_required=["IT infrastructure details", "Budget ceiling"],
        recommended_question_sequence=[{"question": "What is the primary pain point?"}],
        conversation_categories=["Records Management", "Reporting", "HR Processes"],
        discovery_completeness=0.75,
        confidence_score=0.80,
        recommended_next_step="Deep-dive technical workshop",
    )


def _make_knowledge() -> OrganizationalKnowledge:
    return OrganizationalKnowledge(
        knowledge_id="KN-000001",
        title="Prior Education Project",
        category=KnowledgeCategory.EDUCATION,
        source_project_ids=["PROJ-0001"],
        lessons_learned=[],
        best_practices=[],
        reusable_assets=[],
        patterns=[],
        future_recommendations=[
            "Always run a change readiness assessment before go-live.",
            "Involve IT department from Day 1.",
        ],
    )


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------

class TestBusinessTransformationEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = BusinessTransformationEngine()

    # ------------------------------------------------------------------
    # Input Validation
    # ------------------------------------------------------------------

    def test_rejects_none_blueprint(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.transform(None)  # type: ignore

    def test_minimal_transform_blueprint_only(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        self.assertIsInstance(plan, BusinessTransformationPlan)

    # ------------------------------------------------------------------
    # Plan ID Format
    # ------------------------------------------------------------------

    def test_plan_id_format(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        self.assertTrue(plan.plan_id.startswith("BTP-"), f"Expected BTP- prefix, got {plan.plan_id}")

    def test_incrementing_plan_ids(self) -> None:
        engine = BusinessTransformationEngine()
        bp = _make_blueprint()
        p1 = engine.transform(bp)
        p2 = engine.transform(bp)
        self.assertNotEqual(p1.plan_id, p2.plan_id)

    def test_plan_references_blueprint_id(self) -> None:
        bp = _make_blueprint("BP-CUSTOM")
        plan = self.engine.transform(bp)
        self.assertEqual(plan.blueprint_id, "BP-CUSTOM")

    # ------------------------------------------------------------------
    # Transformation Objectives
    # ------------------------------------------------------------------

    def test_objectives_created_per_business_goal(self) -> None:
        bp = _make_blueprint(business_objectives=["Goal A", "Goal B", "Goal C"])
        plan = self.engine.transform(bp)
        self.assertEqual(len(plan.transformation_objectives), 3)

    def test_objectives_link_to_business_goals(self) -> None:
        bp = _make_blueprint(business_objectives=["Digitize student records"])
        plan = self.engine.transform(bp)
        obj = plan.transformation_objectives[0]
        self.assertIn("Digitize student records", obj.linked_business_goals)

    def test_objectives_have_success_criteria(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        for obj in plan.transformation_objectives:
            self.assertGreater(len(obj.success_criteria), 0)

    def test_objective_id_format(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        for obj in plan.transformation_objectives:
            self.assertTrue(obj.objective_id.startswith("OBJ-"))

    def test_empty_objectives_when_no_business_goals(self) -> None:
        bp = _make_blueprint(business_objectives=[])
        plan = self.engine.transform(bp)
        self.assertEqual(len(plan.transformation_objectives), 0)

    # ------------------------------------------------------------------
    # KPI Dashboard
    # ------------------------------------------------------------------

    def test_kpis_derived_from_success_metrics(self) -> None:
        bp = _make_blueprint(success_metrics=["99.9% uptime", "80% manual effort reduction"])
        plan = self.engine.transform(bp)
        self.assertEqual(len(plan.kpi_dashboard), 2)

    def test_kpis_have_measurement_method(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        for kpi in plan.kpi_dashboard:
            self.assertTrue(kpi.measurement_method, f"KPI '{kpi.name}' has no measurement_method")

    def test_kpis_have_target_value(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        for kpi in plan.kpi_dashboard:
            self.assertTrue(kpi.target_value, f"KPI '{kpi.name}' has no target_value")

    def test_kpi_id_format(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        for kpi in plan.kpi_dashboard:
            self.assertTrue(kpi.kpi_id.startswith("KPI-"))

    def test_default_kpi_when_no_success_metrics(self) -> None:
        bp = _make_blueprint(success_metrics=[])
        plan = self.engine.transform(bp)
        self.assertEqual(len(plan.kpi_dashboard), 1)
        self.assertEqual(plan.kpi_dashboard[0].unit, "%")

    def test_kpi_timeframe_uses_estimate_duration(self) -> None:
        bp = _make_blueprint()
        est = _make_estimate()
        plan = self.engine.transform(bp, estimate=est)
        for kpi in plan.kpi_dashboard:
            self.assertIn("16 weeks", kpi.timeframe)

    def test_uptime_metric_infers_monitoring_method(self) -> None:
        bp = _make_blueprint(success_metrics=["99.9% uptime"])
        plan = self.engine.transform(bp)
        kpi = plan.kpi_dashboard[0]
        self.assertIn("monitoring", kpi.measurement_method.lower())

    def test_cost_metric_infers_financial_method(self) -> None:
        bp = _make_blueprint(success_metrics=["30% cost saving"])
        plan = self.engine.transform(bp)
        kpi = plan.kpi_dashboard[0]
        self.assertIn("financial", kpi.measurement_method.lower())

    # ------------------------------------------------------------------
    # Department Impact Analysis
    # ------------------------------------------------------------------

    def test_department_impact_per_required_dept(self) -> None:
        bp = _make_blueprint(departments=["Engineering", "Operations", "HR"])
        plan = self.engine.transform(bp)
        self.assertEqual(len(plan.department_impact_analysis), 3)
        dept_names = [d.department for d in plan.department_impact_analysis]
        self.assertIn("Engineering", dept_names)
        self.assertIn("Operations", dept_names)
        self.assertIn("HR", dept_names)

    def test_impact_id_format(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        for impact in plan.department_impact_analysis:
            self.assertTrue(impact.impact_id.startswith("IMP-"))

    def test_high_complexity_yields_high_impact_level(self) -> None:
        bp = _make_blueprint(complexity="High")
        plan = self.engine.transform(bp)
        for impact in plan.department_impact_analysis:
            self.assertEqual(impact.impact_level, "HIGH")

    def test_non_high_complexity_yields_medium_impact(self) -> None:
        bp = _make_blueprint(complexity="Medium")
        plan = self.engine.transform(bp)
        for impact in plan.department_impact_analysis:
            self.assertEqual(impact.impact_level, "MEDIUM")

    def test_impacts_have_readiness_actions(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        for impact in plan.department_impact_analysis:
            self.assertGreater(len(impact.readiness_actions), 0)

    def test_no_impact_when_no_departments(self) -> None:
        bp = _make_blueprint(departments=[])
        plan = self.engine.transform(bp)
        self.assertEqual(len(plan.department_impact_analysis), 0)

    # ------------------------------------------------------------------
    # Adoption Strategy
    # ------------------------------------------------------------------

    def test_adoption_phases_from_milestones(self) -> None:
        bp = _make_blueprint()
        est = _make_estimate()  # has 4 milestones
        plan = self.engine.transform(bp, estimate=est)
        self.assertEqual(len(plan.adoption_strategy), 4)

    def test_adoption_phase_names_match_milestones(self) -> None:
        bp = _make_blueprint()
        est = _make_estimate()
        plan = self.engine.transform(bp, estimate=est)
        phase_names = [p.name for p in plan.adoption_strategy]
        self.assertIn("Kickoff & Discovery", phase_names)
        self.assertIn("Go-Live", phase_names)

    def test_adoption_phases_sequential(self) -> None:
        bp = _make_blueprint()
        est = _make_estimate()
        plan = self.engine.transform(bp, estimate=est)
        sequences = [p.sequence for p in plan.adoption_strategy]
        self.assertEqual(sequences, sorted(sequences))

    def test_fallback_three_phase_when_no_estimate(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        self.assertEqual(len(plan.adoption_strategy), 3)
        names = [p.name for p in plan.adoption_strategy]
        self.assertIn("Pilot", names)
        self.assertIn("Rollout", names)
        self.assertIn("Full Adoption", names)

    def test_fallback_three_phase_when_no_milestones(self) -> None:
        bp = _make_blueprint()
        est = _make_estimate()
        est.major_milestones = []
        plan = self.engine.transform(bp, estimate=est)
        self.assertEqual(len(plan.adoption_strategy), 3)

    def test_phase_id_format(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        for phase in plan.adoption_strategy:
            self.assertTrue(phase.phase_id.startswith("PHS-"))

    # ------------------------------------------------------------------
    # Risk Register
    # ------------------------------------------------------------------

    def test_risk_register_from_blueprint_risks(self) -> None:
        bp = _make_blueprint(risks=["Scope creep", "Data migration risk"])
        plan = self.engine.transform(bp)
        risk_titles = [r["risk"] for r in plan.risk_register]
        self.assertIn("Scope creep", risk_titles)
        self.assertIn("Data migration risk", risk_titles)

    def test_all_risks_have_mitigations(self) -> None:
        bp = _make_blueprint()
        prop = _make_proposal()
        plan = self.engine.transform(bp, proposal=prop)
        for risk in plan.risk_register:
            self.assertIn("mitigation", risk, f"Risk '{risk.get('risk')}' has no mitigation")
            self.assertTrue(risk["mitigation"])

    def test_commercial_risks_included_from_proposal(self) -> None:
        bp = _make_blueprint()
        prop = _make_proposal()
        plan = self.engine.transform(bp, proposal=prop)
        risk_titles = [r["risk"] for r in plan.risk_register]
        self.assertIn("Budget approval delay", risk_titles)

    def test_commercial_risk_inherits_mitigation(self) -> None:
        bp = _make_blueprint()
        prop = _make_proposal()
        plan = self.engine.transform(bp, proposal=prop)
        budget_risk = next(r for r in plan.risk_register if r["risk"] == "Budget approval delay")
        self.assertIn("Secure provisional approval", budget_risk["mitigation"])

    def test_empty_risks_no_crash(self) -> None:
        bp = _make_blueprint(risks=[])
        plan = self.engine.transform(bp)
        self.assertEqual(len(plan.risk_register), 0)

    # ------------------------------------------------------------------
    # Process Changes
    # ------------------------------------------------------------------

    def test_process_changes_from_technical_considerations(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        self.assertGreater(len(plan.process_changes), 0)
        processes = [c["process"] for c in plan.process_changes]
        self.assertIn("Data migration", processes)

    def test_process_changes_from_discovery_categories(self) -> None:
        bp = _make_blueprint()
        dp = _make_discovery_plan()
        plan = self.engine.transform(bp, discovery_plan=dp)
        processes = [c["process"] for c in plan.process_changes]
        self.assertTrue(any("Records Management" in p for p in processes))

    # ------------------------------------------------------------------
    # Change Management Plan
    # ------------------------------------------------------------------

    def test_change_management_from_estimate_strategy(self) -> None:
        bp = _make_blueprint()
        est = _make_estimate()
        plan = self.engine.transform(bp, estimate=est)
        self.assertEqual(plan.change_management_plan["strategy"], "Agile")

    def test_change_management_has_communication_plan(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        self.assertIn("communication_plan", plan.change_management_plan)
        self.assertIn("channels", plan.change_management_plan["communication_plan"])

    def test_change_management_defaults_without_estimate(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        # Should default gracefully
        self.assertIn("strategy", plan.change_management_plan)
        self.assertTrue(plan.change_management_plan["strategy"])

    # ------------------------------------------------------------------
    # Training Plan
    # ------------------------------------------------------------------

    def test_training_plan_populated(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        tp = plan.training_plan
        self.assertIn("required_skills", tp)
        self.assertIn("required_capabilities", tp)
        self.assertGreater(len(tp["required_skills"]), 0)

    def test_training_plan_has_schedule(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        self.assertIn("training_schedule", plan.training_plan)

    # ------------------------------------------------------------------
    # Executive Recommendations
    # ------------------------------------------------------------------

    def test_executive_recommendations_from_blueprint(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        combined = " ".join(plan.executive_recommendations)
        self.assertIn("SaaS-first", combined)

    def test_executive_recommendations_from_proposal(self) -> None:
        bp = _make_blueprint()
        prop = _make_proposal()
        plan = self.engine.transform(bp, proposal=prop)
        combined = " ".join(plan.executive_recommendations)
        self.assertIn("Strong commercial case", combined)

    def test_historical_knowledge_enriches_recommendations(self) -> None:
        bp = _make_blueprint()
        ka = _make_knowledge()
        plan = self.engine.transform(bp, organizational_knowledge=ka)
        combined = " ".join(plan.executive_recommendations)
        self.assertIn("change readiness", combined)

    # ------------------------------------------------------------------
    # Current State & Future State
    # ------------------------------------------------------------------

    def test_current_state_has_business_problem(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        self.assertIn("business_problem", plan.current_state_assessment)
        self.assertTrue(plan.current_state_assessment["business_problem"])

    def test_current_state_includes_discovery_data(self) -> None:
        bp = _make_blueprint()
        dp = _make_discovery_plan()
        plan = self.engine.transform(bp, discovery_plan=dp)
        known = plan.current_state_assessment["known_information"]
        self.assertIn("Client uses paper records", known)

    def test_future_state_has_vision_statement(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        self.assertIn("vision_statement", plan.future_state_vision)
        self.assertIn("business_benefits", plan.future_state_vision)

    # ------------------------------------------------------------------
    # Immutability
    # ------------------------------------------------------------------

    def test_blueprint_not_mutated(self) -> None:
        bp = _make_blueprint()
        original_objectives = list(bp.business_objectives)
        original_risks = list(bp.risks)
        original_metrics = list(bp.success_metrics)
        self.engine.transform(bp)
        self.assertEqual(bp.business_objectives, original_objectives)
        self.assertEqual(bp.risks, original_risks)
        self.assertEqual(bp.success_metrics, original_metrics)

    def test_estimate_not_mutated(self) -> None:
        bp = _make_blueprint()
        est = _make_estimate()
        original_milestones = list(est.major_milestones)
        self.engine.transform(bp, estimate=est)
        self.assertEqual(est.major_milestones, original_milestones)

    # ------------------------------------------------------------------
    # Warnings
    # ------------------------------------------------------------------

    def test_warnings_on_missing_optional_inputs(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        # Should warn about estimate, proposal, discovery, knowledge
        self.assertGreater(len(plan.warnings), 0)

    def test_no_warnings_with_all_inputs(self) -> None:
        plan = self.engine.transform(
            _make_blueprint(),
            estimate=_make_estimate(),
            proposal=_make_proposal(),
            discovery_plan=_make_discovery_plan(),
            organizational_knowledge=_make_knowledge(),
        )
        self.assertEqual(len(plan.warnings), 0)

    # ------------------------------------------------------------------
    # Serialization (full chain)
    # ------------------------------------------------------------------

    def test_full_serialization(self) -> None:
        bp = _make_blueprint()
        est = _make_estimate()
        prop = _make_proposal()
        dp = _make_discovery_plan()
        ka = _make_knowledge()
        plan = self.engine.transform(bp, estimate=est, proposal=prop,
                                     discovery_plan=dp, organizational_knowledge=ka)
        d = plan.to_dict()
        self.assertIn("plan_id", d)
        self.assertIn("transformation_objectives", d)
        self.assertIn("kpi_dashboard", d)
        self.assertIn("department_impact_analysis", d)
        self.assertIn("adoption_strategy", d)
        self.assertIn("risk_register", d)
        self.assertIn("process_changes", d)
        self.assertIn("change_management_plan", d)
        self.assertIn("training_plan", d)
        self.assertIn("executive_recommendations", d)
        self.assertIn("summary", d)

    def test_objective_serialization(self) -> None:
        obj = TransformationObjective(
            objective_id="OBJ-0001", title="Achieve digital records",
            description="desc", linked_business_goals=["Digitize records"],
            owner_department="IT", success_criteria=["All records digital"],
        )
        d = obj.to_dict()
        self.assertEqual(d["objective_id"], "OBJ-0001")
        self.assertIn("linked_business_goals", d)
        self.assertIn("success_criteria", d)

    def test_kpi_serialization(self) -> None:
        kpi = KPI(
            kpi_id="KPI-0001", name="Uptime", description="System availability",
            baseline="95%", target_value="99.9", unit="%",
            measurement_method="Monitoring dashboard",
            timeframe="Post go-live", owner_department="Operations",
        )
        d = kpi.to_dict()
        self.assertEqual(d["kpi_id"], "KPI-0001")
        self.assertEqual(d["unit"], "%")

    def test_change_impact_serialization(self) -> None:
        ci = ChangeImpact(
            impact_id="IMP-0001", department="Engineering", impact_level="HIGH",
            affected_processes=["CI/CD pipeline"],
            headcount_affected=10,
            change_description="Engineers adopt new tooling.",
            training_required=["New tool training"],
            readiness_actions=["Brief team lead"],
        )
        d = ci.to_dict()
        self.assertEqual(d["impact_id"], "IMP-0001")
        self.assertEqual(d["impact_level"], "HIGH")
        self.assertEqual(d["headcount_affected"], 10)

    def test_adoption_phase_serialization(self) -> None:
        phase = AdoptionPhase(
            phase_id="PHS-0001", name="Pilot", description="Pilot phase",
            sequence=1, duration_weeks=4.0, scope="Pilot group",
            key_activities=["Deploy", "Collect feedback"],
            success_gate="Pilot accepted",
            responsible_parties=["PM"],
        )
        d = phase.to_dict()
        self.assertEqual(d["phase_id"], "PHS-0001")
        self.assertEqual(d["sequence"], 1)

    def test_summary_structure(self) -> None:
        bp = _make_blueprint()
        plan = self.engine.transform(bp)
        s = plan.summary()
        self.assertIn("plan_id", s)
        self.assertIn("objective_count", s)
        self.assertIn("kpi_count", s)
        self.assertIn("department_count", s)
        self.assertIn("adoption_phase_count", s)
        self.assertIn("risk_count", s)
        self.assertIn("process_change_count", s)

    # ------------------------------------------------------------------
    # KPI object validation
    # ------------------------------------------------------------------

    def test_kpi_requires_measurement_method(self) -> None:
        with self.assertRaises(ValueError):
            KPI(
                kpi_id="KPI-0001", name="Uptime", description="desc",
                baseline="0%", target_value="99.9", unit="%",
                measurement_method="",    # empty — must raise
                timeframe="Q4", owner_department="IT",
            )

    def test_kpi_requires_target_value(self) -> None:
        with self.assertRaises(ValueError):
            KPI(
                kpi_id="KPI-0001", name="Uptime", description="desc",
                baseline="0%", target_value="",  # empty — must raise
                unit="%", measurement_method="Monitoring",
                timeframe="Q4", owner_department="IT",
            )

    def test_objective_requires_linked_goal(self) -> None:
        with self.assertRaises(ValueError):
            TransformationObjective(
                objective_id="OBJ-0001", title="Some objective",
                description="desc",
                linked_business_goals=[],  # empty — must raise
                owner_department="IT", success_criteria=[],
            )

    def test_change_impact_normalizes_invalid_level(self) -> None:
        ci = ChangeImpact(
            impact_id="IMP-0001", department="QA",
            impact_level="EXTREME",          # invalid → defaults to MEDIUM
            affected_processes=[], headcount_affected=0,
            change_description="desc", training_required=[], readiness_actions=[],
        )
        self.assertEqual(ci.impact_level, "MEDIUM")

    def test_change_impact_clamps_negative_headcount(self) -> None:
        ci = ChangeImpact(
            impact_id="IMP-0002", department="QA",
            impact_level="LOW", affected_processes=[], headcount_affected=-5,
            change_description="desc", training_required=[], readiness_actions=[],
        )
        self.assertEqual(ci.headcount_affected, 0)


if __name__ == "__main__":
    unittest.main()
