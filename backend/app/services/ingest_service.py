"""
Ingest Service
==============
Handles the full lifecycle of a new email arriving:
  1. Schema validation (done by Pydantic in the router)
  2. Deduplication — idempotent by message_id
  3. Heuristic filter — spam/security/urgency flags
  4. Contact upsert
  5. Thread link or create
  6. Persist Email to DB
  7. Return job_id for async status polling
"""
import uuid
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session
from dateutil import parser as dateparser

from app.models import Contact, Thread, Email, AuditLog
from app.models.email import EmailStatus
from app.models.contact import ContactStatus
from app.models.thread import ThreadStatus
from app.schemas.email import EmailIngestRequest
from app.services.heuristic_filter import run_heuristic_filter, is_auto_newsletter
from app.utils.exceptions import DuplicateEmailError

logger = logging.getLogger(__name__)


# ── Ingest a single email ─────────────────────────────────────────────────────

def ingest_email(payload: EmailIngestRequest, db: Session) -> dict:
    """
    Ingest one email. Idempotent — re-sending the same message_id
    returns the existing record without creating a duplicate.

    Returns: {"job_id": str, "message_id": str, "status": str, "duplicate": bool}
    """

    # ── 1. Deduplication ─────────────────────────────────────────────────────
    existing = db.query(Email).filter(Email.message_id == payload.message_id).first()
    if existing:
        logger.info(f"Duplicate message_id received: {payload.message_id} — skipping")
        return {
            "job_id": existing.id,
            "message_id": payload.message_id,
            "status": existing.status.value,
            "duplicate": True,
        }

    # ── 2. Heuristic filter ───────────────────────────────────────────────────
    heuristic = run_heuristic_filter(
        sender=payload.sender,
        subject=payload.subject or "",
        body=payload.body or "",
    )

    auto_newsletter = is_auto_newsletter(payload.sender, payload.subject or "")

    # ── 3. Parse timestamp ────────────────────────────────────────────────────
    email_ts: Optional[datetime] = None
    if payload.timestamp:
        try:
            email_ts = dateparser.parse(payload.timestamp)
            if email_ts and email_ts.tzinfo is None:
                email_ts = email_ts.replace(tzinfo=timezone.utc)
        except Exception:
            logger.warning(f"Could not parse timestamp '{payload.timestamp}' for {payload.message_id}")

    # ── 4. Contact upsert ─────────────────────────────────────────────────────
    contact = db.query(Contact).filter(Contact.email == payload.sender).first()
    if not contact:
        contact = Contact(
            id=str(uuid.uuid4()),
            email=payload.sender,
            status=ContactStatus.blocked if heuristic.is_spam else ContactStatus.active,
        )
        db.add(contact)
        logger.info(f"New contact created: {payload.sender}")

    contact.last_contact_at = datetime.now(timezone.utc)

    # ── 5. Thread link or create ──────────────────────────────────────────────
    thread_id_key = payload.thread_id or f"thread_{payload.sender}_{payload.message_id}"

    thread = db.query(Thread).filter(Thread.thread_id == thread_id_key).first()
    if not thread:
        thread = Thread(
            id=str(uuid.uuid4()),
            thread_id=thread_id_key,
            subject=payload.subject,
            sender_email=payload.sender,
            first_seen_at=email_ts or datetime.now(timezone.utc),
            status=ThreadStatus.open,
        )
        db.add(thread)
        logger.info(f"New thread created: {thread_id_key}")
    else:
        # Update last_updated_at via the ORM onupdate trigger
        thread.last_updated_at = datetime.now(timezone.utc)
        # If timestamps arrive out of order, update first_seen_at
        if email_ts and thread.first_seen_at and email_ts < thread.first_seen_at:
            thread.first_seen_at = email_ts

    # ── 6. Determine initial status ───────────────────────────────────────────
    if heuristic.is_spam or auto_newsletter:
        initial_status = EmailStatus.ignored
    elif heuristic.is_security_threat or heuristic.is_legal_threat:
        initial_status = EmailStatus.escalated
    else:
        initial_status = EmailStatus.received

    # ── 7. Create Email record ────────────────────────────────────────────────
    email_id = str(uuid.uuid4())
    email = Email(
        id=email_id,
        message_id=payload.message_id,
        thread_id=thread_id_key,
        sender=payload.sender,
        subject=payload.subject,
        body=payload.body,
        timestamp=email_ts,
        is_spam=heuristic.is_spam or auto_newsletter,
        is_internal=heuristic.is_internal,
        is_security_threat=heuristic.is_security_threat,
        priority_score=heuristic.priority_score,
        # Pre-fill urgency from heuristic — LLM will refine this later
        urgency=heuristic.urgency_hint if not heuristic.is_spam else "Low",
        status=initial_status,
    )
    db.add(email)

    # ── 8. Audit log ──────────────────────────────────────────────────────────
    audit = AuditLog(
        id=str(uuid.uuid4()),
        entity_type="email",
        entity_id=email_id,
        action="ingested",
        performed_by="agent",
        diff={
            "message_id": payload.message_id,
            "heuristic_flags": {
                "is_spam": heuristic.is_spam,
                "is_internal": heuristic.is_internal,
                "is_security_threat": heuristic.is_security_threat,
                "is_legal_threat": heuristic.is_legal_threat,
                "urgency_hint": heuristic.urgency_hint,
                "routing_queue": heuristic.routing_queue,
                "triggered_keywords": heuristic.triggered_keywords,
            },
        },
    )
    db.add(audit)

    db.commit()
    db.refresh(email)

    logger.info(
        f"Ingested {payload.message_id} | spam={heuristic.is_spam} | "
        f"security={heuristic.is_security_threat} | urgency={heuristic.urgency_hint} | "
        f"queue={heuristic.routing_queue}"
    )

    return {
        "job_id": email_id,
        "message_id": payload.message_id,
        "status": initial_status.value,
        "duplicate": False,
    }


# ── Bulk seed from JSON file ──────────────────────────────────────────────────

def seed_from_json(json_path: str, db: Session) -> dict:
    """
    Load email-data-advanced.json and ingest all emails.
    Skips duplicates silently. Returns counts.
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(path, "r", encoding="utf-8") as f:
        emails = json.load(f)

    ingested = 0
    duplicates = 0
    errors = 0

    for raw in emails:
        try:
            payload = EmailIngestRequest(**raw)
            result = ingest_email(payload, db)
            if result["duplicate"]:
                duplicates += 1
            else:
                ingested += 1
        except Exception as e:
            errors += 1
            logger.error(f"Failed to ingest {raw.get('message_id', 'unknown')}: {e}")

    return {"ingested": ingested, "duplicates": duplicates, "errors": errors, "total": len(emails)}


# ── Job status lookup ─────────────────────────────────────────────────────────

def get_job_status(job_id: str, db: Session) -> Optional[dict]:
    """Check processing status of an ingested email by its job_id (= email.id)."""
    email = db.query(Email).filter(Email.id == job_id).first()
    if not email:
        return None
    return {
        "job_id": job_id,
        "message_id": email.message_id,
        "status": email.status.value,
        "urgency": email.urgency.value if email.urgency else None,
        "category": email.category.value if email.category else None,
        "is_spam": email.is_spam,
        "is_security_threat": email.is_security_threat,
        "classified": email.category is not None,
    }