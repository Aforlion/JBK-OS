# JBK-OS Infrastructure — Terraform Operator Guide

## Architecture

The infrastructure is split into two independent root modules, each with its own
Terraform state and lifecycle:

```
infra/terraform/
├── foundation/   ← Run once, or when infrastructure changes
└── app/          ← Run on every application deployment
```

This separation eliminates the need for `-target` flags. Each module runs a clean,
unconditional `terraform apply`.

| Module | Manages | Runs When |
| :--- | :--- | :--- |
| `foundation/` | APIs, Artifact Registry, IAM, WIF, Secrets | First setup; infrastructure changes |
| `app/` | Cloud Run service | Every deployment |

The `app/` module resolves `foundation/` resources via **data sources** on their
stable, known identifiers — no `terraform_remote_state` is required.

---

## Prerequisites

- **Terraform** ≥ 1.6.0 — installed at `C:\JBK\bin\terraform.exe`
- **gcloud CLI** — authenticated via `gcloud auth application-default login`
- **GCP project** — created in the GCP Console (personal account) or via `org_id`
- **GCP Billing Account** — found in GCP Console → Billing

---

## Deployment Workflow

### Step 1 — Apply Foundation (once)

```powershell
cd infra\terraform\foundation
C:\JBK\bin\terraform.exe init
C:\JBK\bin\terraform.exe plan
C:\JBK\bin\terraform.exe apply
```

Capture outputs for GitHub Actions:

```powershell
C:\JBK\bin\terraform.exe output
```

Add to GitHub repository secrets (`Settings → Secrets → Actions`):

| Secret Name | Terraform Output |
| :--- | :--- |
| `GCP_PROJECT_ID` | `project_id` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `workload_identity_provider` |
| `GCP_SERVICE_ACCOUNT` | `github_actions_service_account` |

### Step 2 — Populate Secret Values

```powershell
# Generate and store application secret key
$key = [System.Convert]::ToBase64String(
  [System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32)
)
echo $key | gcloud secrets versions add jbk-os-secret-key --data-file=-

# Store Gemini API key
echo "YOUR_GEMINI_API_KEY" | gcloud secrets versions add gemini-api-key --data-file=-
```

### Step 3 — Build and Push Container Image

Push to `main` (or trigger CI manually). The GitHub Actions pipeline will build and
push the image to Artifact Registry. This must happen before Step 4.

### Step 4 — Apply App (every deployment)

```powershell
cd infra\terraform\app
C:\JBK\bin\terraform.exe init
C:\JBK\bin\terraform.exe plan
C:\JBK\bin\terraform.exe apply
```

---

## `terraform.tfvars` Files

Each module requires its own `terraform.tfvars`. Both are gitignored.

**`foundation/terraform.tfvars`** (minimum required):
```hcl
project_id      = "jbk-os-prod-XXXXXX"
billing_account = "01XXXX-XXXXXX-XXXXXX"
```

**`app/terraform.tfvars`** (minimum required):
```hcl
project_id = "jbk-os-prod-XXXXXX"
```

---

## Destroying Infrastructure

> **Warning**: Only destroy non-production environments.

```powershell
# Destroy app first (depends on foundation resources)
cd infra\terraform\app
C:\JBK\bin\terraform.exe destroy

# Then destroy foundation
cd infra\terraform\foundation
C:\JBK\bin\terraform.exe destroy
```
