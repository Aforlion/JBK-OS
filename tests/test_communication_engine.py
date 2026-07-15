import unittest
from datetime import datetime, timezone, timedelta

from core.communication import Communication, IMMUTABLE_STATUSES
from core.notification import Notification
from core.communication_log import CommunicationLog
from core.communication_report import CommunicationReport
from core.communication_engine import CommunicationEngine


class TestCommunicationModel(unittest.TestCase):

    def test_valid_communication(self) -> None:
        comm = Communication(
            communication_id="COM-0001",
            channel="Email",
            sender="ceo@jbk.com",
            recipient="client@example.com",
            subject="Proposal",
            message="Please find attached.",
            source_engine="ProposalGenerator",
            triggering_event="proposal_approved",
            reasoning="Client requested proposal delivery.",
        )
        self.assertEqual(comm.status, "DRAFT")
        self.assertEqual(comm.channel, "Email")

    def test_invalid_channel_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Communication(communication_id="COM-0001", channel="Fax")

    def test_immutability_after_sent(self) -> None:
        """BR-045-004: Content immutable after SENT."""
        comm = Communication(
            communication_id="COM-0001",
            channel="Email",
            subject="Original",
            message="Original message",
        )
        comm.mark_sent()
        self.assertEqual(comm.status, "SENT")

        with self.assertRaises(ValueError) as ctx:
            comm.update_content(subject="Modified")
        self.assertIn("immutable", str(ctx.exception))

    def test_serialization(self) -> None:
        """BR-045-010: Serializable."""
        comm = Communication(
            communication_id="COM-0001",
            channel="Slack",
            source_engine="CRMEngine",
        )
        d = comm.to_dict()
        self.assertEqual(d["communication_id"], "COM-0001")
        self.assertEqual(d["source_engine"], "CRMEngine")
        self.assertIn("triggering_event", d)

    def test_explainability_metadata(self) -> None:
        """BR-045-009: source_engine, triggering_event, reasoning present."""
        comm = Communication(
            communication_id="COM-0001",
            channel="Email",
            source_engine="FinancialOps",
            triggering_event="invoice_created",
            reasoning="Invoice INV-0001 needs to be sent to client.",
        )
        self.assertEqual(comm.source_engine, "FinancialOps")
        self.assertEqual(comm.triggering_event, "invoice_created")
        self.assertIn("INV-0001", comm.reasoning)


class TestNotificationModel(unittest.TestCase):

    def test_valid_notification(self) -> None:
        notif = Notification(
            notification_id="NTF-0001",
            title="Invoice Overdue",
            message="Invoice INV-0001 is overdue by 15 days.",
            recipient_role="CEO",
            severity="HIGH",
            source_engine="FinancialOperationsEngine",
            action_required="Review and escalate collection.",
        )
        self.assertEqual(notif.severity, "HIGH")
        self.assertTrue(notif.is_ceo_briefing)

    def test_mandatory_fields_enforced(self) -> None:
        """BR-045-005: severity, source_engine, timestamp, action_required all mandatory."""
        with self.assertRaises(ValueError):
            Notification(
                notification_id="NTF-0001",
                title="Test",
                message="Test",
                recipient_role="CEO",
                severity="HIGH",
                source_engine="",  # missing
                action_required="Do something",
            )

        with self.assertRaises(ValueError):
            Notification(
                notification_id="NTF-0001",
                title="Test",
                message="Test",
                recipient_role="CEO",
                severity="HIGH",
                source_engine="Engine",
                action_required="",  # missing
            )

    def test_ceo_briefing_flag(self) -> None:
        """BR-045-006: HIGH severity is CEO briefing."""
        high = Notification(
            notification_id="NTF-0001", title="Alert", message="Critical",
            recipient_role="CEO", severity="HIGH",
            source_engine="Engine", action_required="Act now",
        )
        low = Notification(
            notification_id="NTF-0002", title="Info", message="Normal",
            recipient_role="Manager", severity="LOW",
            source_engine="Engine", action_required="Review",
        )
        self.assertTrue(high.is_ceo_briefing)
        self.assertFalse(low.is_ceo_briefing)

    def test_notification_serialization(self) -> None:
        notif = Notification(
            notification_id="NTF-0001", title="Test", message="Body",
            recipient_role="CEO", severity="MEDIUM",
            source_engine="Engine", action_required="Review",
        )
        d = notif.to_dict()
        self.assertEqual(d["notification_id"], "NTF-0001")
        self.assertIn("is_ceo_briefing", d)


