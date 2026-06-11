from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.sql import func
from app.database import Base


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(String, primary_key=True)             # UUID
    source_doc = Column(String, nullable=False, index=True)   # e.g. "refund_policy.md"
    chunk_index = Column(Integer, nullable=False)     # position within doc
    chunk_text = Column(Text, nullable=False)
    # NOTE: actual vector stored in ChromaDB, not here
    # This table is for metadata / audit only
    created_at = Column(DateTime(timezone=True), server_default=func.now())