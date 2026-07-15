from __future__ import annotations

import unittest
from datetime import datetime, timezone, timedelta

from core.identity import Identity
from core.access_control import AuthorizationDecision
from core.session import Session
from core.secret_reference import SecretReference
from core.authentication_manager import AuthenticationManager
from core.authorization_engine import AuthorizationEngine


# ---------------------------------------------------------------------------
# Helper Factories
# ---------------------------------------------------------------------------

def _make_ceo() -> Identity:
    return Identity("CEO-001", "James Blackwood", "EXECUTIVE", roles=["CEO"])


def _make_client() -> Identity:
    return Identity("CLI-001", "Acme Corp", "CLIENT", roles=["CLIENT"])


def _make_ai_exec() -> Identity:
    return Identity("AI-001", "Software Engineer AI", "AI", roles=["AI_EXECUTIVE"])


def _make_svc_account() -> Identity:
    return Identity("SVC-001", "Telemetry Bot", "SERVICE_ACCOUNT", roles=["SERVICE_ACCOUNT"])


def _make_auth() -> AuthenticationManager:
    mgr = AuthenticationManager()
    for identity in [_make_ceo(), _make_client(), _make_ai_exec(), _make_svc_account()]:
        mgr.register_identity(identity, password_hash=f"hash_{identity.identity_id}")
    return mgr


# ---------------------------------------------------------------------------
# Identity Tests
# ---------------------------------------------------------------------------

class TestIdentityModel(unittest.TestCase):

    def test_valid_identity_creation(self) -> None:
        identity = _make_ceo()
        self.assertEqual(identity.identity_id, "CEO-001")
        self.assertEqual(identity.identity_type, "EXECUTIVE")
        self.assertIn("CEO", identity.roles)

    def test_invalid_identity_type_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Identity("X", "Bad Actor", "ALIEN")

    def test_invalid_status_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Identity("X", "Test", "CLIENT", status="SUSPENDED")

    def test_serialization(self) -> None:
        """BR-051-009: Permissions are serializable."""
        d = _make_ceo().to_dict()
        self.assertEqual(d["identity_id"], "CEO-001")
        self.assertEqual(d["roles"], ["CEO"])
        self.assertIn("created_at", d)


# ---------------------------------------------------------------------------
# Session Tests
# ---------------------------------------------------------------------------

class TestSessionModel(unittest.TestCase):

    def test_active_session_valid(self) -> None:
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        session = Session("SES-0001", "CEO-001", expires_at=future)
        self.assertTrue(session.is_valid())

    def test_expired_session_is_invalid(self) -> None:
        """BR-051-008: Expired sessions are invalid."""
        past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        session = Session("SES-0002", "CEO-001", expires_at=past)
        self.assertFalse(session.is_valid())
        self.assertEqual(session.status, "EXPIRED")

    def test_terminated_session_is_invalid(self) -> None:
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        session = Session("SES-0003", "CEO-001", expires_at=future)
        session.terminate()
        self.assertFalse(session.is_valid())
        self.assertEqual(session.status, "TERMINATED")

    def test_session_serialization(self) -> None:
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        d = Session("SES-0004", "CLI-001", expires_at=future).to_dict()
        self.assertEqual(d["session_id"], "SES-0004")
        self.assertEqual(d["status"], "ACTIVE")


# ---------------------------------------------------------------------------
# SecretReference Tests
# ---------------------------------------------------------------------------

class TestSecretReference(unittest.TestCase):

    def test_reference_stores_no_plaintext(self) -> None:
        """BR-051-005: Secrets are never exposed."""
        ref = SecretReference("api-key-001", "GitHub")
        self.assertNotIn("secret", ref.to_dict())
        self.assertNotIn("password", ref.to_dict())
        self.assertIn("reference_hash", ref.to_dict())

    def test_reference_serialization(self) -> None:
        ref = SecretReference("sk_live_abc", "Stripe")
        d = ref.to_dict()
        self.assertEqual(d["provider"], "Stripe")
        self.assertNotEqual(d["reference_hash"], "sk_live_abc")


# ---------------------------------------------------------------------------
# AuthenticationManager Tests
# ---------------------------------------------------------------------------

