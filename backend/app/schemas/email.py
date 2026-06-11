from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List
from datetime import datetime


class EmailIngestRequest(BaseModel):
    """Schema for POST /api/ingest — validates incoming email payload."""
    message_id: str
    sender: str
    subject: Optional[str] = None
    body: Optional[str] = None
    timestamp: Optional[str] = None
    thread_id: Optional[str] = None

    @field_validator("message_id")
    @classmethod
    def message_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("message_id cannot be empty")
        return v.strip()

    @field_validator("sender")
    @classmethod
    def sender_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("sender cannot be empty")
        if "@" not in v:
            raise ValueError("sender must be a valid email address")
        return v.strip().lower()

    @field_validator("body")
    @classmethod
    def sanitize_body(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Truncate extremely long bodies to 10,000 chars for LLM processing
        stripped = v.strip()
        if not stripped:
            return None
        if len(stripped) > 10000:
            return stripped[:10000] + "\n\n[TRUNCATED — body exceeded 10,000 characters]"
        return stripped

    @model_validator(mode="after")
    def at_least_subject_or_body(self) -> "EmailIngestRequest":
        if not self.subject and not self.body:
            raise ValueError("Email must have at least a subject or a body")
        return self


class EmailIngestResponse(BaseModel):
    job_id: str
    message_id: str
    status: str
    duplicate: bool = False


class DetectedEntities(BaseModel):
    order_ids: List[str] = []
    ticket_ids: List[str] = []
    monetary_amounts: List[str] = []
    deadlines: List[str] = []
    products_mentioned: List[str] = []


class ClassificationResult(BaseModel):
    category: str
    sentiment: str
    sentiment_score: float
    urgency: str
    requires_human: bool
    escalation_reason: Optional[str] = None
    suggested_reply: Optional[str] = None
    confidence: float
    detected_entities: DetectedEntities = DetectedEntities()


class EmailOut(BaseModel):
    id: str
    message_id: str
    thread_id: str
    sender: str
    subject: Optional[str]
    body: Optional[str]
    timestamp: Optional[datetime]
    sentiment: Optional[str]
    sentiment_score: Optional[float]
    category: Optional[str]
    urgency: Optional[str]
    requires_human: Optional[bool]
    confidence: Optional[float]
    is_spam: bool
    is_internal: bool
    is_security_threat: bool
    priority_score: float
    status: str

    class Config:
        from_attributes = True