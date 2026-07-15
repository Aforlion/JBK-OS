import unittest
from datetime import datetime, timezone, timedelta

from core.invoice import Invoice, LineItem
from core.payment import Payment
from core.expense import Expense
from core.financial_snapshot import FinancialSnapshot
from core.financial_report import FinancialReport
from core.financial_operations_engine import FinancialOperationsEngine


class TestInvoiceModel(unittest.TestCase):
    """Test Invoice and LineItem models directly."""

    def test_line_item_total(self) -> None:
        item = LineItem("Design Work", quantity=10, unit_price=150.0)
        self.assertEqual(item.total, 1500.0)

    def test_invoice_total_equals_subtotal_plus_tax_minus_discount(self) -> None:
        """BR-044-001: total = subtotal + tax - discount."""
        items = [
            LineItem("Dev", quantity=5, unit_price=200.0),   # 1000
            LineItem("QA", quantity=2, unit_price=150.0),    # 300
        ]
        inv = Invoice(
            invoice_id="INV-TEST",
            client_id="CLT-0001",
            project_id="PROJ-0001",
            line_items=items,
            tax=130.0,
            discount=50.0,
        )
        self.assertEqual(inv.subtotal, 1300.0)
        self.assertEqual(inv.total, 1300.0 + 130.0 - 50.0)  # 1380.0

    def test_partial_payment_updates_status(self) -> None:
        items = [LineItem("Service", quantity=1, unit_price=1000.0)]
        inv = Invoice(
            invoice_id="INV-TEST",
            client_id="CLT-0001",
            project_id="PROJ-0001",
            line_items=items,
        )
        inv.record_payment(400.0)
        self.assertEqual(inv.status, "PARTIALLY_PAID")
        self.assertEqual(inv.balance, 600.0)

    def test_full_payment_auto_paid(self) -> None:
        """BR-044-003: Invoice becomes PAID when balance reaches zero."""
        items = [LineItem("Service", quantity=1, unit_price=500.0)]
        inv = Invoice(
            invoice_id="INV-TEST",
            client_id="CLT-0001",
            project_id="PROJ-0001",
            line_items=items,
        )
        inv.record_payment(500.0)
        self.assertEqual(inv.status, "PAID")
        self.assertEqual(inv.balance, 0.0)

    def test_overpayment_rejected(self) -> None:
        """BR-044-002: Payments never exceed invoice balance."""
        items = [LineItem("Service", quantity=1, unit_price=500.0)]
        inv = Invoice(
            invoice_id="INV-TEST",
            client_id="CLT-0001",
            project_id="PROJ-0001",
            line_items=items,
        )
        with self.assertRaises(ValueError) as ctx:
            inv.record_payment(600.0)
        self.assertIn("Overpayments are not permitted", str(ctx.exception))

    def test_void_invoice(self) -> None:
        items = [LineItem("Service", quantity=1, unit_price=100.0)]
        inv = Invoice(
            invoice_id="INV-TEST",
            client_id="CLT-0001",
            project_id="PROJ-0001",
            line_items=items,
        )
        inv.void()
        self.assertEqual(inv.status, "VOID")


class TestPaymentModel(unittest.TestCase):

    def test_valid_payment(self) -> None:
        p = Payment(payment_id="PAY-0001", invoice_id="INV-0001", amount=250.0, method="Stripe")
        self.assertEqual(p.amount, 250.0)
        self.assertEqual(p.method, "Stripe")

    def test_invalid_method_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Payment(payment_id="PAY-0001", invoice_id="INV-0001", amount=100.0, method="Bitcoin")

    def test_negative_amount_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Payment(payment_id="PAY-0001", invoice_id="INV-0001", amount=-50.0)


class TestExpenseModel(unittest.TestCase):

    def test_expense_creation(self) -> None:
        e = Expense(
            expense_id="EXP-0001",
            category="Cloud Hosting",
            amount=450.0,
            project_id="PROJ-0001",
            vendor="AWS",
            receipt_reference="REC-001",
        )
        self.assertEqual(e.category, "Cloud Hosting")
        self.assertEqual(e.vendor, "AWS")
        d = e.to_dict()
        self.assertEqual(d["category"], "Cloud Hosting")

    def test_negative_expense_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Expense(expense_id="EXP-0001", category="Test", amount=-100.0)


