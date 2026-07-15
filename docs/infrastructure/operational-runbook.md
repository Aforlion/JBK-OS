# Operational Runbook — JBK-OS

**Work Order:** OL-0004
**Category:** Project-Memory
**Owner:** DevOps Engineer
**Status:** Active
**Created:** 2026-07-15
**Review Date:** 2027-07-15
**Related:** [cloud-architecture.md](cloud-architecture.md), [disaster-recovery.md](disaster-recovery.md), [secret-management.md](secret-management.md)

---

## 1. Daily Operations

### 1.1 Service Health Check
```bash
# Check Cloud Run service status
gcloud run services describe jbk-os --region=europe-west1 --format="value(status.conditions)"

# Quick HTTP health check
curl -s https://YOUR_CLOUD_RUN_URL/health | python -m json.tool
```

### 1.2 Review Overnight Logs
```bash
# View last 100 log entries
gcloud logging read \
  'resource.type="cloud_run_revision" AND severity>=WARNING' \
  --limit=100 \
  --format="table(timestamp, severity, textPayload)"
```

### 1.3 Check for Open Alerts
- GitHub → Security → **Dependabot alerts**
- GitHub → Security → **Code scanning alerts**
- GCP → **Cloud Monitoring → Alerting policies**

---

## 2. Deployment Operations

### 2.1 Routine Production Deployment
```bash
# Tag the release (triggers deploy.yml automatically)
git tag v1.x.x
git push origin v1.x.x

# Monitor the deployment
# GitHub → Actions → Deploy workflow run
```

### 2.2 Verify Deployment
```bash
# Check revision is serving traffic
gcloud run revisions list --service=jbk-os --region=europe-west1

# Verify health endpoint
curl -s https://YOUR_CLOUD_RUN_URL/health

# Check for errors in first 5 minutes post-deploy
gcloud logging read \
  'resource.type="cloud_run_revision" AND severity>=ERROR' \
  --freshness=5m \
  --limit=50
```

### 2.3 Rollback
See [disaster-recovery.md — Scenario A](disaster-recovery.md).

---

## 3. Secret Operations

### 3.1 Rotate Application Secret Key (every 90 days)
See [secret-management.md — Section 5](secret-management.md).

### 3.2 Add a New Secret
```bash
# 1. Declare the secret in infra/terraform/secret_manager.tf
# 2. terraform apply to create the secret slot
terraform apply -target=google_secret_manager_secret.your_new_secret

# 3. Populate the value
echo -n "YOUR_VALUE" | gcloud secrets versions add your-secret-id --data-file=-

# 4. Add secret reference to cloud_run.tf if injected as env var
# 5. terraform apply again to update Cloud Run
terraform apply
```

---

## 4. Scaling Operations

### 4.1 Adjust Instance Limits
```bash
# Edit infra/terraform/variables.tf: min_instances / max_instances
# Then apply:
terraform apply -target=google_cloud_run_v2_service.jbk_os
```

### 4.2 Adjust Resource Limits
```bash
# Edit var.cpu_limit and var.memory_limit in terraform.tfvars
# Then apply:
terraform apply -target=google_cloud_run_v2_service.jbk_os
```

---

## 5. Infrastructure Operations

### 5.1 Monthly Terraform Drift Check
```bash
cd infra/terraform
terraform plan

# Expected output: "No changes. Your infrastructure matches the configuration."
# Any unexpected changes must be investigated before the next apply.
```

### 5.2 Update Terraform Provider
```bash
# Review terraform.required_providers version constraint
# Update patch version, run:
terraform init -upgrade
terraform plan
# If plan is clean, commit the updated .terraform.lock.hcl
```

---

## 6. Incident Response

### 6.1 P1 Alert — Service Unavailable

1. **Acknowledge** the alert within 5 minutes.
2. **Identify** the last healthy revision: `gcloud run revisions list`.
3. **Rollback** traffic to last healthy revision (see DR Guide — Scenario A).
4. **Verify** health endpoint responds.
5. **Notify** stakeholders via Slack/email.
6. **Root cause** analysis in Cloud Logging.
7. **Fix** the issue in a new commit.
8. **Deploy** fixed version via new tag.
9. **Post-mortem** written and stored in `docs/incidents/`.

### 6.2 P1 Alert — Security Breach

1. **Immediately revoke** compromised secrets (see secret-management.md — Section 7).
2. **Revoke** the compromised service account if applicable:
   ```bash
   gcloud iam service-accounts disable jbk-os-runtime@PROJECT_ID.iam.gserviceaccount.com
   ```
3. **Audit** Cloud Logging for access patterns in the breach window.
4. **Rotate** all secrets (not just the compromised one).
5. **Re-enable** service account and redeploy.
6. **Report** to relevant stakeholders within 24 hours.

---

## 7. Maintenance Schedule

| Activity | Frequency | Owner |
| :--- | :--- | :--- |
| Review open Dependabot PRs | Monthly | DevOps |
| Review CodeQL security alerts | Quarterly | Security Architect |
| Rotate `jbk-os-secret-key` | Every 90 days | DevOps |
| Terraform drift check | Monthly | DevOps |
| DR verification drill | Annually | DevOps + CTO |
| Full security posture review | Annually | Security Architect |
| Terraform provider update | Quarterly | DevOps |

---

## 8. Useful Commands Reference

```bash
# Cloud Run
gcloud run services list --region=europe-west1
gcloud run services describe jbk-os --region=europe-west1
gcloud run revisions list --service=jbk-os --region=europe-west1

# Logs
gcloud logging read 'resource.type="cloud_run_revision"' --limit=50

# Secrets
gcloud secrets list --project=PROJECT_ID
gcloud secrets versions list SECRET_ID
gcloud secrets versions access latest --secret=SECRET_ID

# Artifact Registry
gcloud artifacts docker images list europe-west1-docker.pkg.dev/PROJECT_ID/jbk-os-registry

# Terraform
terraform plan
terraform apply
terraform output
```
