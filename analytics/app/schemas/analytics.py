from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    PAGE_VIEW = "page_view"
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    ERROR = "error"
    CUSTOM = "custom"

class AnalyticsEvent(BaseModel):
    event_type: EventType
    event_name: str = Field(..., max_length=100)
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AnalyticsEventResponse(BaseModel):
    id: int
    event_type: EventType
    event_name: str
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AnalyticsStats(BaseModel):
    total_events: int
    events_by_type: Dict[str, int]
    events_by_user: Dict[int, int]
    last_event_time: Optional[datetime] = None
    average_events_per_day: Optional[float] = None

class UserAnalytics(BaseModel):
    user_id: int
    total_events: int
    events_by_type: Dict[str, int]
    last_event: Optional[str] = None
    last_event_time: Optional[datetime] = None
    session_count: Optional[int] = None
    average_session_duration: Optional[int] = None  # in seconds 

class APIResponse(BaseModel):
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None 