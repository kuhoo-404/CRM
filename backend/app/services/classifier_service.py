"""
Classifier Service
==================
Orchestrates: retrieve RAG context → build prompt → call Claude → parse JSON → save to DB.
Switched from Gemini to Anthropic Claude API.

"""
import json
import logging
import re
import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from groq import APIError, Groq                    # ← only change to imports

from app.config import get_settings
from app.models.email import Email, EmailStatus, EmailCategory, UrgencyLevel, SentimentLabel
from app.models.action import Action, ActionType
from app.models.audit_log import AuditLog
from app.services.rag.retriever import retrieve_chunks, format_chunks_for_prompt
from app.services.sentiment_tracker import update_sentiment_trend

settings = get_settings()
logger = logging.getLogger(__name__)

# ── GROQ client — created once at module level ───────────────────────────
# Reads GROQ_API_KEY from environment automatically — no explicit key needed
_groq_client = None

def get_groq_client():
    global _groq_client

    if _groq_client is None:
        _groq_client = Groq(
            api_key=settings.GROQ_API_KEY
        )

    return _groq_client


# ── System prompt (sent as system role — cleaner than stuffing into user turn) ─

SYSTEM_PROMPT = """You are an AI triage agent for a B2B SaaS CRM system.
Classify the customer email using ONLY the retrieved policy context provided.
Do not rely on general knowledge about refunds, SLAs, or pricing — use the documents.

HARD RULES — these override everything else:
- Ransomware / BTC payment demands / data extortion threats → category=Legal, urgency=Critical, requires_human=true, suggested_reply=null
- GDPR Article 17 or Article 20 requests → category=Compliance, urgency=High, requires_human=true, suggested_reply=null, escalation_reason must mention "GDPR legal obligation — 30-day statutory window"
- Cease and desist / legal threats → urgency=Critical, requires_human=true, suggested_reply=null
- urgency=Critical → requires_human=true and suggested_reply=null always, no exceptions
- confidence < 0.70 → requires_human=true
- suggested_reply must cite the specific policy document (e.g. "Per our refund_policy.md...")
- When requires_human=true, set suggested_reply=null
- When requires_human=false, set escalation_reason=null

Respond with ONLY valid JSON. No markdown fences. No explanation. Just the JSON object."""


# ── Prompt template (user turn) ───────────────────────────────────────────────

CLASSIFICATION_PROMPT = """## Retrieved Policy Context
{rag_context}

## Full Thread History (oldest first — read before classifying)
{thread_history}

## Email to Classify
From: {sender}
Subject: {subject}

{body}

Classify this email. Return only JSON matching this schema:
{{
  "category": "Complaint|Inquiry|Bug Report|Feature Request|Compliance|Legal|Billing|Spam|Internal|Other",
  "sentiment": "Positive|Neutral|Negative|Mixed",
  "sentiment_score": <float -1.0 to 1.0>,
  "urgency": "Critical|High|Medium|Low",
  "requires_human": <true|false>,
  "escalation_reason": "<string if requires_human=true, else null>",
  "suggested_reply": "<string if requires_human=false AND urgency!=Critical, else null>",
  "confidence": <float 0.0 to 1.0>,
  "detected_entities": {{
    "order_ids": [],
    "ticket_ids": [],
    "monetary_amounts": [],
    "deadlines": [],
    "products_mentioned": []
  }},
  "rag_sources": ["<source_doc names used>"]
}}"""


# ── Helpers (unchanged from your original) ────────────────────────────────────

def _get_thread_history_text(email: Email, db: Session) -> str:
    from app.models.email import Email as EmailModel
    thread_emails = (
        db.query(EmailModel)
        .filter(EmailModel.thread_id == email.thread_id)
        .order_by(EmailModel.timestamp.asc())
        .all()
    )
    if not thread_emails:
        return "No prior thread history."
    lines = []
    for e in thread_emails:
        lines.append(
            f"[{e.timestamp or 'unknown time'}] From: {e.sender}\n"
            f"Subject: {e.subject or 'No subject'}\n"
            f"{e.body or 'No body'}"
        )
    return "\n\n---\n\n".join(lines)


