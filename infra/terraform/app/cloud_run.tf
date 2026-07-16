# ============================================================
# app/cloud_run.tf — JBK-OS Application Infrastructure
# Cloud Run service definition.
#
# The runtime service account and secret are resolved from
# foundation/ via data sources declared in main.tf —
# no direct resource references across module boundaries.
# ============================================================

locals {
  image_uri = "${var.region}-docker.pkg.dev/${var.project_id}/${var.registry_name}/${var.service_name}:${var.image_tag}"
}

resource "google_cloud_run_v2_service" "jbk_os" {
  project  = var.project_id
  name     = var.service_name
  location = var.region

  # ── Traffic Policy ────────────────────────────────────────
  # Route 100% of traffic to the latest revision by default.
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  template {
    # ── Identity ──────────────────────────────────────────
    # Resolved from foundation/ via data source in main.tf.
    service_account = data.google_service_account.runtime.email

    # ── Scaling ───────────────────────────────────────────
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    # ── Timeout ───────────────────────────────────────────
    timeout = "${var.request_timeout_seconds}s"

    # ── Labels ────────────────────────────────────────────
    labels = {
      product     = "jbk-os"
      environment = "production"
      managed-by  = "terraform"
      work-order  = "ol-0004"
    }

    containers {
      # ── Image ─────────────────────────────────────────
      image = local.image_uri
      name  = var.service_name

      # ── Resources ─────────────────────────────────────
      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
        # CPU allocated only during request processing (cost-efficient)
        cpu_idle = false
      }

      # ── Port ──────────────────────────────────────────
      ports {
        name           = "http1"
        container_port = var.container_port
      }

      # ── Environment Variables ──────────────────────────
      # Non-sensitive configuration only.
      env {
        name  = "JBK_ENVIRONMENT"
        value = var.app_environment
      }

      env {
        name  = "JBK_LOG_LEVEL"
        value = "INFO"
      }



      # ── Secret References ─────────────────────────────
      # Secrets are mounted as environment variables at runtime.
      # Values are retrieved from Secret Manager — never stored in Terraform state.
      env {
        name = "JBK_SECRET_KEY"
        value_source {
          secret_key_ref {
            # Resolved from foundation/ via data source in main.tf.
            secret  = data.google_secret_manager_secret.app_secret_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = data.google_secret_manager_secret.gemini_api_key.secret_id
            version = "latest"
          }
        }
      }


      # ── Health Checks ─────────────────────────────────
      # Startup probe: waits up to 30s for the container to boot.
      startup_probe {
        http_get {
          path = "/health"
          port = var.container_port
        }
        initial_delay_seconds = 5
        period_seconds        = 5
        failure_threshold     = 6
        timeout_seconds       = 3
      }

      # Liveness probe: restarts the container if it becomes unresponsive.
      liveness_probe {
        http_get {
          path = "/health"
          port = var.container_port
        }
        period_seconds    = 30
        failure_threshold = 3
        timeout_seconds   = 5
      }
    }
  }

  lifecycle {
    # Prevent accidental destruction of the production service.
    prevent_destroy = false
  }
}

# ── Public Access ─────────────────────────────────────────────
# Allows unauthenticated access to the Cloud Run service URL.

resource "google_cloud_run_v2_service_iam_member" "public_access" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.jbk_os.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
