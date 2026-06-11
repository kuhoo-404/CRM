# Refund Policy and Churn Retention Playbook

## Overview

SenAI's refund policy is designed to be fair to customers while protecting the business from abuse.
This document covers refund eligibility, the exception process, credits versus refunds, and the
internal retention playbook used when a customer signals intent to churn.

---

## Standard Refund Policy

### Core Rule: No Refunds After 14 Days

SenAI does not issue monetary refunds for subscription fees after 14 days from the original
charge date. This applies to all plans (Starter, Standard, Pro, Enterprise).

**The 14-day window begins on the date of the charge**, not the date of the complaint or
the date the customer first notices an issue.

### What Is Refundable
- Charges made within the last 14 days if the customer has not meaningfully used the platform
  (fewer than 100 API calls in the billing period)
- Duplicate charges caused by a billing system error on SenAI's side
- Charges made after a cancellation was submitted and confirmed in writing
- Charges for features that were not delivered as described in the written contract (Enterprise only)

### What Is Not Refundable
- Subscription fees for months already consumed, regardless of satisfaction level
- Pro-rata amounts for unused days when a customer downgrades mid-cycle
- Charges older than 14 days from the date of the payment
- Charges where the service was available but the customer chose not to use it
- Setup or onboarding fees (non-refundable upon completion)

---

## Exception Process

In cases where standard policy does not apply, a refund exception may be granted at SenAI's
discretion. Exceptions are not guaranteed.

### Circumstances That May Qualify for an Exception
1. **Extended platform outage** — if SenAI experienced a P0 outage lasting more than 4 hours
   and the customer was materially impacted, a partial credit or refund may be considered
   in addition to the standard SLA credit
2. **Billing error on SenAI's side** — always corrected with a full refund of the erroneous amount
3. **First-time customer complaint** — for customers in their first billing period who are
   genuinely unsatisfied, a one-time goodwill credit of up to 50% of one month's fee may be offered
4. **Documented product failure** — if a specific feature was non-functional and the customer
   can demonstrate that it was a core reason for their purchase, a credit may be offered

### How to Request an Exception
- Email billing@senai.io with subject "Refund Exception Request — [Account Email]"
- Include: account email, charge date, amount, and reason for exception request
- Decisions are made within 5 business days by the billing team
- Appeals go to the VP of Customer Success

---

## Credits vs Refunds

SenAI strongly prefers issuing account credits over monetary refunds.

### Account Credits
- Applied immediately to the account balance
- Reduce the next invoice automatically
- No processing delay
- Available for all plan types

### Monetary Refunds
- Processed via original payment method only
- Take 5–10 business days to appear
- Only available if explicitly approved by billing team
- Require a signed refund authorization for amounts over $500

**Default resolution:** When an exception is approved, the default is a credit equal to the
disputed amount, not a monetary refund. If a customer explicitly requests a monetary refund,
the billing team may approve it at their discretion for amounts under 14 days old.

---

## Churn Retention Playbook

When a customer signals intent to cancel, churn, or is threatening negative reviews, the
following retention steps must be followed in order. This playbook is for internal use.

### Step 1 — Immediate Response (within 1 hour of churn signal)

A churn signal is defined as any of:
- Customer explicitly says "cancel", "cancelling", "leaving", "switching"
- Customer threatens public reviews (Trustpilot, G2, Capterra, Twitter)
- Three or more negative emails with no resolution in the thread
- Sentiment score drops below −0.6 for two consecutive emails
- Customer requests account deletion

**Action:** The email must be escalated to a human agent immediately. Do not send an automated
reply to a churn-risk email. Assign to Customer Success within 1 hour.

### Step 2 — Acknowledgement Call or Email (within 2 hours)

A human must personally reach out — not an automated template — within 2 hours.

The acknowledgement must:
- Name the specific issue the customer raised
- Apologize for the delay or problem without admitting legal liability
- Confirm a specific follow-up timeline
- Not make promises that cannot be kept

Example language (adapt as needed):
> "I'm [Name] from our Customer Success team. I've read through your messages and I understand
> how frustrating it is to not receive a timely response, especially when your business is
> being affected. I want to personally make this right. Can we jump on a 15-minute call today?"

### Step 3 — Root Cause and Resolution

Identify the actual issue:
- If it's a billing/refund issue → review eligibility, offer credit if within policy
- If it's a support response time issue → escalate to support manager for SLA review
- If it's a product functionality issue → escalate to engineering with priority tag
- If it's a public review threat → see Step 4

### Step 4 — Retention Offer (if Step 3 resolution is insufficient)

If the customer is still unhappy after Step 3, the Customer Success agent may offer one of
the following retention offers. Only one offer per customer per 12 months.

**Tier A — Minor dissatisfaction:**
- 1 month free at current plan (credit applied to next invoice)
- Or: Upgrade to next plan tier at current plan price for 3 months

**Tier B — Significant issue or long-standing customer (> 6 months):**
- 2 months free at current plan
- Or: Permanent 15% discount for the life of the account (requires VP of CS approval)
- Or: Full refund of the disputed month regardless of 14-day policy (requires VP of CS approval)

**Tier C — Enterprise or high-value account (> $10,000/year):**
- 3 months free at current plan
- Or: Custom SLA upgrade for 6 months
- Or: Full monetary refund of disputed amount
- Must be approved by VP of Customer Success and documented in CRM

### Step 5 — Public Review Threat Response

If the customer has explicitly threatened to post on G2, Capterra, Trustpilot, or social media:

1. **Do not ask them not to post reviews.** This escalates the situation and looks defensive.
2. Acknowledge the right to share their experience honestly.
3. Focus entirely on resolving the underlying issue.
4. Internally: trigger a web intelligence check of current review site scores so the response
   is informed by actual public perception.
5. If the review has already been posted: route to Marketing for review response protocol.
   Do not ask the customer to remove or change the review.

### Step 6 — Account Deletion Requests

If a customer requests account deletion:
- Process within 30 days (earlier if requested and no outstanding balance)
- GDPR deletion requests (Article 17) must be processed within 30 days regardless
- Send written confirmation when deletion is complete
- Retain anonymized transaction records for financial compliance (7 years)
- All personal data is deleted from live systems and purged from backups within 90 days

---

## Specific Scenarios

### Scenario: Customer requests refund after chatbot gave wrong information
If a customer was misled by SenAI's AI assistant (chatbot, support bot) and acted on incorrect
information:
- This qualifies for a refund exception review regardless of the 14-day rule
- The customer should not be told they have no recourse because of the chatbot's error
- Acknowledge the discrepancy between what the chatbot said and the actual policy
- Do not admit legal liability — use language like: "I understand you relied on information
  from our support assistant, and I want to make sure we address this fairly."
- Escalate to Customer Success manager with the chatbot conversation evidence attached
- If the chatbot claim was materially different from actual policy, approve a credit or refund
  as a goodwill gesture

### Scenario: Customer claims refund after SLA breach
If a customer wants a refund (not just a credit) citing an SLA breach:
- First apply the standard SLA credit formula (see sla_policy.md)
- If the credit does not satisfy the customer and they are threatening churn, escalate to Tier B
  or Tier C retention offer depending on account value
- Do not offer a monetary refund before exhausting credit options first
- For Enterprise accounts, a monetary refund for the affected month may be approved by VP of CS

### Scenario: Customer angry after no response for several days
If a customer has sent multiple emails with no reply and is escalating:
- The lack of response is a support failure — acknowledge this directly
- Do not cite policy timelines to justify the delay
- Offer an immediate Tier A retention offer as a goodwill gesture
- Escalate to support manager for SLA review internally