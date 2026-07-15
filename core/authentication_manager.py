from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone, timedelta

from core.identity import Identity
from core.session import Session

LOGGER = logging.getLogger(__name__)


class AuthenticationManager:
    """Manages credentials checks, sessions, and lock counts.

    BR-051-006: Every authentication event is audited.
    Locks account after 3 consecutive failures.
    """

    def __init__(self, monitoring_engine: Any = None) -> None:
        self.monitoring_engine = monitoring_engine
        self._identities: dict[str, Identity] = {}
        # Maps identity_id -> raw password hash mock
        self._passwords: dict[str, str] = {}
        # Maps identity_id -> failed count
        self._failed_attempts: dict[str, int] = {}
        self._sessions: dict[str, Session] = {}
        
        self._session_counter = 1

    def register_identity(self, identity: Identity, password_hash: str) -> None:
        self._identities[identity.identity_id] = identity
        self._passwords[identity.identity_id] = password_hash
        self._failed_attempts[identity.identity_id] = 0

    def login(self, identity_id: str, password_hash: str, session_lifetime_minutes: int = 30) -> Session:
        """Authenticate user and return a Session if successful.

        Locks account after 3 failed attempts. Audits events.
        """
        identity = self._identities.get(identity_id)
        if not identity:
            self._audit_auth(actor="SYSTEM", action="LOGIN_FAILED", target=identity_id, explanation="Identity not found.")
            # Fail safely (BR-051-010: fail safe without info leak)
            raise PermissionError("Authentication failed.")

        if identity.status == "LOCKED":
            self._audit_auth(actor=identity_id, action="LOGIN_FAILED", target=identity_id, explanation="Account locked.")
            raise PermissionError("Account is locked.")

        # Check password hash mock
        expected = self._passwords.get(identity_id)
        if expected != password_hash:
            self._failed_attempts[identity_id] = self._failed_attempts.get(identity_id, 0) + 1
            if self._failed_attempts[identity_id] >= 3:
                identity.status = "LOCKED"
                self._audit_auth(actor=identity_id, action="ACCOUNT_LOCKED", target=identity_id, explanation="Locked due to 3 failed attempts.")
            else:
                self._audit_auth(actor=identity_id, action="LOGIN_FAILED", target=identity_id, explanation="Invalid password.")
            raise PermissionError("Authentication failed.")

        # Success: reset fail count
        self._failed_attempts[identity_id] = 0
        identity.last_login = datetime.now(timezone.utc).isoformat()

        # Create session
        sess_id = f"SES-{self._session_counter:04d}"
        self._session_counter += 1

        exp_time = (datetime.now(timezone.utc) + timedelta(minutes=session_lifetime_minutes)).isoformat()
        session = Session(
            session_id=sess_id,
            identity_id=identity_id,
            expires_at=exp_time,
        )
        self._sessions[sess_id] = session

        self._audit_auth(actor=identity_id, action="LOGIN_SUCCESS", target=sess_id, explanation="Session created.")
        return session

    def logout(self, session_id: str) -> None:
        """Terminate an active session."""
        session = self._sessions.get(session_id)
        if session:
            session.terminate()
            self._audit_auth(actor=session.identity_id, action="LOGOUT", target=session_id, explanation="Logged out.")

    def get_session(self, session_id: str) -> Session | None:
        session = self._sessions.get(session_id)
        if session and session.is_valid():
            return session
        return None

    def _audit_auth(self, actor: str, action: str, target: str, explanation: str) -> None:
        """Audit events via monitoring or standard logging."""
        LOGGER.info("auth_event action=%s actor=%s target=%s explanation=%s", action, actor, target, explanation)
        if self.monitoring_engine:
            self.monitoring_engine.record_audit(
                actor=actor,
                action=action,
                target=target,
                outcome="SUCCESS" if "SUCCESS" in action or action == "LOGOUT" else "FAILED",
                explanation=explanation,
            )
