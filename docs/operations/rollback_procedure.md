# JBK-OS Rollback Procedure

This document describes the rollback procedures for different categories of production failures.

## 1. Application Deployment Rollback (P1 Outage)

If a new container tag or version tag results in a production crash or critical bug:

### Step 1: Identify Last Known Good Revision
List all deployed revisions to find the name of the previous healthy revision:
```bash
gcloud run revisions list --service=jbk-os --region=europe-west1
```

### Step 2: Route 100% Traffic to Previous Revision
Direct all traffic to the healthy revision immediately (takes <2 seconds):
```bash
gcloud run services update-traffic jbk-os \
  --region=europe-west1 \
  --to-revisions=jbk-os-<PREVIOUS_REVISION_NAME>=100
```

### Step 3: Validate Recovery
```bash
curl -s -o /dev/null -w "%{http_code}" https://os.jbk.tech/health
```

---

## 2. Configuration & Secret Rollback

If a secret rotation or variable change breaks the service:

### Step 1: Rollback Secret Version
If a newly rotated secret version (e.g. version 2) is corrupt:
```bash
# 1. Disable the bad secret version
gcloud secrets versions disable 2 --secret=jbk-os-secret-key

# 2. Re-enable the previous version (version 1)
gcloud secrets versions enable 1 --secret=jbk-os-secret-key

# 3. Redeploy Cloud Run to force a config reload
gcloud run services update jbk-os --region=europe-west1
```

### Step 2: Rollback Terraform Configuration
If a Terraform apply changed resource configurations unexpectedly:
1. Revert the git commit containing the Terraform configuration changes.
2. Run a plan to verify the changes:
   ```bash
   cd infra/terraform/app
   terraform plan
   ```
3. Apply the reverted configuration:
   ```bash
   terraform apply
   ```
