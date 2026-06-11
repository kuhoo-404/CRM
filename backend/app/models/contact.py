from sqlalchemy import Column, String, Float, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class ContactStatus(str, enum.Enum):
    active = "Active"
    vip = "VIP"
    blocked = "Blocked"
    churned = "Churned"


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(String, primary_key=True)          # UUID, set in service
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    status = Column(SAEnum(ContactStatus), default=ContactStatus.active, nullable=False)
    account_value = Column(Float, default=0.0)
    churn_risk_score = Column(Float, default=0.0)  # 0.0 – 1.0
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_contact_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    threads = relationship("Thread", back_populates="contact", lazy="dynamic")