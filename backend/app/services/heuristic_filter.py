"""
Heuristic Pre-filter
====================
Runs synchronously on every ingest BEFORE any LLM call.
Must stay under 10ms — pure string matching, no I/O, no ML.

Returns a HeuristicResult dataclass that the ingest service
uses to set initial flags and priority score on the Email model.
"""
from dataclasses import dataclass, field
from typing import List
import re


# ── Keyword lists ─────────────────────────────────────────────────────────────

SPAM_KEYWORDS = [
    "boost your seo", "front page of google", "limited offer", "click here to claim",
    "collab opportunity", "dm me", "pure win-win", "quick question for the right person",
    "software purchasing decisions", "prince adewale", "inheritance", "processing fee",
    "bank account details", "50,000,000", "wealth-transfer", "nigerian",
    "marketing-guru", "spammy-outreach", "coldoutreach",
]

SPAM_DOMAINS = [
    "marketing-guru.io", "spammy-outreach.com", "coldoutreach.com",
    "wealth-transfer.com", "review-scraper.io",
]

URGENCY_KEYWORDS = [
    "urgent", "p0", "production down", "not responding", "losing $",
    "legal", "cease and desist", "ransomware", "lawyer", "lawsuit",
    "legal action", "formal correspondence", "legal team", "legal review",
    "losing revenue", "losing approximately", "immediately", "critical",
    "escalation", "sla breach", "breach", "rca", "root cause",
    "cancel", "churn", "public review", "trustpilot", "g2 review",
    "negative review", "board meeting", "deadline", "data portability",
    "gdpr", "article 20", "hipaa", "compliance audit",
]

SECURITY_KEYWORDS = [
    "ransomware", "send 2 btc", "send bitcoin", "exfiltrated",
    "we have your data", "publish data", "dark web", "pay now",
    "suspicious login", "unknown location", "login attempt",
    "credentials", "data breach", "hacked", "malware",
    "anon-collective", "alert-system",
]

LEGAL_KEYWORDS = [
    "cease and desist", "registered trademark", "legal action",
    "formal correspondence", "legal team is now involved",
    "our lawyers", "lawsuit", "litigation",
]

INTERNAL_DOMAINS = ["@internal.com", "@mycompany.com"]

NEVER_AUTO_REPLY_TRIGGERS = [
    # Any of these in the result means the agent must never auto-reply
    "ransomware", "send 2 btc", "exfiltrated", "cease and desist",
    "legal action", "formal correspondence", "legal team is now involved",
    "gdpr article 20", "right to portability",
]


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class HeuristicResult:
    is_spam: bool = False
    is_internal: bool = False
    is_security_threat: bool = False
    is_legal_threat: bool = False
    is_never_auto_reply: bool = False
    urgency_hint: str = "Low"          # "Critical" | "High" | "Medium" | "Low"
    priority_score: float = 0.0        # 0–100
    triggered_keywords: List[str] = field(default_factory=list)
    routing_queue: str = "normal"      # "spam" | "security" | "internal" | "legal" | "normal"


# ── Main filter function ──────────────────────────────────────────────────────

def run_heuristic_filter(
    sender: str,
    subject: str,
    body: str,
) -> HeuristicResult:
    """
    Pure function — no DB, no I/O.
    Call this immediately on ingest before queuing for LLM.
    """
    result = HeuristicResult()

    # Normalise text for matching
    text = f"{subject or ''} {body or ''}".lower()
    sender_lower = (sender or "").lower()

    # ── 1. Internal email detection ──────────────────────────────────────────
    for domain in INTERNAL_DOMAINS:
        if sender_lower.endswith(domain):
            result.is_internal = True
            result.routing_queue = "internal"
            result.priority_score = 10.0
            return result  # internal emails: short-circuit, no further checks needed

    # ── 2. Spam detection ────────────────────────────────────────────────────
    spam_hits = []
    for domain in SPAM_DOMAINS:
        if domain in sender_lower:
            spam_hits.append(f"sender_domain:{domain}")

    for kw in SPAM_KEYWORDS:
        if kw in text:
            spam_hits.append(kw)

    if spam_hits:
        result.is_spam = True
        result.is_never_auto_reply = True
        result.routing_queue = "spam"
        result.triggered_keywords = spam_hits
        result.priority_score = 0.0
        result.urgency_hint = "Low"
        return result  # spam: short-circuit

    # ── 3. Security threat detection ─────────────────────────────────────────
    security_hits = []
    for kw in SECURITY_KEYWORDS:
        if kw in text or kw in sender_lower:
            security_hits.append(kw)

    if security_hits:
        result.is_security_threat = True
        result.is_never_auto_reply = True
        result.routing_queue = "security"
        result.triggered_keywords = security_hits
        result.urgency_hint = "Critical"
        result.priority_score = 100.0
        return result  # security threats: short-circuit, highest priority

    # ── 4. Legal threat detection ─────────────────────────────────────────────
    legal_hits = []
    for kw in LEGAL_KEYWORDS:
        if kw in text:
            legal_hits.append(kw)

    if legal_hits:
        result.is_legal_threat = True
        result.is_never_auto_reply = True
        result.routing_queue = "legal"
        result.triggered_keywords = legal_hits
        result.urgency_hint = "Critical"
        result.priority_score = 95.0

    # ── 5. Never-auto-reply triggers ─────────────────────────────────────────
    for trigger in NEVER_AUTO_REPLY_TRIGGERS:
        if trigger in text:
            result.is_never_auto_reply = True
            if trigger not in result.triggered_keywords:
                result.triggered_keywords.append(trigger)

    # ── 6. Urgency keyword scoring ───────────────────────────────────────────
    urgency_hits = []
    for kw in URGENCY_KEYWORDS:
        if kw in text:
            urgency_hits.append(kw)

    urgency_score = len(urgency_hits) * 10.0

    if not result.is_legal_threat:  # don't downgrade legal threats
        if urgency_score >= 30:
            result.urgency_hint = "Critical"
            result.priority_score = max(result.priority_score, 90.0)
        elif urgency_score >= 20:
            result.urgency_hint = "High"
            result.priority_score = max(result.priority_score, 70.0)
        elif urgency_score >= 10:
            result.urgency_hint = "Medium"
            result.priority_score = max(result.priority_score, 50.0)
        else:
            result.urgency_hint = "Low"
            result.priority_score = max(result.priority_score, 20.0)

    result.triggered_keywords += urgency_hits

    # ── 7. De-duplicate triggered keywords ───────────────────────────────────
    result.triggered_keywords = list(dict.fromkeys(result.triggered_keywords))

    return result


# ── Convenience predicates ────────────────────────────────────────────────────

def is_auto_newsletter(sender: str, subject: str) -> bool:
    """Detect automated newsletters and system notifications — route to ignored."""
    sender_lower = (sender or "").lower()
    subject_lower = (subject or "").lower()
    auto_patterns = [
        "noreply@", "no-reply@", "newsletter@", "notifications@",
        "automated@", "donotreply@", "billing@saas-",
        "renewals@", "support@software.com", "noreply@github.com",
    ]
    for pattern in auto_patterns:
        if pattern in sender_lower:
            return True
    auto_subjects = ["auto-reply", "ticket #", "build failed", "subscription renews"]
    for pattern in auto_subjects:
        if pattern in subject_lower:
            return True
    return False