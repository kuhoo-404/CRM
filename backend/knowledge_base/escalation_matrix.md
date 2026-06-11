# Escalation Matrix

## Overview

This document defines who handles what, at what urgency level, and what actions the agent must take before handing off. Every escalation must include a pre-filled brief. The agent must never escalate without context — a blank handoff is as bad as no escalation.

---

## Urgency Level Definitions

| Level | Definition | Max Auto-Response Time | Agent Action |
|---|---|---|---|
| **Critical** | Immediate business, legal, or security risk. Revenue loss, legal threat, data breach, ransomware. | 0 minutes — immediate escalation | Never auto-reply. Escalate + brief immediately. |
| **High** | Significant customer impact, churn risk, compliance deadline, VIP customer issue. | 15 minutes | Escalate with brief. Draft holding reply for human approval. |
| **Medium** | Standard support issue, feature request, billing question, general complaint. | 4 hours | Attempt auto-reply if confidence ≥ 0.70. Escalate if unresolved. |
| **Low** | General inquiries, newsletters, partnerships, cold outreach, spam-adjacent. | 24 hours or ignore | Auto-reply or ignore. No escalation needed. |

---

## Escalation Owners by Category

### 1. Legal Threats & Cease and Desist

**Owner:** Legal Team (legal@ourplatform.com) + VP of Operations  
**Deputy:** CEO for existential threats  
**Trigger examples:** Cease and desist letters (e.g., trademark disputes), formal legal correspondence, lawsuit threats.  
**Agent actions:**
- `flag_for_legal(email_id, "Legal threat / C&D")` immediately.
- Do NOT auto-reply. Do NOT acknowledge the legal claim.
- Create internal ticket assigned to Legal.
- Notify VP of Operations within 30 minutes.
- Safe holding reply (human must approve before sending): "Thank you for your correspondence. We have forwarded this to our legal team and will respond formally within [timeframe]."

### 2. Security Incidents — Ransomware / Extortion

**Owner:** CISO + Security Team (security@ourplatform.com)  
**Deputy:** CTO  
**Trigger examples:** msg_038 ("Send 2 BTC or we publish data"), data exfiltration claims, any payment demand.  
**Agent actions:**
- Route to security queue with Critical flag.
- `flag_for_legal(email_id, "Ransomware / extortion / data threat")`.
- Notify CISO within 15 minutes.
- **Absolute rule: NEVER auto-reply to the attacker.** Even an automated "we received your email" response is prohibited — it confirms the address is active and may encourage further contact.
- Do NOT forward the email to anyone outside the security team.
- Preserve original as evidence.
- Initiate Incident Response Plan — check if GDPR breach notification is required.
- If data exfiltration is credible, notify DPO within 72 hours (GDPR obligation).

### 3. Security Incidents — Suspicious Login / Account Compromise

**Owner:** Security Team (security@ourplatform.com)  
**Trigger examples:** msg_016 (login from Pyongyang IP using valid admin credentials).  
**Agent actions:**
- `escalate_to_human(email_id, "Suspicious login — admin account", "Critical")`.
- Force session invalidation for the affected account.
- Require password reset and MFA re-enrollment.
- Security team investigates within 1 hour.
- If admin account: assume breach, activate full IRP.

### 4. SLA Breach + Legal Escalation

**Owner:** VP of Customer Success + Legal (for legal component) + Account Executive  
**Trigger examples:** msg_060 (bob.jones@enterprise.net — RCA inadequate, legal team involved, renewal on hold).  
**Agent actions — this is the primary test case, follow exactly:**
1. `get_thread_history("bob.jones@enterprise.net")` — retrieve all 4+ prior emails.
2. `search_knowledge_base("SLA breach credit calculation P0")` — confirm credit entitlement.
3. `check_account_status("bob.jones@enterprise.net")` — confirm Enterprise tier, renewal status.
4. Recognise legal escalation in latest email.
5. `flag_for_legal(email_id, "SLA breach legal escalation — Enterprise renewal at risk")`.
6. `draft_reply(context, tone="empathetic", policy_refs=["sla_policy.md"])` — holding reply that: (a) acknowledges the inadequate RCA, (b) commits to a revised RCA, (c) cites the credit obligation per the SLA, (d) does NOT admit fault on the legal question.
7. `escalate_to_human(email_id, reason="Legal involvement + Enterprise renewal on hold", priority="Critical")` with full pre-filled brief including: thread summary, account value, credit owed, legal risk assessment.
- **Do NOT auto-send the drafted reply** — human must approve.

