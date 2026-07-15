from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from core.commercial_proposal import CommercialProposal
from core.client_proposal import ClientProposal

LOGGER = logging.getLogger(__name__)


class ProposalGenerator:
    def __init__(self) -> None:
        self.default_validity_days = 30

    def generate_executive_summary(self, commercial_proposal: CommercialProposal) -> str:
        if commercial_proposal is None:
            return ""
            
        client_need = commercial_proposal.client_summary or "optimizing business operations"
        project_sum = commercial_proposal.project_summary or "custom platform delivery"
        
        summary = (
            f"This proposal outlines our strategic approach to address the primary business drivers: {client_need}. "
            f"JBK Technologies proposes deploying the recommended solution: {project_sum}. "
            f"This engagement is designed to deliver immediate, measurable business outcomes and lay a foundation for long-term scalability."
        )
        return summary

    def format_scope(self, commercial_proposal: CommercialProposal) -> dict[str, Any]:
        return {
            "included": [
                "Full solution design and system architecture blueprinting.",
                "Development, verification, and containerized deployment of core microservices.",
                "Integration with standard third-party APIs.",
                "Comprehensive user acceptance testing (UAT) and project kickoff handoff."
            ],
            "excluded": [
                "Ongoing infrastructure hosting fees.",
                "Customizations or features not explicitly described in the deliverables checklist."
            ],
            "future_opportunities": [
                "Advanced machine learning optimizations and model retraining.",
                "Multi-region geo-redundancy clustering."
            ]
        }

    def format_deliverables(self, commercial_proposal: CommercialProposal) -> list[str]:
        # Formulate deliverables list in client-friendly language
        return [
            "Enterprise Process Automation Platform",
            "Executive Dashboard & Reporting Interface",
            "System Documentation & Administrative Runbooks",
            "Post-Launch Technical Handoff & Knowledge Transfer Session"
        ]

    def generate_proposal(
        self,
        commercial_proposal: CommercialProposal,
        client_name: str,
        client_organization: str,
    ) -> ClientProposal:
        if commercial_proposal is None:
            raise ValueError("Commercial proposal is required.")
            
        proposal_id = getattr(commercial_proposal, "proposal_id", "UNKNOWN")
        estimate_id = getattr(commercial_proposal, "estimate_id", "UNKNOWN")
        
        LOGGER.info("object_id=%s action=generate_client_proposal actor=system status=DRAFT", proposal_id)

        # 1. Timestamps & Validity
        today = datetime.now(timezone.utc)
        valid_until = today + timedelta(days=self.default_validity_days)
        
        proposal_date = today.strftime("%Y-%m-%d")
        proposal_valid_until = valid_until.strftime("%Y-%m-%d")

        # 2. Section Formulations
        executive_summary = self.generate_executive_summary(commercial_proposal)
        scope = self.format_scope(commercial_proposal)
        deliverables = self.format_deliverables(commercial_proposal)

        # Extract client need
        needs = commercial_proposal.client_summary or "Client needs analysis"
        challenges = commercial_proposal.project_summary or "Operational constraints"

        # 3. Clean Commercial Elements (strictly recommended price, payment terms, and optional services only)
        commercial_investment = getattr(commercial_proposal, "recommended_price", 0.0)
        payment_terms = getattr(commercial_proposal, "payment_structure", "Milestone Payments")
        
        raw_options = getattr(commercial_proposal, "optional_services", [])
        optional_services = []
        for opt in raw_options:
            optional_services.append({
                "service": opt.get("service", "Optional Upgrade"),
                "price": opt.get("price", 0.0),
                "billing_cycle": opt.get("billing_cycle", "One-time")
            })

        # Signature Block
        signature = (
            "--------------------------------------------------\n"
            "Accepted By:\n\n"
            "Name: ______________________  Title: ______________________\n\n"
            "Signature: __________________  Date: ______________________"
        )

        proposal = ClientProposal(
            proposal_id=proposal_id,
            proposal_version="1.0",
            proposal_date=proposal_date,
            client_name=client_name or "Valued Client",
            client_organization=client_organization or "Organization",
            proposal_title=f"Professional Services Proposal - {client_organization or 'Organization'}",
            executive_summary=executive_summary,
            understanding_of_client_needs=needs,
            current_business_challenges=challenges,
            proposed_solution=challenges,
            solution_benefits="Enhanced efficiency, reduced manual effort, stable interface design.",
            project_objectives=needs,
            scope_of_work=scope,
            deliverables=deliverables,
            project_timeline="Details to be finalized during sprint planning workshops.",
            commercial_investment=commercial_investment,
            payment_terms=payment_terms,
            optional_services=optional_services,
            client_responsibilities=[
                "Provide timely access to system databases and configuration properties.",
                "Appoint a single primary point of contact for sprint sign-offs."
            ],
            assumptions=[
                "All hardware and cloud services are provisioned by the client.",
                "No legacy database migration outside of scope boundaries."
            ],
            exclusions=scope["excluded"],
            warranty="90 Days software bugs warranty coverage.",
            support_options="Standard email/support desk ticket systems.",
            acceptance_process="Review deliverables checklist and return signed signature block.",
            next_steps="1. Review proposal terms. 2. Sign signature block. 3. Kickoff project.",
            proposal_valid_until=proposal_valid_until,
            contact_information="JBK Technologies Accounts <accounts@jbk.tech>",
            executive_signature_block=signature,
        )

        LOGGER.info(
            "object_id=%s action=generate_client_proposal actor=system status=READY version=%s",
            proposal_id,
            proposal.proposal_version,
        )
        return proposal
