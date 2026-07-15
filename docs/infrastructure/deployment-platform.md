# Deployment Platform Guide — JBK-OS

**Work Order:** OL-0004
**Category:** Project-Memory
**Owner:** Startup CTO / DevOps Engineer
**Status:** Active
**Created:** 2026-07-15
**Review Date:** 2027-07-15
**Related:** [cloud-architecture.md](cloud-architecture.md), [operational-runbook.md](operational-runbook.md)

---

## 1. Platform Decision — Google Cloud Run

Cloud Run is the selected and standardized production hosting platform for JBK-OS.

### Evaluation Matrix

| Criterion | Cloud Run | GKE | Compute Engine | App Engine |
| :--- | :--- | :--- | :--- | :--- |
| Operational simplicity | ✅ Managed serverless | ❌ Cluster ops | ❌ VM ops | ⚠️ Limited |
| Cost at current load | ✅ Pay-per-request | ❌ Always-on nodes | ❌ Always-on | ✅ |
| Managed TLS & HTTPS | ✅ Automatic | ⚠️ Manual | ❌ Manual | ✅ |
| Python / FastAPI support | ✅ Any container | ✅ | ✅ | ✅ |
| Scales to zero | ✅ | ❌ | ❌ | ✅ |
| Deployment latency | ✅ Seconds | ❌ Minutes | ❌ Minutes | ✅ |
| JBK operational maturity | ✅ Right fit now | ❌ Premature | ❌ Manual overhead | ⚠️ Aging |

**Future path**: GKE is the natural graduation when multi-service deployments or
custom networking requirements emerge.

---

## 2. Container Configuration

| Setting | Value | Rationale |
| :--- | :--- | :--- |
| Base image | `python:3.13-slim` | Matches CI, minimal attack surface |
| Runtime user | `jbkos` (UID 1001) | Non-root for security |
| Port | `8080` | Cloud Run standard |
| CPU | `1 vCPU` | Sufficient for single-instance v1 load |
| Memory | `512Mi` | Conservative — increase if profiling shows need |
| Min instances | `0` | Scale to zero for cost efficiency |
| Max instances | `10` | Prevents runaway cost under unexpected load |
| Request timeout | `300s` | Supports long-running AI operations |

---

## 3. Deployment Process

### First-time Provisioning (Operator)

1. Run `terraform apply` from `infra/terraform/` to create all GCP resources.
2. Populate secrets with `gcloud secrets versions add`.
3. Configure GitHub Actions secrets.
4. Tag and push: `git tag v1.0.0 && git push origin v1.0.0`

### Routine Deployments (Automated)

Every version tag push triggers `.github/workflows/deploy.yml`:

```
git tag v1.x.x
git push origin v1.x.x
     │
     ▼
GitHub Actions
  ├── Authenticate (WIF — keyless)
  ├── Build Docker image
  ├── Push to Artifact Registry
  └── Deploy to Cloud Run (new revision)
```

New revisions receive 100% traffic automatically. Old revisions remain available for rollback.

---

## 4. Health Checks

Cloud Run performs automatic health checks via `scripts/health_check.py`-compatible HTTP probes:

| Probe Type | Endpoint | Period | Failure Threshold |
| :--- | :--- | :--- | :--- |
| Startup | `GET /health` | 5s | 6 failures |
| Liveness | `GET /health` | 30s | 3 failures |

The `GET /health` endpoint must return `HTTP 200`. Any non-200 response triggers a container restart.

---

## 5. Traffic Management

Cloud Run revisions support traffic splitting. For zero-downtime rollbacks:

```bash
# Roll back to a previous revision
gcloud run services update-traffic jbk-os \
  --region=europe-west1 \
  --to-revisions=jbk-os-XXXXXXXX=100

# Gradual traffic migration (canary, if needed in future)
gcloud run services update-traffic jbk-os \
  --region=europe-west1 \
  --to-revisions=jbk-os-NEW=10,jbk-os-STABLE=90
```

---

## 6. Observability

All Cloud Run logs are automatically ingested into **Cloud Logging**:
- Standard output (`stdout`) → `textPayload`
- JSON structured output → parsed into `jsonPayload` (preferred)

The `scripts/health_check.py` outputs JSON for structured log ingestion.

Access logs at: **Cloud Logging → Logs Explorer → Filter: `resource.type="cloud_run_revision"`**

---

## 7. Cost Model

| Scenario | Estimated Monthly Cost |
| :--- | :--- |
| Zero traffic (scale to zero) | ~$0.00 |
| 1M requests/month, 200ms avg | ~$1–5 USD |
| 10M requests/month, 200ms avg | ~$10–20 USD |

Cloud Run pricing: per vCPU-second and GB-second consumed during request handling.
Idle time (between requests) is not charged when min-instances = 0.
