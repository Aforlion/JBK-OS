from __future__ import annotations

from typing import Any

class SupportSchedule:
    """Represents a recommended client support routine schedule."""
    def __init__(self, frequency: str, next_date: str) -> None:
        self.frequency = frequency  # Weekly, Monthly, Quarterly, Annual
        self.next_date = next_date

    def to_dict(self) -> dict[str, Any]:
        return {"frequency": self.frequency, "next_date": self.next_date}


class SuccessMilestone:
    """Represents key adoption milestones for client success."""
    def __init__(self, title: str, target_date: str, completed: bool = False) -> None:
        self.title = title
        self.target_date = target_date
        self.completed = completed

    def to_dict(self) -> dict[str, Any]:
        return {"title": self.title, "target_date": self.target_date, "completed": self.completed}


class RenewalOpportunity:
    """Represents a predicted renewal event opportunity."""
    def __init__(self, renewal_type: str, date: str, estimated_value: float, confidence: str) -> None:
        self.renewal_type = renewal_type  # Support contract, License, Maintenance, Training
        self.date = date
        self.estimated_value = estimated_value
        self.confidence = confidence  # High, Medium, Low

    def to_dict(self) -> dict[str, Any]:
        return {
            "renewal_type": self.renewal_type,
            "date": self.date,
            "estimated_value": self.estimated_value,
            "confidence": self.confidence,
        }


class UpsellOpportunity:
    """Represents a growth upsell opportunity identified by the engine."""
    def __init__(self, upsell_type: str, reasoning: str, value: float) -> None:
        self.upsell_type = upsell_type  # AI Automation, Analytics Dashboard, etc.
        self.reasoning = reasoning
        self.value = value

    def to_dict(self) -> dict[str, Any]:
        return {"upsell_type": self.upsell_type, "reasoning": self.reasoning, "value": self.value}


class RiskAlert:
    """Represents a potential churn risk triggered by the engine."""
    def __init__(self, risk_type: str, description: str, severity: str) -> None:
        self.risk_type = risk_type  # Cold account, declining health, open complaints, late payments
        self.description = description
        self.severity = severity  # High, Medium, Low

    def to_dict(self) -> dict[str, Any]:
        return {"risk_type": self.risk_type, "description": self.description, "severity": self.severity}


class ClientSuccessPlan:
    """Main successor planning framework holding schedules, opportunities, and risks."""

    def __init__(
        self,
        client_id: str,
        support_schedule: SupportSchedule | None = None,
        milestones: list[SuccessMilestone] | None = None,
        renewals: list[RenewalOpportunity] | None = None,
        upsells: list[UpsellOpportunity] | None = None,
        risks: list[RiskAlert] | None = None,
    ) -> None:
        self.client_id = client_id
        self.support_schedule = support_schedule
        self.milestones = milestones or []
        self.renewals = renewals or []
        self.upsells = upsells or []
        self.risks = risks or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_id": self.client_id,
            "support_schedule": self.support_schedule.to_dict() if self.support_schedule else None,
            "milestones": [m.to_dict() for m in self.milestones],
            "renewals": [r.to_dict() for r in self.renewals],
            "upsells": [u.to_dict() for u in self.upsells],
            "risks": [r.to_dict() for r in self.risks],
        }
