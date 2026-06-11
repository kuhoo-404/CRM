# Compliance & Security FAQ

## Overview

This document covers HIPAA, GDPR, SOC 2, ISO 27001, data residency, BAA agreements, and data portability requests. Support agents and the autonomous agent must reference this for any email involving compliance, legal obligations, regulatory requirements, or data handling inquiries. Mishandling compliance emails — especially GDPR requests — carries legal risk.

---

## HIPAA Compliance

### Do you offer HIPAA compliance?

Yes. We offer HIPAA-compliant configurations for customers in clinical, healthcare, and life sciences settings.

### Business Associate Agreements (BAA)

- BAAs are available on **Enterprise plans only**.
- A BAA must be signed before any Protected Health Information (PHI) is processed on our platform.
- To initiate a BAA, contact your Account Executive or email compliance@ourplatform.com.
- BAA signing typically takes **3–5 business days** with legal review.
- We can expedite to **24–48 hours** for time-sensitive deals (e.g., board deadlines).

### HIPAA Technical Controls

| Control | Status |
|---|---|
| Data encryption at rest | AES-256 ✓ |
| Data encryption in transit | TLS 1.2+ ✓ |
| Audit logging | Full access logs retained 7 years ✓ |
| Access controls | Role-based, MFA enforced ✓ |
| Breach notification | 60-day HIPAA notification window ✓ |
| Employee training | Annual HIPAA training for all staff ✓ |

### Data Hosting for Healthcare Customers

- US healthcare customers: data stored in AWS us-east-1 and us-west-2 (US-only residency available on Enterprise).
- EU healthcare customers: data stored in AWS eu-west-1 (Frankfurt available on Enterprise).
- No PHI is ever used for model training or analytics without explicit written consent.

### Agent note — eleanor.voss@healthcare-group.org

This customer (thread_eleanor_compliance) is a 200-seat healthcare deal with a board meeting deadline. When she requests compliance documentation by Thursday for a Friday board meeting:
- **Urgency: Critical** — do not treat as standard inquiry.
- Immediately escalate to Enterprise Sales and the Compliance team.
- Provide the BAA template, SOC 2 report, and HIPAA controls summary proactively.
- Document the deal value (~200 seats × Enterprise pricing) in the escalation brief.
- Missing this deadline = losing the deal. Flag for human review immediately.

---

## GDPR Compliance

### General GDPR Posture

- We are fully GDPR-compliant as a data processor.
- Data Processing Agreement (DPA) available upon request for EU customers.
- Data Protection Officer (DPO) contact: dpo@ourplatform.com.
- EU customer data is stored in AWS eu-west-1 by default. Frankfurt (eu-central-1) available on Enterprise.

### GDPR Article 20 — Right to Data Portability

**This is a formal legal obligation. It must never be handled as a generic inquiry.**

Under GDPR Article 20, any data subject (EU resident) may formally request a machine-readable export of all personal data held about them.

**Statutory obligations:**
- We must acknowledge the request **within 72 hours**.
- We must fulfil the request within **30 calendar days** of receipt.
- The export must be in a commonly used, machine-readable format (JSON or CSV).
- We cannot charge a fee for this export.
- Failure to comply can result in fines of up to **€20M or 4% of global annual turnover**.

**Required actions when a GDPR Article 20 request is received:**
1. Immediately flag as `category: Compliance`, `urgency: High`, `requires_human: true`.
2. Call `flag_for_legal(email_id, "GDPR Article 20 data portability request")`.
3. Create an internal compliance ticket assigned to the DPO team.
4. Send an auto-acknowledgement **only** — do NOT send a full response or make commitments beyond the statutory timeline.
5. The acknowledgement must cite the 30-day statutory window explicitly.
6. Do NOT classify this as a generic "Inquiry" — this is a legal obligation with penalties.

**Auto-acknowledgement template:**
> "We have received your formal GDPR Article 20 data portability request dated [date]. We are legally obligated to fulfil this request within 30 calendar days. Your request has been logged as reference [ticket_id] and assigned to our Data Protection team. You will receive your data export by [date + 30 days]. For questions, contact dpo@ourplatform.com."

### GDPR Article 17 — Right to Erasure (Right to Be Forgotten)

- Customers may request deletion of all personal data.
- We must fulfil within 30 days.
- Some data may be retained for legal/audit purposes (up to 7 years) — this must be communicated to the requestor.
- Route to DPO team immediately.

### GDPR Data Breach Notification

- We must notify the relevant supervisory authority within **72 hours** of becoming aware of a breach.
- Affected data subjects must be notified without undue delay if the breach poses a high risk to their rights.
- Our DPO coordinates all breach notifications.

