"""
Sentiment Tracker
=================
Tracks per-sender sentiment over time.
Detects deterioration: 3+ consecutive negative emails triggers escalation alert.
"""
import logging
from sqlalchemy.orm import Session
from app.models.email import Email, SentimentLabel

logger = logging.getLogger(__name__)

DETERIORATION_THRESHOLD = 3
NEGATIVE_SCORE_THRESHOLD = -0.3


def update_sentiment_trend(sender: str, new_score: float, db: Session) -> dict:
    recent_emails = (
        db.query(Email)
        .filter(
            Email.sender == sender,
            Email.sentiment_score.isnot(None),
        )
        .order_by(Email.timestamp.desc())
        .limit(10)
        .all()
    )

    scores = [e.sentiment_score for e in recent_emails if e.sentiment_score is not None]
    if new_score is not None:
        scores.insert(0, new_score)

    moving_avg = sum(scores) / len(scores) if scores else 0.0

    # Check for consecutive negatives
    consecutive_negatives = 0
    for score in scores:
        if score < NEGATIVE_SCORE_THRESHOLD:
            consecutive_negatives += 1
        else:
            break

    alert = consecutive_negatives >= DETERIORATION_THRESHOLD
    if alert:
        logger.warning(
            f"SENTIMENT ALERT: {sender} has {consecutive_negatives} "
            f"consecutive negative emails. Moving avg: {moving_avg:.2f}"
        )

    return {
        "sender": sender,
        "moving_average": round(moving_avg, 3),
        "consecutive_negatives": consecutive_negatives,
        "deterioration_alert": alert,
        "sample_size": len(scores),
    }


def get_sentiment_trend(sender: str, days: int, db: Session) -> dict:
    from datetime import datetime, timezone, timedelta
    from app.models.email import Email

    # Build query — if days=0 return all time
    query = db.query(Email).filter(
        Email.sender == sender,
        Email.sentiment_score.isnot(None),
    )

    if days > 0:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.filter(Email.timestamp >= since)

    emails = query.order_by(Email.timestamp.asc()).all()

    trend = [
        {
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "sentiment_score": e.sentiment_score,
            "category": e.category.value if e.category else None,
            "message_id": e.message_id,
        }
        for e in emails
    ]

    scores = [e.sentiment_score for e in emails]
    consecutive_negatives = 0
    for score in reversed(scores):
        if score < -0.3:
            consecutive_negatives += 1
        else:
            break

    return {
        "sender": sender,
        "days": days,
        "data_points": len(trend),
        "moving_average": round(sum(scores) / len(scores), 3) if scores else 0.0,
        "consecutive_negatives": consecutive_negatives,
        "deterioration_alert": consecutive_negatives >= 3,
        "trend": trend,
    }