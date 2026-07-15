# ============================================================
# cloud_run.tf — JBK-OS Infrastructure
# Cloud Run service definition for the JBK-OS production runtime.
# ============================================================

locals {
  image_uri = "${var.region}-docker.pkg.dev/${var.project_id}/${var.registry_name}/${var.service_name}:${var.image_tag}"
}

resource "google_cloud_run_v2_service" "jbk_os" {
  depends_on = [
    google_project_service.apis,
    google_service_account.runtime,
  ]

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
    # ── Identity ────────────────────────────────────────────
    service_account = google_service_account.runtime.email

    # ── Scaling ─────────────────────────────────────────────
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    # ── Timeout ─────────────────────────────────────────────
    timeout = "${var.request_timeout_seconds}s"

    # ── Labels ──────────────────────────────────────────────
    labels = {
      product     = "jbk-os"
      environment = "production"
      managed-by  = "terraform"
      work-order  = "ol-0004"
    }

    containers {
      # ── Image ─────────────────────────────────────────────
      image = local.image_uri
      name  = var.service_name

      # ── Resources ─────────────────────────────────────────
      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
        # CPU is allocated only during request processing (cost-efficient)
        cpu_idle = false
      }

      # ── Port ──────────────────────────────────────────────
      ports {
        name           = "http1"
        container_port = var.container_port
      }

      # ── Environment Variables ──────────────────────────────
      # Non-sensitive configuration only.
      # Sensitive values are injected via Secret Manager references below.

      env {
        name  = "JBK_ENVIRONMENT"
        value = var.app_environment
      }

      env {
        name  = "JBK_LOG_LEVEL"
        value = "INFO"
      }

      env {
        name  = "PORT"
        value = tostring(var.container_port)
      }

      # ── Secret References ─────────────────────────────────
      # Secrets are mounted as environment variables at runtime.
      # Values are retrieved from Secret Manager — never stored in Terraform state.

      env {
        name = "JBK_SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.app_secret_key.secret_id
            version = "latest"
          }
        }
      }

      # ── Health Checks ─────────────────────────────────────
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

# ── Public Access ────────────────────────────────────────────
# Allows unauthenticated access to the Cloud Run service URL.
# This can be restricted to specific service accounts in future.

resource "google_cloud_run_v2_service_iam_member" "public_access" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.jbk_os.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