class TestCommunicationLog(unittest.TestCase):

    def test_append_and_search(self) -> None:
        log = CommunicationLog()
        log.append("COM-0001", "CREATED", "Email generated")
        log.append("COM-0001", "QUEUED", "Message queued")
        log.append("COM-0002", "FAILED", "Delivery failed: timeout")

        results = log.search("FAILED")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].communication_id, "COM-0002")

    def test_filter_by_communication_id(self) -> None:
        log = CommunicationLog()
        log.append("COM-0001", "CREATED", "Created")
        log.append("COM-0001", "QUEUED", "Queued")
        log.append("COM-0002", "CREATED", "Created")

        results = log.filter(communication_id="COM-0001")
        self.assertEqual(len(results), 2)

    def test_summary(self) -> None:
        log = CommunicationLog()
        log.append("COM-0001", "CREATED", "")
        log.append("COM-0002", "CREATED", "")
        log.append("COM-0001", "SENT", "")

        summary = log.summary()
        self.assertEqual(summary["total_entries"], 3)
        self.assertEqual(summary["actions"]["CREATED"], 2)
        self.assertEqual(summary["actions"]["SENT"], 1)


class TestCommunicationEngine(unittest.TestCase):

    def test_generate_email(self) -> None:
        engine = CommunicationEngine()
        comm = engine.generate_email(
            sender="ceo@jbk.com",
            recipient="client@example.com",
            subject="Proposal Delivery",
            message="Attached is your proposal.",
            source_engine="ProposalGenerator",
            triggering_event="proposal_approved",
            reasoning="Proposal PROP-0001 was approved by CEO.",
        )
        self.assertEqual(comm.communication_id, "COM-0001")
        self.assertEqual(comm.channel, "Email")
        self.assertEqual(comm.status, "DRAFT")
        self.assertEqual(comm.source_engine, "ProposalGenerator")

    def test_email_requires_sender_and_recipient(self) -> None:
        engine = CommunicationEngine()
        with self.assertRaises(ValueError):
            engine.generate_email(sender="", recipient="a@b.com", subject="Test", message="Body")
        with self.assertRaises(ValueError):
            engine.generate_email(sender="a@b.com", recipient="", subject="Test", message="Body")

    def test_unique_ids(self) -> None:
        """BR-045-001: Every communication gets a unique ID."""
        engine = CommunicationEngine()
        c1 = engine.generate_email(sender="a@b.com", recipient="c@d.com", subject="S1", message="M1")
        c2 = engine.generate_email(sender="a@b.com", recipient="c@d.com", subject="S2", message="M2")
        self.assertNotEqual(c1.communication_id, c2.communication_id)

    def test_queue_message(self) -> None:
        engine = CommunicationEngine()
        comm = engine.generate_email(sender="a@b.com", recipient="c@d.com", subject="S", message="M")
        queued = engine.queue_message(comm.communication_id)
        self.assertEqual(queued.status, "QUEUED")

    def test_queue_only_from_draft(self) -> None:
        engine = CommunicationEngine()
        comm = engine.generate_email(sender="a@b.com", recipient="c@d.com", subject="S", message="M")
        engine.queue_message(comm.communication_id)
        with self.assertRaises(ValueError):
            engine.queue_message(comm.communication_id)  # Already QUEUED

    def test_record_delivery(self) -> None:
        engine = CommunicationEngine()
        comm = engine.generate_email(sender="a@b.com", recipient="c@d.com", subject="S", message="M")
        engine.queue_message(comm.communication_id)
        delivered = engine.record_delivery(comm.communication_id)
        self.assertEqual(delivered.status, "DELIVERED")
        self.assertIsNotNone(delivered.sent_at)

    def test_immutability_after_delivery(self) -> None:
        """BR-045-004: Content immutable after delivery."""
        engine = CommunicationEngine()
        comm = engine.generate_email(sender="a@b.com", recipient="c@d.com", subject="S", message="M")
        engine.queue_message(comm.communication_id)
        engine.record_delivery(comm.communication_id)

        with self.assertRaises(ValueError):
            comm.update_content(subject="Changed")

    def test_record_failure(self) -> None:
        """BR-045-003: Failed deliveries remain searchable."""
        engine = CommunicationEngine()
        comm = engine.generate_email(sender="a@b.com", recipient="c@d.com", subject="S", message="M")
        engine.record_failure(comm.communication_id, reason="SMTP timeout")
        self.assertEqual(comm.status, "FAILED")

        # Searchable in history
        results = engine.search_history("FAILED")
        self.assertTrue(len(results) > 0)

    def test_audit_trail_on_every_action(self) -> None:
        """BR-045-002: Nothing without an audit log."""
        engine = CommunicationEngine()
        comm = engine.generate_email(sender="a@b.com", recipient="c@d.com", subject="S", message="M")
        engine.queue_message(comm.communication_id)
        engine.record_delivery(comm.communication_id)

        log = engine.get_audit_log()
        entries = log.filter(communication_id=comm.communication_id)
        actions = [e.action for e in entries]
        self.assertIn("CREATED", actions)
        self.assertIn("QUEUED", actions)
        self.assertIn("SENT", actions)
        self.assertIn("DELIVERED", actions)

    def test_duplicate_notification_suppression(self) -> None:
        """BR-045-007: Duplicate notifications within window are merged."""
        engine = CommunicationEngine(suppression_window_seconds=300)
        n1 = engine.generate_notification(
            title="Invoice Overdue", message="INV-0001 overdue",
            recipient_role="CEO", severity="HIGH",
            source_engine="FinancialOps", action_required="Review",
        )
        n2 = engine.generate_notification(
            title="Invoice Overdue", message="INV-0001 overdue again",
            recipient_role="CEO", severity="HIGH",
            source_engine="FinancialOps", action_required="Review",
        )
        # Should return the same notification (merged)
        self.assertEqual(n1.notification_id, n2.notification_id)
        self.assertEqual(len(engine.list_notifications()), 1)

    def test_ceo_briefing_notifications(self) -> None:
        """BR-045-006: HIGH severity in CEO briefing list."""
        engine = CommunicationEngine()
        engine.generate_notification(
            title="Critical Alert", message="System down",
            recipient_role="CEO", severity="HIGH",
            source_engine="AutonomousOps", action_required="Investigate immediately",
        )
        engine.generate_notification(
            title="Info Update", message="Report ready",
            recipient_role="Manager", severity="LOW",
            source_engine="ReportEngine", action_required="Review report",
        )

        ceo_items = engine.get_ceo_briefing_notifications()
        self.assertEqual(len(ceo_items), 1)
        self.assertEqual(ceo_items[0].title, "Critical Alert")

    def test_generate_report(self) -> None:
        engine = CommunicationEngine()
        c1 = engine.generate_email(sender="a@b.com", recipient="c@d.com", subject="S1", message="M1")
        c2 = engine.generate_email(sender="a@b.com", recipient="e@f.com", subject="S2", message="M2")
        engine.queue_message(c1.communication_id)
        engine.record_delivery(c1.communication_id)
        engine.record_failure(c2.communication_id, reason="Rejected")

        engine.generate_notification(
            title="Alert", message="Test",
            recipient_role="CEO", severity="MEDIUM",
            source_engine="Engine", action_required="Review",
        )

        report = engine.generate_report()
        self.assertEqual(report.total_generated, 2)
        self.assertEqual(report.total_sent, 1)
        self.assertEqual(report.total_failed, 1)
        self.assertEqual(report.unread_notifications, 1)
        self.assertEqual(len(report.failures), 1)
        self.assertTrue(len(report.recommendations) > 0)

    def test_report_serialization(self) -> None:
        report = CommunicationReport(
            report_id="COMREP-TEST",
            total_generated=5,
            total_sent=3,
            total_failed=1,
            total_pending=1,
            unread_notifications=2,
        )
        d = report.to_dict()
        self.assertEqual(d["report_id"], "COMREP-TEST")
        self.assertEqual(d["total_generated"], 5)

    def test_advisory_boundary_no_direct_send(self) -> None:
        """BR-045-008: Engine returns Communication objects, never sends directly.
        Verify engine only produces objects — no side effects beyond logging."""
        engine = CommunicationEngine()
        comm = engine.generate_email(
            sender="a@b.com", recipient="c@d.com",
            subject="Test", message="Body",
        )
        # Communication is DRAFT — engine did not send
        self.assertEqual(comm.status, "DRAFT")
        # Even after queueing, engine just transitions status
        engine.queue_message(comm.communication_id)
        self.assertEqual(comm.status, "QUEUED")


if __name__ == "__main__":
    unittest.main()
