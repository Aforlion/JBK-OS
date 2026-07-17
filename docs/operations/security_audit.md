# JBK-OS Security Audit Report

This report documents the security posture, IAM configuration, secret rotation guidelines, and codebase compliance verification for JBK-OS V1.0.

## 1. IAM Permissions Verification

The production IAM structure follows the principle of least privilege. There are two principal service accounts:

### 1.1 Runtime Service Account (`jbk-os-runtime@PROJECT_ID.iam.gserviceaccount.com`)
This identity runs the JBK-OS Cloud Run container. It has **no** admin permissions and is restricted to:
- `roles/secretmanager.secretAccessor` (access secrets at startup).
- `roles/logging.logWriter` (write stdout/stderr logs to Cloud Logging).
- `roles/monitoring.metricWriter` (write performance counters to Cloud Monitoring).
- `roles/errorreporting.writer` (report runtime exceptions).

### 1.2 CI/CD Deployment Service Account (`github-actions@PROJECT_ID.iam.gserviceaccount.com`)
This identity is used by GitHub Actions via Workload Identity Federation (WIF) to build and deploy. It is restricted to:
- `roles/artifactregistry.writer` (push built Docker images).
- `roles/run.developer` (create new Cloud Run service revisions).
- `roles/iam.serviceAccountUser` (act as the runtime service account to assign it to Cloud Run).

## 2. Secrets Rotation

All production secrets must be rotated periodically. The commands below execute rotation for the two core test keys:

### 2.1 Rotating `jbk-os-secret-key`
```bash
# 1. Generate new 32-byte secret key
NEW_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# 2. Add new version to Secret Manager
echo -n "$NEW_KEY" | gcloud secrets versions add jbk-os-secret-key --data-file=-

# 3. Redeploy service to load new version
gcloud run services update jbk-os --region=europe-west1
```

### 2.2 Rotating `gemini-api-key`
```bash
# 1. Add new version to Secret Manager
echo -n "NEW_API_KEY_VALUE" | gcloud secrets versions add gemini-api-key --data-file=-

# 2. Redeploy service to load new version
gcloud run services update jbk-os --region=europe-west1
```

## 3. Codebase Audits

### 3.1 Debug & Testing Bypass Endpoints
We audited the web and core controllers. 
- All endpoints verify caller identities and execute proper authentication checks.
- No testing bypass routes, default development passwords, or backdoor endpoints exist in the production branch.

### 3.2 Logging Security Audit
We validated the Python `logging` configuration:
- System logs record execution metadata (Latencies, Engine names, Status metrics).
- Sensitive variables (like `JBK_SECRET_KEY`, `GEMINI_API_KEY`, API tokens, and passwords) are fetched dynamically from environments and are **never** logged to stdout/stderr.
