from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy import select

from ...core.db import get_postgres_db
from ...core.dependencies import get_decrypted_payload, get_optional_decrypted_payload, PostgresDB, MongoDB
from ...core.mongodb import get_mongo_collection
from ...schemas.analytics import (
    AnalyticsEvent,
    AnalyticsEventResponse,
    APIResponse,
    EventType,
    AnalyticsStats,
    UserAnalytics
)
from .services.create_event import create_analytics_event
from .services.get_analytics_stats import get_events_count
from ms_communicator import MicroServiceClient
import logging
from ...models.analytics import AnalyticsEvent as AnalyticsEventModel

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)

# Initialize the microservice client
service_client = MicroServiceClient("analytics-service")

@router.post("/events", response_model=APIResponse)
async def create_event(
    request: Request,
    event_data: AnalyticsEvent,
    db: AsyncSession = Depends(get_postgres_db),
    decrypted_payload: Optional[Dict[str, Any]] = Depends(get_decrypted_payload)
):
    """Create a new analytics event"""
    try:
        # Use decrypted payload if available
        if decrypted_payload:
            event_data = AnalyticsEvent(**decrypted_payload)
        
        # Create event
        new_event = await create_analytics_event(db, event_data)
        logger.info(f"Created analytics event: {new_event.id}")
        
        return APIResponse(
            message="Event created successfully",
            data={"event_id": new_event.id, "event_type": new_event.event_type}
        )
    
    except Exception as e:
        logger.error(f"Failed to create event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create event"
        )

@router.get("/stats", response_model=APIResponse)
async def get_analytics_stats(
    request: Request,
    db: AsyncSession = Depends(get_postgres_db),
    decrypted_payload: Optional[Dict[str, Any]] = Depends(get_optional_decrypted_payload)
):
    """Get analytics statistics and optionally get user count from user service"""
    try:
        # Get local analytics stats
        total_events = await get_events_count(db)
        logger.info(f"Retrieved analytics stats: {total_events} events")
        
        # Get user stats from user service
        user_stats = None
        try:
            user_stats_response = await service_client.request(
                target_service="user-service",
                endpoint="/api/v1/users/stats/count",
                method="GET"
            )
            user_stats = user_stats_response.get("data")
            logger.info("Successfully retrieved user stats")
        except Exception as e:
            # User service call failed, continue without user stats
            logger.error(f"Failed to get user stats: {str(e)}")
        
        return APIResponse(
            message="Analytics statistics retrieved",
            data={
                "total_events": total_events,
                "user_stats": user_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    except Exception as e:
        logger.error(f"Failed to get analytics stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analytics stats"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint for the analytics service"""
    return {
        "status": "healthy",
        "service": "analytics-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/events/mongodb", response_model=APIResponse)
async def create_analytics_event_mongodb(
    event: AnalyticsEvent,
    mongo_db: MongoDB
):
    """Create a new analytics event in MongoDB"""
    try:
        result = await mongo_db.insert_one(event.model_dump())
        return APIResponse(
            success=True,
            message="Analytics event created successfully",
            data={"event_id": str(result.inserted_id)}
        )
    except Exception as e:
        logger.error(f"Failed to create analytics event: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create analytics event"
        )

@router.get("/events/mongodb", response_model=APIResponse)
async def get_analytics_events_mongodb(
    mongo_db: MongoDB,
    event_type: EventType | None = None,
    limit: int = 100
):
    """Get analytics events from MongoDB"""
    try:
        query = {"event_type": event_type} if event_type else {}
        cursor = mongo_db.find(query).limit(limit)
        events = await cursor.to_list(length=limit)
        return APIResponse(
            success=True,
            message="Analytics events retrieved successfully",
            data={"events": events}
        )
    except Exception as e:
        logger.error(f"Failed to retrieve analytics events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics events"
        )

@router.get("/user/{user_id}", response_model=APIResponse)
async def get_user_analytics_events(
    user_id: str,
    mongo_db: MongoDB,
    limit: int = 100
):
    """Get analytics events for a specific user from MongoDB"""
    try:
        query = {"user_id": int(user_id)}
        cursor = mongo_db.find(query).limit(limit)
        events = await cursor.to_list(length=limit)
        # Convert ObjectId to str for each event
        for event in events:
            if "_id" in event:
                event["_id"] = str(event["_id"])
        return APIResponse(
            success=True,
            message=f"Analytics events for user {user_id} retrieved successfully",
            data={"events": events}
        )
    except Exception as e:
        logger.error(f"Failed to retrieve analytics events for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics events for user {user_id}: {str(e)}"
        ) 