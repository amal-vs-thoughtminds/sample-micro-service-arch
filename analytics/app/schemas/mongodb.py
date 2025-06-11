from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AnalyticsEventType(str, Enum):
    PAGE_VIEW = "page_view"
    BUTTON_CLICK = "button_click"
    FORM_SUBMIT = "form_submit"
    USER_REGISTRATION = "user_registration"
    USER_LOGIN = "user_login"
    PURCHASE = "purchase"
    SEARCH = "search"
    CUSTOM = "custom"


class AnalyticsEvent(BaseModel):
    event_type: AnalyticsEventType
    event_name: str
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AnalyticsEventResponse(BaseModel):
    id: str = Field(alias="_id")
    event_type: str
    event_name: str
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    class Config:
        populate_by_name = True


class AnalyticsSession(BaseModel):
    session_id: str
    user_id: Optional[int] = None
    start_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration: Optional[int] = None  # in seconds
    page_views: int = 0
    events_count: int = 0
    properties: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True


class AnalyticsSessionResponse(BaseModel):
    id: str = Field(alias="_id")
    session_id: str
    user_id: Optional[int] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    page_views: int = 0
    events_count: int = 0
    properties: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool
    
    class Config:
        populate_by_name = True


class EventQuery(BaseModel):
    event_type: Optional[AnalyticsEventType] = None
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=50, le=100)
    skip: int = Field(default=0, ge=0)


class SessionAnalyticsQuery(BaseModel):
    user_id: Optional[int] = None
    is_active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=50, le=100)
    skip: int = Field(default=0, ge=0) 