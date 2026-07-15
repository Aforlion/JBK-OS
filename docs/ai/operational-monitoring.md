# Operational Monitoring Guide — JBK-OS

**Work Order:** OL-0005
**Category:** Project-Memory
**Owner:** DevOps Engineer
**Status:** Active
**Created:** 2026-07-15
**Review Date:** 2027-07-15
**Related:** [gemini-integration-architecture.md](gemini-integration-architecture.md)

---

## 1. Telemetry Capture

For every generation dispatch, `AIGateway` compiles execution metrics and records them as an `AIUsageRecord`.

Captured attributes include:
- `provider_id`: Used model API identifier
- `model`: Specific model version deployed
- `latency_ms`: Server turn-around response time
- `token_usage`: Nested `input` and `output` token metrics
- `estimated_cost`: Computed cost based on configured rates
- `success`: Execution outcome state (Boolean)

---

## 2. Model Billing Rates

Estimated cost calculation is run using standard pricing models configured in `_MODEL_RATES` (`core/ai_provider.py`):

| Model | Input Rate (per 1K) | Output Rate (per 1K) |
| :--- | :--- | :--- |
| `gemini-2.5-pro` | $0.00125 | $0.00125 |
| `gemini-2.5-flash` | $0.000075 | $0.000075 |

---

## 3. Log Ingestion

All structured metrics from `AIUsageRecord` are written to standard outputs and automatically ingested by GCP Cloud Logging, allowing operators to run real-time dashboards mapping request counts, total tokens consumed, and operational cost projections.
