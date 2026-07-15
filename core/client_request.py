from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any


LOGGER = logging.getLogger(__name__)


class ClientRequestStatus(str, Enum):
    NEW = "NEW"
    UNDER_REVIEW = "UNDER_REVIEW"
    QUALIFIED = "QUALIFIED"
    PROPOSAL_SENT = "PROPOSAL_SENT"
    APPROVED = "APPROVED"
    PROJECT_CREATED = "PROJECT_CREATED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


class ClientRequestPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ClientRequest:
    _next_id = 1

    def __init__(
        self,
        client_name: str,
        organization: str,
        contact_person: str,
        contact_email: str,
        contact_phone: str,
        industry: str,
        title: str,
        problem_statement: str,
        desired_outcome: str,
        priority: ClientRequestPriority | str = ClientRequestPriority.MEDIUM,
        request_id: str | None = None,
    ) -> None:
        self._require_value(client_name, "Client name")
        self._require_value(organization, "Organization")
        self._require_value(contact_person, "Contact person")
        self._require_value(contact_email, "Contact email")
        self._require_value(contact_phone, "Contact phone")
        self._require_value(industry, "Industry")
        self._require_value(title, "Client request title")
        self._require_value(problem_statement, "Problem statement")
        self._require_value(desired_outcome, "Desired outcome")

        self._id = request_id or self._generate_id()
        self.client_name = client_name
        self.organization = organization
        self.contact_person = contact_person
        self.contact_email = contact_email
        self.contact_phone = contact_phone
        self.industry = industry
        self.title = title
        self.problem_statement = problem_statement
        self.desired_outcome = desired_outcome
        self.priority = self._normalize_priority(priority)
        self.status = ClientRequestStatus.NEW
        self.created_at = self._current_timestamp()
        self.updated_at = self.created_at
        self.approved_at: str | None = None
        self.project_id: str | None = None
        self.notes: list[dict[str, str]] = []

    @property
    def id(self) -> str:
        return self._id

    def approve(self, actor: str = "system") -> ClientRequestStatus:
        self._require_mutable()
        self.status = ClientRequestStatus.APPROVED
        self.approved_at = self._current_timestamp()
        self.updated_at = self.approved_at
        self._log_state_change("approve", actor, "approved")
        return self.status

    def reject(self, actor: str = "system") -> ClientRequestStatus:
        self._require_mutable()
        self.status = ClientRequestStatus.REJECTED
        self.updated_at = self._current_timestamp()
        self._log_state_change("reject", actor, "rejected")
        return self.status

    def withdraw(self, actor: str = "system") -> ClientRequestStatus:
        self._require_mutable()
        self.status = ClientRequestStatus.WITHDRAWN
        self.updated_at = self._current_timestamp()
        self._log_state_change("withdraw", actor, "withdrawn")
        return self.status

    def link_project(self, project_id: str, actor: str = "system") -> str:
        self._require_mutable()
        if self.project_id is not None:
            raise ValueError("Client Request can be linked to only one Project.")
        if self.status != ClientRequestStatus.APPROVED:
            raise ValueError("Only APPROVED Client Requests may be linked to Projects.")
        self._require_value(project_id, "Project ID")

        self.project_id = project_id
        self.status = ClientRequestStatus.PROJECT_CREATED
        self.updated_at = self._current_timestamp()
        self._log_state_change("link_project", actor, "linked")
        return self.project_id

    def update_priority(
        self,
        priority: ClientRequestPriority | str,
        actor: str = "system",
    ) -> ClientRequestPriority:
        self._require_mutable()
        self.priority = self._normalize_priority(priority)
        self.updated_at = self._current_timestamp()
        self._log_state_change("update_priority", actor, "updated")
        return self.priority

    def add_note(self, note: str, actor: str = "system") -> dict[str, str]:
        self._require_value(note, "Note")
        timestamp = self._current_timestamp()
        note_entry = {
            "note": note,
            "created_at": timestamp,
        }
        self.notes.append(note_entry)
        self.updated_at = timestamp
        self._log_state_change("add_note", actor, "added")
        return note_entry

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "client_name": self.client_name,
            "organization": self.organization,
            "title": self.title,
            "status": self.status.value,
            "priority": self.priority.value,
            "industry": self.industry,
            "project_id": self.project_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "client_name": self.client_name,
            "organization": self.organization,
            "contact_person": self.contact_person,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "industry": self.industry,
            "title": self.title,
            "problem_statement": self.problem_statement,
            "desired_outcome": self.desired_outcome,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "approved_at": self.approved_at,
            "project_id": self.project_id,
            "notes": list(self.notes),
        }

    @classmethod
    def _generate_id(cls) -> str:
        request_id = f"CR-{cls._next_id:04d}"
        cls._next_id += 1
        return request_id

    @staticmethod
    def _current_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _normalize_priority(
        priority: ClientRequestPriority | str,
    ) -> ClientRequestPriority:
        try:
            return ClientRequestPriority(priority)
        except ValueError as exc:
            allowed_priorities = ", ".join(
                priority.value for priority in ClientRequestPriority
            )
            raise ValueError(
                f"Invalid client request priority. Allowed values: {allowed_priorities}."
            ) from exc

    @staticmethod
    def _require_value(value: Any, label: str) -> None:
        if not value:
            raise ValueError(f"{label} is required.")

    def _require_mutable(self) -> None:
        if self.status in {
            ClientRequestStatus.REJECTED,
            ClientRequestStatus.WITHDRAWN,
        }:
            raise ValueError("REJECTED and WITHDRAWN Client Requests are read-only except for notes.")

    def _log_state_change(self, action: str, actor: str, result: str) -> None:
        LOGGER.info(
            "timestamp=%s object_id=%s action=%s actor=%s result=%s",
            self.updated_at,
            self.id,
            action,
            actor,
            result,
        )
