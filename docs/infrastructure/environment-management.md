# Environment Management Guide — JBK-OS

**Work Order:** OL-0004
**Category:** Project-Memory
**Owner:** DevOps Engineer
**Status:** Active
**Created:** 2026-07-15
**Review Date:** 2027-07-15
**Related:** [cloud-architecture.md](cloud-architecture.md), [secret-management.md](secret-management.md)

---

## 1. Environment Strategy

JBK-OS operates two official environments. A staging environment will be introduced
when client deployments begin and there is a demonstrated operational need.

| Environment | Purpose | Infrastructure |
| :--- | :--- | :--- |
| **Development** | Local developer machines | No GCP resources — runs locally |
| **Production** | Live system on GCP | Cloud Run (`europe-west1`) |

---

## 2. Environment Profiles

Environment profiles are defined in `core/deployment_manager.py` (`_DEFAULT_PROFILES`).
The active profile is selected by the `JBK_ENVIRONMENT` environment variable.

| Setting | DEVELOPMENT | PRODUCTION |
| :--- | :--- | :--- |
| `logging` | `DEBUG` | `INFO` |
| `ai_provider` | `mock` | `openai` |
| `monitoring` | `False` | `True` |
| `security` | `relaxed` | `strict` |
| `hot_reload` | `True` | `False` |

---

## 3. Configuration Files

| File | Environment | Committed |
| :--- | :--- | :--- |
| `.env.example` | Reference only | ✅ Yes |
| `.env` | Development | ❌ Never |
| `config/environments/development.yaml` | Development | ✅ Yes |
| `config/environments/production.yaml` | Production | ✅ Yes (no secrets) |
| `infra/terraform/terraform.tfvars` | Operator | ❌ Never |

---

## 4. Development Setup

```bash
# 1. Copy the example environment file
cp .env.example .env

# 2. Edit .env with local values (never commit this file)
# Set JBK_ENVIRONMENT=DEVELOPMENT and fill in JBK_SECRET_KEY

# 3. Install dependencies
pip install -r requirements-dev.txt

# 4. Run JBK-OS locally
python main.py
```

The `JBK_ENVIRONMENT=DEVELOPMENT` profile automatically:
- Uses the mock AI provider (no API keys required)
- Sets DEBUG logging
- Enables hot reload
- Relaxes security for local development

---

## 5. Production Configuration

Production configuration is entirely managed through:

1. **Terraform** — non-sensitive env vars injected directly into Cloud Run template.
2. **Secret Manager** — sensitive values injected as env vars at container startup.
3. `config/environments/production.yaml` — application-layer configuration (no secrets).

**Configuration boundary**: Application behavior changes through configuration — never through code modification.

---

## 6. Configuration Boundaries

| Config Category | Development | Production |
| :--- | :--- | :--- |
| Non-sensitive env vars | `.env` file | Terraform Cloud Run template |
| Sensitive secrets | `.env` file (local only) | Secret Manager → Cloud Run env injection |
| App-layer config | `config/environments/development.yaml` | `config/environments/production.yaml` |
| Infrastructure config | N/A | `infra/terraform/*.tf` |

---

## 7. Adding a New Environment Variable

1. Add it to `.env.example` with description and safe example value.
2. Add it to `config/environments/development.yaml` under the appropriate section.
3. Add it to `config/environments/production.yaml` (use secret reference if sensitive).
4. If sensitive: add a Secret Manager declaration in `infra/terraform/secret_manager.tf`.
5. If injected into Cloud Run: add `env {}` block in `infra/terraform/cloud_run.tf`.
6. Document the new variable in this guide.
