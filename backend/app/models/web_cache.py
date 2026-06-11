from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class WebIntelligenceCache(Base):
    __tablename__ = "web_intelligence_cache"

    id = Column(String, primary_key=True)             # UUID
    source_url = Column(String, nullable=False)
    target_entity = Column(String, nullable=False, index=True)  # company name or domain
    scraped_data = Column(JSON, nullable=True)        # {rating, review_count, themes, ...}
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)