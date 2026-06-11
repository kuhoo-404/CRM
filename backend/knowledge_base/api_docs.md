# API Documentation & Integration Guide

## Overview

This document covers API versions, rate limits, authentication, endpoint behaviour, breaking changes, and migration guidance. Support agents should reference this when handling integration questions, 403 errors, rate limit complaints, and v1 deprecation inquiries.

---

## API Versions

### v1 (Legacy — Deprecated)

- **Status:** Sunset on **December 31, 2023**. No new features. Security patches only.
- All v1 integrations **must** migrate to v2 before December 31, 2023 or service will be interrupted.
- v1 uses legacy API key authentication via the `Authorization: Bearer <key>` header.
- v1 responses are not paginated — full result sets are returned in a single response.
- v1 webhooks do not include signature validation.

### v2 (Current — Production)

- **Status:** Stable. All new features ship here only.
- Authentication requires **two headers** on every request:
  - `Authorization: Bearer <api_key>`
  - `X-Workspace-ID: <workspace_id>` ← **This is a common integration mistake. Missing this header returns 403 even with a valid API key.**
- All list endpoints in v2 return paginated responses (default page size: 100).
- Webhooks include HMAC-SHA256 signature validation via the `X-Webhook-Signature` header.
- Rate limits are enforced per workspace, not per API key.

---

## Authentication

### Common 403 Errors

| Cause | Fix |
|---|---|
| Missing `X-Workspace-ID` header | Add `X-Workspace-ID: <your_workspace_id>` to all v2 requests |
| API key scoped to v1 only | Generate a new v2-enabled key in Settings → API Keys |
| Key has insufficient permissions | Check key scopes; v2 endpoints require explicit scope grants |
| IP allowlist violation | Add your server IP in Settings → Security → API Access |

**Agent note:** When charlie@fastlane-startup.com reported a 403 on POST /v2/events, the root cause was the missing `X-Workspace-ID` header — a known friction point that is not clearly documented. This should be proactively mentioned when v2 403 issues are reported.

---

## Rate Limits by Plan Tier

| Plan | Rate Limit | Burst Allowance | Overage Behaviour |
|---|---|---|---|
| Starter | 100 req/min | 150 req/min for 30s | HTTP 429, retry after 60s |
| Standard | 1,000 req/min | 1,500 req/min for 30s | HTTP 429, retry after 60s |
| Pro | 2,000 req/min | 3,000 req/min for 30s | HTTP 429, retry after 60s |
| Enterprise | Custom (default 5,000 req/min) | Negotiable | Custom, can be configured |
| Enterprise (High-Volume) | Up to 10,000 req/min | By arrangement | Custom SLA |

### Rate Limit Response Headers

Every API response includes:
- `X-RateLimit-Limit`: Your current limit
- `X-RateLimit-Remaining`: Requests remaining in this window
- `X-RateLimit-Reset`: Unix timestamp when the window resets

### Requesting a Rate Limit Increase

- **Standard → Pro upgrade:** Self-serve via the billing portal.
- **Pro → Enterprise upgrade:** Contact sales for a custom quote.
- **Enterprise custom limit increase (e.g., 10,000 req/min):** Requires account review and written SLA confirmation. Sales must confirm in writing before the new limit is applied. A board meeting deadline or contractual requirement is a valid escalation trigger.

**Agent note:** When bob.jones@enterprise.net requested a 10,000 req/min limit and written confirmation before their board meeting on Oct 20, this requires escalation to the Sales/Enterprise team for written SLA confirmation. Do not confirm limits verbally or via support ticket — only the Account Executive can issue written confirmation.

---

## v1 to v2 Migration Guide

### Breaking Changes in v2

| Area | v1 Behaviour | v2 Behaviour |
|---|---|---|
| Authentication | `Authorization` header only | `Authorization` + `X-Workspace-ID` both required |
| Responses | Full result sets | Paginated (cursor-based, default 100 per page) |
| Webhooks | No signature validation | HMAC-SHA256 signature in `X-Webhook-Signature` |
| Event endpoint | `POST /v1/events` | `POST /v2/events` |
| Error format | Plain string messages | Structured JSON `{error_code, message, details}` |

### Migration Steps

1. Generate a v2-enabled API key in Settings → API Keys → Create New Key (select v2 scopes).
2. Add `X-Workspace-ID` header to all requests (find your workspace ID in Settings → General).
3. Update pagination handling — v2 returns `{data: [...], next_cursor: "..."}`.
4. Implement webhook signature validation using the shared secret from Settings → Webhooks.
5. Update error handling to parse the new structured JSON error format.
6. Test in the staging environment before switching production traffic.
7. Decommission v1 keys after successful migration.

### Migration Deadline

**December 31, 2023.** After this date, v1 endpoints will return HTTP 410 Gone. There will be no extension. Customers who have not migrated by November 30 should be proactively contacted by their account manager.

---

## Endpoint Reference — Key Endpoints

### POST /v2/events
Ingest workflow events. Requires `X-Workspace-ID`. Returns `{event_id, status, queued_at}`.

### GET /v2/contacts
List contacts. Paginated. Supports `?cursor=`, `?limit=` (max 500), `?filter[status]=`.

### POST /v2/webhooks
Register a webhook endpoint. Returns a shared secret for signature validation.

### GET /v2/usage
Returns current rate limit usage, plan tier, and billing cycle data. Useful for customers monitoring their own usage.

---

## Known Documentation Gaps

- The requirement for `X-Workspace-ID` on all v2 requests is **not prominently documented** in the public docs. This is a known issue causing recurring 403 support tickets. When customers hit this, acknowledge the documentation gap and escalate for a docs update.
- Webhook signature validation requirements for v2 are covered only in the migration guide, not in the main webhook docs page.

---

## Handling Integration Escalations

- **Launch-critical 403 issues (e.g., launch in 48 hours):** Treat as High urgency. Provide the fix immediately (check for missing `X-Workspace-ID`). Do not wait for standard SLA.
- **v1 deprecation migration help:** Offer a migration call with the technical onboarding team.
- **Rate limit 429 errors causing production impact:** Escalate to Enterprise Sales for emergency limit increase review.