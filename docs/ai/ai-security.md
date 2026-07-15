# AI Security Guide — JBK-OS

**Work Order:** OL-0005
**Category:** Project-Memory
**Owner:** Security Architect
**Status:** Active
**Created:** 2026-07-15
**Review Date:** 2027-07-15
**Related:** [gemini-integration-architecture.md](gemini-integration-architecture.md), [secret-management.md](../infrastructure/secret-management.md)

---

## 1. Credentials Isolation

No API credentials or key files are ever written to configuration files or committed to Git. All environments enforce dynamic lookup from `os.environ` settings:

- **Local Dev**: Sourced from git-ignored `.env` file.
- **Production (GCP)**: Injected dynamically by Cloud Run from Secret Manager at container launch.

---

## 2. API Logging Safeguards

To prevent leaking sensitive corporate data or proprietary system instructions into logging indexes:

- Log files capture execution metadata only (request ID, model ID, latency, token count, cost, and success status).
- **Prompt content and system instruction texts are excluded from metrics and standard logging output.**
- The `health_check.py` and adapter status metrics log structured JSON telemetry without printing payload content.

---

## 3. Least-Privilege Execution

The `jbk-os-runtime` service account is the sole identity authorized to access `gemini-api-key` secret version. Future developer access is restricted via IAM roles allowing audit-level overview of usage records only.
