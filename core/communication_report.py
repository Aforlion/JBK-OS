from __future__ import annotations

from typing import Any


class CommunicationReport:
    """Report summarizing communication activity, delivery stats, failures, and recommendations."""

    def __init__(
        self,
        report_id: str,
        total_generated: int = 0,
        total_sent: int = 0,
        total_failed: int = 0,
        total_pending: int = 0,
        unread_notifications: int = 0,
        delivery_stats: dict[str, int] | None = None,
        failures: list[dict[str, Any]] | None = None,
        recommendations: list[str] | None = None,
    ) -> None:
        self.report_id = report_id
        self.total_generated = total_generated
        self.total_sent = total_sent
        self.total_failed = total_failed
        self.total_pending = total_pending
        self.unread_notifications = unread_notifications
        self.delivery_stats = delivery_stats or {}
        self.failures = failures or []
        self.recommendations = recommendations or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "total_generated": self.total_generated,
            "total_sent": self.total_sent,
            "total_failed": self.total_failed,
            "total_pending": self.total_pending,
            "unread_notifications": self.unread_notifications,
            "delivery_stats": self.delivery_stats,
            "failures": self.failures,
            "recommendations": self.recommendations,
        }
