import unittest
from core.chief_of_staff import ChiefOfStaff
from core.project_registry import ProjectRegistry
from core.worker_registry import WorkerRegistry
from core.skill_registry import SkillRegistry
from core.knowledge_registry import KnowledgeRegistry
from core.executive import Executive
from core.ai_executive_assistant import AIExecutiveAssistant, AssistantResponse
from core.executive_conversation_record import ExecutiveConversationRecord


class TestAIExecutiveAssistant(unittest.TestCase):

    def setUp(self) -> None:
        self.project_registry = ProjectRegistry()
        self.worker_registry = WorkerRegistry()
        self.skill_registry = SkillRegistry()
        self.knowledge_registry = KnowledgeRegistry()

        self.chief_of_staff = ChiefOfStaff(
            worker_registry=self.worker_registry,
            project_registry=self.project_registry,
            knowledge_registry=self.knowledge_registry,
        )

        # Register mock worker
        self.worker = Executive(
            executive_id="EXEC-0001",
            title="CEO Assistant",
            mission="Coordinating company execution",
        )
        self.worker_registry.register(self.worker)

        self.assistant = AIExecutiveAssistant(
            chief_of_staff=self.chief_of_staff,
            skill_registry=self.skill_registry,
            knowledge_registry=self.knowledge_registry,
        )

    # ------------------------------------------------------------------
    # GREETING & STARTUP BRIEFING (BR-035-012)
    # ------------------------------------------------------------------

    def test_greeting_triggers_briefing(self) -> None:
        response = self.assistant.converse("Good morning JBK-OS.")
        self.assertEqual(response.intent, "GREETING")
        self.assertIn("Good Morning", response.message)
        self.assertGreater(len(response.engines_consulted), 0)
        self.assertGreater(len(response.execution_timeline), 0)
        self.assertIn("ChiefOfStaff", response.engines_consulted)

    # ------------------------------------------------------------------
    # INTENT CLASSIFICATION & ENTITY EXTRACTION (BR-035-002)
    # ------------------------------------------------------------------

    def test_new_client_intent_recognition(self) -> None:
        # Full details -> Should not require clarification
        req = "We have a new client. Contact: Alice (alice@jbk.tech) Budget: $50,000 for Acme Corp, 6 weeks timeline."
        response = self.assistant.converse(req)
        self.assertEqual(response.intent, "NEW_CLIENT")
        self.assertIsNone(response.follow_up_question)
        self.assertIn("Proposal Document Generation", [step["step"] for step in response.execution_timeline])

    # ------------------------------------------------------------------
    # CLARIFICATION MANAGEMENT (BR-035-006)
    # ------------------------------------------------------------------

    def test_clarification_on_ambiguous_input(self) -> None:
        # Client name / organization completely missing -> Should ask for clarification
        response = self.assistant.converse("We have a new lead. Budget is $10k.")
        self.assertEqual(response.intent, "NEW_CLIENT")
        self.assertIsNotNone(response.follow_up_question)
        self.assertEqual(response.follow_up_question, "Which client or organization is this initiative regarding?")

    # ------------------------------------------------------------------
    # CONTEXT AWARENESS (BR-035-003)
    # ------------------------------------------------------------------

    def test_context_awareness_across_turns(self) -> None:
        # Turn 1: Specify name
        self.assistant.converse("We have a new client named Alice at Acme Corp.")
        self.assertEqual(self.assistant.context["active_client_name"], "Alice")
        self.assertEqual(self.assistant.context["active_organization"], "Acme Corp")

        # Turn 2: Mention budget only, should remember client
        response = self.assistant.converse("Budget is $50,000, timeline is 6 weeks.")
        self.assertEqual(response.intent, "NEW_CLIENT")
        self.assertIsNone(response.follow_up_question)
        self.assertIn("Acme Corp", response.message)

    # ------------------------------------------------------------------
    # DECISION BOUNDARY ENFORCEMENT (BR-035-009)
    # ------------------------------------------------------------------

    def test_decision_boundary_enforcement(self) -> None:
        # Setup active proposal in context
        self.assistant.converse("We have a new client named Alice at Acme Corp. Budget is $50,000, 6 weeks.")
        
        # Request proposal review
        response = self.assistant.converse("Review the proposal")
        self.assertEqual(response.intent, "PROPOSAL_REVIEW")
        # Ensure it requires authorization and does NOT auto-approve
        self.assertTrue(response.requires_authorization)
        self.assertIn("explicitly authorize", response.message)

    # ------------------------------------------------------------------
    # EXPLAINABILITY (BR-035-011)
    # ------------------------------------------------------------------

    def test_explainability(self) -> None:
        response = self.assistant.converse("How healthy is the company?")
        self.assertEqual(response.intent, "PORTFOLIO_REVIEW")
        self.assertIsNotNone(response.reasoning)
        self.assertIn("PortfolioManagementEngine", response.engines_consulted)
        self.assertGreaterEqual(response.confidence, 0.9)

    # ------------------------------------------------------------------
    # CONVERSATION RECORD LOGGING (BR-035-014)
    # ------------------------------------------------------------------

    def test_conversation_record_logging(self) -> None:
        self.assistant.converse("Good morning.")
        self.assistant.converse("How healthy is the company?")
        
        record = self.assistant.active_record
        self.assertIsInstance(record, ExecutiveConversationRecord)
        self.assertEqual(len(record.turns), 2)
        
        data = record.to_dict()
        self.assertEqual(data["session_id"], "SESS-0001")
        self.assertEqual(len(data["turns"]), 2)
        self.assertEqual(data["turns"][0]["intent"], "GREETING")
        self.assertEqual(data["turns"][1]["intent"], "PORTFOLIO_REVIEW")


if __name__ == "__main__":
    unittest.main()
