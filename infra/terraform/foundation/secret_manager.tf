# ============================================================
# foundation/secret_manager.tf — JBK-OS Infrastructure
# Secret declarations only. Operators populate secret values
# using `gcloud secrets versions add` — never Terraform.
#
# SECURITY RULES:
#   - Never store secret values in Terraform code.
#   - Never store secret values in terraform.tfstate.
#   - Rotate secrets using gcloud CLI per the Secret Management Guide.
# ============================================================

# ── Application Secret Key ───────────────────────────────────
# Used to sign internal session tokens and application payloads.

resource "google_secret_manager_secret" "app_secret_key" {
  depends_on = [google_project_service.apis]

  project   = var.project_id
  secret_id = "jbk-os-secret-key"

  labels = {
    product    = "jbk-os"
    managed-by = "terraform"
    category   = "application"
  }

  replication {
    auto {}
  }
}

# ── Gemini API Key ───────────────────────────────────────────
# Declared to establish naming standard and IAM path (OL-0005).

resource "google_secret_manager_secret" "gemini_api_key" {
  depends_on = [google_project_service.apis]

  project   = var.project_id
  secret_id = "gemini-api-key"

  labels = {
    product    = "jbk-os"
    managed-by = "terraform"
    category   = "ai-integration"
  }

  replication {
    auto {}
  }
}

# ── OAuth Client Secret ──────────────────────────────────────
# Reserved for future OAuth provider integration.

resource "google_secret_manager_secret" "oauth_client_secret" {
  depends_on = [google_project_service.apis]

  project   = var.project_id
  secret_id = "oauth-client-secret"

  labels = {
    product    = "jbk-os"
    managed-by = "terraform"
    category   = "oauth"
  }

  replication {
    auto {}
  }
}

# ── Database Credentials ─────────────────────────────────────
# Reserved for future database integration.

resource "google_secret_manager_secret" "database_url" {
  depends_on = [google_project_service.apis]

  project   = var.project_id
  secret_id = "database-url"

  labels = {
    product    = "jbk-os"
    managed-by = "terraform"
    category   = "database"
  }

  replication {
    auto {}
  }
}
