# Disaster Recovery Guide — JBK-OS

**Work Order:** OL-0004
**Category:** Project-Memory
**Owner:** DevOps Engineer / Security Architect
**Status:** Active
**Created:** 2026-07-15
**Review Date:** 2027-07-15
**Related:** [cloud-architecture.md](cloud-architecture.md), [operational-runbook.md](operational-runbook.md)

---

## 1. Recovery Objectives

| Metric | Target | Rationale |
| :--- | :--- | :--- |
| **RPO** (Recovery Point Objective) | 0 (stateless) | JBK-OS v1 is stateless. No data store to recover. |
| **RTO** (Recovery Time Objective) | < 10 minutes | Cloud Run revision rollback takes seconds. Full re-deploy takes ~5 minutes. |

> As a stateless application in v1.0.0, JBK-OS has no database and no persistent state.
> The "backup" for a stateless system is its container image and configuration in version control.
> This RTO/RPO will be revised when a database is introduced.

---

## 2. Infrastructure as Recovery

The entire JBK-OS production environment is recoverable from two sources:

| Source | Contains | Recovery Time |
| :--- | :--- | :--- |
| **GitHub repository** | All code, IaC, config, workflows | `terraform apply` < 10 minutes |
| **Artifact Registry** | All container image versions | Immediate — already built |
| **Secret Manager** | All secret slots (values must be re-populated if project is destroyed) | 5 minutes with documented procedure |

---

## 3. Incident Classification

| Severity | Description | Example |
| :--- | :--- | :--- |
| **P1 — Critical** | Production completely unavailable | Cloud Run service down, all requests failing |
| **P2 — High** | Degraded performance or partial failure | High error rate, slow response times |
| **P3 — Medium** | Non-critical component failure | Logging pipeline disruption |
| **P4 — Low** | Advisory / monitoring alert | Dependabot PR opened |

---

## 4. Scenario Runbooks

### Scenario A — Bad Deployment (P1)

**Symptom**: New revision deployed, health checks failing, error rate spikes.

```bash
# 1. Identify the last known-good revision
gcloud run revisions list --service=jbk-os --region=europe-west1

# 2. Roll back 100% traffic to previous revision
gcloud run services update-traffic jbk-os \
  --region=europe-west1 \
  --to-revisions=<PREVIOUS_REVISION_NAME>=100

# 3. Verify health
curl https://YOUR_CLOUD_RUN_URL/health

# 4. Investigate bad revision logs
# Cloud Logging → Logs Explorer → Filter by bad revision name
```

**RTO**: < 2 minutes.

---

### Scenario B — GCP Region Outage (P1)

**Symptom**: `europe-west1` region completely unavailable (rare — GCP SLA 99.95%).

```bash
# 1. Deploy to backup region (europe-west2) using same image
gcloud run deploy jbk-os \
  --image=europe-west1-docker.pkg.dev/PROJECT_ID/jbk-os-registry/jbk-os:latest \
  --region=europe-west2 \
  --service-account=jbk-os-runtime@PROJECT_ID.iam.gserviceaccount.com

# 2. Update DNS / share new Cloud Run URL with users
# 3. Monitor for region recovery
# 4. When europe-west1 recovers, redeploy there and revert DNS
```

**RTO**: < 10 minutes.

---

### Scenario C — Accidental Infrastructure Deletion (P1)

**Symptom**: Terraform state destroyed or GCP project deleted.

```bash
# 1. Recreate project using Terraform
cd infra/terraform
terraform init
terraform apply

# 2. Re-populate secrets using documented values from secure vault
echo -n "SECRET" | gcloud secrets versions add jbk-os-secret-key --data-file=-

# 3. Configure GitHub Actions secrets (WIF outputs from terraform apply)

# 4. Trigger redeployment via version tag
git push origin v1.0.0
```

**RTO**: < 15 minutes (assumes secrets are securely documented offline).

---

### Scenario D — Compromised Secret (P2)

Follow the Emergency Secret Revocation procedure in [secret-management.md](secret-management.md).

**RTO**: < 5 minutes.

---

## 5. Backup Verification Schedule

| Verification | Frequency | Procedure |
| :--- | :--- | :--- |
| `terraform plan` runs clean | Monthly | `terraform plan` must show zero changes |
| Clean deploy from tag | Quarterly | Push a test tag to staging (when staging exists) |
| Secret rotation drill | Quarterly | Rotate `jbk-os-secret-key` following Section 5 of secret-management.md |
| Full DR drill | Annually | Execute Scenario C procedure against a temporary test project |
