# Pilot Onboarding Deployment Checklist

Complete this checklist for every new client pilot environment before handing access credentials over to the client.

## 1. Environment Provisioning
- [ ] Deploy new isolated project container to Cloud Run using client-specific service name.
- [ ] Set `JBK_ENVIRONMENT` environment variable to `PRODUCTION`.
- [ ] Configure client custom subdomain (e.g. `clientname.os.jbk.tech`).
- [ ] Wait for SSL certificate mapping to transition to active.

## 2. Secrets & Integrations Setup
- [ ] Generate and populate unique `JBK_SECRET_KEY` value in GCP Secret Manager.
- [ ] Configure client's custom `GEMINI_API_KEY` for AI executive operations.
- [ ] Verify that service accounts have read access to target secret versions.

## 3. Data Seeding
- [ ] Seed the Worker Registry with the client's internal executive staff IDs.
- [ ] Seed the Skill Registry with matching capabilities for the registered workers.
- [ ] Run a test kernel boot to confirm registries load without failures.

## 4. Verification & Handover
- [ ] Perform a GET request to `/health` and ensure status is `HEALTHY`.
- [ ] Send welcome onboarding email containing registration link and login instructions.