### 5. GDPR / Legal Data Requests

**Owner:** Data Protection Officer (dpo@ourplatform.com) + Legal  
**Trigger examples:** msg_052 (marcus.del@fintech-startup.co — formal GDPR Article 20 request).  
**Agent actions — mandatory sequence:**
1. Detect GDPR Article 20 language ("right to portability", "personal data export", "Article 20", "GDPR").
2. `flag_for_legal(email_id, "GDPR Article 20 data portability request")`.
3. `create_internal_ticket("GDPR Article 20 Request — marcus.del@fintech-startup.co", body, assignee="dpo-team")`.
4. Send auto-acknowledgement ONLY — citing the 30-day statutory window. Do NOT send a full response.
5. Log the request date — 30-day clock starts immediately.
- **Critical distinction:** This is a legal obligation, not a customer service request. Classifying it as a generic "Inquiry" is an error. It must be `category: Compliance`, `urgency: High`, `requires_human: true`.

### 6. Enterprise Compliance Deals (HIPAA / SOC 2)

**Owner:** Enterprise Sales + Compliance Team  
**Trigger examples:** msg_051 (eleanor.voss@healthcare-group.org — 200-seat HIPAA deal, board deadline).  
**Agent actions:**
- `escalate_to_human(email_id, reason="200-seat HIPAA deal, board deadline [date]", priority="Critical")`.
- `create_internal_ticket("HIPAA Compliance Package Request — healthcare-group.org", body, assignee="enterprise-sales")`.
- Include in brief: deal size, deadline, documents requested (BAA, HIPAA controls, SOC 2).
- Do NOT attempt to answer compliance questions from the knowledge base alone — compliance documentation must be reviewed and signed off by a human.
- BAA generation requires Legal sign-off; do not auto-generate.

### 7. RFP / Large Deal Compliance (e.g., BigCorp $2.4M)

**Owner:** VP of Sales + Security & Compliance Team + Legal  
**Trigger examples:** msg_029 (BigCorp $2.4M RFP), msg_030 (ISO 27001 / SOC 2 questionnaire).  
**Agent actions:**
- `escalate_to_human(email_id, reason="$2.4M RFP compliance questionnaire", priority="High")`.
- Notify VP of Sales immediately.
- Do not share SOC 2 report without confirmed NDA.
- Link all BigCorp emails (msg_029, msg_030, msg_047) together in the brief — they are part of the same $2.4M opportunity.

### 8. VIP Churn Threat / Reputation Crisis

**Owner:** Customer Success Manager + Head of Customer Success  
**Trigger examples:** msg_033 (karen.w@retail-co.com — 3 emails no reply, threatening G2/Capterra/Trustpilot reviews).  
**Agent actions:**
1. Detect churn pattern: 3+ emails with zero replies AND public review threat.
2. `scrape_public_sentiment("our platform name")` — check current G2/Trustpilot score.
3. `search_knowledge_base("churn retention refund exception")` — retrieve retention playbook.
4. `escalate_to_human(email_id, reason="Churn threat + public review threat — 0 replies in 4 days", priority="Critical")` with pre-filled brief including: account value, emails sent, days without reply, platforms threatened, current public sentiment score.
5. Suggest a retention offer from the refund policy (e.g., partial credit, account credit, extended trial).
6. Do NOT auto-reply without human approval — an ill-considered auto-reply to an angry customer in crisis is worse than no reply.
- **Time sensitivity:** Once a customer threatens public reviews and acts on it, damage is done. This is a 15-minute response window.

### 9. PR / Press Inquiries

**Owner:** Head of Marketing + CEO (for major pieces)  
**Trigger examples:** msg_055 (TechCrunch reporter, piece publishes Monday, quote needed by Thursday).  
**Agent actions:**
- `escalate_to_human(email_id, reason="Press inquiry — TechCrunch, deadline EOD Thursday", priority="High")`.
- Do NOT respond on behalf of the company — even a "no comment" must be approved.
- Note the publication, deadline, and topic in the escalation brief.
- If the inquiry involves a negative story (e.g., about a known incident), treat as Crisis, notify CEO.

### 10. Investor Inquiries

**Owner:** CEO / CFO  
**Trigger examples:** msg_019 (Series A interest from Tier 1 VC, $200M AUM fund).  
**Agent actions:**
- `escalate_to_human(email_id, reason="Series A investor inquiry — $200M AUM fund", priority="High")`.
- Do not disclose any financial information, metrics, or fundraising status.
- Draft a neutral acknowledgement for human approval: "Thank you for reaching out. We've passed your details to the right person and will be in touch shortly."

