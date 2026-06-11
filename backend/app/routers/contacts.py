"""
Contacts Router
===============
GET   /contacts/{email}         — contact profile with open threads + churn risk
PATCH /contacts/{email}/status  — update contact status (VIP, Blocked, etc.)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime, timezone

from app.database import get_db
from app.schemas.common import ApiResponse
from app.models.contact import Contact, ContactStatus
from app.models.thread import Thread, ThreadStatus
from app.models.email import Email
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/contacts", tags=["contacts"])


class ContactStatusUpdate(BaseModel):
    status: str
    updated_by: Optional[str] = "human"


@router.get("", response_model=ApiResponse)
def get_all_contacts(db: Session = Depends(get_db)):
    """Return all contacts ordered by last contact."""
    contacts = db.query(Contact).order_by(Contact.last_contact_at.desc()).all()
    result = []
    for c in contacts:
        thread_count = db.query(func.count(Thread.id)).filter(
            Thread.sender_email == c.email
        ).scalar()
        result.append({
            "email": c.email,
            "name": c.name,
            "company": c.company,
            "status": c.status.value,
            "account_value": c.account_value,
            "churn_risk_score": c.churn_risk_score,
            "thread_count": thread_count,
            "last_contact_at": c.last_contact_at.isoformat() if c.last_contact_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return ApiResponse.ok(data=result, message=f"{len(result)} contacts found")


@router.get("/{contact_email}", response_model=ApiResponse)
def get_contact(contact_email: str, db: Session = Depends(get_db)):
    """
    Contact profile with churn risk, account value, and open threads.
    """
    contact = db.query(Contact).filter(Contact.email == contact_email).first()
    if not contact:
        return ApiResponse.fail(
            error_code="NOT_FOUND",
            message=f"Contact {contact_email} not found",
        )

    # Get threads with status
    threads = db.query(Thread).filter(Thread.sender_email == contact_email).all()
    open_threads = [t for t in threads if t.status == ThreadStatus.open]
    escalated_threads = [t for t in threads if t.status == ThreadStatus.escalated]

    # Get recent emails for sentiment context
    recent_emails = (
        db.query(Email)
        .filter(Email.sender == contact_email, Email.sentiment_score.isnot(None))
        .order_by(Email.timestamp.desc())
        .limit(5)
        .all()
    )

    sentiment_history = [
        {
            "message_id": e.message_id,
            "sentiment_score": e.sentiment_score,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
        }
        for e in recent_emails
    ]

    scores = [e.sentiment_score for e in recent_emails]
    moving_avg = round(sum(scores) / len(scores), 3) if scores else None

    return ApiResponse.ok(data={
        "email": contact.email,
        "name": contact.name,
        "company": contact.company,
        "status": contact.status.value,
        "account_value": contact.account_value,
        "churn_risk_score": contact.churn_risk_score,
        "created_at": contact.created_at.isoformat() if contact.created_at else None,
        "last_contact_at": contact.last_contact_at.isoformat() if contact.last_contact_at else None,
        "thread_summary": {
            "total": len(threads),
            "open": len(open_threads),
            "escalated": len(escalated_threads),
        },
        "sentiment_summary": {
            "moving_average": moving_avg,
            "recent_scores": sentiment_history,
        },
        "open_threads": [
            {
                "thread_id": t.thread_id,
                "subject": t.subject,
                "status": t.status.value,
                "last_updated_at": t.last_updated_at.isoformat() if t.last_updated_at else None,
            }
            for t in open_threads
        ],
    })


@router.patch("/{contact_email}/status", response_model=ApiResponse)
def update_contact_status(
    contact_email: str,
    body: ContactStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update contact status — VIP, Blocked, Active, Churned."""
    contact = db.query(Contact).filter(Contact.email == contact_email).first()
    if not contact:
        return ApiResponse.fail(
            error_code="NOT_FOUND",
            message=f"Contact {contact_email} not found",
        )

    allowed = [s.value for s in ContactStatus]
    if body.status not in allowed:
        return ApiResponse.fail(
            error_code="INVALID_STATUS",
            message=f"Invalid status '{body.status}'",
            details={"allowed_values": allowed},
        )

    old_status = contact.status.value
    contact.status = ContactStatus(body.status)

    # Audit log
    audit = AuditLog(
        id=str(uuid.uuid4()),
        entity_type="contact",
        entity_id=contact.email,
        action="status_updated",
        performed_by=body.updated_by,
        diff={"before": old_status, "after": body.status},
    )
    db.add(audit)
    db.commit()

    return ApiResponse.ok(
        data={
            "email": contact.email,
            "old_status": old_status,
            "new_status": contact.status.value,
        },
        message=f"Contact status updated to {body.status}",
    )