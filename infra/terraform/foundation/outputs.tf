# ============================================================
# foundation/outputs.tf — JBK-OS Infrastructure
# Values exported after successful terraform apply.
# Use these to configure GitHub Actions secrets.
# The app/ module does NOT consume these via remote_state;
# it resolves foundation resources using data sources directly.
# ============================================================

output "artifact_registry_url" {
  description = "Full Artifact Registry repository URL for docker push/pull."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.registry_name}"
}

output "runtime_service_account" {
  description = "Email of the Cloud Run runtime service account."
  value       = google_service_account.runtime.email
}

output "github_actions_service_account" {
  description = "Email of the GitHub Actions CI/CD service account. Set as GCP_SERVICE_ACCOUNT in GitHub Actions secrets."
  value       = google_service_account.github_actions.email
}

output "workload_identity_provider" {
  description = "Full WIF provider resource name. Set as GCP_WORKLOAD_IDENTITY_PROVIDER in GitHub Actions secrets."
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "project_id" {
  description = "GCP project ID."
  value       = var.project_id
}

output "region" {
  description = "GCP region."
  value       = var.region
}
