# Import all models here so Alembic autogenerate picks them up
from app.models.contact import Contact, ContactStatus
from app.models.thread import Thread, ThreadStatus
from app.models.email import Email, EmailStatus, UrgencyLevel, EmailCategory, SentimentLabel
from app.models.action import Action, ActionType
from app.models.knowledge_chunk import KnowledgeChunk
from app.models.web_cache import WebIntelligenceCache
from app.models.audit_log import AuditLog

__all__ = [
    "Contact", "ContactStatus",
    "Thread", "ThreadStatus",
    "Email", "EmailStatus", "UrgencyLevel", "EmailCategory", "SentimentLabel",
    "Action", "ActionType",
    "KnowledgeChunk",
    "WebIntelligenceCache",
    "AuditLog",
]