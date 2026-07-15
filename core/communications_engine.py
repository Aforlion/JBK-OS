from __future__ import annotations

import logging
import hashlib
from typing import Any
from datetime import datetime, timezone, timedelta

from core.communication_message import CommunicationMessage
from core.notification import Notification
from core.message_thread import MessageThread

LOGGER = logging.getLogger(__name__)


class CommunicationsEngine:
    """Centralized messaging infrastructure routing JBK OS communications.

    BR-049-010: Never executes business logic. Only routes.
    BR-049-003: Duplicate notifications are automatically suppressed.
    BR-049-004: Delivery failures are retried.
    BR-049-007: Priority determines delivery order.
    BR-049-008: Client conversations remain isolated.
    BR-049-009: Executive conversations are internal only.
    """

    def __init__(self, duplicate_suppression_window_seconds: int = 300) -> None:
        self._messages: dict[str, CommunicationMessage] = {}
        self._notifications: list[Notification] = []
        self._threads: dict[str, MessageThread] = {}
        
        # User inboxes: username/role -> list of message IDs
        self._inboxes: dict[str, list[str]] = {}
        
        # Retry Queue and Dead-Letter Queue (DLQ)
        self._retry_queue: list[dict[str, Any]] = []
        self._dead_letter_queue: list[dict[str, Any]] = []
        
        # Counters
        self._msg_counter = 1
        self._notif_counter = 1
        self._thread_counter = 1
        
        # Config
        self.duplicate_suppression_window_seconds = duplicate_suppression_window_seconds
        
        # Templates registry
        self._templates = {
            "Proposal Ready": "Dear {client_name}, your JBK Technologies proposal for {project_name} is ready for review.",
            "Invoice Ready": "Dear {client_name}, Invoice {invoice_id} for {amount:.2f} has been issued.",
            "Meeting Reminder": "Reminder: Upcoming executive meeting '{meeting_title}' is scheduled at {time}.",
            "Project Started": "Project {project_name} has officially kicked off. View portal for live status updates.",
        }

    # ------------------------------------------------------------------
    # Messaging
    # ------------------------------------------------------------------

    def send_message(
        self,
        sender: str,
        recipients: list[str],
        subject: str,
        body: str,
        channel: str = "Internal Inbox",
        priority: str = "NORMAL",
        scheduled_at: str | None = None,
        attachments: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CommunicationMessage:
        """Sends or schedules a communication message."""
        msg_id = f"MSG-{self._msg_counter:04d}"
        self._msg_counter += 1

        message = CommunicationMessage(
            message_id=msg_id,
            sender=sender,
            recipients=recipients,
            subject=subject,
            body=body,
            channel=channel,
            priority=priority,
            status="QUEUED" if scheduled_at else "SENT",
            scheduled_at=scheduled_at,
            attachments=attachments,
            metadata=metadata,
        )

        self._messages[msg_id] = message

        # Route or schedule
        if scheduled_at:
            LOGGER.info("object_id=%s action=schedule_message actor=system status=QUEUED", msg_id)
        else:
            self._route_message(message)

        return message

    def _route_message(self, message: CommunicationMessage) -> None:
        """Route message to specific recipient inboxes, enforcing isolation rules."""
        # BR-049-008 & BR-049-009: Check isolation flags in metadata
        is_client_isolated = message.metadata.get("client_isolated", False)
        is_executive_internal = message.metadata.get("executive_internal", False)

        for r in message.recipients:
            # Client isolation boundary: if client isolated, do not allow non-mapped participants
            if is_client_isolated:
                client_id = message.metadata.get("client_id")
                # Ensure recipient is either the specific client or an authorized internal staff mapped to client
                # In V1, client IDs start with 'CLT-'
                if r.startswith("CLT-") and r != client_id:
                    LOGGER.warning("Security Breach Blocked: Client workspace isolation crossed.")
                    continue

            # Executive internal only boundary
            if is_executive_internal:
                if r.startswith("CLT-"):
                    LOGGER.warning("Security Breach Blocked: Executive internal thread leaked to client.")
                    continue

            # Route to recipient inbox
            if r not in self._inboxes:
                self._inboxes[r] = []
            self._inboxes[r].append(message.message_id)

        message.mark_status("DELIVERED")

    # ------------------------------------------------------------------
    # Notification & Duplicate Suppression
    # ------------------------------------------------------------------

    def send_notification(
        self,
        title: str,
        message: str,
        recipient_role: str,
        severity: str,
        source_engine: str,
        action_required: str,
        category: str = "General",
        metadata: dict[str, Any] | None = None,
    ) -> Notification | None:
        """Sends a notification with duplicate suppression and routing rule triggers.

        BR-049-003: Duplicate notifications are automatically suppressed.
        BR-049-005: Every automated notification includes originating engine.
        """
        # BR-049-003: Check duplicate suppression
        if self._is_duplicate_notification(title, message, source_engine):
            LOGGER.info("Duplicate notification suppressed: %s from %s", title, source_engine)
            return None

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
            category=category,
        )

        self._notifications.append(notif)
        LOGGER.info(
            "object_id=%s action=route_notification actor=system severity=%s engine=%s",
            notif_id, severity, source_engine
        )
        return notif

    def _is_duplicate_notification(self, title: str, message: str, source_engine: str) -> bool:
        """Helper checking if an identical notification was generated within window."""
        now = datetime.now(timezone.utc)
        for n in reversed(self._notifications):
            if n.title == title and n.message == message and n.source_engine == source_engine:
                try:
                    created = datetime.fromisoformat(n.created_at)
                    if hasattr(created, "tzinfo") and created.tzinfo is None:
                        created = created.replace(tzinfo=timezone.utc)
                    if now - created < timedelta(seconds=self.duplicate_suppression_window_seconds):
                        return True
                except Exception:
                    pass
        return False

    # ------------------------------------------------------------------
    # Threading
    # ------------------------------------------------------------------

    def create_thread(self, subject: str, participants: list[str], metadata: dict[str, Any] | None = None) -> MessageThread:
        """Create a new conversational message thread."""
        thread_id = f"THR-{self._thread_counter:04d}"
        self._thread_counter += 1

        thread = MessageThread(
            thread_id=thread_id,
            subject=subject,
            participants=participants,
            metadata=metadata,
        )
        self._threads[thread_id] = thread
        return thread

    # ------------------------------------------------------------------
    # Queue, Retries, and Priorities (BR-049-004, BR-049-007)
    # ------------------------------------------------------------------

    def queue_for_retry(self, message_id: str, error_reason: str) -> None:
        """Pushes failed message into retry queue (BR-049-004)."""
        msg = self._messages.get(message_id)
        if not msg:
            return

        msg.mark_status("FAILED")
        
        # Check retry limit (max 3 retries in V1)
        retry_record = next((r for r in self._retry_queue if r["message_id"] == message_id), None)
        if retry_record:
            retry_record["attempts"] += 1
            retry_record["last_error"] = error_reason
            if retry_record["attempts"] > 3:
                # Exceeded retry count: escalate to Dead-Letter Queue
                self._retry_queue.remove(retry_record)
                self._dead_letter_queue.append(retry_record)
                LOGGER.warning(" Escalated message %s to dead-letter queue (DLQ).", message_id)
        else:
            self._retry_queue.append({
                "message_id": message_id,
                "attempts": 1,
                "last_error": error_reason,
            })

    def process_retry_queue(self) -> int:
        """Process messages pending retry. Returns successfully delivered count."""
        success_count = 0
        resolved = []
        
        # BR-049-007: Priority determines retry delivery order
        # Sort retry queue by message priority weights
        self._retry_queue.sort(
            key=lambda r: self._messages[r["message_id"]].priority_weight if r["message_id"] in self._messages else 0,
            reverse=True
        )

        for record in list(self._retry_queue):
            msg_id = record["message_id"]
            msg = self._messages.get(msg_id)
            if msg:
                try:
                    # Attempt redelivery
                    self._route_message(msg)
                    msg.mark_status("DELIVERED")
                    success_count += 1
                    resolved.append(record)
                except Exception as e:
                    record["attempts"] += 1
                    record["last_error"] = str(e)
                    if record["attempts"] > 3:
                        self._dead_letter_queue.append(record)
                        resolved.append(record)

        for r in resolved:
            if r in self._retry_queue:
                self._retry_queue.remove(r)

        return success_count

    # ------------------------------------------------------------------
    # Template Rendering
    # ------------------------------------------------------------------

    def render_template(self, template_name: str, **kwargs: Any) -> str:
        """Retrieve and format a standard communication template."""
        tpl = self._templates.get(template_name)
        if not tpl:
            raise ValueError(f"Template not found: {template_name}")
        return tpl.format(**kwargs)

    # ------------------------------------------------------------------
    # Search and Filter
    # ------------------------------------------------------------------

    def search_messages(self, query: str) -> list[CommunicationMessage]:
        """Search communication messages by sender, recipient, subject, or body."""
        q = query.lower()
        results = []
        for msg in self._messages.values():
            if (
                q in msg.sender.lower()
                or any(q in r.lower() for r in msg.recipients)
                or q in msg.subject.lower()
                or q in msg.body.lower()
                or q in msg.priority.lower()
            ):
                results.append(msg)
        return results

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_inbox(self, user_or_role: str) -> list[CommunicationMessage]:
        """Fetch list of delivered messages for a participant."""
        msg_ids = self._inboxes.get(user_or_role, [])
        return [self._messages[mid] for mid in msg_ids if mid in self._messages]

    def get_message(self, message_id: str) -> CommunicationMessage | None:
        return self._messages.get(message_id)

    def get_thread(self, thread_id: str) -> MessageThread | None:
        return self._threads.get(thread_id)

    def get_notifications(self, role: str | None = None) -> list[Notification]:
        """Fetch notifications, optionally filtered by role."""
        if role:
            return [n for n in self._notifications if n.recipient_role == role]
        return list(self._notifications)
        
    def get_dead_letter_queue(self) -> list[dict[str, Any]]:
        return list(self._dead_letter_queue)
