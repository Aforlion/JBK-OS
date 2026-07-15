from __future__ import annotations

from typing import Any
from datetime import datetime, timezone


# V1 supported payment methods (record-only, BR-044-009)
PAYMENT_METHODS = ("Bank Transfer", "Stripe", "Paystack", "Flutterwave", "Cash")


class Payment:
    """Records a payment received against an invoice.

    V1 is record-only. The engine never authorizes or initiates payments (BR-044-009).
    """

    def __init__(
        self,
        payment_id: str,
        invoice_id: str,
        amount: float,
        date: str | None = None,
        method: str = "Bank Transfer",
    ) -> None:
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")
        if method not in PAYMENT_METHODS:
            raise ValueError(f"Unsupported payment method: {method}. Supported: {PAYMENT_METHODS}")

        self.payment_id = payment_id
        self.invoice_id = invoice_id
        self.amount = amount
        self.date = date or datetime.now(timezone.utc).isoformat()
        self.method = method

    def to_dict(self) -> dict[str, Any]:
        return {
            "payment_id": self.payment_id,
            "invoice_id": self.invoice_id,
            "amount": self.amount,
            "date": self.date,
            "method": self.method,
        }