### 11. P0 Production Outages

**Owner:** On-call Engineer + Engineering Manager + VP Engineering  
**Trigger examples:** msg_002 (bob.jones@enterprise.net — production down, $10k/min loss).  
**Agent actions:**
- Detect P0 signals: "production down", "P0", "service unavailable", "losing $X/minute".
- `escalate_to_human(email_id, reason="P0 production outage — customer reporting $X/min revenue loss", priority="Critical")`.
- Notify on-call engineer within 5 minutes.
- Draft a holding reply: "We have received your P0 alert and our on-call team has been notified. We are investigating immediately and will update you within 15 minutes."
- Human must approve before sending.
- Post-incident: RCA must be delivered within 24 hours per SLA policy.

### 12. Silent Data Corruption / Data Loss Bugs

**Owner:** Engineering (P0 treatment) + VP Engineering  
**Trigger examples:** msg_054 (nadia.k@global-logistics.com — 50,000 records imported, 12,340 appear, success message shown, no error log, Q4 mission-critical).  
**Agent actions:**
- Treat data corruption bugs as P0 severity — data loss is always Critical.
- `create_internal_ticket("P0 Bug: Silent data loss on CSV bulk import — 37,660 records missing", body, assignee="engineering")`.
- `escalate_to_human(email_id, reason="Silent data corruption — 50k record import, 37k missing, no error surfaced", priority="Critical")`.
- Do NOT tell the customer to re-upload — the root cause is unknown and re-uploading may compound data integrity issues.
- Do NOT minimise the issue in the reply ("we'll look into it") — acknowledge the severity explicitly.

---

## Pre-filled Escalation Brief Template

Every call to `escalate_to_human()` must populate this brief:

```
ESCALATION BRIEF
================
Email ID: [email_id]
Sender: [sender_email] | [company]
Thread: [thread_id] | [thread_subject]
Urgency: [Critical/High/Medium]
Category: [category]

SITUATION SUMMARY:
[2-3 sentences describing what happened, in what sequence, and the current state]

ACCOUNT CONTEXT:
- Plan tier: [Starter/Standard/Pro/Enterprise]
- Account value: [if known]
- Churn risk: [Low/Medium/High/Critical]
- Prior interactions: [summary of thread history]

WHAT THE AGENT DID:
- [List of tool calls made and their outcomes]
- [RAG chunks retrieved and their relevance]

WHAT NEEDS HUMAN DECISION:
[Specific question or decision the human needs to make — be precise]

SUGGESTED DRAFT REPLY:
[If a draft was generated, include it here for approval]

TIME SENSITIVITY:
[Deadline, if any — board meeting date, statutory window, renewal date, etc.]
```

---

## Contacts Directory (Internal)

| Role | Name | Contact |
|---|---|---|
| Legal Team | — | legal@ourplatform.com |
| Data Protection Officer | — | dpo@ourplatform.com |
| CISO | — | security@ourplatform.com |
| Enterprise Sales | — | enterprise@ourplatform.com |
| Customer Success | — | cs@ourplatform.com |
| Marketing / PR | — | marketing@ourplatform.com |
| Engineering On-Call | — | oncall@ourplatform.com |
| CEO | — | Escalate via VP layer first |

---

## Do Not Auto-Reply Rules (Absolute)

The agent must NEVER auto-reply to the following, regardless of confidence score:

| Email Type | Reason |
|---|---|
| Spam / cold outreach / SEO pitches | Confirms live inbox, invites more spam |
| Ransomware / extortion demands | Confirms active address, may escalate attacker behaviour |
| Cease and desist / legal threats | Any reply may constitute legal admission |
| GDPR Article 20 requests | Requires DPO review; auto-ack template only |
| Press inquiries | Unauthorised company statements |
| Critical urgency emails (any category) | Always escalate, never auto-reply |
| Emails where `requires_human: true` and urgency is Critical | By definition |

---

## Sentiment Deterioration Escalation

If a sender has sent **3 or more consecutive emails with negative sentiment** and no replies:
- Automatically escalate to Customer Success with a deterioration alert.
- Include in brief: number of emails, days elapsed, topics raised, account value.
- This is a churn signal — treat as High urgency even if individual emails are Medium.
- Example: karen.w@retail-co.com sent 3 negative emails (Oct 2, Oct 6, Oct 10) with zero replies before threatening public reviews. This pattern should have triggered escalation at the second email.