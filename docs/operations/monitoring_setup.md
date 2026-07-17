# Production Monitoring Setup & Verification Guide

This document describes how to deploy, configure, and verify the production monitoring infrastructure for JBK-OS using Google Cloud Platform (GCP) and Terraform.

## 1. Monitoring Architecture

JBK-OS uses GCP Cloud Monitoring to track service health. The resources defined in `infra/terraform/app/monitoring.tf` configure:

- **Uptime Checks**: Periodically ping `/health` endpoint to verify status code and content matches `"status": "HEALTHY"`.
- **Latency Alerting**: Fires when 99th percentile HTTP latency exceeds 5 seconds.
- **Error Log Alerting**: Fires immediately if any error logs (`severity = "ERROR"`) are detected.
- **Unified Dashboard**: Displays real-time request counts, response latencies, CPU usage, and Memory utilization.

## 2. Deploying Monitoring Infrastructure

To deploy the monitoring resources, execute the following commands from the `infra/terraform/app` directory:

```bash
cd infra/terraform/app
terraform init
terraform plan -target=google_monitoring_dashboard.jbk_os_dashboard -target=google_monitoring_alert_policy.latency_alert -target=google_monitoring_alert_policy.error_alert -target=google_monitoring_uptime_check_config.uptime_check
terraform apply
```

## 3. Daily Backup Verification Workflow

Since JBK-OS V1 operates as a stateless platform, its backups correspond to:
1. **Infrastructure State**: Terraform state stored in Google Cloud Storage (`jbk-os-terraform-state`).
2. **Configuration Secrets**: Secret versions inside GCP Secret Manager.
3. **Release Codebase**: Release tags and source history in GitHub.

### Daily Verification Checklist:
- Check that GitHub Action build and deploy logs ran successfully.
- Run `terraform plan` in the `infra/terraform/app` and `foundation` folders to confirm state file alignment and identify any infrastructure drift.
- Verify `jbk-os-secret-key` is populated and matches active secret accessor count.
