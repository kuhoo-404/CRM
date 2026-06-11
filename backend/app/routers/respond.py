"""
Respond, Drafts, and Audit Routers
===================================
POST /respond/{email_id}         — send a reply, update status
PATCH /drafts/{id}               — edit a proposed auto-reply draft
POST  /drafts/{id}/approve       — approve and send, trigger audit log
GET   /audit/{entity_type}/{id}  — full audit history for any entity
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

from app.database import get_db
from app.schemas.common import ApiResponse
from app.models.email import Email, EmailStatus
from app.models.action import Action, ActionType
from app.models.audit_log import AuditLog
from app.models.thread import Thread, ThreadStatus

router = APIRouter(tags=["respond"])


# ── Pydantic request bodies ────────────────────────────────────────────────────

class ReplyRequest(BaseModel):
    reply_text: str
    sent_by: Optional[str] = "human"


class DraftEditRequest(BaseModel):
    proposed_content: str


# ── POST /respond/{email_id} ───────────────────────────────────────────────────

@router.post("/respond/{email_id}", response_model=ApiResponse)
def send_reply(
    email_id: str,
    body: ReplyRequest,
    db: Session = Depends(get_db),
):
    """
    Send a reply to an email.
    Updates email status → Replied.
    Appends to thread. Writes audit log.
    """
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        return ApiResponse.fail(
            error_code="NOT_FOUND",
            message=f"Email {email_id} not found",
        )

    # Safety: never send reply to spam or security threats
    if email.is_spam:
        return ApiResponse.fail(
            error_code="BLOCKED",
            message="Cannot reply to spam email",
        )
    if email.is_security_threat:
        return ApiResponse.fail(
            error_code="BLOCKED",
            message="Cannot reply to security threat email",
        )

    # Update email status
    email.status = EmailStatus.replied
    email.requires_human = False

    # Update thread status
    thread = db.query(Thread).filter(Thread.thread_id == email.thread_id).first()
    if thread:
        thread.status = ThreadStatus.resolved
        thread.last_updated_at = datetime.now(timezone.utc)

    # Create action record
    action = Action(
        id=str(uuid.uuid4()),
        email_id=email.id,
        action_type=ActionType.auto_reply,
        proposed_content=body.reply_text,
        is_approved=True,
        approved_by=body.sent_by,
        executed_at=datetime.now(timezone.utc),
    )
    db.add(action)

    # Audit log
    audit = AuditLog(
        id=str(uuid.uuid4()),
        entity_type="email",
        entity_id=email.id,
        action="reply_sent",
        performed_by=body.sent_by,
        diff={"reply_preview": body.reply_text[:200]},
    )
    db.add(audit)
    db.commit()

    return ApiResponse.ok(
        data={
            "email_id": email_id,
            "status": email.status.value,
            "reply_preview": body.reply_text[:100],
        },
        message="Reply sent successfully",
    )


# ── PATCH /drafts/{id} ─────────────────────────────────────────────────────────

@router.patch("/drafts/{action_id}", response_model=ApiResponse)
def edit_draft(
    action_id: str,
    body: DraftEditRequest,
    db: Session = Depends(get_db),
):
    """Edit a proposed auto-reply draft before sending."""
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        return ApiResponse.fail(
            error_code="NOT_FOUND",
            message=f"Draft {action_id} not found",
        )
    if action.is_approved:
        return ApiResponse.fail(
            error_code="ALREADY_APPROVED",
            message="This draft has already been approved and sent",
        )

    old_content = action.proposed_content
    action.proposed_content = body.proposed_content

    # Audit the edit
    audit = AuditLog(
        id=str(uuid.uuid4()),
        entity_type="action",
        entity_id=action_id,
        action="draft_edited",
        performed_by="human",
        diff={
            "before": (old_content or "")[:200],
            "after": body.proposed_content[:200],
        },
    )
    db.add(audit)
    db.commit()

    return ApiResponse.ok(
        data={
            "action_id": action_id,
            "proposed_content": action.proposed_content,
        },
        message="Draft updated successfully",
    )


# ── POST /drafts/{id}/approve ──────────────────────────────────────────────────

@router.post("/drafts/{action_id}/approve", response_model=ApiResponse)
def approve_draft(
    action_id: str,
    db: Session = Depends(get_db),
):
    """Approve and send a draft. Updates email status and triggers audit log."""
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        return ApiResponse.fail(
            error_code="NOT_FOUND",
            message=f"Draft {action_id} not found",
        )
    if action.is_approved:
        return ApiResponse.fail(
            error_code="ALREADY_APPROVED",
            message="This draft has already been approved",
        )

    # Get the associated email
    email = db.query(Email).filter(Email.id == action.email_id).first()
    if not email:
        return ApiResponse.fail(
            error_code="NOT_FOUND",
            message="Associated email not found",
        )

    # Safety checks
    if email.is_spam:
        return ApiResponse.fail(error_code="BLOCKED", message="Cannot approve reply to spam")
    if email.is_security_threat:
        return ApiResponse.fail(error_code="BLOCKED", message="Cannot approve reply to security threat")

    # Approve the action
    action.is_approved = True
    action.approved_by = "human"
    action.executed_at = datetime.now(timezone.utc)

    # Update email status
    email.status = EmailStatus.replied
    email.requires_human = False

    # Update thread status
    thread = db.query(Thread).filter(Thread.thread_id == email.thread_id).first()
    if thread:
        thread.status = ThreadStatus.resolved
        thread.last_updated_at = datetime.now(timezone.utc)

    # Audit log
    audit = AuditLog(
        id=str(uuid.uuid4()),
        entity_type="action",
        entity_id=action_id,
        action="draft_approved_and_sent",
        performed_by="human",
        diff={
            "email_id": email.id,
            "reply_preview": (action.proposed_content or "")[:200],
        },
    )
    db.add(audit)
    db.commit()

    return ApiResponse.ok(
        data={
            "action_id": action_id,
            "email_id": email.id,
            "status": email.status.value,
            "reply_sent": action.proposed_content,
        },
        message="Draft approved and sent",
    )


# ── GET /audit/{entity_type}/{entity_id} ──────────────────────────────────────

@router.get("/audit/{entity_type}/{entity_id}", response_model=ApiResponse)
def get_audit_history(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db),
):
    """Full audit history for any entity (email, action, contact, ticket)."""
    logs = (
        db.query(AuditLog)
        .filter(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id,
        )
        .order_by(AuditLog.timestamp.asc())
        .all()
    )

    result = [
        {
            "id": log.id,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "action": log.action,
            "performed_by": log.performed_by,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "diff": log.diff,
        }
        for log in logs
    ]

    return ApiResponse.ok(
        data={"entity_type": entity_type, "entity_id": entity_id, "logs": result},
        message=f"{len(result)} audit entries found",
    )