from __future__ import annotations

import unittest
from core.learning_observation import LearningObservation
from core.learning_recommendation import LearningRecommendation
from core.continuous_learning_report import ContinuousLearningReport
from core.continuous_learning_engine import ContinuousLearningEngine


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

def _mock_k_registry(skills=None, standards=None, plugins=None, specs=None, nodes=None) -> dict:
    return {
        "skills": skills or ["PythonCoding"],
        "standards": standards or ["PEP8"],
        "plugins": plugins or [],
        "specifications": specs or ["Spec-001"],
        "knowledge_nodes": nodes or ["Basic OCR"],
    }


def _mock_portfolio(completed=None, active_domains=None) -> dict:
    return {
        "completed_projects": completed if completed is not None else [
            {"project_id": "PROJ-101", "technology_stack": ["AI-OCR", "LLM-Search"]}
        ],
        "domains_active": active_domains if active_domains is not None else ["Education"],
    }


# ---------------------------------------------------------------------------
# LearningObservation Tests
# ---------------------------------------------------------------------------

class TestLearningObservation(unittest.TestCase):

    def test_valid_observation(self) -> None:
        obs = LearningObservation(
            observation_id="OBS-001",
            title="AI NLP models",
            source="MARKET_RESEARCH",
            description="NLP technologies accelerating",
            confidence=0.95,
        )
        self.assertEqual(obs.domain, "AI")
        self.assertEqual(obs.confidence, 0.95)

    def test_invalid_source_rejected(self) -> None:
        with self.assertRaises(ValueError):
            LearningObservation("O1", "Title", "REDDIT_POST", "Desc", 0.9)

    def test_invalid_confidence_rejected(self) -> None:
        with self.assertRaises(ValueError):
            LearningObservation("O1", "Title", "MARKET_RESEARCH", "Desc", 1.5)

    def test_serialization(self) -> None:
        """BR-055-010: Observation is serializable."""
        obs = LearningObservation("OBS-001", "NLP", "MARKET_RESEARCH", "Desc", 0.8)
        d = obs.to_dict()
        self.assertEqual(d["observation_id"], "OBS-001")


# ---------------------------------------------------------------------------
# LearningRecommendation Tests
# ---------------------------------------------------------------------------

class TestLearningRecommendation(unittest.TestCase):

    def test_valid_recommendation(self) -> None:
        rec = LearningRecommendation(
            recommendation_id="REC-001",
            title="OCR specialist training",
            category="TRAINING",
            priority="CRITICAL",
            reasoning="Explainable reason",
            confidence=0.9,
            evidence=["OBS-001"],
        )
        self.assertEqual(rec.priority, "CRITICAL")

    def test_missing_reasoning_fails(self) -> None:
        """BR-055-004: Recommendations require explainability reasoning."""
        with self.assertRaises(ValueError):
            LearningRecommendation(
                recommendation_id="REC-001",
                title="T1",
                category="TRAINING",
                priority="HIGH",
                reasoning="",  # Empty
                confidence=0.8,
                evidence=[],
            )


# ---------------------------------------------------------------------------
# ContinuousLearningReport Tests
# ---------------------------------------------------------------------------

class TestContinuousLearningReport(unittest.TestCase):

    def test_report_immutability(self) -> None:
        """BR-055-008: Reports are immutable."""
        report = ContinuousLearningReport(
            report_id="LER-123",
            observations=[],
            recommendations=[],
            duplicate_observations=[],
            learning_domains=[],
            confidence_scores={},
            recommended_research_topics=[],
            recommended_new_skills=[],
            recommended_new_plugins=[],
        )
        with self.assertRaises(AttributeError):
            report.report_id = "LER-MUTATED"


# ---------------------------------------------------------------------------
# ContinuousLearningEngine Integration Tests
# ---------------------------------------------------------------------------

class TestContinuousLearningEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = ContinuousLearningEngine()

    def test_engine_stateless_execution(self) -> None:
        """BR-055-001: The engine is stateless."""
        k_reg = _mock_k_registry()
        port = _mock_portfolio()
        report = self.engine.learn(k_reg, {}, {}, {}, {}, port)
        self.assertIsNotNone(report)
        self.assertEqual(len(report.observations), 2)  # Ingested from stack: AI-OCR, LLM-Search

    def test_duplicate_suppression(self) -> None:
        """BR-055-003: Duplicate observations are suppressed."""
        k_reg = _mock_k_registry(skills=["PythonCoding"], nodes=["AI-OCR"])
        port = _mock_portfolio(completed=[
            {"project_id": "PROJ-101", "technology_stack": ["AI-OCR"]}  # duplicate
        ])
        report = self.engine.learn(k_reg, {}, {}, {}, {}, port)
        self.assertEqual(len(report.observations), 0)
        self.assertIn("AI-powered AI-OCR usage", report.duplicate_observations)

    def test_knowledge_gap_detection(self) -> None:
        """BR-055-009: Gaps identified automatically."""
        k_reg = _mock_k_registry()
        port = _mock_portfolio(active_domains=["Education"])  # Missing Healthcare, Finance, Legal
        report = self.engine.learn(k_reg, {}, {}, {}, {}, port)
        gaps = [r.title for r in report.recommendations if r.category == "KNOWLEDGE"]
        self.assertIn("Acquire Healthcare Domain Experience", gaps)
        self.assertIn("Acquire Finance Domain Experience", gaps)
        self.assertIn("Acquire Legal Domain Experience", gaps)

    def test_confidence_scores_mandatory(self) -> None:
        """BR-055-005: Confidence scores present."""
        k_reg = _mock_k_registry()
        port = _mock_portfolio()
        report = self.engine.learn(k_reg, {}, {}, {}, {}, port)
        for domain, score in report.confidence_scores.items():
            self.assertTrue(0.0 <= score <= 1.0)

    def test_external_observations_optional(self) -> None:
        """BR-055-007: External observations are optional inputs."""
        k_reg = _mock_k_registry()
        port = _mock_portfolio(completed=[])
        
        # Run with None external observations
        report_none = self.engine.learn(k_reg, {}, {}, {}, {}, port, external_observations=None)
        self.assertEqual(len(report_none.observations), 0)

        # Run with external observations
        ext = LearningObservation("OBS-009", "Education Attendance Plugin", "MARKET_RESEARCH", "Desc", 0.9)
        report_ext = self.engine.learn(k_reg, {}, {}, {}, {}, port, external_observations=[ext])
        self.assertEqual(len(report_ext.observations), 1)
        self.assertEqual(report_ext.recommendations[-1].title, "Education Attendance Plugin")

    def test_empty_input_handling(self) -> None:
        report = self.engine.learn(None, None, None, None, None, None)
        self.assertTrue(len(report.observations) == 0)
        self.assertTrue(len(report.recommendations) > 0)  # Gaps still detected

    def test_decision_boundary_enforcement(self) -> None:
        """Engine is advisory only. Verify it only generates recommendations."""
        k_reg = _mock_k_registry()
        port = _mock_portfolio()
        
        # Capture registry counts before run
        skills_count = len(k_reg["skills"])

        report = self.engine.learn(k_reg, {}, {}, {}, {}, port)
        
        # Verify registries are not modified
        self.assertEqual(len(k_reg["skills"]), skills_count)
        self.assertTrue(len(report.recommendations) > 0)


if __name__ == "__main__":
    unittest.main()
