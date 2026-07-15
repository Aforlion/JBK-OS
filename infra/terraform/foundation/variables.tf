# ============================================================
# foundation/variables.tf — JBK-OS Infrastructure
# Foundation-layer variables only. Cloud Run configuration
# belongs in app/variables.tf.
# Set values in terraform.tfvars before running terraform apply.
# ============================================================

# ── Project ──────────────────────────────────────────────────

variable "project_id" {
  description = "Google Cloud project ID. Must be globally unique."
  type        = string
  # Example: "jbk-os-prod-492851"
}

variable "project_name" {
  description = "Human-readable display name for the GCP project."
  type        = string
  default     = "JBK-OS Production"
}

variable "billing_account" {
  description = "GCP billing account ID. Found in GCP Console → Billing."
  type        = string
  # Format: "01A2B3-C4D5E6-F7G8H9"
}

variable "org_id" {
  description = "Google Cloud organization ID. Leave empty for personal accounts."
  type        = string
  default     = ""
}

# ── Region ───────────────────────────────────────────────────

variable "region" {
  description = "Primary GCP region for all resources."
  type        = string
  default     = "europe-west1"
}

# ── Artifact Registry ────────────────────────────────────────

variable "registry_name" {
  description = "Artifact Registry repository name for Docker images."
  type        = string
  default     = "jbk-os-registry"
}

# ── GitHub ───────────────────────────────────────────────────

variable "github_repo" {
  description = "GitHub repository in 'owner/repo' format for Workload Identity Federation."
  type        = string
  default     = "Aforlion/JBK-OS"
}
