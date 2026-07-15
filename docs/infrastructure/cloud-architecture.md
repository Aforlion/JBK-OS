# Cloud Architecture — JBK-OS Production Infrastructure

**Work Order:** OL-0004
**Category:** Project-Memory
**Owner:** Startup CTO / DevOps Engineer
**Status:** Active
**Created:** 2026-07-15
**Review Date:** 2027-07-15
**Related:** [environment-management.md](environment-management.md), [deployment-platform.md](deployment-platform.md), [operational-runbook.md](operational-runbook.md)

---

## 1. Executive Summary

JBK-OS is deployed on Google Cloud Platform using a serverless-first architecture. The production environment is provisioned via Terraform and operates in the `europe-west1` (Belgium) region. All infrastructure is defined as code, version-controlled, and reproducible from a clean state.

---

## 2. Platform Overview

```
┌─────────────────────────────────────────────────────┐
│            Google Cloud Project: jbk-os-production  │
│            Region: europe-west1 (Belgium)           │
│                                                     │
│  ┌──────────────────┐    ┌───────────────────────┐  │
│  │  Artifact        │    │  Cloud Run             │  │
│  │  Registry        │───▶│  Service: jbk-os       │  │
│  │  (Docker images) │    │  Identity: jbk-os-     │  │
│  └──────────────────┘    │  runtime SA            │  │
│                          └──────────┬────────────┘  │
│                                     │               │
│  ┌──────────────────────────────────▼────────────┐  │
│  │  Secret Manager                               │  │
│  │  - jbk-os-secret-key                         │  │
│  │  - gemini-api-key        (reserved)           │  │
│  │  - oauth-client-secret   (reserved)           │  │
│  │  - database-url          (reserved)           │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  Cloud Logging + Cloud Monitoring             │  │
│  │  Cloud Error Reporting                        │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘

GitHub Actions ──WIF──▶ github-actions SA ──▶ deploy to Cloud Run
```

---

## 3. Architectural Decisions

### Region — `europe-west1` (Belgium)
- **Rationale**: Optimal latency (~100ms) from West Africa. Full Cloud Run, Secret Manager, and Artifact Registry support. Cost-efficient egress.

### Deployment Target — Cloud Run
- **Rationale**: Serverless, scales to zero, managed HTTPS, pay-per-request. No cluster management overhead. Correct fit for JBK-OS v1.x operational stage.
- **Future path**: GKE when multi-service deployments are required.

### Authentication — Workload Identity Federation
- **Rationale**: Eliminates all static service account keys. GitHub Actions authenticates via short-lived OIDC tokens. No credential rotation needed.

### IaC — Terraform
- **Rationale**: Provider-independent, reproducible, readable. All infrastructure changes are code-reviewed before application.

---

## 4. Resource Naming Standards

| Resource | Pattern | Example |
| :--- | :--- | :--- |
| GCP Project | `jbk-os-<env>` | `jbk-os-production` |
| Cloud Run Service | `jbk-os` | `jbk-os` |
| Service Account | `jbk-os-<role>` | `jbk-os-runtime` |
| Artifact Registry | `jbk-os-registry` | `jbk-os-registry` |
| Secret Manager | `<component>-<qualifier>` | `gemini-api-key` |
| Terraform State Bucket | `jbk-os-terraform-state` | `jbk-os-terraform-state` |

---

## 5. Labels and Tagging Conventions

All GCP resources carry the following labels:

| Label Key | Required | Values |
| :--- | :--- | :--- |
| `product` | Yes | `jbk-os` |
| `environment` | Yes | `production`, `development` |
| `managed-by` | Yes | `terraform` |
| `work-order` | Recommended | `ol-0004` |

---

## 6. IAM Role Matrix

| Identity | Role | Scope |
| :--- | :--- | :--- |
| `jbk-os-runtime` | `secretmanager.secretAccessor` | Project |
| `jbk-os-runtime` | `logging.logWriter` | Project |
| `jbk-os-runtime` | `monitoring.metricWriter` | Project |
| `jbk-os-runtime` | `errorreporting.writer` | Project |
| `github-actions` | `artifactregistry.writer` | Project |
| `github-actions` | `run.developer` | Project |
| `github-actions` | `iam.serviceAccountUser` | jbk-os-runtime SA |
| `allUsers` | `run.invoker` | Cloud Run service |

---

## 7. Enabled APIs

| API | Purpose |
| :--- | :--- |
| `run.googleapis.com` | Cloud Run hosting |
| `artifactregistry.googleapis.com` | Docker image storage |
| `secretmanager.googleapis.com` | Secret management |
| `iam.googleapis.com` | Identity management |
| `iamcredentials.googleapis.com` | WIF token exchange |
| `logging.googleapis.com` | Log ingestion |
| `monitoring.googleapis.com` | Metrics collection |
| `clouderrorreporting.googleapis.com` | Error reporting |
| `cloudresourcemanager.googleapis.com` | Project management |
