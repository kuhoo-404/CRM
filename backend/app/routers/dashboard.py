from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.schemas.common import ApiResponse
from app.models.email import Email, EmailStatus, UrgencyLevel

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

    return ApiResponse.ok(data={
        "total": total,
        "pending": pending,
        "replied": replied,
        "escalated": escalated,
        "spam": spam,
        "critical": critical,
        "security_threats": security,
        "requires_human": requires_human,
    })