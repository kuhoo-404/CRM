from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.schemas.common import ApiResponse
from app.models.email import Email, EmailStatus, UrgencyLevel, EmailCategory

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=ApiResponse)
def get_stats(db: Session = Depends(get_db)):
    """Dashboard counts: Pending, Replied, Escalated, Critical, Spam."""
    total = db.query(func.count(Email.id)).scalar()
    pending = db.query(func.count(Email.id)).filter(Email.status == EmailStatus.received).scalar()
    replied = db.query(func.count(Email.id)).filter(Email.status == EmailStatus.replied).scalar()
    escalated = db.query(func.count(Email.id)).filter(Email.status == EmailStatus.escalated).scalar()
    spam = db.query(func.count(Email.id)).filter(Email.is_spam == True).scalar()
    critical = db.query(func.count(Email.id)).filter(Email.urgency == UrgencyLevel.critical).scalar()
    security = db.query(func.count(Email.id)).filter(Email.is_security_threat == True).scalar()
    requires_human = db.query(func.count(Email.id)).filter(Email.requires_human == True).scalar()
    processing = db.query(func.count(Email.id)).filter(Email.status == EmailStatus.processing).scalar()

    return ApiResponse.ok(data={
        "total": total,
        "pending": pending,
        "replied": replied,
        "escalated": escalated,
        "spam": spam,
        "critical": critical,
        "security_threats": security,
        "requires_human": requires_human,
        "processing": processing,
    })


@router.get("/category-breakdown", response_model=ApiResponse)
def get_category_breakdown(
    days: int = Query(30, description="Number of days to look back. 0 = all time."),
    db: Session = Depends(get_db),
):
    """Category distribution over configurable date range."""
    query = db.query(Email.category, func.count(Email.id)).filter(
        Email.category.isnot(None)
    )

    if days > 0:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.filter(Email.timestamp >= since)

    rows = query.group_by(Email.category).all()

    breakdown = [
        {"category": row[0].value if row[0] else "Unknown", "count": row[1]}
        for row in rows
    ]
    breakdown.sort(key=lambda x: x["count"], reverse=True)

    total_classified = sum(b["count"] for b in breakdown)

    return ApiResponse.ok(data={
        "days": days,
        "total_classified": total_classified,
        "breakdown": breakdown,
    })