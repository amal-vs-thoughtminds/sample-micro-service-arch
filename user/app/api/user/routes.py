from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, Optional

from ...core.db import get_postgres_db
from ...core.dependencies import get_decrypted_payload, get_optional_decrypted_payload
from ...core.encryption import encrypt_response_data
from ...core.dispatcher import dispatcher
from ...core.jwt_handler import create_access_token
from ...models.user import User
from .schemas import UserCreate, UserLogin, UserResponse, Token, APIResponse
from .services.create_user import create_user
from .services.authenticate_user import authenticate_user
from .services.get_user_stats import get_user_stats

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=APIResponse)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_postgres_db),
    decrypted_payload: Optional[Dict[str, Any]] = Depends(get_decrypted_payload)
):
    """Register a new user and notify analytics service"""
    try:
        # Use decrypted payload if available
        if decrypted_payload:
            user_data = UserCreate(**decrypted_payload)
        
        # Create user
        new_user = await create_user(db, user_data)
        
        # Notify analytics service via dispatcher
        try:
            analytics_data = {
                "event_type": "user_action",
                "event_name": "user_registered", 
                "user_id": new_user.id,
                "properties": {"username": new_user.username}
            }
            analytics_response = await dispatcher.call_analytics_service(
                "/api/v1/analytics/events", 
                analytics_data
            )
        except Exception as e:
            # Analytics notification failed, but user creation succeeded
            pass
        
        response_data = {
            "message": "User created successfully",
            "data": {"user_id": new_user.id, "username": new_user.username}
        }
        
        # Return encrypted response for service communication
        if decrypted_payload:
            return encrypt_response_data(response_data)
        
        return APIResponse(**response_data)
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/login")
async def login_user(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_postgres_db),
    decrypted_payload: Optional[Dict[str, Any]] = Depends(get_optional_decrypted_payload)
):
    """Login user and track login event via dispatcher (optional encryption)"""
    try:
        # Use decrypted payload if available
        if decrypted_payload:
            login_data = UserLogin(**decrypted_payload)
        
        # Authenticate user
        user = await authenticate_user(db, login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": user.username, "user_id": user.id})
        
        # Track login event via dispatcher
        try:
            analytics_data = {
                "event_type": "user_action",
                "event_name": "user_login",
                "user_id": user.id,
                "properties": {"login_method": "password"}
            }
            await dispatcher.call_analytics_service(
                "/api/v1/analytics/events",
                analytics_data
            )
        except Exception as e:
            # Analytics tracking failed, but login succeeded
            pass
        
        token_data = {"access_token": access_token, "token_type": "bearer"}
        
        # Return encrypted response only if originally encrypted or specifically requested
        if decrypted_payload:
            return encrypt_response_data(token_data)
        
        return Token(**token_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/stats/count", response_model=APIResponse)
async def get_user_count(
    db: AsyncSession = Depends(get_postgres_db)
):
    """Get total user count - called by analytics service (always public, no encryption needed)"""
    try:
        stats_data = await get_user_stats(db)
        
        response_data = {
            "message": "User statistics retrieved",
            "data": stats_data
        }
        
        return APIResponse(**response_data)
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user count")


@router.get("/profile")
async def get_user_profile(
    username: str,
    db: AsyncSession = Depends(get_postgres_db),
    decrypted_payload: Optional[Dict[str, Any]] = Depends(get_optional_decrypted_payload)
):
    """Demo endpoint showing optional encryption - can be called with or without encryption"""
    try:
        # Find user
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        profile_data = {
            "message": "User profile retrieved",
            "data": {
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat()
            }
        }
        
        # Return encrypted response only if client requested encryption
        if decrypted_payload:
            return encrypt_response_data(profile_data)
        
        return APIResponse(**profile_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get profile") 