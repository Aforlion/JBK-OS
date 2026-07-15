# ============================================================
# foundation/iam.tf — JBK-OS Infrastructure
# Least-privilege service accounts and IAM bindings.
#
# Roles defined:
#   1. jbk-os-runtime     — Cloud Run container identity
#   2. github-actions      — CI/CD pipeline identity (WIF, keyless)
# ============================================================

# ── 1. Cloud Run Runtime Service Account ─────────────────────
# Minimal identity used by the JBK-OS container at runtime.

resource "google_service_account" "runtime" {
  project      = var.project_id
  account_id   = "jbk-os-runtime"
  display_name = "JBK-OS Cloud Run Runtime"
  description  = "Identity for the JBK-OS Cloud Run service. Least-privilege."
}

# Runtime: read secrets from Secret Manager
resource "google_project_iam_member" "runtime_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

# Runtime: write structured logs to Cloud Logging
resource "google_project_iam_member" "runtime_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

# Runtime: write metrics to Cloud Monitoring
resource "google_project_iam_member" "runtime_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

# Runtime: write error events to Cloud Error Reporting
resource "google_project_iam_member" "runtime_error_writer" {
  project = var.project_id
  role    = "roles/errorreporting.writer"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

# ── 2. GitHub Actions CI/CD Service Account ──────────────────
# Used exclusively by the GitHub Actions deployment workflow.
# Authenticates via Workload Identity Federation — NO stored keys.

resource "google_service_account" "github_actions" {
  project      = var.project_id
  account_id   = "github-actions"
  display_name = "JBK-OS GitHub Actions CI/CD"
  description  = "Identity for GitHub Actions deployment pipeline. Uses WIF — no keys."
}

# CI/CD: push images to Artifact Registry
resource "google_project_iam_member" "cicd_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# CI/CD: deploy to Cloud Run
resource "google_project_iam_member" "cicd_run_developer" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# CI/CD: act as the runtime service account during deployment
resource "google_service_account_iam_member" "cicd_act_as_runtime" {
  service_account_id = google_service_account.runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.github_actions.email}"
}

# ── 3. Workload Identity Federation Pool ─────────────────────
# Allows GitHub Actions to authenticate to GCP without stored keys.

resource "google_iam_workload_identity_pool" "github" {
  project                   = var.project_id
  workload_identity_pool_id = "github-actions-pool"
  display_name              = "GitHub Actions Pool"
  description               = "WIF pool for GitHub Actions — JBK-OS repository"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-actions-provider"
  display_name                       = "GitHub Actions Provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  attribute_condition = "assertion.repository == '${var.github_repo}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Bind the GitHub Actions service account to the WIF pool
resource "google_service_account_iam_member" "github_wif_binding" {
  service_account_id = google_service_account.github_actions.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}