class TestAuthenticationManager(unittest.TestCase):

    def setUp(self) -> None:
        self.auth = _make_auth()

    def test_successful_login_creates_session(self) -> None:
        session = self.auth.login("CEO-001", "hash_CEO-001")
        self.assertIsNotNone(session)
        self.assertEqual(session.identity_id, "CEO-001")
        self.assertTrue(session.is_valid())

    def test_wrong_password_raises(self) -> None:
        with self.assertRaises(PermissionError):
            self.auth.login("CEO-001", "wrong_password")

    def test_account_locks_after_three_failures(self) -> None:
        for _ in range(3):
            try:
                self.auth.login("CLI-001", "bad_hash")
            except PermissionError:
                pass

        # Account should now be LOCKED
        identity = self.auth._identities["CLI-001"]
        self.assertEqual(identity.status, "LOCKED")

    def test_locked_account_blocks_login(self) -> None:
        identity = self.auth._identities["AI-001"]
        identity.status = "LOCKED"
        with self.assertRaises(PermissionError):
            self.auth.login("AI-001", "hash_AI-001")

    def test_logout_terminates_session(self) -> None:
        session = self.auth.login("SVC-001", "hash_SVC-001")
        self.auth.logout(session.session_id)
        retrieved = self.auth.get_session(session.session_id)
        self.assertIsNone(retrieved)

    def test_expired_session_not_returned_by_get_session(self) -> None:
        """BR-051-008: Expired sessions return None."""
        session = self.auth.login("CEO-001", "hash_CEO-001")
        # Manually expire
        session.expires_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        retrieved = self.auth.get_session(session.session_id)
        self.assertIsNone(retrieved)

    def test_unknown_identity_fails_safely(self) -> None:
        """BR-051-010: Security failures never expose sensitive details."""
        with self.assertRaises(PermissionError) as ctx:
            self.auth.login("GHOST-999", "anything")
        # Error must not expose internal data
        self.assertNotIn("Identity not found", str(ctx.exception))


# ---------------------------------------------------------------------------
# AuthorizationEngine Tests
# ---------------------------------------------------------------------------

class TestAuthorizationEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = AuthorizationEngine()

    def test_ceo_can_view_strategic_intel(self) -> None:
        decision = self.engine.can_execute(_make_ceo(), "view_strategic_intel")
        self.assertTrue(decision.authorized)
        self.assertEqual(decision.code, "AUTHORIZED")

    def test_client_denied_strategic_intel(self) -> None:
        """BR-051-004: Client hard boundary enforced."""
        decision = self.engine.can_execute(_make_client(), "view_strategic_intel")
        self.assertFalse(decision.authorized)
        self.assertEqual(decision.code, "DENIED")

    def test_client_denied_executive_meetings(self) -> None:
        decision = self.engine.can_execute(_make_client(), "view_executive_meetings")
        self.assertFalse(decision.authorized)

    def test_client_denied_modify_work_orders(self) -> None:
        decision = self.engine.can_execute(_make_client(), "modify_work_orders")
        self.assertFalse(decision.authorized)

    def test_client_can_view_own_workspace(self) -> None:
        decision = self.engine.can_execute(_make_client(), "view_client_workspace")
        self.assertTrue(decision.authorized)

    def test_ai_exec_can_create_deliverables(self) -> None:
        decision = self.engine.can_execute(_make_ai_exec(), "create_deliverables")
        self.assertTrue(decision.authorized)

    def test_ai_exec_cannot_approve_spending(self) -> None:
        """BR-051-004: AI decision boundary — financial approval forbidden."""
        decision = self.engine.can_execute(_make_ai_exec(), "approve_spending")
        self.assertFalse(decision.authorized)
        self.assertIn("human-only oversight", decision.reason)

    def test_ai_exec_cannot_sign_contracts(self) -> None:
        decision = self.engine.can_execute(_make_ai_exec(), "sign_contracts")
        self.assertFalse(decision.authorized)

    def test_ai_exec_cannot_hire_staff(self) -> None:
        decision = self.engine.can_execute(_make_ai_exec(), "hire_staff")
        self.assertFalse(decision.authorized)

    def test_locked_identity_denied(self) -> None:
        identity = _make_ceo()
        identity.status = "LOCKED"
        decision = self.engine.can_execute(identity, "view_strategic_intel")
        self.assertFalse(decision.authorized)
        self.assertIn("LOCKED", decision.reason)

    def test_least_privilege_unknown_action_denied(self) -> None:
        """BR-051-002: Least privilege — unknown action is denied."""
        decision = self.engine.can_execute(_make_client(), "delete_database")
        self.assertFalse(decision.authorized)

    def test_decision_is_explainable(self) -> None:
        """BR-051-007: Every authorization decision is explainable."""
        decision = self.engine.can_execute(_make_client(), "view_strategic_intel")
        self.assertIsNotNone(decision.reason)
        self.assertGreater(len(decision.reason), 5)

    def test_decision_serialization(self) -> None:
        """BR-051-009: Authorization decisions serialize."""
        decision = self.engine.can_execute(_make_ceo(), "approve_spending")
        d = decision.to_dict()
        self.assertIn("authorized", d)
        self.assertIn("reason", d)
        self.assertIn("code", d)


if __name__ == "__main__":
    unittest.main()
