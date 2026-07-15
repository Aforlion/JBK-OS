Specification 044 — Financial Operations Engine
Goal

Create the financial operating layer that manages the commercial lifecycle after proposal approval and throughout project execution.

It should remain advisory and never connect directly to banks in V1.

New Models
invoice.py
Invoice

Fields

invoice_id
client_id
project_id
issue_date
due_date
status

Statuses

DRAFT

SENT

PARTIALLY_PAID

PAID

OVERDUE

VOID

Contains

line items
subtotal
tax
discounts
total
payment.py
Payment

Fields

payment_id
invoice_id
amount
date
method

Methods

Bank Transfer
Stripe
Paystack
Flutterwave
Cash

(V1 only stores them.)

expense.py
Expense

Tracks

category
amount
project
vendor
receipt reference
financial_snapshot.py

Captures

Revenue

Expenses

Profit

Outstanding invoices

Cash flow

Accounts receivable

Margin

Utilization

financial_report.py

Output object.

Contains

Executive Summary

KPIs

Warnings

Recommendations

Cash health

Outstanding invoices

Projected runway

Engine
financial_operations_engine.py

Main methods

create_invoice()

record_payment()

record_expense()

calculate_profitability()

generate_financial_report()

forecast_cashflow()
Business Rules
BR-044-001

Invoice totals must equal

subtotal
-tax
-discount
BR-044-002

Payments never exceed invoice balance.

BR-044-003

Invoice becomes PAID automatically when balance reaches zero.

BR-044-004

Outstanding invoices appear in financial reports.

BR-044-005

Cash flow

Revenue

- Expenses

= Cash Flow
BR-044-006

Project profitability

Revenue

- Internal Cost

= Profit
BR-044-007

Warn when

Accounts Receivable >

30 days

BR-044-008

Never modify proposals.

Financial Operations begins only AFTER proposal approval.

BR-044-009

Never authorize payments.

It records them only.

BR-044-010

Explainability

Every recommendation explains

why
calculations
assumptions
Tests

Approximately 20–25 tests.

Examples

Invoice totals

Partial payments

Overpayments rejected

Profit calculation

Cash flow

Invoice aging

Forecasting

Expense recording

Financial report generation

Explainability
Brain Entry
Financial-Operations-Standards.md

Principles

Financial engines are advisory.
Never authorize spending.
Never connect to banking APIs in V1.
Preserve complete audit trails.
Every financial metric must be reproducible.