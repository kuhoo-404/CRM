from sqlalchemy import Column, String, Float, DateTime, Boolean, Text, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class EmailStatus(str, enum.Enum):
    received = "Received"
    processing = "Processing"
    replied = "Replied"
    escalated = "Escalated"
    ignored = "Ignored"


class UrgencyLevel(str, enum.Enum):
    critical = "Critical"
    high = "High"
    medium = "Medium"
    low = "Low"


class EmailCategory(str, enum.Enum):
    complaint = "Complaint"
    inquiry = "Inquiry"
    bug_report = "Bug Report"
    feature_request = "Feature Request"
    compliance = "Compliance"
    legal = "Legal"
    billing = "Billing"
    spam = "Spam"
    internal = "Internal"
    other = "Other"


class SentimentLabel(str, enum.Enum):
    positive = "Positive"
    neutral = "Neutral"
    negative = "Negative"
    mixed = "Mixed"


class Email(Base):
    __tablename__ = "emails"

    id = Column(String, primary_key=True)              # UUID
    message_id = Column(String, unique=True, nullable=False, index=True)  # from JSON e.g. "msg_001"
    thread_id = Column(String, ForeignKey("threads.thread_id"), nullable=False, index=True)
    sender = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=True, index=True)
    received_at = Column(DateTime(timezone=True), server_default=func.now())

    # Classification results — null until classified
    sentiment = Column(SAEnum(SentimentLabel), nullable=True)
    sentiment_score = Column(Float, nullable=True)    # -1.0 to +1.0
    category = Column(SAEnum(EmailCategory), nullable=True)
    urgency = Column(SAEnum(UrgencyLevel), nullable=True)
    requires_human = Column(Boolean, nullable=True)
    confidence = Column(Float, nullable=True)         # 0.0 to 1.0
    escalation_reason = Column(Text, nullable=True)
    suggested_reply = Column(Text, nullable=True)
    raw_entities = Column(JSON, nullable=True)        # {order_ids, ticket_ids, ...}

    # Heuristic flags (set before LLM)
    is_spam = Column(Boolean, default=False)
    is_internal = Column(Boolean, default=False)
    is_security_threat = Column(Boolean, default=False)
    priority_score = Column(Float, default=0.0)       # heuristic score before LLM

    status = Column(SAEnum(EmailStatus), default=EmailStatus.received, nullable=False)

    # Relationships
    thread = relationship("Thread", back_populates="emails")
    actions = relationship("Action", back_populates="email", lazy="dynamic")