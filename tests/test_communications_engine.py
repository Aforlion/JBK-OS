import unittest
from datetime import datetime, timezone, timedelta
from core.communication_message import CommunicationMessage
from core.notification import Notification
from core.message_thread import MessageThread
from core.communications_engine import CommunicationsEngine


class TestCommunicationMessageModel(unittest.TestCase):

    def test_message_creation_and_defaults(self) -> None:
        msg = CommunicationMessage(
            message_id="MSG-0001",
            sender="ceo",
            recipients=["cos"],
            subject="Briefing",
            body="Review required",
        )
        self.assertEqual(msg.status, "DRAFT")
        self.assertEqual(msg.priority, "NORMAL")
        self.assertEqual(msg.priority_weight, 2)

    def test_message_priority_weights(self) -> None:
        c = CommunicationMessage("M1", "s", ["r"], "sub", "body", priority="CRITICAL")
        h = CommunicationMessage("M2", "s", ["r"], "sub", "body", priority="HIGH")
        n = CommunicationMessage("M3", "s", ["r"], "sub", "body", priority="NORMAL")
        l = CommunicationMessage("M4", "s", ["r"], "sub", "body", priority="LOW")

        self.assertEqual(c.priority_weight, 4)
        self.assertEqual(h.priority_weight, 3)
        self.assertEqual(n.priority_weight, 2)
        self.assertEqual(l.priority_weight, 1)

    def test_message_immutability(self) -> None:
        """BR-049-001: Every communication is immutable once marked SENT."""
        msg = CommunicationMessage("M1", "s", ["r"], "Original Subject", "Original Body")
        msg.mark_status("SENT")

        with self.assertRaises(ValueError):
            msg.update_content("New Subject", "New Body")

    def test_serialization(self) -> None:
        """BR-049-006: Communications are fully serializable."""
        msg = CommunicationMessage("M1", "s", ["r"], "Sub", "Body")
        d = msg.to_dict()
        self.assertEqual(d["message_id"], "M1")
        self.assertEqual(d["subject"], "Sub")


class TestMessageThreadModel(unittest.TestCase):

    def test_thread_boundaries(self) -> None:
        thread = MessageThread(
            thread_id="THR-0001",
            subject="Client Discuss",
            participants=["CLT-0001"],
            metadata={"client_isolated": True, "client_id": "CLT-0001"},
        )
        self.assertTrue(thread.is_client_isolated())
        self.assertFalse(thread.is_executive_internal())

        msg = CommunicationMessage("M1", "ceo", ["CLT-0001"], "Sub", "Body")
        thread.add_message(msg)
        self.assertIn("ceo", thread.participants)


