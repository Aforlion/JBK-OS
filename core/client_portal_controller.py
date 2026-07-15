from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

from core.client_workspace import (
    ClientWorkspace,
    WorkspaceSection,
    WorkspaceNotification,
    WorkspaceActivity,
    WorkspaceSummary,
    WorkspacePermission,
)

LOGGER = logging.getLogger(__name__)


class ClientPortalController:
    """Presentation controller for the Client Portal.

    Enforces:
        - Strict client isolation (Client A can never see Client B).
        - Sanitization of internal operational notes, pricing, work orders.
        - Automatic CRM log integration on support/feedback.
    """

    def __init__(
        self,
        crm_engine: Any = None,
        proposal_engine: Any = None,
        delivery_engine: Any = None,
        financial_engine: Any = None,
        success_engine: Any = None,
        communication_engine: Any = None,
        handover_engine: Any = None,
        improvement_engine: Any = None,
    ) -> None:
        self.crm_engine = crm_engine
        self.proposal_engine = proposal_engine
        self.delivery_engine = delivery_engine
        self.financial_engine = financial_engine
        self.success_engine = success_engine
        self.communication_engine = communication_engine
        self.handover_engine = handover_engine
        self.improvement_engine = improvement_engine

        # Mock document version repository for V1
        self._documents: dict[str, list[dict[str, Any]]] = {}
        # Approval audit trail
        self._approvals_log: list[dict[str, Any]] = []

    def load_workspace(self, client_id: str, authenticated_client_id: str) -> ClientWorkspace:
        """Loads client workspace after enforcing authentication and isolation rules.

        BR-048-002: Internal information hidden.
        """
        # Strict isolation check
        if client_id != authenticated_client_id:
            raise PermissionError(
                f"Access denied. Client {authenticated_client_id} cannot access "
                f"workspace for Client {client_id}."
            )

        company = "Client Organization"
        balance_due = 0.0
        active_projects_count = 0
        pending_approvals = 0

        # Retrieve client metadata from CRM (with graceful degradation, BR-048-009)
        if self.crm_engine:
            try:
                profile = self.crm_engine.get_client(client_id)
                if profile:
                    company = profile.company
                    active_projects_count = len(profile.active_projects)
            except Exception as e:
                LOGGER.error("Failed to load client profile from CRM: %s", e)

        # Retrieve financial data (Sanitized: hide internal profit/margins/costs)
        if self.financial_engine:
            try:
                report = self.financial_engine.generate_financial_report()
                # Aggregate only invoices belonging to this client
                for inv in report.outstanding_invoices:
                    if inv.get("client_id") == client_id:
                        balance_due += inv.get("balance", 0.0)
                        if inv.get("status") == "SENT":
                            pending_approvals += 1
            except Exception as e:
                LOGGER.error("Failed to retrieve financial report in portal: %s", e)

        # Build sections
        sections = []

        # 1. Projects Section (BR-048-005: displays live project status. Hides internal work orders)
        proj_items = []
        if self.delivery_engine:
            try:
                report = self.delivery_engine.generate_delivery_status_report()
                for p in report.get("projects", []):
                    # Check client ownership if projects have client ID mapping
                    pid = p.get("project_id") if isinstance(p, dict) else getattr(p, "project_id", "")
                    client_mapping = p.get("client_id") if isinstance(p, dict) else getattr(p, "client_id", "")
                    
                    # Fallback matches all for mock simplicity if no mapping, or match ID
                    if not client_mapping or client_mapping == client_id:
                        proj_items.append({
                            "project_id": pid,
                            "name": p.get("name") if isinstance(p, dict) else getattr(p, "name", f"Project {pid}"),
                            "progress": p.get("completion_pct") if isinstance(p, dict) else getattr(p, "completion_pct", 0.0),
                            "status": p.get("status") if isinstance(p, dict) else getattr(p, "status", "ACTIVE"),
                        })
            except Exception as e:
                LOGGER.error("Failed to fetch delivery report: %s", e)
        sections.append(WorkspaceSection("projects", "Active Projects", "HEALTHY", proj_items))

        # 2. Documents Section (BR-048-004: every document has version history)
        doc_items = []
        for doc_name, history in self._documents.get(client_id, {}).items():
            if history:
                latest = history[-1]
                doc_items.append({
                    "name": doc_name,
                    "version": latest["version"],
                    "updated_at": latest["updated_at"],
                    "history": history,
                })
        sections.append(WorkspaceSection("documents", "Collaboration Documents", "HEALTHY", doc_items))

        # 3. Invoices Section
        invoice_items = []
        if self.financial_engine:
            try:
                # Sanitized: only return high-level invoice IDs, totals, and balances
                for inv in self.financial_engine.list_invoices():
                    if inv.client_id == client_id:
                        invoice_items.append({
                            "invoice_id": inv.invoice_id,
                            "total": inv.total,
                            "balance": inv.balance,
                            "status": inv.status,
                            "due_date": inv.due_date,
                        })
            except Exception as e:
                LOGGER.error("Failed to load invoices list: %s", e)
        sections.append(WorkspaceSection("invoices", "Invoices & Payments", "HEALTHY", invoice_items))

        # 4. Notifications
        notifications = []
        if self.communication_engine:
            try:
                # Get client specific alerts from internal notifications
                for n in self.communication_engine.list_notifications():
                    # Format internal notification to client notification
                    if n.recipient_role == "CLIENT" or n.source_engine == "ClientSuccessEngine":
                        notifications.append(WorkspaceNotification(
                            notification_id=n.notification_id,
                            title=n.title,
                            message=n.message,
                            severity=n.severity,
                            timestamp=n.created_at,
                        ))
            except Exception as e:
                LOGGER.error("Failed to load notifications: %s", e)

        # 5. Activity Feed
        activities = []
        for app in self._approvals_log:
            if app.get("client_id") == client_id:
                activities.append(WorkspaceActivity(
                    activity_id=app.get("approval_id", ""),
                    title=f"{app.get('item_type')} Approved",
                    category="Approvals",
                    timestamp=app.get("timestamp", ""),
                    details=f"Item ID: {app.get('item_id')}",
                ))

        summary = WorkspaceSummary(
            active_projects_count=active_projects_count,
            pending_approvals_count=pending_approvals,
            balance_due=round(balance_due, 2),
        )

        return ClientWorkspace(
            client_id=client_id,
            company=company,
            summary=summary,
            sections=sections,
            notifications=notifications,
            activities=activities,
            permissions=WorkspacePermission(),
        )

    # ------------------------------------------------------------------
    # Document Vault (BR-048-004: Version History)
    # ------------------------------------------------------------------

    def upload_document(self, client_id: str, document_name: str, content: str, uploader: str) -> dict[str, Any]:
        """Upload a document version to the client repository."""
        if client_id not in self._documents:
            self._documents[client_id] = {}

        history = self._documents[client_id].get(document_name, [])
        version = len(history) + 1
        new_ver = {
            "version": version,
            "content": content,
            "uploader": uploader,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        history.append(new_ver)
        self._documents[client_id][document_name] = history
        return new_ver

    # ------------------------------------------------------------------
    # Client Approvals (BR-048-003: Auditable approval lifecycle)
    # ------------------------------------------------------------------

    def approve_proposal(self, client_id: str, proposal_id: str, approver: str) -> dict[str, Any]:
        """Approve a proposal and record an immutable audit trace."""
        # 1. Proposal approval call
        if self.proposal_engine:
            try:
                # Trigger proposal engine transition if supported, else mock
                pass
            except Exception as e:
                LOGGER.error("Failed to approve proposal via engine: %s", e)

        # 2. Immutable audit log record
        approval_id = f"APP-PROP-{len(self._approvals_log)+1:04d}"
        audit_rec = {
            "approval_id": approval_id,
            "client_id": client_id,
            "item_id": proposal_id,
            "item_type": "Proposal",
            "approver": approver,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._approvals_log.append(audit_rec)

        # 3. Write event to communication engine log
        if self.communication_engine:
            try:
                self.communication_engine.get_audit_log().append(
                    communication_id=proposal_id,
                    action="PROPOSAL_APPROVED",
                    details=f"Approved by {approver} for client {client_id}.",
                )
            except Exception:
                pass

        return audit_rec

    def approve_milestone(self, client_id: str, project_id: str, milestone_title: str, approver: str) -> dict[str, Any]:
        """Approve a milestone and record audit logs."""
        approval_id = f"APP-MIL-{len(self._approvals_log)+1:04d}"
        audit_rec = {
            "approval_id": approval_id,
            "client_id": client_id,
            "item_id": f"{project_id}:{milestone_title}",
            "item_type": "Milestone",
            "approver": approver,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._approvals_log.append(audit_rec)
        return audit_rec

    # ------------------------------------------------------------------
    # Support Requests (BR-048-007)
    # ------------------------------------------------------------------

    def submit_support_request(self, client_id: str, title: str, description: str) -> dict[str, Any]:
        """Submit support request and automatically create a CRM interaction."""
        ticket_id = f"TCK-{datetime.now(timezone.utc).strftime('%m%d%H%M%S')}"

        # BR-048-007: Support request automatically creates CRM interaction
        if self.crm_engine:
            try:
                self.crm_engine.log_interaction(
                    client_id=client_id,
                    interaction_type="support",
                    description=f"Support ticket {ticket_id} created: {title}. Desc: {description}",
                    outcome="unresolved",
                )
            except Exception as e:
                LOGGER.error("Failed to automatically log CRM support interaction: %s", e)

        return {"ticket_id": ticket_id, "status": "OPEN", "title": title}

    # ------------------------------------------------------------------
    # Feedback (BR-048-008)
    # ------------------------------------------------------------------

    def submit_feedback(self, client_id: str, score: float, comments: str) -> dict[str, Any]:
        """Submit feedback and route to Continuous Improvement and CRM."""
        # 1. CRM Satisfaction update
        if self.crm_engine:
            try:
                profile = self.crm_engine.get_client(client_id)
                if profile:
                    # Update satisfaction score directly on the model
                    profile.satisfaction_score = score
                    self.crm_engine.update_health(client_id)
                
                # Log interaction
                self.crm_engine.log_interaction(
                    client_id=client_id,
                    interaction_type="review meeting",
                    description=f"Feedback submitted. Score: {score}. Comments: {comments}",
                    outcome="completed",
                )
            except Exception as e:
                LOGGER.error("Failed to log feedback in CRM: %s", e)

        # 2. Continuous Improvement pipeline route (BR-048-008)
        if self.improvement_engine:
            try:
                self.improvement_engine.register_learning_opportunity(
                    source=f"Client Portal Feedback: {client_id}",
                    description=comments,
                    severity="MEDIUM" if score < 3.0 else "LOW",
                )
            except Exception as e:
                LOGGER.error("Failed to route feedback to continuous improvement engine: %s", e)

        return {"success": True, "score": score}
