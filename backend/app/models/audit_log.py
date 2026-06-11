from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True)             # UUID
    entity_type = Column(String, nullable=False, index=True)   # "email", "contact", "action", etc.
    entity_id = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)           # "classified", "escalated", "replied", etc.
    performed_by = Column(String, nullable=False)     # "agent" or user email
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    diff = Column(JSON, nullable=True)                # before/after snapshot