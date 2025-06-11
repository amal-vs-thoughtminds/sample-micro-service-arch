from fastapi import APIRouter, Depends, HTTPException, status, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional

from ...core.mongodb import get_mongodb
from ...core.jwt_handler import get_current_user, get_optional_current_user
from ...schemas.mongodb import (
    AnalyticsEvent, AnalyticsEventResponse, EventQuery,
    AnalyticsSession, AnalyticsSessionResponse, SessionAnalyticsQuery
)
from ...schemas.common import APIResponse
from ..analytics.services.analytics_events import (
    create_analytics_event, get_analytics_events
)

router = APIRouter()


@router.post("/events", response_model=APIResponse)
async def create_event(
    event_data: AnalyticsEvent,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """Create a new analytics event record"""
    try:
        # Add IP and User Agent from request
        event_data.ip_address = request.client.host
        event_data.user_agent = request.headers.get("user-agent")
        
        event = await create_analytics_event(db, event_data)
        
        return APIResponse(
            success=True,
            message="Analytics event created successfully",
            data=event.dict()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create event: {str(e)}"
        )


@router.get("/events", response_model=APIResponse)
async def get_events(
    event_type: Optional[str] = None,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
    current_user: dict = Depends(get_current_user)
):
    """Get analytics events with filtering"""
    try:
        query = EventQuery(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            limit=limit,
            skip=skip
        )
        
        events = await get_analytics_events(db, query)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(events)} analytics events",
            data=[event.dict() for event in events]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get events: {str(e)}"
        )


@router.post("/sessions", response_model=APIResponse)
async def create_analytics_session(
    session_data: AnalyticsSession,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    """Create a new analytics session record"""
    try:
        collection = db.analytics_sessions
        
        # Add IP and User Agent from request
        session_data.ip_address = request.client.host
        session_data.user_agent = request.headers.get("user-agent")
        
        session_dict = session_data.dict()
        result = await collection.insert_one(session_dict)
        
        # Retrieve the created document
        created_session = await collection.find_one({"_id": result.inserted_id})
        created_session["_id"] = str(created_session["_id"])
        
        return APIResponse(
            success=True,
            message="Analytics session created successfully",
            data=created_session
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create analytics session: {str(e)}"
        )


@router.get("/sessions", response_model=APIResponse)
async def get_analytics_sessions(
    user_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    limit: int = 50,
    skip: int = 0,
    db: AsyncIOMotorDatabase = Depends(get_mongodb),
    current_user: dict = Depends(get_current_user)
):
    """Get analytics sessions with filtering"""
    try:
        collection = db.analytics_sessions
        
        # Build MongoDB filter
        filter_dict = {}
        if user_id:
            filter_dict["user_id"] = user_id
        if is_active is not None:
            filter_dict["is_active"] = is_active
        
        # Execute query with pagination
        cursor = collection.find(filter_dict).sort("start_time", -1).skip(skip).limit(limit)
        
        sessions = []
        async for session in cursor:
            session["_id"] = str(session["_id"])
            sessions.append(session)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(sessions)} analytics sessions",
            data=sessions
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics sessions: {str(e)}"
        ) 