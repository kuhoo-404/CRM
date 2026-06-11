from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.email import EmailOut


class ThreadOut(BaseModel):
    id: str
    thread_id: str
    subject: Optional[str]
    sender_email: str
    first_seen_at: Optional[datetime]
    last_updated_at: Optional[datetime]
    status: str
    assigned_to: Optional[str]
    emails: List[EmailOut] = []

    class Config:
        from_attributes = True