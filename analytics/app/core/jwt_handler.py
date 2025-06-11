from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status, Request

from .config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)  # Default 24 hours
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.encryption_key, algorithm="HS256")
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.encryption_key, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


def decode_token(token: str) -> Optional[dict]:
    """Decode JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.encryption_key, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


def get_token_from_header(request: Request) -> Optional[str]:
    """Extract JWT token from x-access-token header"""
    token = request.headers.get("x-access-token")
    if token:
        return token
    return None


async def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from JWT token in x-access-token header"""
    token = get_token_from_header(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


async def get_optional_current_user(request: Request) -> Optional[dict]:
    """Get current user from JWT token in x-access-token header (optional)"""
    token = get_token_from_header(request)
    if not token:
        return None
    
    payload = verify_token(token)
    return payload 