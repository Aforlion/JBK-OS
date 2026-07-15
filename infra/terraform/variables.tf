# ============================================================
# variables.tf — JBK-OS Infrastructure
# All operator-configurable values.
# Set these in terraform.tfvars before running terraform apply.
# ============================================================

# ── Project ─────────────────────────────────────────────────

variable "project_id" {
  description = "Google Cloud project ID. Must be globally unique."
  type        = string
  # TODO: Replace with your provisioned project ID before running.
  # Example: "jbk-os-production-123456"
}

variable "project_name" {
  description = "Human-readable display name for the GCP project."
  type        = string
  default     = "JBK-OS Production"
}

variable "billing_account" {
  description = "GCP billing account ID to associate with the project."
  type        = string
  # TODO: Replace with your billing account ID.
  # Example: "01A2B3-C4D5E6-F7G8H9"
}

variable "org_id" {
  description = "Google Cloud organization ID (leave empty if using personal account)."
  type        = string
  default     = ""
}

# ── Region ──────────────────────────────────────────────────

variable "region" {
  description = "Primary GCP region for all resources."
  type        = string
  default     = "europe-west1"
}

# ── Application ─────────────────────────────────────────────

variable "service_name" {
  description = "Name of the Cloud Run service."
  type        = string
  default     = "jbk-os"
}

variable "image_tag" {
  description = "Container image tag to deploy to Cloud Run."
  type        = string
  default     = "latest"
}

variable "container_port" {
  description = "Port the JBK-OS container listens on."
  type        = number
  default     = 8080
}

variable "app_environment" {
  description = "Runtime environment label injected as JBK_ENVIRONMENT env var."
  type        = string
  default     = "PRODUCTION"
}

variable "min_instances" {
  description = "Minimum Cloud Run instances. Set to 1 for warm start in production."
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum Cloud Run instances. Caps horizontal scale to control cost."
  type        = number
  default     = 10
}

variable "request_timeout_seconds" {
  description = "Maximum request handling time before Cloud Run terminates the request."
  type        = number
  default     = 300
}

variable "cpu_limit" {
  description = "vCPU allocation per Cloud Run instance."
  type        = string
  default     = "1"
}

variable "memory_limit" {
  description = "Memory allocation per Cloud Run instance."
  type        = string
  default     = "512Mi"
}

# ── Artifact Registry ───────────────────────────────────────

variable "registry_name" {
  description = "Artifact Registry repository name for Docker images."
  type        = string
  default     = "jbk-os-registry"
}

# ── GitHub ──────────────────────────────────────────────────

variable "github_repo" {
  description = "GitHub repository in 'owner/repo' format for Workload Identity Federation."
  type        = string
  default     = "Aforlion/JBK-OS"
}
