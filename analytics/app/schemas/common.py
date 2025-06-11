from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime


class HealthCheck(BaseModel):
    status: str = "healthy"
    service: str
    version: str
    timestamp: str


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