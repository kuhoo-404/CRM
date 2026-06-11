# Pricing Policy

## Overview

SenAI offers four pricing tiers designed to serve individuals, growing teams, enterprise organizations,
and non-profit entities. All prices are in USD and billed monthly or annually. Annual billing provides
a 20% discount over the monthly equivalent.

---

## Pricing Tiers

### Starter Plan — $49/month
- Up to 3 users
- 5,000 API calls/month
- Basic email triage and classification
- Standard support (email only, 48-hour response SLA)
- Community knowledge base access
- No custom integrations

### Standard Plan — $149/month
- Up to 15 users
- 50,000 API calls/month
- Full AI classification + sentiment tracking
- Priority support (24-hour response SLA)
- Webhook integrations (Slack, Zapier)
- CSV data export
- 30-day data retention

### Pro Plan — $299/month
- Up to 50 users
- 200,000 API calls/month (approx. 1,000 req/min)
- Full AI agent with autonomous triage
- Priority support (12-hour response SLA)
- All integrations including REST API v2
- 90-day data retention
- Custom escalation rules
- Dedicated onboarding session

### Enterprise Plan — Custom pricing (starting at $999/month)
- Unlimited users
- Custom API rate limits (up to 10,000 req/min or more upon request)
- Full autonomous agent with custom workflows
- 24/7 dedicated support with named account manager
- SLA: 1-hour response for P0, 4-hour for P1
- 365-day data retention
- On-premise or private cloud deployment options
- Custom data residency (EU, US, APAC)
- HIPAA BAA available (see compliance_faq.md)
- SSO / SAML 2.0 integration
- Audit log export and SIEM integration
- Custom model fine-tuning (negotiated)
- White-label options available (negotiated separately)

---

## Non-Profit Discount Program

SenAI offers a **30% discount on the Standard plan** for registered non-profit organizations.

### Eligibility Requirements
- Must be a registered 501(c)(3) (US) or equivalent non-profit status in your jurisdiction
- Must provide proof of non-profit registration at sign-up
- Discount applies to the Standard plan only
- Non-profits requiring more than 15 users or advanced features should contact sales for
  custom Enterprise non-profit pricing

### How to Apply
1. Sign up for the Standard plan
2. Email billing@senai.io with subject "Non-Profit Discount Request"
3. Attach your IRS determination letter or equivalent documentation
4. The 30% discount will be applied to the next billing cycle within 5 business days

### Important Notes
- Non-profit discount cannot be combined with annual billing discount
- Non-profit discount does not apply to Pro or Enterprise plans unless separately negotiated
- Discount is reviewed annually — organizations must re-verify status each year

---

## Pro-Rata Billing

When a customer upgrades their plan mid-billing cycle, SenAI applies pro-rata billing.

### How Pro-Rata Works
- The customer is charged only for the remaining days in the current cycle at the new plan rate
- The unused portion of the old plan is credited to the account
- Net charge = (new plan daily rate × remaining days) − (old plan credit for remaining days)

### Example
- Customer is on Standard ($149/month), upgrades to Pro ($299/month) on day 15 of a 30-day cycle
- Remaining days: 15
- Standard credit: $149 × (15/30) = $74.50
- Pro charge: $299 × (15/30) = $149.50
- Net charge on upgrade: $149.50 − $74.50 = **$75.00**
- Next full cycle billed at $299/month

### Adding Seats Mid-Cycle
- Adding users/seats within the same plan tier is also pro-rated
- Seat additions are processed immediately
- Seat removals take effect at the next billing cycle — no refund for partial-month seat removal

---

## API Rate Limits by Tier

| Plan       | Requests/min | Burst Limit | Daily Cap    |
|------------|-------------|-------------|--------------|
| Starter    | 100         | 200         | 170/day      |
| Standard   | 1,000       | 2,000       | 50,000/month |
| Pro        | 1,000       | 3,000       | 200,000/month|
| Enterprise | 5,000+      | 10,000+     | Custom       |

Customers consistently exceeding their tier limits will receive an automated warning and an invitation
to discuss an upgrade. Rate limit increases beyond tier defaults require Enterprise plan or a custom
add-on, negotiated with the account team.

---

## Custom and Enterprise Pricing Process

For organizations with more than 50 users, specific compliance requirements, or revenue exceeding
$2M/year in software spend, contact sales@senai.io.

The enterprise pricing process:
1. Discovery call with sales engineer (30 minutes)
2. Technical assessment and requirements document
3. Custom proposal within 5 business days
4. Legal review of BAA/DPA if required
5. Contract execution
6. Dedicated onboarding (2–4 weeks depending on complexity)

For RFP responses, SenAI requires a minimum of 10 business days to prepare a comprehensive proposal.
RFP submissions should be directed to rfp@senai.io with all requirements and deadline clearly stated.

---

## White-Label and Reseller Agreements

SenAI offers white-label arrangements for consulting firms and resellers who wish to brand the
platform under their own identity.

- Minimum commitment: 80 end-client seats or $24,000/year in annual contract value
- Resellers set their own end-client pricing
- SenAI provides the platform, infrastructure, and model updates
- Reseller is responsible for first-line customer support to their clients
- SenAI provides second-line technical support to the reseller
- Interested parties should contact partnerships@senai.io

---

## Academic and Educational Licensing

SenAI offers educational pricing for accredited universities and academic institutions.

- Up to 200 students per semester: 70% discount on Standard plan
- More than 200 students: contact edu@senai.io for custom institutional pricing
- Educational licenses are for classroom and research use only — not for commercial projects
- Faculty or department heads must sign an educational use agreement
- License is per semester and must be renewed each term