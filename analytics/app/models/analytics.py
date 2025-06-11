from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime

from ..core.db import Base


class AnalyticsEvent(Base):
    """Analytics event model - included in Alembic migrations"""
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    event_name = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, index=True)
    properties = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AnalyticsReport(Base):
    """Analytics report model - NOT included in Alembic migrations (for access only)"""
    __tablename__ = "analytics_reports"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    report_name = Column(String(200), nullable=False)
    report_type = Column(String(50), nullable=False)
    filters = Column(JSON)
    created_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="pending") 