# JBK-OS Business Readiness Plan

This document details the business preparations, domain configurations, HTTPS setup, and demo environments needed to support production rollout.

## 1. Domain Registration & Management

The canonical production URL for clients is registered as:
- **Production URL**: `https://os.jbk.tech`
- **Domain Registrar**: GoDaddy / Google Domains
- **DNS Hosting**: Cloudflare (for edge security, caching, and DNS resilience)

### DNS Records Table:
| Type | Host | Value | TTL | Notes |
| :--- | :--- | :--- | :--- | :--- |
| CNAME | `os` | `ghs.googlehosted.com.` | Automatic (300s) | Routes custom subdomain to Cloud Run |
| TXT | `@` | `google-site-verification=...` | 3600 | Verifies domain ownership on GCP |

## 2. HTTPS Configuration

HTTPS is enforced by default on Cloud Run.

1. **Custom Domain Mapping**:
   Configure custom domain mapping on GCP:
   ```bash
   gcloud beta run domain-mappings create \
     --service=jbk-os \
     --domain=os.jbk.tech \
     --region=europe-west1
   ```
2. **SSL/TLS Certificates**:
   - Google Cloud automatically provisions and rotates managed Let's Encrypt SSL/TLS certificates for the mapped custom domain.
   - Cloudflare is configured in "Full (strict)" encryption mode to ensure traffic is encrypted from the user's browser all the way to Cloud Run.

## 3. Demo Environment Setup

To support product demonstrations without affecting production systems, a separate Demo environment is configured.

- **Demo URL**: `https://demo.os.jbk.tech`
- **GCP Project**: `jbk-os-staging`
- **Profile Configuration**: Set `JBK_ENVIRONMENT = "DEMO"` in the environment variables.
- **Seeded Data**: Seeding is populated automatically with mock organizations, default workers, and pilot opportunities to allow salespeople to perform realistic workflows during client pitches.
