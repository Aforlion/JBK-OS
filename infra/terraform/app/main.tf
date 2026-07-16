# ============================================================
# app/main.tf — JBK-OS Application Infrastructure
# Cloud Run deployment layer.
#
# LIFECYCLE: Run this module on every application deployment,
# after foundation/ has been applied and a container image
# has been pushed to Artifact Registry.
#
# DEPENDENCIES: This module resolves foundation/ resources via
# data sources — no terraform_remote_state is required.
# ============================================================

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # ── Remote State ──────────────────────────────────────────
  # Uncomment and configure after provisioning a GCS bucket
  # for Terraform state storage.
  #
  # backend "gcs" {
  #   bucket = "jbk-os-terraform-state"
  #   prefix = "app"
  # }
}

# ── Provider ─────────────────────────────────────────────────

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Data Sources ─────────────────────────────────────────────
# Resolve foundation/ resources by their stable, known identifiers.
# These IDs are constants defined in foundation/iam.tf and
# foundation/secret_manager.tf — they never change.

data "google_service_account" "runtime" {
  account_id = "jbk-os-runtime"
  project    = var.project_id
}

data "google_secret_manager_secret" "app_secret_key" {
  secret_id = "jbk-os-secret-key"
  project   = var.project_id
}

data "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"
  project   = var.project_id
}

