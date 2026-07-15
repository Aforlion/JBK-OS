# JBK-OS Infrastructure — Terraform Operator Guide

## Overview

This directory contains the Terraform configuration that provisions the JBK-OS production cloud
infrastructure on Google Cloud Platform.

| File | Purpose |
| :--- | :--- |
| `main.tf` | GCP provider, project, API enablement, Artifact Registry |
| `variables.tf` | All configurable parameters |
| `iam.tf` | Service accounts and Workload Identity Federation |
| `cloud_run.tf` | Cloud Run service definition |
| `secret_manager.tf` | Secret slot declarations (no values) |
| `outputs.tf` | Post-apply output values |

---

## Prerequisites

1. **Terraform** ≥ 1.6.0 installed locally.
2. **gcloud CLI** authenticated with an account that has Project Creator and Billing Account User permissions.
3. A GCP **Billing Account** ID.

---

## Step 1 — Create `terraform.tfvars`

Create a `terraform.tfvars` file in this directory (**never commit this file**):

```hcl
project_id      = "jbk-os-production-XXXXXX"   # Globally unique GCP project ID
billing_account = "01XXXX-XXXXXX-XXXXXX"
org_id          = ""                            # Leave empty if personal GCP account
```

> **Security**: `terraform.tfvars` is listed in `.gitignore`. Never commit it.

---

## Step 2 — Initialize Terraform

```bash
terraform init
```

---

## Step 3 — Plan Infrastructure

Review what Terraform will create before applying:

```bash
terraform plan
```

Verify the plan includes:
- 1 GCP Project (if org_id is set)
- 9 API enablements
- 1 Artifact Registry repository
- 2 Service accounts (runtime, github-actions)
- Workload Identity Federation pool + provider
- 1 Cloud Run service
- 4 Secret Manager secrets

---

## Step 4 — Apply Infrastructure

```bash
terraform apply
```

This will provision all resources. Note the outputs for the next step.

---

## Step 5 — Populate Secrets

After `terraform apply`, populate secret values using gcloud (never Terraform):

```bash
# Application secret key (generate a strong random value)
echo -n "YOUR_SECRET_KEY" | gcloud secrets versions add jbk-os-secret-key --data-file=-

# Gemini API key (when Gemini integration begins — OL-0005 or later)
# echo -n "YOUR_GEMINI_KEY" | gcloud secrets versions add gemini-api-key --data-file=-
```

---

## Step 6 — Configure GitHub Actions Secrets

After `terraform apply`, add the following secrets to the GitHub repository
(**Settings → Secrets and variables → Actions**):

| Secret Name | Value Source |
| :--- | :--- |
| `GCP_PROJECT_ID` | Your GCP project ID |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `terraform output workload_identity_provider` |
| `GCP_SERVICE_ACCOUNT` | `terraform output github_actions_service_account` |

---

## Step 7 — Deploy JBK-OS

Trigger the deployment by pushing a version tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

The GitHub Actions `deploy.yml` workflow will:
1. Authenticate to GCP via Workload Identity Federation (keyless)
2. Build the Docker image
3. Push to Artifact Registry
4. Deploy to Cloud Run

---

## Destroying Infrastructure

> **Warning**: Only destroy non-production environments. The production service has business continuity implications.

```bash
terraform destroy
```
