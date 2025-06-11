from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    USER_ACTION = "user_action"
    PAGE_VIEW = "page_view"
    API_CALL = "api_call"


class AnalyticsEventCreate(BaseModel):
    event_type: EventType
    event_name: str = Field(..., max_length=100)
    user_id: Optional[int] = None
    properties: Optional[Dict[str, Any]] = None


class AnalyticsEventResponse(BaseModel):
    id: int
    event_type: str
    event_name: str
    user_id: Optional[int]
    properties: Optional[Dict[str, Any]]
    timestamp: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class APIResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[dict] = None 