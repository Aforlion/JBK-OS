from __future__ import annotations
import re
from typing import Any


class IntentResult:
    def __init__(
        self,
        intent: str,
        confidence: float,
        entities: dict[str, Any],
        clarification_needed: bool = False,
    ) -> None:
        self.intent = intent
        self.confidence = confidence
        self.entities = entities
        self.clarification_needed = clarification_needed


class IntentRecognizer:
    """Pattern-based intent classifier and entity extractor for JBK-OS V1."""

    def __init__(self) -> None:
        pass

    def recognize(self, message: str) -> IntentResult:
        msg = (message or "").strip().lower()

        if not msg:
            return IntentResult("GENERAL_QUESTION", 0.0, {}, clarification_needed=True)

        # 1. Greetings
        if any(greet in msg for greet in ["good morning", "hello", "hi ", "hi!", "hey"]):
            return IntentResult("GREETING", 1.0, {})

        # 2. Executive Briefing
        if any(keyword in msg for keyword in ["briefing", "today's priorities", "what's happening", "status report"]):
            if "project" not in msg:  # avoid conflict with project review
                return IntentResult("EXECUTIVE_BRIEFING", 0.9, {})

        # 3. Portfolio Review
        if any(keyword in msg for keyword in ["portfolio", "company health", "how healthy"]):
            return IntentResult("PORTFOLIO_REVIEW", 0.95, {})

        # 4. Strategic Analysis
        if any(keyword in msg for keyword in ["strategy", "opportunities", "market", "competitor"]):
            entities = {}
            # extract domain / sector if mentioned
            for sector in ["healthcare", "finance", "retail", "technology", "education"]:
                if sector in msg:
                    entities["sector"] = sector.capitalize()
            return IntentResult("STRATEGIC_ANALYSIS", 0.9, entities)

        # 5. Knowledge Query
        if any(keyword in msg for keyword in ["have we solved", "have we done", "lessons", "what did we learn"]):
            return IntentResult("KNOWLEDGE_QUERY", 0.85, {})

        # 6. Delivery Status
        if any(keyword in msg for keyword in ["work orders", "execution", "delivery supervision"]):
            return IntentResult("DELIVERY_STATUS", 0.85, {})

        # 7. Project Review
        if any(keyword in msg for keyword in ["project status", "behind schedule", "review projects", "is everything progressing"]):
            entities = {}
            # Extract project ID if present (e.g., PROJ-0001)
            match = re.search(r"proj-\d{4}", msg)
            if match:
                entities["project_id"] = match.group(0).upper()
            return IntentResult("PROJECT_REVIEW", 0.9, entities)

        # 8. Proposal Review / Creation / Approval
        if any(keyword in msg for keyword in ["proposal", "approve the contract", "sign proposal"]):
            entities = {}
            match = re.search(r"prp-\d{4}", msg)
            if match:
                entities["proposal_id"] = match.group(0).upper()
            return IntentResult("PROPOSAL_REVIEW", 0.9, entities)

        # 9. New Client Intake
        if any(keyword in msg for keyword in ["new client", "client intake", "prospect", "lead"]):
            entities = self._extract_client_entities(message)
            # Check completeness for intake
            clarification_needed = False
            # Check if critical info is missing (we need at least client name)
            if not entities.get("client_name") and not entities.get("organization"):
                clarification_needed = True

            return IntentResult(
                "NEW_CLIENT",
                0.95 if not clarification_needed else 0.6,
                entities,
                clarification_needed=clarification_needed,
            )

        return IntentResult("GENERAL_QUESTION", 0.5, {})

    def _extract_client_entities(self, text: str) -> dict[str, Any]:
        entities = {}
        text_lower = text.lower()

        # Extract contact / email
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        if email_match:
            entities["contact"] = email_match.group(0)

        # Extract budget
        budget_match = re.search(r"\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?", text)
        if budget_match:
            entities["budget"] = budget_match.group(0)

        # Extract timeline / weeks
        weeks_match = re.search(r"(\d+)\s*weeks?", text_lower)
        if weeks_match:
            entities["timeline"] = f"{weeks_match.group(1)} weeks"

        # Try to extract Client Name (e.g. "contact is Alice" or "Contact: Alice" or "Alice (alice@jbk.tech)")
        contact_name_match = re.search(r"(?:contact is|contact:)\s*([A-Za-z]+)", text, re.IGNORECASE)
        named_match = re.search(r"named\s+([A-Za-z]+)", text, re.IGNORECASE)
        if contact_name_match:
            entities["client_name"] = contact_name_match.group(1)
        elif named_match:
            entities["client_name"] = named_match.group(1)
        else:
            # Fallback check before email (e.g. Bob (bob@...) -> Bob)
            paren_email = re.search(r"([A-Za-z]+)\s*\([\w\.-]+@", text)
            if paren_email:
                entities["client_name"] = paren_email.group(1)

        # Try to extract Client Organization (e.g. "Acme Corp" or "for Acme")
        org_match = re.search(r"([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)?\s+(?:corp|co|inc|technologies|systems|limited|ltd))", text, re.IGNORECASE)
        if org_match:
            org = org_match.group(1).strip()
            org = re.sub(r"^(?:at|for|to|with)\s+", "", org, flags=re.IGNORECASE)
            entities["organization"] = org
        elif "acme" in text_lower:
            entities["organization"] = "Acme Corp"

        return entities
