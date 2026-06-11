# SLA Policy — Service Level Agreement

## Overview

SenAI is committed to platform reliability. This document defines uptime guarantees, incident
response timelines, credit entitlements, and root cause analysis (RCA) obligations. All Enterprise
customers are covered under this full SLA. Standard and Pro customers receive a limited SLA as
described below.

---

## Uptime Guarantee

| Plan       | Uptime SLA | Measurement Window |
|------------|-----------|-------------------|
| Starter    | No SLA    | —                 |
| Standard   | 99.5%     | Monthly           |
| Pro        | 99.9%     | Monthly           |
| Enterprise | 99.95%    | Monthly           |

**99.9% uptime** means a maximum of **43.8 minutes of unplanned downtime per month**.
**99.95% uptime** means a maximum of **21.9 minutes of unplanned downtime per month**.

Uptime is measured by SenAI's monitoring infrastructure using external probes from three geographic
regions. A service is considered "down" when two or more probes cannot reach the primary API endpoint
for three consecutive checks (60-second intervals).

Scheduled maintenance windows are excluded from uptime calculations (see Maintenance section below).

---

## Incident Severity Levels

### P0 — Critical (Production Down)
**Definition:** The platform is completely unavailable, or a core feature is non-functional for
more than 50% of users. Data loss or corruption is occurring or imminent.

**Examples:**
- API returning 5xx errors for all requests
- Authentication system down (no users can log in)
- Data ingestion pipeline stopped processing
- Production database unreachable
- Ransomware or security breach affecting customer data

**Response SLA:**
- Acknowledgement: within **15 minutes** of detection or report
- Initial update: within **30 minutes**
- Subsequent updates: every **30 minutes** until resolved
- Resolution target: within **4 hours**
- RCA delivery: within **24 hours** of resolution

### P1 — High (Major Feature Impaired)
**Definition:** A significant feature is degraded or unavailable, but the platform is partially
functional. No data loss occurring.

**Examples:**
- AI classification taking > 30 seconds per email
- Dashboard loading times exceeding 10 seconds
- Webhooks delayed by more than 15 minutes
- API rate limits incorrectly enforced

**Response SLA:**
- Acknowledgement: within **1 hour**
- Initial update: within **2 hours**
- Subsequent updates: every **4 hours**
- Resolution target: within **24 hours**
- RCA delivery: within **48 hours** of resolution (Enterprise only)

### P2 — Medium (Minor Degradation)
**Definition:** A non-critical feature is impaired. Workarounds exist.

**Response SLA:**
- Acknowledgement: within **4 hours** (business hours)
- Resolution target: within **5 business days**
- No RCA obligation

### P3 — Low (Cosmetic / Minor Bug)
**Definition:** UI issues, minor display errors, feature requests, documentation gaps.

**Response SLA:**
- Acknowledgement: within **2 business days**
- Resolution target: next scheduled release (typically monthly)

---

## SLA Credit Calculation

When SenAI fails to meet its uptime SLA in a given month, affected customers are entitled to
service credits applied to future invoices.

### Credit Formula

```
Credit (%) = (Actual Downtime Minutes − SLA Allowance Minutes) / Total Monthly Minutes × 100
```

### Credit Table

| Downtime Exceeding SLA | Credit Applied |
|------------------------|---------------|
| Up to 60 minutes over  | 10% of monthly fee |
| 60–240 minutes over    | 25% of monthly fee |
| 240–480 minutes over   | 50% of monthly fee |
| More than 480 minutes  | 100% of monthly fee |

### Example Calculation (Enterprise, 99.95% SLA)

- SLA allowance: 21.9 minutes/month
- Actual downtime in October: 69 minutes (the bob.jones@enterprise.net P0 incident)
- Downtime exceeding SLA: 69 − 21.9 = **47.1 minutes**
- This falls in the "up to 60 minutes" band
- Credit: **10% of monthly Enterprise fee**

### Credit Rules
- Credits are applied to the next invoice automatically — no manual claim required for Enterprise
- Standard and Pro customers must submit a credit request to billing@senai.io within 30 days
  of the incident
- Credits are non-transferable and have no cash value
- Credits cannot exceed 100% of the monthly fee for the affected month
- If a customer churns before the credit is applied, the credit is forfeited

---

## Root Cause Analysis (RCA) Obligations

For P0 incidents, SenAI commits to delivering a written RCA document.

### RCA Delivery Timeline
- **Enterprise:** RCA within **24 hours** of incident resolution
- **Pro:** RCA within **72 hours** upon request
- **Standard/Starter:** No RCA obligation

### RCA Contents (Minimum Requirements)
A valid RCA must contain:
1. **Incident summary** — what happened, when it started, when it was resolved
2. **Root cause** — the specific technical cause of the incident, not a general description
3. **Timeline** — minute-by-minute log of key events (detection, escalation, mitigation, resolution)
4. **Impact assessment** — number of affected customers, data affected, duration of impact per region
5. **Corrective actions** — specific engineering changes being made to prevent recurrence,
   with owner names and target completion dates
6. **Prevention measures** — systemic improvements (monitoring, alerting, architecture changes)

An RCA that states only "we experienced an outage and have resolved it" without root cause
and corrective actions does **not** meet the RCA obligation and the customer is entitled to
request a revised document within 5 business days.

---

## Escalation Path for SLA Disputes

If a customer believes the RCA is inadequate or the credit calculation is incorrect:

1. Email sla-disputes@senai.io with subject "SLA Dispute — [Account Name] — [Incident Date]"
2. Include the original RCA document and the specific sections you believe are incomplete
3. SenAI will respond within 3 business days with a revised RCA or formal written explanation
4. If unresolved, the dispute escalates to the VP of Engineering and VP of Customer Success
5. If still unresolved after 10 business days, the matter may be submitted to binding arbitration
   per the terms of the Master Services Agreement

Customers with legal teams involved in an SLA dispute should note: formal legal correspondence
should be directed to legal@senai.io and will be acknowledged within 24 hours.

---

## Scheduled Maintenance Windows

- Standard maintenance window: **Saturdays 02:00–04:00 UTC**
- Emergency maintenance: minimum **4 hours notice** via status page and email to account owner
- Major infrastructure upgrades: minimum **7 days notice** via email

Maintenance windows are excluded from uptime SLA calculations.

---

## API Rate Limit SLA

For Enterprise customers with a negotiated rate limit:
- SenAI guarantees the agreed rate limit is available **99.9% of the time**
- Rate limit should not be reduced without 14 days written notice to the customer
- If a rate limit is reduced without notice, the affected period is treated as a P1 incident
  for credit calculation purposes
- Enterprise customers requiring written confirmation of rate limit SLA before a board meeting
  or contract renewal should contact their account manager directly

---

## Status Page and Incident Communication

SenAI maintains a public status page at status.senai.io.

- All P0 and P1 incidents are published to the status page within 15 minutes of internal detection
- Customers can subscribe to SMS, email, or webhook notifications for incident updates
- Historical uptime data is available for the trailing 90 days
- Enterprise customers receive direct communication via their dedicated Slack channel (if configured)
  in addition to status page updates