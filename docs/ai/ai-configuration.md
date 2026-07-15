# AI Configuration Guide — JBK-OS

**Work Order:** OL-0005
**Category:** Project-Memory
**Owner:** DevOps Engineer
**Status:** Active
**Created:** 2026-07-15
**Review Date:** 2027-07-15
**Related:** [gemini-integration-architecture.md](gemini-integration-architecture.md), [secret-management.md](../infrastructure/secret-management.md)

---

## 1. Parameters Reference

AI subsystems are driven entirely through the configuration yaml overlays.

| Parameter | Development Value | Production Value | Description |
| :--- | :--- | :--- | :--- |
| `ai.provider` | `gemini` | `gemini` | Primary registered adapter ID |
| `ai.model` | `gemini-2.5-flash` | `gemini-2.5-flash` | LLM version identifier |
| `ai.timeout_seconds` | `15` | `30` | Network request cancellation limit |
| `ai.max_retries` | `2` | `3` | Maximum retry attempts for transient errors |
| `ai.backoff_factor` | `1.5` | `2.0` | Exponential retry sleep multiplier |
| `ai.temperature` | `0.7` | `0.7` | Model response creativity value (0.0 to 1.0) |
| `ai.max_tokens` | `2048` | `4096` | Output token generation ceiling |

---

## 2. Credentials Configuration

The Gemini API key is loaded dynamically from environment variables at runtime.

- **Local Development**: Configured via the `.env` configuration file:
  ```
  GEMINI_API_KEY=your-local-key
  ```
- **Production (GCP Cloud Run)**: Loaded directly from Secret Manager and injected at container startup as an environment variable (`GEMINI_API_KEY`). No secrets are committed to Git.
