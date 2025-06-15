from app.core.jwt_handler import get_current_user, create_access_token
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from ...core.db import get_postgres_db
from ...core.dependencies import get_decrypted_payload
from ...models.user import User
from .schemas import UserCreate, APIResponse, UserLogin
from .services.create_user import create_user
from .services.get_user_stats import get_user_stats
from .services.authenticate_user import authenticate_user
from ms_communicator import MicroServiceClient
import logging

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)

# Initialize the microservice client
service_client = MicroServiceClient("user-service")

@router.post("/register", response_model=APIResponse)
async def register_user(
    request: Request,
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
        
        # Notify analytics service
        try:
            analytics_data = {
                "event_type": "user_action",
                "event_name": "user_registered", 
                "user_id": new_user.id,
                "properties": {"username": new_user.username}
            }
            
            await service_client.request(
                target_service="analytics-service",
                endpoint="/api/v1/analytics/events",
                method="POST",
                payload=analytics_data
            )
            logger.info(f"Analytics event sent for user registration: {new_user.id}")
        except Exception as e:
            # Analytics notification failed, but user creation succeeded
            logger.error(f"Failed to send analytics event: {str(e)}")
        
        return APIResponse(
            message="User created successfully",
            data={"user_id": new_user.id, "username": new_user.username}
        )
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"User registration failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/login", response_model=APIResponse)
async def user_login(
    login_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_postgres_db)
):
    """Handle user login, generate JWT token, and send analytics"""
    try:
        # Authenticate user
        user = await authenticate_user(db, login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        # Generate JWT token
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "exp": datetime.utcnow() + timedelta(days=1)  # Token expires in 1 day
        }
        access_token = create_access_token(token_data)

        # Send analytics about the login
        try:
            analytics_response = await service_client.request(
                target_service="analytics-service",
                endpoint="/api/v1/analytics/track",
                method="POST",
                payload={
                    "user_id": str(user.id),
                    "action": "login",
                    "metadata": {
                        "ip_address": request.client.host if request.client else "unknown",
                        "user_agent": request.headers.get("user-agent", "unknown"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )
            analytics_tracked = analytics_response.get("status") == "success"
        except Exception as e:
            logger.error(f"Failed to send analytics event: {str(e)}")
            analytics_tracked = False

        return APIResponse(
            message="Login successful",
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": user.id,
                "username": user.username,
                "analytics_tracked": analytics_tracked
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{user_id}/analytics")
async def get_user_analytics(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Get analytics data for a user"""
    try:
        # Get analytics data
        analytics_response = await service_client.request(
            target_service="analytics-service",
            endpoint=f"/api/v1/analytics/user/{user_id}",
            method="GET"
        )
        
        return {
            "status": "success",
            "user_id": user_id,
            "analytics": analytics_response
        }
        
    except Exception as e:
        logger.error(f"Failed to get analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/count", response_model=APIResponse)
async def get_user_count(
    request: Request,
    db: AsyncSession = Depends(get_postgres_db),
    decrypted_payload: Optional[Dict[str, Any]] = Depends(get_decrypted_payload)
):
    """Get total user count - called by analytics service"""
    try:
        # Get user stats
        stats_data = await get_user_stats(db)
        
        return APIResponse(
            message="User statistics retrieved",
            data=stats_data
        )
    
    except Exception as e:
        logger.error(f"Failed to get user count: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user count")