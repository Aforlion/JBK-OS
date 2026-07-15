from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone, timedelta

from core.invoice import Invoice, LineItem
from core.payment import Payment
from core.expense import Expense
from core.financial_snapshot import FinancialSnapshot
from core.financial_report import FinancialReport

LOGGER = logging.getLogger(__name__)


class FinancialOperationsEngine:
    """Advisory financial operations layer for the post-proposal commercial lifecycle.

    This engine is strictly advisory (BR-044-008, BR-044-009):
        - It never modifies proposals.
        - It never authorizes or initiates payments.
        - It never connects to banking APIs (V1).
        - It records financial events and produces reports.
    """

    def __init__(self) -> None:
        self._invoices: dict[str, Invoice] = {}
        self._payments: list[Payment] = []
        self._expenses: list[Expense] = []
        self._invoice_counter = 1
        self._payment_counter = 1
        self._expense_counter = 1
        self._report_counter = 1

    # ------------------------------------------------------------------
    # Invoice Management
    # ------------------------------------------------------------------

    def create_invoice(
        self,
        client_id: str,
        project_id: str,
        line_items: list[dict[str, Any]],
        tax: float = 0.0,
        discount: float = 0.0,
        issue_date: str | None = None,
        due_date: str | None = None,
    ) -> Invoice:
        """Create an invoice with line items, tax, and discount.

        BR-044-001: total = subtotal + tax - discount.
        """
        if not client_id or not client_id.strip():
            raise ValueError("Client ID is required.")
        if not project_id or not project_id.strip():
            raise ValueError("Project ID is required.")
        if not line_items:
            raise ValueError("At least one line item is required.")

        items = []
        for li in line_items:
            items.append(LineItem(
                description=li.get("description", ""),
                quantity=li.get("quantity", 1),
                unit_price=li.get("unit_price", 0.0),
            ))

        invoice_id = f"INV-{self._invoice_counter:04d}"
        self._invoice_counter += 1

        invoice = Invoice(
            invoice_id=invoice_id,
            client_id=client_id.strip(),
            project_id=project_id.strip(),
            issue_date=issue_date,
            due_date=due_date,
            line_items=items,
            tax=tax,
            discount=discount,
        )

        self._invoices[invoice_id] = invoice
        LOGGER.info(
            "object_id=%s action=create_invoice actor=system result=created client=%s project=%s total=%.2f",
            invoice_id, client_id, project_id, invoice.total,
        )
        return invoice

    def record_payment(
        self,
        invoice_id: str,
        amount: float,
        method: str = "Bank Transfer",
        date: str | None = None,
    ) -> Payment:
        """Record a payment against an invoice (BR-044-009: record only, never authorize).

        BR-044-002: Payments never exceed invoice balance.
        BR-044-003: Invoice becomes PAID when balance reaches zero.
        """
        if invoice_id not in self._invoices:
            raise ValueError(f"Invoice not found: {invoice_id}")

        invoice = self._invoices[invoice_id]
        if invoice.status == "VOID":
            raise ValueError(f"Cannot apply payment to voided invoice: {invoice_id}")

        # This enforces BR-044-002 and BR-044-003 inside Invoice.record_payment
        invoice.record_payment(amount)

        payment_id = f"PAY-{self._payment_counter:04d}"
        self._payment_counter += 1

        payment = Payment(
            payment_id=payment_id,
            invoice_id=invoice_id,
            amount=amount,
            date=date,
            method=method,
        )
        self._payments.append(payment)

        LOGGER.info(
            "object_id=%s action=record_payment actor=system result=recorded invoice=%s amount=%.2f method=%s",
            payment_id, invoice_id, amount, method,
        )
        return payment

    # ------------------------------------------------------------------
    # Expense Tracking
    # ------------------------------------------------------------------

    def record_expense(
        self,
        category: str,
        amount: float,
        project_id: str = "",
        vendor: str = "",
        receipt_reference: str = "",
        date: str | None = None,
    ) -> Expense:
        """Record a business expense."""
        if not category or not category.strip():
            raise ValueError("Expense category is required.")

        expense_id = f"EXP-{self._expense_counter:04d}"
        self._expense_counter += 1

        expense = Expense(
            expense_id=expense_id,
            category=category.strip(),
            amount=amount,
            project_id=project_id,
            vendor=vendor,
            receipt_reference=receipt_reference,
            date=date,
        )
        self._expenses.append(expense)

        LOGGER.info(
            "object_id=%s action=record_expense actor=system result=recorded category=%s amount=%.2f",
            expense_id, category, amount,
        )
        return expense

    # ------------------------------------------------------------------
    # Profitability
    # ------------------------------------------------------------------

    def calculate_profitability(self, project_id: str | None = None) -> dict[str, float]:
        """Calculate profitability: Revenue - Internal Cost = Profit (BR-044-006).

        If project_id is provided, scopes to that project. Otherwise company-wide.
        """
        revenue = self._total_revenue(project_id)
        cost = self._total_expenses(project_id)
        profit = round(revenue - cost, 2)
        margin = round((profit / revenue) * 100, 2) if revenue > 0 else 0.0

        return {
            "revenue": revenue,
            "cost": cost,
            "profit": profit,
            "margin_pct": margin,
        }

    # ------------------------------------------------------------------
    # Financial Report
    # ------------------------------------------------------------------

    def generate_financial_report(self) -> FinancialReport:
        """Generate a comprehensive financial report with KPIs, warnings, and recommendations.

        BR-044-004: Outstanding invoices appear in reports.
        BR-044-007: Warn when accounts receivable > 30 days.
        BR-044-010: Every recommendation explains why, calculations, assumptions.
        """
        revenue = self._total_revenue()
        expenses = self._total_expenses()
        profit = round(revenue - expenses, 2)
        cash_flow = round(revenue - expenses, 2)  # BR-044-005
        margin = round((profit / revenue) * 100, 2) if revenue > 0 else 0.0

        # Outstanding invoices (BR-044-004)
        outstanding = self._outstanding_invoices()
        outstanding_value = round(sum(inv.balance for inv in outstanding), 2)

        # Accounts receivable aging (BR-044-007)
        warnings: list[str] = []
        aged_invoices = self._aged_invoices(days=30)
        for inv in aged_invoices:
            warnings.append(
                f"Invoice {inv.invoice_id} is outstanding > 30 days "
                f"(due: {inv.due_date}, balance: {inv.balance})."
            )

        # Cash health assessment
        if cash_flow > 0 and not aged_invoices:
            cash_health = "Healthy"
        elif cash_flow > 0 and aged_invoices:
            cash_health = "Caution"
        elif cash_flow == 0:
            cash_health = "Neutral"
        else:
            cash_health = "Critical"

        # Runway projection
        runway = self._project_runway(revenue, expenses)

        # Recommendations with explainability (BR-044-010)
        recommendations = self._generate_recommendations(
            profit, margin, outstanding_value, aged_invoices, cash_flow, runway,
        )

        # KPIs
        kpis = {
            "total_revenue": revenue,
            "total_expenses": expenses,
            "profit": profit,
            "margin_pct": margin,
            "cash_flow": cash_flow,
            "outstanding_invoices_count": len(outstanding),
            "outstanding_invoices_value": outstanding_value,
            "accounts_receivable_aged_30d": len(aged_invoices),
        }

        # Executive summary
        executive_summary = (
            f"Revenue: {revenue:.2f} | Expenses: {expenses:.2f} | "
            f"Profit: {profit:.2f} ({margin:.1f}%) | "
            f"Cash Flow: {cash_flow:.2f} | "
            f"Outstanding: {len(outstanding)} invoices ({outstanding_value:.2f}) | "
            f"Cash Health: {cash_health}"
        )

        snapshot = FinancialSnapshot(
            total_revenue=revenue,
            total_expenses=expenses,
            profit=profit,
            outstanding_invoices_count=len(outstanding),
            outstanding_invoices_value=outstanding_value,
            cash_flow=cash_flow,
            accounts_receivable=outstanding_value,
            margin_pct=margin,
        )

        report_id = f"FIN-{self._report_counter:04d}"
        self._report_counter += 1

        report = FinancialReport(
            report_id=report_id,
            executive_summary=executive_summary,
            kpis=kpis,
            warnings=warnings,
            recommendations=recommendations,
            cash_health=cash_health,
            outstanding_invoices=[inv.to_dict() for inv in outstanding],
            projected_runway_days=runway,
            snapshot=snapshot,
        )

        LOGGER.info(
            "object_id=%s action=generate_financial_report actor=system result=generated revenue=%.2f profit=%.2f",
            report_id, revenue, profit,
        )
        return report

    # ------------------------------------------------------------------
    # Cash Flow Forecasting
    # ------------------------------------------------------------------

    def forecast_cashflow(self, horizon_days: int = 90) -> dict[str, Any]:
        """Forecast future cash position from outstanding invoices and expense burn rate.

        Advisory only. Returns projected inflows, outflows, and net position.
        """
        # Projected inflows: outstanding invoice balances expected to be collected
        outstanding = self._outstanding_invoices()
        projected_inflows = round(sum(inv.balance for inv in outstanding), 2)

        # Burn rate: average daily expense
        total_exp = self._total_expenses()
        # Estimate days of operation from expense history
        if self._expenses:
            dates = []
            for exp in self._expenses:
                try:
                    dates.append(datetime.fromisoformat(exp.date))
                except (ValueError, TypeError):
                    pass
            if len(dates) >= 2:
                span = (max(dates) - min(dates)).days or 1
            else:
                span = 30  # default assumption
        else:
            span = 30

        daily_burn = round(total_exp / span, 2) if span > 0 else 0.0
        projected_outflows = round(daily_burn * horizon_days, 2)

        # Current cash position (revenue collected minus expenses)
        revenue_collected = round(sum(p.amount for p in self._payments), 2)
        current_cash = round(revenue_collected - total_exp, 2)

        net_position = round(current_cash + projected_inflows - projected_outflows, 2)

        return {
            "horizon_days": horizon_days,
            "current_cash": current_cash,
            "projected_inflows": projected_inflows,
            "projected_outflows": projected_outflows,
            "daily_burn_rate": daily_burn,
            "net_position": net_position,
        }

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _total_revenue(self, project_id: str | None = None) -> float:
        """Total revenue = sum of payments on non-void invoices."""
        valid_invoice_ids = set()
        for inv in self._invoices.values():
            if inv.status != "VOID":
                if project_id is None or inv.project_id == project_id:
                    valid_invoice_ids.add(inv.invoice_id)

        total = sum(p.amount for p in self._payments if p.invoice_id in valid_invoice_ids)
        return round(total, 2)

    def _total_expenses(self, project_id: str | None = None) -> float:
        """Total expenses, optionally scoped to a project."""
        if project_id:
            return round(sum(e.amount for e in self._expenses if e.project_id == project_id), 2)
        return round(sum(e.amount for e in self._expenses), 2)

    def _outstanding_invoices(self) -> list[Invoice]:
        """All non-void invoices with a positive balance (BR-044-004)."""
        return [
            inv for inv in self._invoices.values()
            if inv.status not in ("PAID", "VOID") and inv.balance > 0
        ]

    def _aged_invoices(self, days: int = 30) -> list[Invoice]:
        """Invoices outstanding longer than the specified days (BR-044-007)."""
        aged = []
        now = datetime.now(timezone.utc)
        for inv in self._outstanding_invoices():
            if inv.due_date:
                try:
                    due = datetime.fromisoformat(inv.due_date)
                    if hasattr(due, 'tzinfo') and due.tzinfo is None:
                        due = due.replace(tzinfo=timezone.utc)
                    if now - due > timedelta(days=days):
                        aged.append(inv)
                except (ValueError, TypeError):
                    pass
        return aged

    def _project_runway(self, revenue: float, expenses: float) -> float:
        """Estimate runway in days based on current cash and burn rate."""
        revenue_collected = round(sum(p.amount for p in self._payments), 2)
        current_cash = revenue_collected - expenses
        if current_cash <= 0:
            return 0.0

        # Daily burn
        if self._expenses:
            dates = []
            for exp in self._expenses:
                try:
                    dates.append(datetime.fromisoformat(exp.date))
                except (ValueError, TypeError):
                    pass
            if len(dates) >= 2:
                span = (max(dates) - min(dates)).days or 1
            else:
                span = 30
        else:
            return 365.0  # No expenses, default assumption

        daily_burn = expenses / span if span > 0 else 0.0
        if daily_burn <= 0:
            return 365.0

        return round(current_cash / daily_burn, 1)

    def _generate_recommendations(
        self,
        profit: float,
        margin: float,
        outstanding_value: float,
        aged_invoices: list[Invoice],
        cash_flow: float,
        runway: float,
    ) -> list[dict[str, str]]:
        """Generate advisory recommendations with full explainability (BR-044-010).

        Each recommendation includes: why, calculations, assumptions.
        """
        recommendations: list[dict[str, str]] = []

        if aged_invoices:
            aged_total = round(sum(inv.balance for inv in aged_invoices), 2)
            recommendations.append({
                "action": "Pursue outstanding collections",
                "why": (
                    f"{len(aged_invoices)} invoice(s) have been outstanding for more than 30 days, "
                    "creating accounts receivable risk."
                ),
                "calculations": f"Aged AR total: {aged_total:.2f}",
                "assumptions": "Due dates are accurate. Payment terms have not been renegotiated.",
            })

        if margin < 20.0 and profit > 0:
            recommendations.append({
                "action": "Review project cost structure",
                "why": f"Profit margin is {margin:.1f}%, which is below the 20% healthy threshold.",
                "calculations": f"Profit: {profit:.2f}, Margin: {margin:.1f}%",
                "assumptions": "All expenses have been recorded. No deferred revenue.",
            })

        if profit < 0:
            recommendations.append({
                "action": "Urgent cost review required",
                "why": "The company is currently operating at a loss.",
                "calculations": f"Profit: {profit:.2f} (negative)",
                "assumptions": "All revenue has been collected. All expenses are accounted for.",
            })

        if cash_flow < 0:
            recommendations.append({
                "action": "Improve cash position",
                "why": "Cash flow is negative, indicating outflows exceed inflows.",
                "calculations": f"Cash flow: {cash_flow:.2f}",
                "assumptions": "Revenue is based on collected payments. Expenses are fully recorded.",
            })

        if runway < 90 and runway > 0:
            recommendations.append({
                "action": "Extend financial runway",
                "why": f"Projected runway is {runway:.0f} days, which is below the 90-day safety threshold.",
                "calculations": f"Runway: {runway:.1f} days",
                "assumptions": "Burn rate remains constant. No additional revenue streams.",
            })

        if outstanding_value > 0 and not aged_invoices:
            recommendations.append({
                "action": "Monitor outstanding invoices",
                "why": f"There are outstanding invoices totalling {outstanding_value:.2f} not yet past aging threshold.",
                "calculations": f"Outstanding value: {outstanding_value:.2f}",
                "assumptions": "Invoices will be paid within terms. No disputes pending.",
            })

        if not recommendations:
            recommendations.append({
                "action": "Maintain current financial trajectory",
                "why": "All financial indicators are within healthy ranges.",
                "calculations": f"Profit: {profit:.2f}, Margin: {margin:.1f}%, Cash flow: {cash_flow:.2f}",
                "assumptions": "All financial data is current and complete.",
            })

        return recommendations

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_invoice(self, invoice_id: str) -> Invoice | None:
        return self._invoices.get(invoice_id)

    def list_invoices(self) -> list[Invoice]:
        return list(self._invoices.values())

    def list_payments(self) -> list[Payment]:
        return list(self._payments)

    def list_expenses(self) -> list[Expense]:
        return list(self._expenses)
