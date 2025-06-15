from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Optional


class HealthCheck(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of the health check")
    service: str = Field(..., description="Service name")
    details: Optional[dict] = Field(default=None, description="Additional health check details")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        from_attributes = True


class APIResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None 