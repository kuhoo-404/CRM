from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse
from app.services.thread_service import (
    get_all_threads,
    get_thread_by_contact,
    get_thread_history_for_agent,
)

router = APIRouter(prefix="/threads", tags=["threads"])


@router.get("", response_model=ApiResponse)
def fetch_all_threads(db: Session = Depends(get_db)):
    """Return all threads with their emails."""
    try:
        threads = get_all_threads(db)
        result = []
        for item in threads:
            thread = item["thread"]
            emails = item["emails"]
            result.append({
                "thread_id": thread.thread_id,
                "subject": thread.subject,
                "sender_email": thread.sender_email,
                "status": thread.status.value,
                "last_updated_at": thread.last_updated_at.isoformat() if thread.last_updated_at else None,
                "email_count": len(emails),
                "latest_email": {
                    "message_id": emails[-1].message_id,
                    "body_preview": (emails[-1].body or "")[:100],
                    "urgency": emails[-1].urgency.value if emails[-1].urgency else None,
                    "category": emails[-1].category.value if emails[-1].category else None,
                    "sentiment_score": emails[-1].sentiment_score,
                } if emails else None,
            })
        return ApiResponse.ok(data=result, message=f"{len(result)} threads found")
    except Exception as e:
        return ApiResponse.fail(error_code="THREAD_ERROR", message=str(e))


@router.get("/{contact_email}", response_model=ApiResponse)
def fetch_thread_by_contact(contact_email: str, db: Session = Depends(get_db)):
    """Return all threads for a specific contact email."""
    try:
        threads = get_thread_by_contact(contact_email, db)
        if not threads:
            return ApiResponse.fail(
                error_code="NOT_FOUND",
                message=f"No threads found for {contact_email}",
            )
        result = []
        for item in threads:
            thread = item["thread"]
            emails = item["emails"]
            result.append({
                "thread_id": thread.thread_id,
                "subject": thread.subject,
                "status": thread.status.value,
                "first_seen_at": thread.first_seen_at.isoformat() if thread.first_seen_at else None,
                "last_updated_at": thread.last_updated_at.isoformat() if thread.last_updated_at else None,
                "emails": [
                    {
                        "id": e.id,
                        "message_id": e.message_id,
                        "subject": e.subject,
                        "body": e.body,
                        "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                        "sentiment": e.sentiment.value if e.sentiment else None,
                        "sentiment_score": e.sentiment_score,
                        "category": e.category.value if e.category else None,
                        "urgency": e.urgency.value if e.urgency else None,
                        "requires_human": e.requires_human,
                        "confidence": e.confidence,
                        "is_spam": e.is_spam,
                        "is_security_threat": e.is_security_threat,
                        "status": e.status.value,
                    }
                    for e in emails
                ],
            })
        return ApiResponse.ok(data=result)
    except Exception as e:
        return ApiResponse.fail(error_code="THREAD_ERROR", message=str(e))


@router.get("/{contact_email}/history", response_model=ApiResponse)
def fetch_thread_history(contact_email: str, db: Session = Depends(get_db)):
    """Agent tool endpoint — full email history for a sender ordered by time."""
    try:
        history = get_thread_history_for_agent(contact_email, db)
        return ApiResponse.ok(data=history, message=f"{len(history)} emails in history")
    except Exception as e:
        return ApiResponse.fail(error_code="HISTORY_ERROR", message=str(e))