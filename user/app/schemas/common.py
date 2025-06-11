from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional


class HealthCheck(BaseModel):
    status: str = "healthy"
    service: str
    version: str
    timestamp: str


class APIResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[Any] = None 