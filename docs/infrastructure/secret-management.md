# Secret Management Guide — JBK-OS

**Work Order:** OL-0004
**Category:** Project-Memory
**Owner:** Security Architect / DevOps Engineer
**Status:** Active
**Created:** 2026-07-15
**Review Date:** 2027-07-15
**Related:** [cloud-architecture.md](cloud-architecture.md), [environment-management.md](environment-management.md)

---

## 1. Principles

- **No secrets in Git.** Ever. Not in code, config files, or history.
- **No secrets in Terraform state.** Secret slots are declared in Terraform; values are populated via `gcloud` CLI.
- **No secrets in CI/CD logs.** GitHub Actions secrets are masked automatically.
- **Least privilege access.** Only the runtime service account can read secrets. The CI/CD account cannot.

---

## 2. Secret Inventory

| Secret ID | Category | Status | Consuming Component |
| :--- | :--- | :--- | :--- |
| `jbk-os-secret-key` | Application | Active | JBK-OS kernel |
| `gemini-api-key` | AI Integration | Reserved (v2+) | AI Gateway |
| `oauth-client-secret` | OAuth | Reserved (v2+) | Auth module |
| `database-url` | Database | Reserved (v2+) | Data layer |

---

## 3. Creating a Secret Value

Secrets must be populated via `gcloud` CLI after `terraform apply`.
**Never populate secrets through the GCP Console** for audit traceability.

```bash
# Generate a strong application secret key
python -c "import secrets; print(secrets.token_hex(32))" | \
  gcloud secrets versions add jbk-os-secret-key --data-file=-

# Add Gemini API key (when Gemini integration begins)
echo -n "YOUR_GEMINI_API_KEY" | \
  gcloud secrets versions add gemini-api-key --data-file=-
```

---

## 4. Accessing Secrets at Runtime

The Cloud Run runtime service account (`jbk-os-runtime`) has `secretmanager.secretAccessor`
permission. Secrets are injected as environment variables at container startup via the
Cloud Run secret reference configuration in `infra/terraform/cloud_run.tf`.

The application reads secrets from environment variables (e.g., `os.environ["JBK_SECRET_KEY"]`).

**No application code calls the Secret Manager API directly.**

---

## 5. Rotating a Secret

```bash
# 1. Generate new value
NEW_VALUE=$(python -c "import secrets; print(secrets.token_hex(32))")

# 2. Add as a new version (old version remains available during rotation)
echo -n "$NEW_VALUE" | \
  gcloud secrets versions add jbk-os-secret-key --data-file=-

# 3. Verify the new version exists
gcloud secrets versions list jbk-os-secret-key

# 4. Deploy new container revision (forces Cloud Run to reload env vars)
gcloud run services update jbk-os --region=europe-west1

# 5. Verify application health after rotation
curl -s https://YOUR_CLOUD_RUN_URL/health

# 6. Disable (not delete) the old version after verification
gcloud secrets versions disable <OLD_VERSION_NUMBER> \
  --secret=jbk-os-secret-key
```

---

## 6. Rotation Schedule

| Secret | Rotation Frequency |
| :--- | :--- |
| `jbk-os-secret-key` | Every 90 days |
| `gemini-api-key` | Per provider recommendation |
| `oauth-client-secret` | Every 90 days |
| `database-url` | Upon credential change |

---

## 7. Emergency Secret Revocation

If a secret is suspected to be compromised:

```bash
# 1. Immediately disable ALL versions of the secret
gcloud secrets versions list <secret-id> --format="value(name)" | \
  xargs -I{} gcloud secrets versions disable {} --secret=<secret-id>

# 2. Create a new version with a new value immediately
echo -n "NEW_VALUE" | gcloud secrets versions add <secret-id> --data-file=-

# 3. Redeploy Cloud Run to force reload
gcloud run services update jbk-os --region=europe-west1

# 4. Audit access logs in Cloud Logging
# Filter: resource.type="secretmanager.googleapis.com/Secret"
```

---

## 8. Audit Trail

All Secret Manager access is recorded in **Cloud Audit Logs** under:
- **Data Access logs**: Secret version reads by the runtime service account.
- **Admin Activity logs**: Secret creation, rotation, and deletion.

Access at: **Cloud Logging → Logs Explorer → Filter: `protoPayload.serviceName="secretmanager.googleapis.com"`**
