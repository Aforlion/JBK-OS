# JBK-OS Incident Response Guide

This document establishes the incident response process, severity classifications, paging paths, escalation points, and post-mortem template for JBK-OS production environments.

## 1. Incident Severity Matrix

| Severity | Description | Target Response | Target Resolution |
| :--- | :--- | :--- | :--- |
| **P1 — Critical** | Service is completely down or critical business features (like approvals/estimation) are fully broken. | Immediate (<5 mins) | <2 hours |
| **P2 — High** | Performance is severely degraded, or secondary features are failing. | <15 mins | <6 hours |
| **P3 — Medium** | Non-critical service degradations, UI glitches, or isolated errors. | <2 hours | <24 hours |
| **P4 — Low** | General questions, dependency upgrades, or cosmetic adjustments. | Next business day | N/A |

## 2. Paging & Escalation Path

When a P1/P2 alert is triggered by Cloud Monitoring (e.g. Uptime Check failure or high error count):

1. **PagerDuty/Opsgenie Alert**: The automated paging system triggers an alert to the On-Call DevOps Engineer.
2. **Acknowledgment (On-Call)**:
   - On-call engineer must acknowledge the alert within 10 minutes.
   - If not acknowledged, the alert escalates to the **Startup CTO**.
3. **Escalation Path**:
   - **Level 1**: On-call DevOps Engineer
   - **Level 2**: Startup CTO (if Level 1 doesn't respond or resolve in 30 mins)
   - **Level 3**: CEO / JBK-Core (if Level 2 is unavailable or incident has direct commercial impact)

## 3. Communication Protocol

During an active P1 incident:
- Establish a dedicated incident chat channel (e.g., Slack `#incident-jbk-os`).
- Update internal status reports every 30 minutes.
- For external-facing outages, notify pilot clients within 1 hour of outage confirmation.

## 4. Post-Mortem Template

Every P1 or P2 incident requires a post-mortem report stored in `docs/incidents/` within 3 business days:

```markdown
# Incident Post-Mortem: [Incident ID / Description]

## Executive Summary
- **Date**: YYYY-MM-DD
- **Duration**: [e.g., 45 minutes]
- **Impact**: [e.g., Acme Corp could not access the system]
- **Lead Investigator**: [Name]

## Timeline
- **HH:MM UTC**: Incident triggered by alert.
- **HH:MM UTC**: On-call engineer acknowledged.
- **HH:MM UTC**: Mitigation applied.
- **HH:MM UTC**: Health checks verified successful.

## Root Cause Analysis
Explain why the incident occurred (use the 5 Whys framework).

## Action Items
- [ ] Task 1 (Owner, Deadline)
- [ ] Task 2 (Owner, Deadline)
```
