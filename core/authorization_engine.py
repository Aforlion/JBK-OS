from __future__ import annotations

import logging
from typing import Any

from core.identity import Identity
from core.access_control import ROLE_POLICIES, AuthorizationDecision

LOGGER = logging.getLogger(__name__)

# Hard decision boundaries - no role overrides these
# Maps action -> set of denied identity_types or roles
_CLIENT_FORBIDDEN = {
    "view_strategic_intel",
    "view_executive_meetings",
    "access_knowledge_registry",
    "modify_work_orders",
    "approve_spending",
    "sign_contracts",
    "hire_staff",
    "view_financials",
    "create_project",
    "trigger_quick_action",
}

_AI_EXECUTIVE_FORBIDDEN = {
    "approve_spending",
    "sign_contracts",
    "hire_staff",
    "approve_milestone",
    "approve_proposal",
}


class AuthorizationEngine:
    """Evaluates whether an identity can perform an action.

    BR-051-002: Least-privilege access.
    BR-051-003: Unauthorized actions are denied.
    BR-051-004: Decision boundaries are immutable.
    BR-051-007: Every decision is explainable.
    """

    def __init__(self, monitoring_engine: Any = None) -> None:
        self.monitoring_engine = monitoring_engine

    def can_execute(self, identity: Identity, action: str, resource: str = "") -> AuthorizationDecision:
        """Check if the given identity can perform the specified action.

        Returns an AuthorizationDecision with reason and code.
        """
        # BR-051-004: Hard boundary enforcement first (before any role checks)
        if identity.identity_type == "CLIENT" and action in _CLIENT_FORBIDDEN:
            decision = AuthorizationDecision(
                authorized=False,
                reason=f"Clients are not authorized to perform '{action}'. This is a protected executive operation.",
                code="DENIED",
            )
            self._audit_decision(identity.identity_id, action, resource, decision)
            return decision

        if identity.identity_type == "AI" and action in _AI_EXECUTIVE_FORBIDDEN:
            decision = AuthorizationDecision(
                authorized=False,
                reason=f"AI Executives cannot perform '{action}'. Decision boundaries enforce human-only oversight.",
                code="DENIED",
            )
            self._audit_decision(identity.identity_id, action, resource, decision)
            return decision

        # Check account status
        if identity.status != "ACTIVE":
            decision = AuthorizationDecision(
                authorized=False,
                reason=f"Identity is {identity.status}. Access denied.",
                code="DENIED",
            )
            self._audit_decision(identity.identity_id, action, resource, decision)
            return decision

        # Build effective permission set from roles (BR-051-002: least-privilege)
        effective_permissions: set[str] = set()
        for role in identity.roles:
            effective_permissions.update(ROLE_POLICIES.get(role, set()))
        # Also include any directly assigned permissions
        effective_permissions.update(identity.permissions)

        if action in effective_permissions:
            decision = AuthorizationDecision(
                authorized=True,
                reason=f"'{action}' is permitted via roles: {identity.roles}.",
                code="AUTHORIZED",
            )
            self._audit_decision(identity.identity_id, action, resource, decision)
            return decision

        # Not found in any role policy
        decision = AuthorizationDecision(
            authorized=False,
            reason=f"'{action}' is not in the permission set for roles: {identity.roles}.",
            code="DENIED",
        )
        self._audit_decision(identity.identity_id, action, resource, decision)
        return decision

    def _audit_decision(self, actor: str, action: str, resource: str, decision: AuthorizationDecision) -> None:
        LOGGER.info(
            "authz action=%s actor=%s resource=%s result=%s reason=%s",
            action, actor, resource, decision.code, decision.reason,
        )
        if self.monitoring_engine:
            try:
                self.monitoring_engine.record_audit(
                    actor=actor,
                    action=f"AUTHZ:{action}",
                    target=resource or action,
                    outcome=decision.code,
                    explanation=decision.reason,
                )
            except Exception:
                pass
