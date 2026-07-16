# ============================================================
# app/variables.tf — JBK-OS Application Infrastructure
# Cloud Run deployment configuration.
# Set values in terraform.tfvars before running terraform apply.
# ============================================================

# ── Identity ─────────────────────────────────────────────────
# project_id and region must match the values used in foundation/.

variable "project_id" {
  description = "Google Cloud project ID. Must match the project used in foundation/."
  type        = string
}

variable "region" {
  description = "Primary GCP region. Must match the region used in foundation/."
  type        = string
  default     = "europe-west2"
}

# ── Application ──────────────────────────────────────────────

variable "service_name" {
  description = "Name of the Cloud Run service."
  type        = string
  default     = "jbk-os"
}

variable "registry_name" {
  description = "Artifact Registry repository name. Must match foundation/var.registry_name."
  type        = string
  default     = "jbk-os-registry"
}

variable "image_tag" {
  description = "Container image tag to deploy. Set by CI pipeline (e.g. git SHA or semver)."
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

# ── Scaling ──────────────────────────────────────────────────

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

# ── Resources ────────────────────────────────────────────────

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
