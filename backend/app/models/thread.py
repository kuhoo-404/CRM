from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class ThreadStatus(str, enum.Enum):
    open = "Open"
    resolved = "Resolved"
    escalated = "Escalated"
    ignored = "Ignored"


class Thread(Base):
    __tablename__ = "threads"

    id = Column(String, primary_key=True)              # UUID
    thread_id = Column(String, unique=True, nullable=False, index=True)  # from JSON e.g. "thread_alice_pricing"
    subject = Column(String, nullable=True)
    sender_email = Column(String, ForeignKey("contacts.email"), nullable=False, index=True)
    first_seen_at = Column(DateTime(timezone=True), nullable=True)
    last_updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    status = Column(SAEnum(ThreadStatus), default=ThreadStatus.open, nullable=False)
    assigned_to = Column(String, nullable=True)        # email of assignee

    # Relationships
    contact = relationship("Contact", back_populates="threads")
    emails = relationship("Email", back_populates="thread", order_by="Email.timestamp", lazy="dynamic")