from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class CommercialProposal:
    def __init__(
        self,
        proposal_id: str,
        estimate_id: str,
        client_summary: str,
        project_summary: str,
        commercial_strategy: str,
        conservative_price: float,
        recommended_price: float,
        premium_price: float,
        expected_gross_margin: float,
        pricing_rationale: str,
        commercial_risks: list[dict[str, Any]],
        payment_structure: str,
        payment_milestones: list[dict[str, Any]],
        maintenance_recommendation: str,
        support_recommendation: str,
        warranty_recommendation: str,
        licensing_recommendation: str,
        optional_services: list[dict[str, Any]],
        commercial_assumptions: list[str],
        negotiation_notes: dict[str, Any],
        executive_recommendation: str,
        confidence_score: float,
        created_at: str | None = None,
    ) -> None:
        self.proposal_id = proposal_id
        self.estimate_id = estimate_id
        self.client_summary = client_summary or ""
        self.project_summary = project_summary or ""
        self.commercial_strategy = commercial_strategy or "Value-Based"
        self.conservative_price = float(conservative_price)
        self.recommended_price = float(recommended_price)
        self.premium_price = float(premium_price)
        self.expected_gross_margin = float(expected_gross_margin)
        self.pricing_rationale = pricing_rationale or ""
        self.commercial_risks = commercial_risks or []
        self.payment_structure = payment_structure or "Milestone Payments"
        self.payment_milestones = payment_milestones or []
        self.maintenance_recommendation = maintenance_recommendation or ""
        self.support_recommendation = support_recommendation or ""
        self.warranty_recommendation = warranty_recommendation or ""
        self.licensing_recommendation = licensing_recommendation or ""
        self.optional_services = optional_services or []
        self.commercial_assumptions = commercial_assumptions or []
        self.negotiation_notes = negotiation_notes or {}
        self.executive_recommendation = executive_recommendation or ""
        self.confidence_score = float(confidence_score)
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "estimate_id": self.estimate_id,
            "commercial_strategy": self.commercial_strategy,
            "recommended_price": self.recommended_price,
            "expected_gross_margin": self.expected_gross_margin,
            "confidence_score": self.confidence_score,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "estimate_id": self.estimate_id,
            "client_summary": self.client_summary,
            "project_summary": self.project_summary,
            "commercial_strategy": self.commercial_strategy,
            "conservative_price": self.conservative_price,
            "recommended_price": self.recommended_price,
            "premium_price": self.premium_price,
            "expected_gross_margin": self.expected_gross_margin,
            "pricing_rationale": self.pricing_rationale,
            "commercial_risks": [dict(r) for r in self.commercial_risks],
            "payment_structure": self.payment_structure,
            "payment_milestones": [dict(m) for m in self.payment_milestones],
            "maintenance_recommendation": self.maintenance_recommendation,
            "support_recommendation": self.support_recommendation,
            "warranty_recommendation": self.warranty_recommendation,
            "licensing_recommendation": self.licensing_recommendation,
            "optional_services": [dict(s) for s in self.optional_services],
            "commercial_assumptions": list(self.commercial_assumptions),
            "negotiation_notes": dict(self.negotiation_notes),
            "executive_recommendation": self.executive_recommendation,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at,
        }
