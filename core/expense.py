from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class Expense:
    """Tracks a business expense against a project or operational category."""

    def __init__(
        self,
        expense_id: str,
        category: str,
        amount: float,
        project_id: str = "",
        vendor: str = "",
        receipt_reference: str = "",
        date: str | None = None,
    ) -> None:
        if amount < 0:
            raise ValueError("Expense amount cannot be negative.")

        self.expense_id = expense_id
        self.category = category
        self.amount = amount
        self.project_id = project_id
        self.vendor = vendor
        self.receipt_reference = receipt_reference
        self.date = date or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "expense_id": self.expense_id,
            "category": self.category,
            "amount": self.amount,
            "project_id": self.project_id,
            "vendor": self.vendor,
            "receipt_reference": self.receipt_reference,
            "date": self.date,
        }
