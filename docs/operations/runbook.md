# JBK-OS Production Operator Runbook

This Operator Runbook outlines the daily operations, verification steps, and standard operating procedures (SOPs) for maintaining JBK-OS in the production environment.

## 1. Daily Health Audits

Operators must execute these commands daily to check system health:

### 1.1 Service Status Check
Ensure the Cloud Run service is running and serving traffic correctly:
```bash
gcloud run services describe jbk-os --region=europe-west1 --format="value(status.url)"
```

### 1.2 Uptime Checks & HTTP Status
```bash
curl -s -o /dev/null -w "%{http_code}" https://os.jbk.tech/health
# Expected Output: 200
```

### 1.3 Check Recent Errors
Query the last 24 hours of error logs in Cloud Logging:
```bash
gcloud logging read 'resource.type="cloud_run_revision" AND severity>=ERROR' --limit=50
```

## 2. Daily Backup & Drift Verification

Since JBK-OS v1.0.0 is a stateless engine, backup verification comprises:
1. **GitHub Repository**: Ensure the codebase is securely backed up and recent release tags are pushed.
2. **Secret Manager Integrity**: Verify all required production secrets exist.
   ```bash
   gcloud secrets versions list jbk-os-secret-key
   gcloud secrets versions list gemini-api-key
   ```
3. **Terraform Configuration Drift**: Check if active cloud resources match configuration.
   ```bash
   cd infra/terraform/app
   terraform plan
   ```
   *Expected Output: "No changes. Your infrastructure matches the configuration."*

## 3. Maintenance Workflows

### 3.1 Scaling Resources
Adjust scaling limits when load spikes:
- Modify `min_instances` and `max_instances` in `infra/terraform/app/terraform.tfvars`.
- Apply changes using:
  ```bash
  terraform apply -target=google_cloud_run_v2_service.jbk_os
  ```

### 3.2 Access Token Expirations
Review service account credential expirations and rotate test secrets every 90 days.

---

## 4. Operational Telemetry Auditing

Operators can query real-time operational metrics for JBK-OS using the built-in HTTP telemetry endpoint:

### 4.1 Querying Real-Time Metrics
```bash
curl -s https://os.jbk.tech/api/dashboard/metrics | python -m json.tool
```

### 4.2 Telemetry Output Schema
The endpoint returns the following metrics:
- `average_response_time_ms`: Average execution latency of web requests.
- `ai_latency_ms`: Average response latency for Gemini and fallback AI calls.
- `requests_per_day`: 24-hour total requests volume.
- `token_usage`: Total tokens consumed.
- `estimated_ai_cost`: Total estimated cost based on token usage.
- `error_rate_pct`: Percentage of failed web server requests.