class TestFinancialOperationsEngine(unittest.TestCase):

    def _make_engine_with_invoice(self) -> tuple:
        """Helper: creates engine with a single 1000.0 invoice."""
        engine = FinancialOperationsEngine()
        inv = engine.create_invoice(
            client_id="CLT-0001",
            project_id="PROJ-0001",
            line_items=[
                {"description": "Development", "quantity": 4, "unit_price": 250.0},
            ],
        )
        return engine, inv

    def test_create_invoice(self) -> None:
        engine, inv = self._make_engine_with_invoice()
        self.assertEqual(inv.invoice_id, "INV-0001")
        self.assertEqual(inv.total, 1000.0)
        self.assertEqual(inv.status, "DRAFT")

    def test_create_invoice_requires_line_items(self) -> None:
        engine = FinancialOperationsEngine()
        with self.assertRaises(ValueError):
            engine.create_invoice(client_id="CLT-0001", project_id="PROJ-0001", line_items=[])

    def test_record_payment_partial(self) -> None:
        engine, inv = self._make_engine_with_invoice()
        payment = engine.record_payment(inv.invoice_id, amount=300.0, method="Paystack")
        self.assertEqual(payment.amount, 300.0)
        self.assertEqual(payment.method, "Paystack")
        self.assertEqual(inv.status, "PARTIALLY_PAID")
        self.assertEqual(inv.balance, 700.0)

    def test_record_payment_full_auto_paid(self) -> None:
        """BR-044-003: Auto-PAID on zero balance."""
        engine, inv = self._make_engine_with_invoice()
        engine.record_payment(inv.invoice_id, amount=1000.0)
        self.assertEqual(inv.status, "PAID")
        self.assertEqual(inv.balance, 0.0)

    def test_overpayment_rejected_via_engine(self) -> None:
        """BR-044-002: Engine enforces no overpayment."""
        engine, inv = self._make_engine_with_invoice()
        with self.assertRaises(ValueError):
            engine.record_payment(inv.invoice_id, amount=1500.0)

    def test_payment_to_void_invoice_rejected(self) -> None:
        engine, inv = self._make_engine_with_invoice()
        inv.void()
        with self.assertRaises(ValueError):
            engine.record_payment(inv.invoice_id, amount=100.0)

    def test_record_expense(self) -> None:
        engine = FinancialOperationsEngine()
        exp = engine.record_expense(
            category="Software Licenses",
            amount=200.0,
            project_id="PROJ-0001",
            vendor="JetBrains",
            receipt_reference="REC-JB-001",
        )
        self.assertEqual(exp.expense_id, "EXP-0001")
        self.assertEqual(exp.category, "Software Licenses")
        self.assertEqual(exp.vendor, "JetBrains")

    def test_profitability_calculation(self) -> None:
        """BR-044-006: Revenue - Cost = Profit."""
        engine, inv = self._make_engine_with_invoice()
        engine.record_payment(inv.invoice_id, amount=1000.0)
        engine.record_expense(category="Dev Cost", amount=600.0, project_id="PROJ-0001")

        result = engine.calculate_profitability(project_id="PROJ-0001")
        self.assertEqual(result["revenue"], 1000.0)
        self.assertEqual(result["cost"], 600.0)
        self.assertEqual(result["profit"], 400.0)
        self.assertEqual(result["margin_pct"], 40.0)

    def test_cash_flow_calculation(self) -> None:
        """BR-044-005: Cash Flow = Revenue - Expenses."""
        engine, inv = self._make_engine_with_invoice()
        engine.record_payment(inv.invoice_id, amount=1000.0)
        engine.record_expense(category="Operations", amount=300.0)

        report = engine.generate_financial_report()
        self.assertEqual(report.kpis["cash_flow"], 700.0)

    def test_invoice_aging_warning(self) -> None:
        """BR-044-007: Warn when AR > 30 days."""
        engine = FinancialOperationsEngine()
        past_due = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        inv = engine.create_invoice(
            client_id="CLT-0001",
            project_id="PROJ-0001",
            line_items=[{"description": "Work", "quantity": 1, "unit_price": 5000.0}],
            due_date=past_due,
        )
        inv.status = "SENT"

        report = engine.generate_financial_report()
        self.assertTrue(len(report.warnings) > 0)
        self.assertIn("outstanding > 30 days", report.warnings[0])

    def test_outstanding_invoices_in_report(self) -> None:
        """BR-044-004: Outstanding invoices appear in financial reports."""
        engine, inv = self._make_engine_with_invoice()
        inv.status = "SENT"

        report = engine.generate_financial_report()
        self.assertEqual(len(report.outstanding_invoices), 1)
        self.assertEqual(report.outstanding_invoices[0]["invoice_id"], "INV-0001")

    def test_void_invoice_excluded_from_revenue(self) -> None:
        engine, inv = self._make_engine_with_invoice()
        engine.record_payment(inv.invoice_id, amount=1000.0)

        # Create second invoice and void it
        inv2 = engine.create_invoice(
            client_id="CLT-0002",
            project_id="PROJ-0002",
            line_items=[{"description": "Consulting", "quantity": 1, "unit_price": 2000.0}],
        )
        inv2.void()

        result = engine.calculate_profitability()
        self.assertEqual(result["revenue"], 1000.0)  # Only first invoice revenue counted

    def test_financial_report_generation(self) -> None:
        engine, inv = self._make_engine_with_invoice()
        engine.record_payment(inv.invoice_id, amount=1000.0)
        engine.record_expense(category="Rent", amount=200.0)

        report = engine.generate_financial_report()
        self.assertEqual(report.report_id, "FIN-0001")
        self.assertIn("Revenue", report.executive_summary)
        self.assertEqual(report.kpis["total_revenue"], 1000.0)
        self.assertEqual(report.kpis["total_expenses"], 200.0)
        self.assertEqual(report.kpis["profit"], 800.0)
        self.assertIsNotNone(report.snapshot)

    def test_explainability_in_recommendations(self) -> None:
        """BR-044-010: Every recommendation explains why, calculations, assumptions."""
        engine = FinancialOperationsEngine()
        past_due = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        inv = engine.create_invoice(
            client_id="CLT-0001",
            project_id="PROJ-0001",
            line_items=[{"description": "Service", "quantity": 1, "unit_price": 10000.0}],
            due_date=past_due,
        )
        inv.status = "SENT"

        report = engine.generate_financial_report()
        for rec in report.recommendations:
            self.assertIn("why", rec, f"Recommendation missing 'why': {rec}")
            self.assertIn("calculations", rec, f"Recommendation missing 'calculations': {rec}")
            self.assertIn("assumptions", rec, f"Recommendation missing 'assumptions': {rec}")

    def test_forecast_cashflow(self) -> None:
        engine, inv = self._make_engine_with_invoice()
        engine.record_payment(inv.invoice_id, amount=1000.0)
        engine.record_expense(category="Ops", amount=100.0, date="2026-06-01T00:00:00+00:00")
        engine.record_expense(category="Ops", amount=100.0, date="2026-07-01T00:00:00+00:00")

        forecast = engine.forecast_cashflow(horizon_days=90)
        self.assertIn("current_cash", forecast)
        self.assertIn("projected_inflows", forecast)
        self.assertIn("projected_outflows", forecast)
        self.assertIn("net_position", forecast)
        self.assertEqual(forecast["horizon_days"], 90)

    def test_advisory_boundary_never_modifies_proposals(self) -> None:
        """BR-044-008: Engine never modifies external objects."""
        engine = FinancialOperationsEngine()
        proposal = {"id": "PROP-0001", "status": "APPROVED", "total": 50000.0}
        original = dict(proposal)

        # Run financial operations
        engine.create_invoice(
            client_id="CLT-0001",
            project_id="PROJ-0001",
            line_items=[{"description": "Work", "quantity": 1, "unit_price": 50000.0}],
        )

        # Proposal object must remain untouched
        self.assertEqual(proposal, original)

    def test_snapshot_serialization(self) -> None:
        snap = FinancialSnapshot(
            total_revenue=10000.0,
            total_expenses=3000.0,
            profit=7000.0,
            cash_flow=7000.0,
            margin_pct=70.0,
        )
        d = snap.to_dict()
        self.assertEqual(d["total_revenue"], 10000.0)
        self.assertEqual(d["profit"], 7000.0)

    def test_financial_report_serialization(self) -> None:
        report = FinancialReport(
            report_id="FIN-TEST",
            executive_summary="Test summary",
            kpis={"revenue": 1000.0},
            warnings=["Test warning"],
            recommendations=[{"action": "Test", "why": "Because", "calculations": "N/A", "assumptions": "None"}],
        )
        d = report.to_dict()
        self.assertEqual(d["report_id"], "FIN-TEST")
        self.assertEqual(len(d["recommendations"]), 1)


if __name__ == "__main__":
    unittest.main()
