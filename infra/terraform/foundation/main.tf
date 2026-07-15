# ============================================================
# foundation/main.tf — JBK-OS Infrastructure
# GCP Provider, Project, API enablement, and Artifact Registry.
#
# LIFECYCLE: This module runs once, or when infrastructure
# changes (new APIs, registry config). It is NOT re-applied
# on every application deployment.
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
  #   prefix = "foundation"
  # }
}

# ── Provider ─────────────────────────────────────────────────

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Project ──────────────────────────────────────────────────
# Creates the GCP project only when org_id is provided.
# Personal Google accounts must create the project manually
# in the GCP Console, then pass the existing project_id.

resource "google_project" "jbk_os" {
  count = var.org_id != "" ? 1 : 0

  name            = var.project_name
  project_id      = var.project_id
  org_id          = var.org_id
  billing_account = var.billing_account

  labels = {
    environment = "production"
    product     = "jbk-os"
    managed-by  = "terraform"
    work-order  = "ol-0004"
  }
}

# ── API Enablement ───────────────────────────────────────────
# Explicitly enable only the APIs that JBK-OS requires.

locals {
  required_apis = [
    "run.googleapis.com",                    # Cloud Run
    "artifactregistry.googleapis.com",       # Container image storage
    "secretmanager.googleapis.com",          # Secret management
    "iam.googleapis.com",                    # Identity & Access Management
    "iamcredentials.googleapis.com",         # Workload Identity Federation
    "cloudresourcemanager.googleapis.com",   # Project management
    "logging.googleapis.com",               # Cloud Logging
    "monitoring.googleapis.com",            # Cloud Monitoring
    "clouderrorreporting.googleapis.com",    # Error Reporting
  ]
}

resource "google_project_service" "apis" {
  for_each = toset(local.required_apis)

  project                    = var.project_id
  service                    = each.value
  disable_dependent_services = false
  disable_on_destroy         = false
}

# ── Artifact Registry ────────────────────────────────────────
# Docker image repository for JBK-OS container images.

resource "google_artifact_registry_repository" "jbk_os" {
  depends_on = [google_project_service.apis]

  project       = var.project_id
  location      = var.region
  repository_id = var.registry_name
  description   = "JBK-OS container image registry"
  format        = "DOCKER"

  labels = {
    product    = "jbk-os"
    managed-by = "terraform"
  }
}
