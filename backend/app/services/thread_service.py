from sqlalchemy.orm import Session, joinedload
from app.models import Thread, Email
from app.utils.exceptions import ThreadNotFoundError


def get_thread_by_contact(contact_email: str, db: Session) -> list:
    """
    Return all threads for a contact email, each with its emails ordered by timestamp.
    Designed to hit the index on sender_email and thread_id for <100ms response.
    """
    threads = (
        db.query(Thread)
        .filter(Thread.sender_email == contact_email)
        .order_by(Thread.last_updated_at.desc())
        .all()
    )

    result = []
    for thread in threads:
        emails = (
            db.query(Email)
            .filter(Email.thread_id == thread.thread_id)
            .order_by(Email.timestamp.asc())
            .all()
        )
        result.append({"thread": thread, "emails": emails})

    return result


def get_all_threads(db: Session) -> list:
    """Return all threads with their emails. Used by dashboard."""
    threads = db.query(Thread).order_by(Thread.last_updated_at.desc()).all()
    result = []
    for thread in threads:
        emails = (
            db.query(Email)
            .filter(Email.thread_id == thread.thread_id)
            .order_by(Email.timestamp.asc())
            .all()
        )
        result.append({"thread": thread, "emails": emails})
    return result


def get_thread_history_for_agent(sender_email: str, db: Session) -> list:
    """
    Used by the agent's get_thread_history tool.
    Returns all emails from this sender ordered by timestamp — full thread context.
    """
    emails = (
        db.query(Email)
        .filter(Email.sender == sender_email)
        .order_by(Email.timestamp.asc())
        .all()
    )
    return [
        {
            "message_id": e.message_id,
            "thread_id": e.thread_id,
            "subject": e.subject,
            "body": e.body,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "sentiment": e.sentiment.value if e.sentiment else None,
            "urgency": e.urgency.value if e.urgency else None,
            "category": e.category.value if e.category else None,
        }
        for e in emails
    ]