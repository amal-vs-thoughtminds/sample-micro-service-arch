from fastapi import APIRouter, Depends, HTTPException, status, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional

from ...core.mongodb import get_mongodb
from ...core.jwt_handler import get_current_user, get_optional_current_user
from ...schemas.mongodb import (
    UserActivity, UserActivityResponse, ActivityQuery,
    UserSession, UserSessionResponse, SessionQuery
)
from ...schemas.common import APIResponse
from ..user.services.user_activities import (
    create_user_activity, get_user_activities, get_user_activity_stats
)
from ..user.services.user_sessions import (
    create_user_session, get_user_sessions, update_session_activity,
    end_user_session, get_active_sessions_count
)

router = APIRouter()


@router.post("/activities", response_model=APIResponse)
async def create_activity(
    activity_data: UserActivity,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
    current_user: dict = Depends(get_current_user)
):
    """Create a new user activity record"""
    try:
        # Add IP and User Agent from request
        activity_data.ip_address = request.client.host
        activity_data.user_agent = request.headers.get("user-agent")
        
        activity = await create_user_activity(db, activity_data)
        
        return APIResponse(
            success=True,
            message="User activity created successfully",
            data=activity.dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create activity: {str(e)}"
        )


@router.get("/activities", response_model=APIResponse)
async def get_activities(
    user_id: Optional[int] = None,
    activity_type: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
    current_user: dict = Depends(get_current_user)
):
    """Get user activities with filtering"""
    try:
        query = ActivityQuery(
            user_id=user_id,
            activity_type=activity_type,
            limit=limit,
            skip=skip
        )
        
        activities = await get_user_activities(db, query)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(activities)} activities",
            data=[activity.dict() for activity in activities]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get activities: {str(e)}"
        )


@router.get("/activities/stats", response_model=APIResponse)
async def get_activity_stats(
    user_id: Optional[int] = None,
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
    current_user: dict = Depends(get_current_user)
):
    """Get user activity statistics"""
    try:
        stats = await get_user_activity_stats(db, user_id)
        
        return APIResponse(
            success=True,
            message="Activity statistics retrieved",
            data=stats
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get activity stats: {str(e)}"
        )


@router.post("/sessions", response_model=APIResponse)
async def create_session(
    session_data: UserSession,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
    current_user: dict = Depends(get_current_user)
):
    """Create a new user session record"""
    try:
        # Add IP and User Agent from request
        session_data.ip_address = request.client.host
        session_data.user_agent = request.headers.get("user-agent")
        
        session = await create_user_session(db, session_data)
        
        return APIResponse(
            success=True,
            message="User session created successfully",
            data=session.dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/sessions", response_model=APIResponse)
async def get_sessions(
    user_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    limit: int = 50,
    skip: int = 0,
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
    current_user: dict = Depends(get_current_user)
):
    """Get user sessions with filtering"""
    try:
        query = SessionQuery(
            user_id=user_id,
            is_active=is_active,
            limit=limit,
            skip=skip
        )
        
        sessions = await get_user_sessions(db, query)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(sessions)} sessions",
            data=[session.dict() for session in sessions]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}"
        )


@router.put("/sessions/{session_id}/activity", response_model=APIResponse)
async def update_session_activity_endpoint(
    session_id: str,
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
    current_user: dict = Depends(get_current_user)
):
    """Update session last activity timestamp"""
    try:
        success = await update_session_activity(db, session_id)
        
        if success:
            return APIResponse(
                success=True,
                message="Session activity updated",
                data={"session_id": session_id}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session activity: {str(e)}"
        )


@router.delete("/sessions/{session_id}", response_model=APIResponse)
async def end_session(
    session_id: str,
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
    current_user: dict = Depends(get_current_user)
):
    """End a user session"""
    try:
        success = await end_user_session(db, session_id)
        
        if success:
            return APIResponse(
                success=True,
                message="Session ended successfully",
                data={"session_id": session_id}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end session: {str(e)}"
        ) 