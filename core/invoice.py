from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


class LineItem:
    """Represents one line item on an invoice."""

    def __init__(self, description: str, quantity: float, unit_price: float) -> None:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if unit_price < 0:
            raise ValueError("Unit price cannot be negative.")
        self.description = description
        self.quantity = quantity
        self.unit_price = unit_price

    @property
    def total(self) -> float:
        return round(self.quantity * self.unit_price, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total": self.total,
        }


# Valid invoice statuses
INVOICE_STATUSES = ("DRAFT", "SENT", "PARTIALLY_PAID", "PAID", "OVERDUE", "VOID")


class Invoice:
    """Represents an invoice issued to a client for a project.

    Business Rules:
        BR-044-001: total = subtotal + tax - discount
        BR-044-002: Payments never exceed invoice balance.
        BR-044-003: Invoice becomes PAID automatically when balance reaches zero.
    """

    def __init__(
        self,
        invoice_id: str,
        client_id: str,
        project_id: str,
        issue_date: str | None = None,
        due_date: str | None = None,
        status: str = "DRAFT",
        line_items: list[LineItem] | None = None,
        tax: float = 0.0,
        discount: float = 0.0,
    ) -> None:
        if status not in INVOICE_STATUSES:
            raise ValueError(f"Invalid invoice status: {status}")
        if tax < 0:
            raise ValueError("Tax cannot be negative.")
        if discount < 0:
            raise ValueError("Discount cannot be negative.")

        self.invoice_id = invoice_id
        self.client_id = client_id
        self.project_id = project_id
        self.issue_date = issue_date or datetime.now(timezone.utc).isoformat()
        self.due_date = due_date or ""
        self.status = status
        self.line_items: list[LineItem] = line_items or []
        self.tax = tax
        self.discount = discount
        self.amount_paid = 0.0

    @property
    def subtotal(self) -> float:
        """Sum of all line item totals."""
        return round(sum(item.total for item in self.line_items), 2)

    @property
    def total(self) -> float:
        """BR-044-001: total = subtotal + tax - discount."""
        return round(self.subtotal + self.tax - self.discount, 2)

    @property
    def balance(self) -> float:
        """Outstanding balance remaining on this invoice."""
        return round(self.total - self.amount_paid, 2)

    def record_payment(self, amount: float) -> None:
        """Apply a payment amount to this invoice.

        BR-044-002: Payments never exceed invoice balance.
        BR-044-003: Invoice becomes PAID when balance reaches zero.
        """
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")
        if amount > self.balance:
            raise ValueError(
                f"Payment of {amount} exceeds remaining balance of {self.balance}. "
                "Overpayments are not permitted (BR-044-002)."
            )

        self.amount_paid = round(self.amount_paid + amount, 2)

        if self.balance == 0:
            self.status = "PAID"
        elif self.amount_paid > 0 and self.status not in ("PAID", "VOID"):
            self.status = "PARTIALLY_PAID"

    def void(self) -> None:
        """Mark invoice as voided. Voided invoices are excluded from revenue."""
        self.status = "VOID"

    def to_dict(self) -> dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "client_id": self.client_id,
            "project_id": self.project_id,
            "issue_date": self.issue_date,
            "due_date": self.due_date,
            "status": self.status,
            "line_items": [item.to_dict() for item in self.line_items],
            "subtotal": self.subtotal,
            "tax": self.tax,
            "discount": self.discount,
            "total": self.total,
            "amount_paid": self.amount_paid,
            "balance": self.balance,
        }
