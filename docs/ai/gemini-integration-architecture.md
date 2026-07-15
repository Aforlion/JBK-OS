# Gemini Integration Architecture — JBK-OS

**Work Order:** OL-0005
**Category:** Project-Memory
**Owner:** AI Integration Engineer
**Status:** Active
**Created:** 2026-07-15
**Review Date:** 2027-07-15
**Related:** [ai-capability.md](ai-capability.md), [prompt-management.md](prompt-management.md), [operational-monitoring.md](operational-monitoring.md)

---

## 1. Executive Summary

JBK-OS integrates Google Gemini models as a core platform capability. The integration preserves provider neutrality via the `AIGateway` (`core/ai_gateway.py`), routing requests to the appropriate adapter while exposing vendor-agnostic APIs to downstream business engines.

---

## 2. Intelligence Layer Architecture

The JBK-OS intelligence system is structured hierarchically to prevent business logic from depending on direct vendor SDK details.

```
┌─────────────────────────────────────────────────────────┐
│                    Business Engines                     │
│    (AI Executive Assistant, Skill Runtime, etc.)        │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                       AIGateway                         │
│   - Provider Discovery      - Usage Telemetry           │
│   - Capability Matching     - Failover & Rollback       │
└────────────────────────────┬────────────────────────────┘
                             │
                             ├──────────────────────────────┐
                             ▼                              ▼
                 ┌───────────────────────┐      ┌───────────────────────┐
                 │     GeminiAdapter     │      │     ClaudeAdapter     │
                 │    (google-genai)     │      │     (Anthropic)       │
                 └───────────┬───────────┘      └───────────────────────┘
                             │
                             ▼
                Google Gemini API endpoint
```

---

## 3. Gemini Adapter Implementation

The `GeminiAdapter` (`core/ai_provider.py`) maps the standard `AIRequest` payload to the official Google Gemini API format using the new `google-genai` SDK:

- **SDK Package**: `google-genai==0.1.1`
- **Client Instantiation**: `genai.Client(api_key=...)`
- **Generation Method**: `client.models.generate_content(...)`
- **Fallback Simulation**: If `GEMINI_API_KEY` is not detected in the environment, the adapter drops back to a simulated generation format to support local offline development without breaking the boot sequence.

---

## 4. Error Handling and Resilience

To ensure JBK-OS stability, the Gemini adapter wraps API requests with extensive exception guards:

- **Transient Failures (429 Rate Limits, 500, 503)**: Retried up to 3 times using an exponential backoff factor of 2.0.
- **Permanent Errors (Authentication failure, Invalid parameters)**: Instantly converted to standard `success=False` responses with populated error descriptions to allow `AIGateway` to perform automatic fallback routing to backup providers.
