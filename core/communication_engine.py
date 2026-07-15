from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone, timedelta

from core.communication import Communication
from core.notification import Notification
from core.communication_log import CommunicationLog
from core.communication_report import CommunicationReport

LOGGER = logging.getLogger(__name__)


class CommunicationEngine:
    """Advisory communication hub for JBK-OS.

    Generates, routes, tracks, and audits all organizational communications.
    V1 generates and logs only — actual delivery is delegated to adapters (BR-045-008).
    """

    def __init__(self, suppression_window_seconds: int = 300) -> None:
        self._communications: dict[str, Communication] = {}
        self._notifications: list[Notification] = []
        self._log = CommunicationLog()
        self._comm_counter = 1
        self._notif_counter = 1
        self._report_counter = 1
        self._suppression_window_seconds = suppression_window_seconds

    # ------------------------------------------------------------------
    # Email Generation
    # ------------------------------------------------------------------

    def generate_email(
        self,
        sender: str,
        recipient: str,
        subject: str,
        message: str,
        priority: str = "MEDIUM",
        attachments: list[str] | None = None,
        source_engine: str = "",
        triggering_event: str = "",
        reasoning: str = "",
    ) -> Communication:
        """Generate an outbound email communication.

        BR-045-001: Unique ID assigned.
        BR-045-009: Explainability metadata required.
        BR-045-002: Audit logged on creation.
        """
        if not sender or not sender.strip():
            raise ValueError("Sender is required.")
        if not recipient or not recipient.strip():
            raise ValueError("Recipient is required.")
        if not subject or not subject.strip():
            raise ValueError("Subject is required.")

        comm_id = f"COM-{self._comm_counter:04d}"
        self._comm_counter += 1

        comm = Communication(
            communication_id=comm_id,
            channel="Email",
            direction="OUTBOUND",
            sender=sender.strip(),
            recipient=recipient.strip(),
            subject=subject.strip(),
            message=message,
            attachments=attachments,
            priority=priority,
            status="DRAFT",
            source_engine=source_engine,
            triggering_event=triggering_event,
            reasoning=reasoning,
        )

        self._communications[comm_id] = comm

        # BR-045-002: Audit log
        self._log.append(comm_id, "CREATED", f"Email generated: {subject.strip()}")

        LOGGER.info(
            "object_id=%s action=generate_email actor=system result=created recipient=%s",
            comm_id, recipient,
        )
        return comm

    # ------------------------------------------------------------------
    # Notification Generation
    # ------------------------------------------------------------------

    def generate_notification(
        self,
        title: str,
        message: str,
        recipient_role: str,
        severity: str,
        source_engine: str,
        action_required: str,
    ) -> Notification:
        """Generate an internal notification.

        BR-045-005: Mandatory fields enforced by Notification model.
        BR-045-006: HIGH severity flagged for CEO briefing.
        BR-045-007: Duplicate suppression within configurable window.
        """
        # BR-045-007: Check for duplicates within suppression window
        existing = self._find_duplicate_notification(title, source_engine)
        if existing is not None:
            LOGGER.info(
                "object_id=%s action=suppress_duplicate actor=system result=merged title=%s",
                existing.notification_id, title,
            )
            return existing

        notif_id = f"NTF-{self._notif_counter:04d}"
        self._notif_counter += 1

        notif = Notification(
            notification_id=notif_id,
            title=title,
            message=message,
            recipient_role=recipient_role,
            severity=severity,
            source_engine=source_engine,
            action_required=action_required,
        )

        self._notifications.append(notif)

        # Audit log
        self._log.append(notif_id, "NOTIFICATION_CREATED", f"{severity} notification: {title}")

        # BR-045-006: CEO briefing flag
        if notif.is_ceo_briefing:
            LOGGER.warning(
                "CEO_BRIEFING: HIGH severity notification %s from %s — %s",
                notif_id, source_engine, title,
            )
            self._log.append(notif_id, "CEO_BRIEFING_FLAGGED", f"HIGH severity: {title}")

        LOGGER.info(
            "object_id=%s action=generate_notification actor=system result=created severity=%s",
            notif_id, severity,
        )
        return notif

    # ------------------------------------------------------------------
    # Queue Management
    # ------------------------------------------------------------------

    def queue_message(self, communication_id: str) -> Communication:
        """Move a communication to QUEUED status.

        BR-045-002: Audit logged.
        """
        comm = self._get_communication(communication_id)
        if comm.status not in ("DRAFT",):
            raise ValueError(
                f"Cannot queue communication {communication_id}: "
                f"current status is {comm.status}. Only DRAFT can be queued."
            )

        comm.status = "QUEUED"
        self._log.append(communication_id, "QUEUED", "Message queued for delivery")

        LOGGER.info("object_id=%s action=queue_message actor=system result=queued", communication_id)
        return comm

    # ------------------------------------------------------------------
    # Delivery Recording
    # ------------------------------------------------------------------

    def record_delivery(self, communication_id: str) -> Communication:
        """Mark communication as DELIVERED.

        BR-045-004: Content becomes immutable after this.
        BR-045-002: Audit logged.
        """
        comm = self._get_communication(communication_id)
        if comm.status not in ("QUEUED", "SENT"):
            raise ValueError(
                f"Cannot mark {communication_id} as delivered: "
                f"current status is {comm.status}."
            )

        if comm.status != "SENT":
            comm.mark_sent()
            self._log.append(communication_id, "SENT", "Message sent")

        comm.status = "DELIVERED"
        self._log.append(communication_id, "DELIVERED", "Message delivered")

        LOGGER.info("object_id=%s action=record_delivery actor=system result=delivered", communication_id)
        return comm

    # ------------------------------------------------------------------
    # Failure Recording
    # ------------------------------------------------------------------

    def record_failure(self, communication_id: str, reason: str = "") -> Communication:
        """Mark communication as FAILED.

        BR-045-003: Failed deliveries remain searchable.
        BR-045-002: Audit logged.
        """
        comm = self._get_communication(communication_id)

        comm.status = "FAILED"
        self._log.append(communication_id, "FAILED", f"Delivery failed: {reason}")

        LOGGER.info(
            "object_id=%s action=record_failure actor=system result=failed reason=%s",
            communication_id, reason,
        )
        return comm

    # ------------------------------------------------------------------
    # History Search
    # ------------------------------------------------------------------

    def search_history(self, query: str) -> list[dict[str, Any]]:
        """Search the audit log. BR-045-003: Failed deliveries are searchable."""
        entries = self._log.search(query)
        return [e.to_dict() for e in entries]

    # ------------------------------------------------------------------
    # Report Generation
    # ------------------------------------------------------------------

    def generate_report(self) -> CommunicationReport:
        """Generate a comprehensive communication report."""
        total_generated = len(self._communications)
        total_sent = sum(1 for c in self._communications.values() if c.status in ("SENT", "DELIVERED", "READ"))
        total_failed = sum(1 for c in self._communications.values() if c.status == "FAILED")
        total_pending = sum(1 for c in self._communications.values() if c.status in ("DRAFT", "QUEUED"))
        unread_notifications = sum(1 for n in self._notifications if not n.read)

        # Delivery stats by channel
        delivery_stats: dict[str, int] = {}
        for comm in self._communications.values():
            delivery_stats[comm.channel] = delivery_stats.get(comm.channel, 0) + 1

        # Failures list
        failures = [
            {"communication_id": c.communication_id, "recipient": c.recipient, "subject": c.subject}
            for c in self._communications.values()
            if c.status == "FAILED"
        ]

        # Recommendations
        recommendations: list[str] = []
        if total_failed > 0:
            recommendations.append(
                f"{total_failed} communication(s) failed delivery. Review failure logs and retry or escalate."
            )
        if unread_notifications > 5:
            recommendations.append(
                f"{unread_notifications} unread notifications. Review notification queue to avoid missed actions."
            )
        if total_pending > 10:
            recommendations.append(
                f"{total_pending} messages pending. Consider processing the queue to reduce backlog."
            )
        if not recommendations:
            recommendations.append("All communications are operating normally.")

        report_id = f"COMREP-{self._report_counter:04d}"
        self._report_counter += 1

        report = CommunicationReport(
            report_id=report_id,
            total_generated=total_generated,
            total_sent=total_sent,
            total_failed=total_failed,
            total_pending=total_pending,
            unread_notifications=unread_notifications,
            delivery_stats=delivery_stats,
            failures=failures,
            recommendations=recommendations,
        )

        self._log.append(report_id, "REPORT_GENERATED", "Communication report generated")

        LOGGER.info(
            "object_id=%s action=generate_report actor=system result=generated sent=%d failed=%d pending=%d",
            report_id, total_sent, total_failed, total_pending,
        )
        return report

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_communication(self, communication_id: str) -> Communication | None:
        return self._communications.get(communication_id)

    def list_communications(self) -> list[Communication]:
        return list(self._communications.values())

    def list_notifications(self) -> list[Notification]:
        return list(self._notifications)

    def get_ceo_briefing_notifications(self) -> list[Notification]:
        """BR-045-006: Return all HIGH severity notifications for CEO briefing."""
        return [n for n in self._notifications if n.is_ceo_briefing]

    def get_audit_log(self) -> CommunicationLog:
        return self._log

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _get_communication(self, communication_id: str) -> Communication:
        if communication_id not in self._communications:
            raise ValueError(f"Communication not found: {communication_id}")
        return self._communications[communication_id]

    def _find_duplicate_notification(self, title: str, source_engine: str) -> Notification | None:
        """BR-045-007: Check for duplicate notification within suppression window."""
        now = datetime.now(timezone.utc)
        title_clean = title.strip().lower()
        source_clean = source_engine.strip().lower()

        for notif in reversed(self._notifications):
            if notif.title.lower() == title_clean and notif.source_engine.lower() == source_clean:
                try:
                    created = datetime.fromisoformat(notif.created_at)
                    if hasattr(created, 'tzinfo') and created.tzinfo is None:
                        created = created.replace(tzinfo=timezone.utc)
                    if now - created < timedelta(seconds=self._suppression_window_seconds):
                        return notif
                except (ValueError, TypeError):
                    pass
        return None
