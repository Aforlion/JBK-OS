from __future__ import annotations

from typing import Any


class FinancialSnapshot:
    """Point-in-time capture of the company's financial position."""

    def __init__(
        self,
        total_revenue: float = 0.0,
        total_expenses: float = 0.0,
        profit: float = 0.0,
        outstanding_invoices_count: int = 0,
        outstanding_invoices_value: float = 0.0,
        cash_flow: float = 0.0,
        accounts_receivable: float = 0.0,
        margin_pct: float = 0.0,
        utilization_pct: float = 0.0,
    ) -> None:
        self.total_revenue = total_revenue
        self.total_expenses = total_expenses
        self.profit = profit
        self.outstanding_invoices_count = outstanding_invoices_count
        self.outstanding_invoices_value = outstanding_invoices_value
        self.cash_flow = cash_flow
        self.accounts_receivable = accounts_receivable
        self.margin_pct = margin_pct
        self.utilization_pct = utilization_pct

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_revenue": self.total_revenue,
            "total_expenses": self.total_expenses,
            "profit": self.profit,
            "outstanding_invoices_count": self.outstanding_invoices_count,
            "outstanding_invoices_value": self.outstanding_invoices_value,
            "cash_flow": self.cash_flow,
            "accounts_receivable": self.accounts_receivable,
            "margin_pct": self.margin_pct,
            "utilization_pct": self.utilization_pct,
        }