class TestCommunicationsEngine(unittest.TestCase):

    def test_send_message_immediate(self) -> None:
        engine = CommunicationsEngine()
        msg = engine.send_message(
            sender="ceo",
            recipients=["cos"],
            subject="Immediate Review",
            body="Look at this.",
        )
        self.assertEqual(msg.status, "DELIVERED")
        self.assertIsNotNone(msg.delivered_at)

        # Verify inbox routing
        inbox = engine.get_inbox("cos")
        self.assertEqual(len(inbox), 1)
        self.assertEqual(inbox[0].message_id, msg.message_id)

    def test_send_message_scheduled(self) -> None:
        engine = CommunicationsEngine()
        future_time = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        msg = engine.send_message(
            sender="ceo",
            recipients=["cos"],
            subject="Delayed Review",
            body="Review later.",
            scheduled_at=future_time,
        )
        self.assertEqual(msg.status, "QUEUED")
        self.assertEqual(msg.scheduled_at, future_time)

        # Not routed to inbox yet
        inbox = engine.get_inbox("cos")
        self.assertEqual(len(inbox), 0)

    def test_send_notification_success(self) -> None:
        engine = CommunicationsEngine()
        notif = engine.send_notification(
            title="Work Order Assigned",
            message="WO-0001 is assigned to you.",
            recipient_role="PM",
            severity="MEDIUM",
            source_engine="WorkBreakdownEngine",
            action_required="Acknowledge and start.",
        )
        self.assertIsNotNone(notif)
        self.assertEqual(notif.severity, "MEDIUM")
        self.assertEqual(notif.category, "General")

    def test_notification_duplicate_suppression(self) -> None:
        """BR-049-003: Duplicate notifications are automatically suppressed."""
        engine = CommunicationsEngine(duplicate_suppression_window_seconds=10)
        
        n1 = engine.send_notification(
            title="Blocker", message="CRITICAL BLOCKER", recipient_role="CEO",
            severity="CRITICAL", source_engine="Delivery", action_required="Fix",
        )
        n2 = engine.send_notification(
            title="Blocker", message="CRITICAL BLOCKER", recipient_role="CEO",
            severity="CRITICAL", source_engine="Delivery", action_required="Fix",
        )

        self.assertIsNotNone(n1)
        self.assertIsNone(n2)  # Suppressed duplicate
        self.assertEqual(len(engine.get_notifications()), 1)

    def test_retry_failure_escalation(self) -> None:
        """BR-049-004: Delivery failures are retried, then escalated to DLQ."""
        engine = CommunicationsEngine()
        msg = engine.send_message("ceo", ["cos"], "Task", "Do it")
        
        # Simulate redelivery failures
        engine.queue_for_retry(msg.message_id, "Timeout")
        self.assertEqual(msg.status, "FAILED")
        self.assertEqual(len(engine.get_dead_letter_queue()), 0)

        # Retry 2
        engine.queue_for_retry(msg.message_id, "Timeout again")
        # Retry 3
        engine.queue_for_retry(msg.message_id, "Timeout again again")
        # Retry 4 (Exceeds limit of 3)
        engine.queue_for_retry(msg.message_id, "DLQ Trigger")
        
        self.assertEqual(len(engine.get_dead_letter_queue()), 1)
        self.assertEqual(engine.get_dead_letter_queue()[0]["message_id"], msg.message_id)

    def test_retry_queue_priority_sorting(self) -> None:
        """BR-049-007: Priority determines retry delivery order."""
        engine = CommunicationsEngine()
        m_low = engine.send_message("s", ["r"], "Low Priority", "Body", priority="LOW")
        m_crit = engine.send_message("s", ["r"], "Critical Priority", "Body", priority="CRITICAL")

        # Force fail both
        engine.queue_for_retry(m_low.message_id, "Failed")
        engine.queue_for_retry(m_crit.message_id, "Failed")

        # Process retry queue
        engine.process_retry_queue()

        # Check delivered status
        self.assertEqual(m_crit.status, "DELIVERED")
        self.assertEqual(m_low.status, "DELIVERED")

    def test_client_isolation_enforced(self) -> None:
        """BR-049-008: Client conversations remain isolated."""
        engine = CommunicationsEngine()
        msg = engine.send_message(
            sender="ceo",
            recipients=["CLT-0002"],
            subject="Private Info",
            body="Secrets",
            metadata={"client_isolated": True, "client_id": "CLT-0001"},
        )
        # Should not route to CLT-0002 due to client isolation check matching client_id CLT-0001
        inbox_b = engine.get_inbox("CLT-0002")
        self.assertEqual(len(inbox_b), 0)

    def test_executive_conversation_isolation(self) -> None:
        """BR-049-009: Executive conversations are internal only."""
        engine = CommunicationsEngine()
        msg = engine.send_message(
            sender="ceo",
            recipients=["CLT-0001"],
            subject="Discussion",
            body="Internal review notes",
            metadata={"executive_internal": True},
        )
        # Blocked routing to Client CLT-0001
        inbox_client = engine.get_inbox("CLT-0001")
        self.assertEqual(len(inbox_client), 0)

    def test_templates_rendering(self) -> None:
        engine = CommunicationsEngine()
        text = engine.render_template("Proposal Ready", client_name="Acme", project_name="Software Build")
        self.assertIn("Acme", text)
        self.assertIn("Software Build", text)

    def test_global_search(self) -> None:
        engine = CommunicationsEngine()
        engine.send_message("ceo", ["cos"], "Urgent check", "Review proposals")
        engine.send_message("ceo", ["cos"], "Weekly update", "Everything stable")

        results = engine.search_messages("Urgent")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].subject, "Urgent check")


if __name__ == "__main__":
    unittest.main()
