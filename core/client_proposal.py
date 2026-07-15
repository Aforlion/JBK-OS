from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class ClientProposal:
    def __init__(
        self,
        proposal_id: str,
        proposal_version: str,
        proposal_date: str,
        client_name: str,
        client_organization: str,
        proposal_title: str,
        executive_summary: str,
        understanding_of_client_needs: str,
        current_business_challenges: str,
        proposed_solution: str,
        solution_benefits: str,
        project_objectives: str,
        scope_of_work: dict[str, Any],
        deliverables: list[str],
        project_timeline: str,
        commercial_investment: float,
        payment_terms: str,
        optional_services: list[dict[str, Any]],
        client_responsibilities: list[str],
        assumptions: list[str],
        exclusions: list[str],
        warranty: str,
        support_options: str,
        acceptance_process: str,
        next_steps: str,
        proposal_valid_until: str,
        contact_information: str,
        executive_signature_block: str,
        created_at: str | None = None,
    ) -> None:
        self.proposal_id = proposal_id
        self.proposal_version = proposal_version
        self.proposal_date = proposal_date
        self.client_name = client_name
        self.client_organization = client_organization
        self.proposal_title = proposal_title
        self.executive_summary = executive_summary or ""
        self.understanding_of_client_needs = understanding_of_client_needs or ""
        self.current_business_challenges = current_business_challenges or ""
        self.proposed_solution = proposed_solution or ""
        self.solution_benefits = solution_benefits or ""
        self.project_objectives = project_objectives or ""
        self.scope_of_work = scope_of_work or {}
        self.deliverables = deliverables or []
        self.project_timeline = project_timeline or ""
        self.commercial_investment = float(commercial_investment)
        self.payment_terms = payment_terms or ""
        self.optional_services = optional_services or []
        self.client_responsibilities = client_responsibilities or []
        self.assumptions = assumptions or []
        self.exclusions = exclusions or []
        self.warranty = warranty or ""
        self.support_options = support_options or ""
        self.acceptance_process = acceptance_process or ""
        self.next_steps = next_steps or ""
        self.proposal_valid_until = proposal_valid_until or ""
        self.contact_information = contact_information or ""
        self.executive_signature_block = executive_signature_block or ""
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def summary(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "proposal_version": self.proposal_version,
            "proposal_title": self.proposal_title,
            "client_name": self.client_name,
            "client_organization": self.client_organization,
            "commercial_investment": self.commercial_investment,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "proposal_version": self.proposal_version,
            "proposal_date": self.proposal_date,
            "client_name": self.client_name,
            "client_organization": self.client_organization,
            "proposal_title": self.proposal_title,
            "executive_summary": self.executive_summary,
            "understanding_of_client_needs": self.understanding_of_client_needs,
            "current_business_challenges": self.current_business_challenges,
            "proposed_solution": self.proposed_solution,
            "solution_benefits": self.solution_benefits,
            "project_objectives": self.project_objectives,
            "scope_of_work": dict(self.scope_of_work),
            "deliverables": list(self.deliverables),
            "project_timeline": self.project_timeline,
            "commercial_investment": self.commercial_investment,
            "payment_terms": self.payment_terms,
            "optional_services": [dict(s) for s in self.optional_services],
            "client_responsibilities": list(self.client_responsibilities),
            "assumptions": list(self.assumptions),
            "exclusions": list(self.exclusions),
            "warranty": self.warranty,
            "support_options": self.support_options,
            "acceptance_process": self.acceptance_process,
            "next_steps": self.next_steps,
            "proposal_valid_until": self.proposal_valid_until,
            "contact_information": self.contact_information,
            "executive_signature_block": self.executive_signature_block,
            "created_at": self.created_at,
        }

    def render_markdown(self) -> str:
        md = []
        md.append(f"# {self.proposal_title}")
        md.append(f"**Proposal ID:** {self.proposal_id} | **Version:** {self.proposal_version} | **Date:** {self.proposal_date}")
        md.append(f"**Prepared For:** {self.client_name} ({self.client_organization})")
        md.append("")
        md.append("## Executive Summary")
        md.append(self.executive_summary)
        md.append("")
        md.append("## Understanding of Client Needs")
        md.append(self.understanding_of_client_needs)
        md.append("")
        md.append("## Current Business Challenges")
        md.append(self.current_business_challenges)
        md.append("")
        md.append("## Proposed Solution")
        md.append(self.proposed_solution)
        md.append("")
        md.append("## Solution Benefits")
        md.append(self.solution_benefits)
        md.append("")
        md.append("## Project Objectives")
        md.append(self.project_objectives)
        md.append("")
        md.append("## Scope of Work")
        md.append("### Included:")
        for item in self.scope_of_work.get("included", []):
            md.append(f"- {item}")
        md.append("")
        md.append("### Excluded:")
        for item in self.scope_of_work.get("excluded", []):
            md.append(f"- {item}")
        md.append("")
        md.append("### Future Phase Opportunities:")
        for item in self.scope_of_work.get("future_opportunities", []):
            md.append(f"- {item}")
        md.append("")
        md.append("## Deliverables")
        for item in self.deliverables:
            md.append(f"- {item}")
        md.append("")
        md.append("## Project Timeline")
        md.append(self.project_timeline)
        md.append("")
        md.append("## Commercial Investment")
        md.append(f"**Total Professional Fee:** ${self.commercial_investment:,.2f}")
        md.append("")
        md.append(f"**Payment Structure:** {self.payment_terms}")
        md.append("")
        if self.optional_services:
            md.append("### Optional Services:")
            for s in self.optional_services:
                md.append(f"- **{s.get('service')}**: ${s.get('price'):,.2f} ({s.get('billing_cycle')})")
            md.append("")
        md.append("## Client Responsibilities")
        for item in self.client_responsibilities:
            md.append(f"- {item}")
        md.append("")
        md.append("## Assumptions")
        for item in self.assumptions:
            md.append(f"- {item}")
        md.append("")
        md.append("## Exclusions")
        for item in self.exclusions:
            md.append(f"- {item}")
        md.append("")
        md.append("## Warranty")
        md.append(self.warranty)
        md.append("")
        md.append("## Support Options")
        md.append(self.support_options)
        md.append("")
        md.append("## Acceptance Process")
        md.append(self.acceptance_process)
        md.append("")
        md.append("## Next Steps")
        md.append(self.next_steps)
        md.append("")
        md.append(f"**Proposal Valid Until:** {self.proposal_valid_until}")
        md.append("")
        md.append(f"**Contact Information:** {self.contact_information}")
        md.append("")
        md.append(self.executive_signature_block)
        return "\n".join(md)

    def render_text(self) -> str:
        # Simple text representation of markdown structure
        return self.render_markdown().replace("# ", "").replace("## ", "").replace("### ", "").replace("**", "")
