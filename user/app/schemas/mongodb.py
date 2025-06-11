from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ActivityType(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    PROFILE_UPDATE = "profile_update"
    PASSWORD_CHANGE = "password_change"
    API_CALL = "api_call"


class UserActivity(BaseModel):
    user_id: int
    activity_type: ActivityType
    description: str
    metadata: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class UserActivityResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: int
    activity_type: str
    description: str
    metadata: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime
    
    class Config:
        populate_by_name = True


class UserSession(BaseModel):
    user_id: int
    session_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    login_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    last_activity: Optional[datetime] = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class UserSessionResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: int
    session_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    login_time: datetime
    last_activity: datetime
    is_active: bool
    
    class Config:
        populate_by_name = True


class ActivityQuery(BaseModel):
    user_id: Optional[int] = None
    activity_type: Optional[ActivityType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=50, le=100)
    skip: int = Field(default=0, ge=0)


class SessionQuery(BaseModel):
    user_id: Optional[int] = None
    is_active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=50, le=100)
    skip: int = Field(default=0, ge=0) 