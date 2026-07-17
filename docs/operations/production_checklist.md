# JBK-OS Production Checklist

This checklist must be fully completed and signed off before declaring a new build ready for production deployment.

## 1. Kernel Verification
- [ ] JBK OS boots successfully on a clean environment without errors.
- [ ] Runtime registries (Worker, Project, Skill, Knowledge) load and serialize correctly.
- [ ] AI Gateway connects to the configured model provider (Gemini/Claude).
- [ ] Subsystem health statuses are computed as healthy.

## 2. Configuration Validation
- [ ] The `JBK_ENVIRONMENT` environment variable is explicitly set to `PRODUCTION`.
- [ ] Logger level is set to `INFO` (do not use `DEBUG` in production).
- [ ] The GCP project ID is set to `jbk-os-production`.
- [ ] Terraform state matches the deployed resources (no drift).

## 3. Security Hardening
- [ ] Production secrets are rotated and securely stored in GCP Secret Manager (not in code).
- [ ] IAM service account permissions are validated for least privilege.
- [ ] No debug or mock development endpoints (e.g. testing bypass routes) remain active in the release.
- [ ] Public access on the Cloud Run service is restricted via HTTPS.

## 4. Deployment Sanity Checks
- [ ] The container image tag matches the release tag (e.g., `v1.0.0`).
- [ ] The Cloud Run service URL responds with `200 OK` on `/health`.
- [ ] Custom domain DNS mappings are active and routing correctly.
- [ ] SSL certificate is valid and active on HTTPS.