def _parse_llm_response(raw: str) -> dict:
    """Extract JSON from LLM response — strips markdown fences if present."""
    raw = raw.strip()
    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```\s*", "", raw)
    return json.loads(raw)


def _map_category(value: str) -> EmailCategory:
    mapping = {
        "complaint": EmailCategory.complaint,
        "inquiry": EmailCategory.inquiry,
        "bug report": EmailCategory.bug_report,
        "feature request": EmailCategory.feature_request,
        "compliance": EmailCategory.compliance,
        "legal": EmailCategory.legal,
        "billing": EmailCategory.billing,
        "spam": EmailCategory.spam,
        "internal": EmailCategory.internal,
    }
    return mapping.get(value.lower(), EmailCategory.other)


def _map_urgency(value: str) -> UrgencyLevel:
    mapping = {
        "critical": UrgencyLevel.critical,
        "high": UrgencyLevel.high,
        "medium": UrgencyLevel.medium,
        "low": UrgencyLevel.low,
    }
    return mapping.get(value.lower(), UrgencyLevel.medium)


def _map_sentiment(value: str) -> SentimentLabel:
    mapping = {
        "positive": SentimentLabel.positive,
        "neutral": SentimentLabel.neutral,
        "negative": SentimentLabel.negative,
        "mixed": SentimentLabel.mixed,
    }
    return mapping.get(value.lower(), SentimentLabel.neutral)


def _enforce_rules(result: dict, email: Email) -> dict:
    """
    Hard post-parse enforcement — LLM output cannot override these.
    Mirrors the system prompt rules as a safety net.
    """
    # Security threat (set by heuristic filter on your Email model)
    if getattr(email, "is_security_threat", False):
        result["urgency"] = "Critical"
        result["requires_human"] = True
        result["suggested_reply"] = None
        if not result.get("escalation_reason"):
            result["escalation_reason"] = "Security threat detected — never auto-reply. Route to security team."

    # Critical always blocks auto-reply
    if result.get("urgency") == "Critical":
        result["requires_human"] = True
        result["suggested_reply"] = None

    # Low confidence → human
    if result.get("confidence", 1.0) < 0.70:
        result["requires_human"] = True
        if not result.get("escalation_reason"):
            result["escalation_reason"] = f"Low confidence ({result.get('confidence', 0):.2f}) — manual review required."

    # Consistency cleanup
    if result.get("requires_human"):
        result["suggested_reply"] = None
    else:
        result["escalation_reason"] = None

    # Ensure all entity keys exist
    entities = result.get("detected_entities", {})
    for key in ["order_ids", "ticket_ids", "monetary_amounts", "deadlines", "products_mentioned"]:
        entities.setdefault(key, [])
    result["detected_entities"] = entities

    return result


# ── Main classification function ──────────────────────────────────────────────

def classify_email(email_id: str, db: Session) -> Optional[dict]:
    """
    Full classification pipeline for one email.
    Retrieve RAG → build prompt → call Claude Haiku → parse → enforce rules → save to DB.
    Returns the classification result dict or None if skipped.
    """
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        logger.error(f"Email {email_id} not found")
        return None

    # Skip spam and internal — heuristic already handled them
    if email.is_spam or email.is_internal:
        logger.info(f"Skipping classification for spam/internal: {email_id}")
        return None

    # Mark as processing
    email.status = EmailStatus.processing
    db.commit()

    try:
        # ── 1. Build retrieval query ──────────────────────────────────────────
        retrieval_query = f"{email.subject or ''} {email.body or ''}".strip()[:500]

        # ── 2. Retrieve RAG context ───────────────────────────────────────────
        chunks = retrieve_chunks(retrieval_query)
        rag_context = format_chunks_for_prompt(chunks)

        # ── 3. Get full thread history ────────────────────────────────────────
        thread_history = _get_thread_history_text(email, db)

        # ── 4. Build user message ─────────────────────────────────────────────
        user_message = CLASSIFICATION_PROMPT.format(
            rag_context=rag_context,
            thread_history=thread_history,
            sender=email.sender,
            subject=email.subject or "No subject",
            body=email.body or "No body",
        )

        # ── 5. Call Claude Haiku ──────────────────────────────────────────────
        # Using synchronous client here to match your existing sync Session pattern.
        # If you move to async sessions later, swap to AsyncAnthropic + await.
        client = get_groq_client()

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0,
            max_tokens=1000,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )

        raw_text = response.choices[0].message.content

        # ── 6. Parse JSON response ────────────────────────────────────────────
        result = _parse_llm_response(raw_text)

        # ── 7. Enforce hard safety rules ──────────────────────────────────────
        result = _enforce_rules(result, email)

        # ── 8. Persist classification results to email record ─────────────────
        email.category = _map_category(result.get("category", "Other"))
        email.sentiment = _map_sentiment(result.get("sentiment", "Neutral"))
        email.sentiment_score = float(result.get("sentiment_score", 0.0))
        email.urgency = _map_urgency(result.get("urgency", "Medium"))
        email.requires_human = bool(result.get("requires_human", True))
        email.confidence = float(result.get("confidence", 0.5))
        email.escalation_reason = result.get("escalation_reason")
        email.suggested_reply = result.get("suggested_reply")
        email.raw_entities = result.get("detected_entities", {})
        email.status = (
            EmailStatus.escalated if email.requires_human else EmailStatus.replied
        )
        db.commit()

        # ── 9. Update sentiment trend ─────────────────────────────────────────
        update_sentiment_trend(email.sender, email.sentiment_score, db)

        # ── 10. Create action record with full reasoning log ──────────────────
        action = Action(
            id=str(uuid.uuid4()),
            email_id=email.id,
            action_type=ActionType.escalate if email.requires_human else ActionType.auto_reply,
            proposed_content=email.suggested_reply,
            agent_reasoning_log={
                "rag_chunks_used": [c["source_doc"] for c in chunks],
                "rag_sources": result.get("rag_sources", []),
                "confidence": email.confidence,
                "classification_raw": result,
                "model_used": "llama-3.3-70b-versatile",   # good to log which model ran
            },
            is_approved=not email.requires_human,
        )
        db.add(action)

        # ── 11. Write audit log ───────────────────────────────────────────────
        audit = AuditLog(
            id=str(uuid.uuid4()),
            entity_type="email",
            entity_id=email.id,
            action="classified",
            performed_by="agent",
            diff=result,
        )
        db.add(audit)
        db.commit()

        logger.info(
            f"Classified {email.message_id} → {email.category} | "
            f"sentiment={email.sentiment_score} | urgency={email.urgency} | "
            f"requires_human={email.requires_human} | confidence={email.confidence}"
        )

        return result

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed for {email_id}: {e}. Raw: {raw_text[:300]}")
        # Safe fallback — human review, don't crash the pipeline
        email.category = EmailCategory.other
        email.urgency = UrgencyLevel.medium
        email.requires_human = True
        email.confidence = 0.0
        email.escalation_reason = "Classification failed — LLM returned invalid JSON. Manual review required."
        email.status = EmailStatus.escalated
        db.commit()
        return None

        # except APIError as e:
        # logger.error(f"Groq API error for {email_id}: {str(e)}")
        # email.status = EmailStatus.received
        # db.commit()
        # raise

    except Exception as e:
        logger.error(f"Classification failed for {email_id}: {e}")
        email.status = EmailStatus.received
        db.commit()
        raise