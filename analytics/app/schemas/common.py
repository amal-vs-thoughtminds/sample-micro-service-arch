from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime


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


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 100


class PaginatedResponse(BaseModel):
    items: list
    total: int
    skip: int
    limit: int
    has_next: bool
    has_prev: bool


class EncryptedRequest(BaseModel):
    encrypted_data: str


class EncryptedResponse(BaseModel):
    encrypted_data: str 