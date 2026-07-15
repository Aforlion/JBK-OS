# JBK-OS Application Infrastructure

## Purpose

This module deploys the **JBK-OS application layer** — the Cloud Run service
and its public invoker IAM binding.

**Run this module on every deployment**, after:
1. `../foundation/` has been applied (IAM, APIs, Artifact Registry, secrets exist)
2. A container image has been pushed to Artifact Registry

This module has **no dependency on `terraform_remote_state`**. It resolves
foundation resources using `data` source lookups on their stable, known identifiers.

## Resources Managed

| Resource | Description |
| :--- | :--- |
| `google_cloud_run_v2_service` | JBK-OS production Cloud Run service |
| `google_cloud_run_v2_service_iam_member` | Public invoker binding (`allUsers`) |

## Usage

### 1. Create `terraform.tfvars`

```hcl
# Never commit this file — it is gitignored.
project_id = "jbk-os-prod-XXXXXX"   # Must match foundation/terraform.tfvars
# region   = "europe-west2"          # Must match foundation/ if overridden
# image_tag = "v1.0.0"               # Set by CI pipeline
```

### 2. Initialize and Apply

```powershell
C:\JBK\bin\terraform.exe init
C:\JBK\bin\terraform.exe plan
C:\JBK\bin\terraform.exe apply
```

### 3. Capture the Service URL

```powershell
C:\JBK\bin\terraform.exe output cloud_run_url
```

## CI/CD Integration

The GitHub Actions deploy workflow passes `image_tag` as a variable:

```yaml
- run: |
    terraform apply -auto-approve \
      -var="project_id=${{ vars.GCP_PROJECT_ID }}" \
      -var="image_tag=${{ github.sha }}"
```

## Prerequisite

Run `../foundation/` first if this is a new environment.
