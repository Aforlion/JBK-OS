# JBK-OS Foundation Infrastructure

## Purpose

This module provisions the **stable infrastructure layer** that changes rarely:
GCP APIs, Artifact Registry, IAM service accounts, Workload Identity Federation,
and Secret Manager secret slots.

**Run this module once** on first setup, and again only when the underlying
infrastructure configuration changes (e.g., adding a new API, rotating IAM bindings).
Do not re-run this on every application deployment.

## Resources Managed

| Resource | Description |
| :--- | :--- |
| `google_project_service` × 9 | Required GCP API enablements |
| `google_artifact_registry_repository` | Docker image registry |
| `google_service_account` × 2 | `jbk-os-runtime`, `github-actions` |
| `google_project_iam_member` × 5 | Least-privilege IAM bindings |
| `google_iam_workload_identity_pool` | WIF pool for GitHub Actions |
| `google_iam_workload_identity_pool_provider` | WIF OIDC provider |
| `google_secret_manager_secret` × 4 | Secret slots (values populated via gcloud) |

## Usage

### 1. Create `terraform.tfvars`

```hcl
# Never commit this file — it is gitignored.
project_id      = "jbk-os-prod-XXXXXX"
billing_account = "01XXXX-XXXXXX-XXXXXX"
# org_id        = ""   # Leave empty for personal GCP accounts
# region        = "europe-west2"  # London (default: europe-west1)
```

### 2. Initialize and Apply

```powershell
C:\JBK\bin\terraform.exe init
C:\JBK\bin\terraform.exe plan
C:\JBK\bin\terraform.exe apply
```

### 3. Capture Outputs

```powershell
C:\JBK\bin\terraform.exe output
```

Add the following to GitHub repository secrets (`Settings → Secrets → Actions`):

| GitHub Secret | Terraform Output |
| :--- | :--- |
| `GCP_PROJECT_ID` | `project_id` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `workload_identity_provider` |
| `GCP_SERVICE_ACCOUNT` | `github_actions_service_account` |

### 4. Populate Secret Values

```powershell
# Generate and store application secret key
$key = [System.Convert]::ToBase64String(
  [System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32)
)
echo $key | gcloud secrets versions add jbk-os-secret-key --data-file=-

# Store Gemini API key (OL-0005)
echo "YOUR_GEMINI_API_KEY" | gcloud secrets versions add gemini-api-key --data-file=-
```

## Next Step

Once foundation is applied and secrets are populated, proceed to `../app/`.
