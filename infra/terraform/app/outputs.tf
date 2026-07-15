# ============================================================
# app/outputs.tf — JBK-OS Application Infrastructure
# ============================================================

output "cloud_run_url" {
  description = "Default Cloud Run service URL (HTTPS). This is the production endpoint."
  value       = google_cloud_run_v2_service.jbk_os.uri
}

output "container_image_uri" {
  description = "Full container image URI deployed to Cloud Run."
  value       = local.image_uri
}
