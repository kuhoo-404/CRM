from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ContactOut(BaseModel):
    id: str
    email: str
    name: Optional[str]
    company: Optional[str]
    status: str
    account_value: float
    churn_risk_score: float
    created_at: Optional[datetime]
    last_contact_at: Optional[datetime]

    class Config:
        from_attributes = True


class ContactStatusUpdate(BaseModel):
    status: str  # "VIP" | "Blocked" | "Active" | "Churned"