---

## SOC 2 Type II

- We hold a current SOC 2 Type II certification.
- The report covers: Security, Availability, Confidentiality, and Processing Integrity trust service criteria.
- The report is available under NDA to enterprise prospects and customers.
- To request a copy: email compliance@ourplatform.com or ask your Account Executive.
- Latest report period: **October 2022 – September 2023**.

### For RFP Compliance Questionnaires (e.g., BigCorp)

When a prospect (such as procurement@bigcorp-global.com) requests SOC 2 reports, ISO 27001 compliance questionnaires, penetration test reports, or data residency documentation as part of an RFP:
- **Treat as High urgency** given deal value.
- Route to the Security & Compliance team immediately.
- Do not share the SOC 2 report without first obtaining a signed NDA.
- Estimated response time for completed compliance questionnaires: 5–7 business days.
- For $1M+ deals, escalate to VP of Sales to expedite.

---

## ISO 27001

- We are ISO 27001 certified (Information Security Management System).
- Certification body: BSI Group.
- Certificate number: available upon NDA request.
- Annual surveillance audits are conducted; recertification every 3 years.

---

## Data Residency Options

| Region | Available Plans | Data Location |
|---|---|---|
| United States (default) | All plans | AWS us-east-1, us-west-2 |
| European Union | Standard+ | AWS eu-west-1 (Ireland) |
| EU (Frankfurt) | Enterprise only | AWS eu-central-1 |
| APAC | Enterprise only | AWS ap-southeast-1 (Singapore) |
| Custom / on-premise | Enterprise (custom contract) | Customer-specified |

Data residency configuration requires an Enterprise plan and must be set at account creation. Migration between regions is possible but requires a 2-week migration window.

---

## Security Incident Handling

### Ransomware or Extortion Threats

**If an email threatens to publish stolen data, demands payment (e.g., BTC), or claims to have exfiltrated customer records:**

1. **CRITICAL urgency. Route to security queue immediately.**
2. Do NOT reply to the attacker under any circumstances — this confirms the email address is active.
3. Do NOT pay any ransom — company policy prohibits this and payment does not guarantee data safety.
4. Notify the CISO and Security team via the escalation matrix within 15 minutes.
5. Preserve the original email as evidence (do not delete).
6. Initiate the Incident Response Plan (IRP) — contact security@ourplatform.com.
7. Assess whether a GDPR breach notification obligation is triggered (if EU customer data may be affected).
8. Do NOT auto-reply, do NOT forward outside the security team, do NOT discuss externally.

### Suspicious Login Alerts

**If an alert is received about login from an unusual location or IP (especially a known threat actor geography):**

1. Immediately alert the Security team and CISO.
2. Force-invalidate all sessions for the affected account.
3. Require password reset and MFA re-enrollment.
4. Investigate whether credentials were legitimately compromised.
5. If the account is an admin account, assume worst-case breach until investigation concludes.
6. Escalation: security@ourplatform.com + CISO direct line within 30 minutes.

---

## Handling Chatbot Misinformation

If a customer reports that our AI chatbot provided incorrect information (e.g., told them they could get a prorated refund when our policy does not allow this):

1. Retrieve the actual policy via the RAG knowledge base.
2. Acknowledge the discrepancy empathetically — do not dismiss the customer's account.
3. Draft a reply that: (a) apologises for the confusion, (b) clearly states the correct policy, (c) does NOT admit legal liability or use language like "we were wrong" or "you are entitled to...".
4. Escalate to the product team to flag the chatbot error for retraining.
5. If the customer feels misled and demands compensation based on the chatbot's incorrect advice, escalate to human support — do not make unilateral concessions.
6. Suggested safe language: "We sincerely apologise for the confusion caused by our automated assistant. Our actual policy is [X]. While we cannot override our policy in this instance, we'd like to [offer credit/retention offer] as a gesture of goodwill."

---

## Summary — Compliance Urgency Routing

| Scenario | Urgency | Action |
|---|---|---|
| GDPR Article 20 data portability | High | flag_for_legal, DPO ticket, auto-ack only |
| GDPR Article 17 erasure request | High | DPO ticket, fulfil in 30 days |
| HIPAA BAA request (active deal) | Critical | Escalate to Enterprise Sales + Compliance |
| SOC 2 / ISO 27001 request (RFP) | High | NDA first, then compliance team |
| Ransomware / extortion email | Critical | Security queue, CISO, never auto-reply |
| Suspicious login alert | Critical | Security team, force session invalidation |
| Chatbot misinformation complaint | Medium | RAG policy lookup, empathetic reply, no liability admission |
| Data residency inquiry | Medium | Route to Sales/Enterprise |