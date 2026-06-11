from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Enum as SAEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class ActionType(str, enum.Enum):
    auto_reply = "Auto-Reply"
    escalate = "Escalate"
    legal_flag = "Legal-Flag"
    ticket_created = "Ticket-Created"
    ignored = "Ignored"
    dry_run = "Dry-Run"


class Action(Base):
    __tablename__ = "actions"

    id = Column(String, primary_key=True)             # UUID
    email_id = Column(String, ForeignKey("emails.id"), nullable=False, index=True)

    # Full ReAct reasoning trace: [{thought, action, observation}, ...]
    agent_reasoning_log = Column(JSON, nullable=True)

    action_type = Column(SAEnum(ActionType), nullable=True)
    proposed_content = Column(Text, nullable=True)    # draft reply text
    is_approved = Column(Boolean, default=False)
    approved_by = Column(String, nullable=True)       # "agent" or user email
    executed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    email = relationship("Email", back_populates="actions")