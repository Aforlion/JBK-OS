from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

from core.project_estimate import ProjectEstimate
from core.commercial_proposal import CommercialProposal

LOGGER = logging.getLogger(__name__)


class PricingEngine:
    def __init__(self) -> None:
        self._next_id = 1
        self.internal_hourly_rate = 150.0 # Standard hourly cost basis

    def _generate_proposal_id(self) -> str:
        prp_id = f"PRP-{self._next_id:04d}"
        self._next_id += 1
        return prp_id

    def recommend_pricing_strategy(self, estimate: ProjectEstimate) -> str:
        if estimate is None:
            return "Fixed Project Pricing"
            
        effort = getattr(estimate, "expected_effort", 160.0)
        complexity = getattr(estimate, "delivery_complexity", "Medium")
        
        if complexity == "Enterprise":
            return "Strategic Partnership Pricing"
        elif effort > 480.0:
            return "Milestone Pricing"
        elif effort <= 80.0:
            return "Fixed Project Pricing"
        else:
            return "Value-Based Pricing"

    def recommend_payment_terms(self, complexity: str) -> str:
        if complexity in ["Very Low", "Low"]:
            return "50/50 Split (50% upfront, 50% on final delivery)"
        elif complexity == "Medium":
            return "Milestone Payments (30% Upfront, 40% Midpoint, 30% Delivery)"
        else:
            return "Milestone Payments (20% Upfront, 20% Architecture Approved, 30% MVP, 30% Delivery)"

    def identify_commercial_risks(self, estimate: ProjectEstimate) -> list[dict[str, Any]]:
        complexity = getattr(estimate, "delivery_complexity", "Medium")
        
        risks = [
            {
                "risk": "Scope Creep",
                "mitigation": "Establish strict change request procedures with pre-agreed hourly rates."
            },
            {
                "risk": "Delayed Client Decisions",
                "mitigation": "Include clause specifying project suspension if reviews exceed 5 business days."
            }
        ]
        
        if complexity in ["Very High", "Enterprise"]:
            risks.append({
                "risk": "Resource Availability Bottlenecks",
                "mitigation": "Lock technical architecture team schedules 2 weeks prior to project start."
            })
            risks.append({
                "risk": "FX Fluctuation Exposure",
                "mitigation": "Denominate all commercial milestone invoices in stabilized USD."
            })
            
        return risks

    def generate_negotiation_notes(self, estimate: ProjectEstimate) -> dict[str, Any]:
        return {
            "discount_guidance": "Executive discount limit is capped at 10% of recommended price only if upfront payment is increased to 50%.",
            "non_negotiables": [
                "IP rights remain JBK property until final invoice is cleared.",
                "Maintenance support requires separate Service Level Agreement (SLA)."
            ],
            "concessions": [
                "Will include 1 additional week of post-live warranty support in exchange for joint marketing case study rights."
            ],
            "upsell_opportunities": [
                "Cross-sell Monthly Maintenance Agreement",
                "Cross-sell Staff Training Program"
            ]
        }

    def calculate_confidence(self, estimate: ProjectEstimate) -> float:
        if estimate is None:
            return 0.0
        est_conf = getattr(estimate, "confidence_score", 0.5)
        score = est_conf * 0.9
        return round(score, 2)

    def price_project(self, estimate: ProjectEstimate) -> CommercialProposal:
        return self.generate_commercial_proposal(estimate)

    def generate_commercial_proposal(self, estimate: ProjectEstimate) -> CommercialProposal:
        if estimate is None:
            raise ValueError("Project estimate is required.")
            
        estimate_id = getattr(estimate, "estimate_id", "UNKNOWN")
        proposal_id = self._generate_proposal_id()
        
        LOGGER.info("object_id=%s action=generate_proposal actor=system status=DRAFT", proposal_id)

        # 1. Calculate Tiers
        expected_effort = getattr(estimate, "expected_effort", 160.0)
        complexity = getattr(estimate, "delivery_complexity", "Medium")
        
        cost_basis = expected_effort * self.internal_hourly_rate
        
        # Applying tier multipliers
        conservative_price = cost_basis * 1.5
        recommended_price = cost_basis * 2.0
        premium_price = cost_basis * 3.0
        
        expected_gross_margin = ((recommended_price - cost_basis) / recommended_price) * 100.0
        expected_gross_margin = round(expected_gross_margin, 2)

        # 2. Strategies & Options
        commercial_strategy = self.recommend_pricing_strategy(estimate)
        payment_structure = self.recommend_payment_terms(complexity)

        # Build payment milestones based on structure
        payment_milestones = []
        if "50/50" in payment_structure:
            payment_milestones = [
                {"milestone": "Project Kickoff", "percentage": 50.0, "amount": recommended_price * 0.5},
                {"milestone": "Final Delivery", "percentage": 50.0, "amount": recommended_price * 0.5}
            ]
        elif "30/40/30" in payment_structure:
            payment_milestones = [
                {"milestone": "Project Kickoff", "percentage": 30.0, "amount": recommended_price * 0.3},
                {"milestone": "Midpoint Milestone", "percentage": 40.0, "amount": recommended_price * 0.4},
                {"milestone": "Final Delivery", "percentage": 30.0, "amount": recommended_price * 0.3}
            ]
        else:
            payment_milestones = [
                {"milestone": "Project Kickoff", "percentage": 20.0, "amount": recommended_price * 0.2},
                {"milestone": "Architecture Approved", "percentage": 20.0, "amount": recommended_price * 0.2},
                {"milestone": "MVP Completed", "percentage": 30.0, "amount": recommended_price * 0.3},
                {"milestone": "Final Delivery", "percentage": 30.0, "amount": recommended_price * 0.3}
            ]

        # 3. Optional services recommendations
        optional_services = [
            {
                "service": "Monthly Post-Launch Maintenance SLA",
                "price": recommended_price * 0.1,
                "billing_cycle": "Monthly"
            },
            {
                "service": "Staff Training & Onboarding Workshop",
                "price": 2500.0,
                "billing_cycle": "One-time"
            }
        ]

        pricing_rationale = (
            f"Recommended price derived using {commercial_strategy} strategy. "
            f"Cost basis of {expected_effort} hours valued at internal rate of ${self.internal_hourly_rate}/hr."
        )

        commercial_risks = self.identify_commercial_risks(estimate)
        negotiation_notes = self.generate_negotiation_notes(estimate)
        confidence_score = self.calculate_confidence(estimate)

        proposal = CommercialProposal(
            proposal_id=proposal_id,
            estimate_id=estimate_id,
            client_summary=getattr(estimate, "client_summary", ""),
            project_summary=getattr(estimate, "solution_summary", ""),
            commercial_strategy=commercial_strategy,
            conservative_price=round(conservative_price, 2),
            recommended_price=round(recommended_price, 2),
            premium_price=round(premium_price, 2),
            expected_gross_margin=expected_gross_margin,
            pricing_rationale=pricing_rationale,
            commercial_risks=commercial_risks,
            payment_structure=payment_structure,
            payment_milestones=payment_milestones,
            maintenance_recommendation="Recommended Monthly Maintenance SLA starting at 10% of project cost.",
            support_recommendation="90 days post-launch support included; extended support via SLA.",
            warranty_recommendation="90 days warranty covering system bug resolution.",
            licensing_recommendation="Proprietary commercial license handed over upon final payment clearance.",
            optional_services=optional_services,
            commercial_assumptions=[
                "Client provides system access within 5 business days of contract kickoff.",
                "Third-party API subscriptions are paid directly by client."
            ],
            negotiation_notes=negotiation_notes,
            executive_recommendation=f"Approve recommended proposal {proposal_id} at {expected_gross_margin}% gross margin.",
            confidence_score=confidence_score,
        )

        LOGGER.info(
            "object_id=%s action=generate_proposal actor=system status=READY confidence=%s",
            proposal_id,
            proposal.confidence_score,
        )
        return proposal
