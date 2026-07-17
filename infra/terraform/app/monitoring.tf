# ============================================================
# app/monitoring.tf — JBK-OS Operations Monitoring
# Provisions dashboard, alert policies, and uptime checks.
# ============================================================

# ── Cloud Run Uptime Check ────────────────────────────────────
resource "google_monitoring_uptime_check_config" "uptime_check" {
  display_name = "jbk-os-uptime-check"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path         = "/health"
    port         = "443"
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = replace(replace(google_cloud_run_v2_service.jbk_os.uri, "https://", ""), "/", "")
    }
  }

  content_matchers {
    content = "\"status\": \"HEALTHY\""
    matcher = "CONTAINS_STRING"
  }
}

# ── Latency Alert Policy ──────────────────────────────────────
resource "google_monitoring_alert_policy" "latency_alert" {
  display_name = "JBK-OS Latency Alert"
  combiner     = "OR"
  conditions {
    display_name = "Request Latency > 5s"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND metric.type = \"run.googleapis.com/request_latencies\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5000.0 # 5000 milliseconds
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_PERCENTILE_99"
        cross_series_reducer = "REDUCE_NONE"
      }
    }
  }

  notification_channels = []
}

# ── Error Log Alert Policy ────────────────────────────────────
resource "google_monitoring_alert_policy" "error_alert" {
  display_name = "JBK-OS Error Log Alert"
  combiner     = "OR"
  conditions {
    display_name = "Error Logs count > 0"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.service_name}\" AND metric.type = \"logging.googleapis.com/log_entry_count\" AND metric.labels.severity = \"ERROR\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  notification_channels = []
}

# ── Cloud Monitoring Dashboard ───────────────────────────────
resource "google_monitoring_dashboard" "jbk_os_dashboard" {
  dashboard_json = <<EOF
{
  "displayName": "JBK-OS Production Dashboard",
  "gridLayout": {
    "columns": "2",
    "widgets": [
      {
        "title": "Request Count",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.service_name}\" AND metric.type=\"run.googleapis.com/request_count\"",
                "aggregation": {
                  "alignmentPeriod": "60s",
                  "perSeriesAligner": "ALIGN_RATE"
                }
              }
            },
            "plotType": "LINE"
          }]
        }
      },
      {
        "title": "99th Percentile Latency (ms)",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.service_name}\" AND metric.type=\"run.googleapis.com/request_latencies\"",
                "aggregation": {
                  "alignmentPeriod": "60s",
                  "perSeriesAligner": "ALIGN_PERCENTILE_99"
                }
              }
            },
            "plotType": "LINE"
          }]
        }
      },
      {
        "title": "Container CPU Utilization",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.service_name}\" AND metric.type=\"run.googleapis.com/container/cpu/utilizations\"",
                "aggregation": {
                  "alignmentPeriod": "60s",
                  "perSeriesAligner": "ALIGN_MEAN"
                }
              }
            },
            "plotType": "LINE"
          }]
        }
      },
      {
        "title": "Container Memory Utilization",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.service_name}\" AND metric.type=\"run.googleapis.com/container/memory/utilizations\"",
                "aggregation": {
                  "alignmentPeriod": "60s",
                  "perSeriesAligner": "ALIGN_MEAN"
                }
              }
            },
            "plotType": "LINE"
          }]
        }
      }
    ]
  }
}
EOF
}
