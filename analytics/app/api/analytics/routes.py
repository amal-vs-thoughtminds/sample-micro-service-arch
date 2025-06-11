from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional

from ...core.db import get_postgres_db
from ...core.dependencies import get_decrypted_payload, get_optional_decrypted_payload
from ...core.encryption import encrypt_response_data
from ...core.dispatcher import dispatcher
from .schemas import AnalyticsEventCreate, AnalyticsEventResponse, APIResponse
from .services.create_event import create_analytics_event
from .services.get_analytics_stats import get_events_count

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/events", response_model=APIResponse)
async def create_event(
    event_data: AnalyticsEventCreate,
    db: AsyncSession = Depends(get_postgres_db),
    decrypted_payload: Optional[Dict[str, Any]] = Depends(get_decrypted_payload)
):
    """Create a new analytics event"""
    try:
        # Use decrypted payload if available
        if decrypted_payload:
            event_data = AnalyticsEventCreate(**decrypted_payload)
        
        # Create event
        new_event = await create_analytics_event(db, event_data)
        
        response_data = {
            "message": "Event created successfully",
            "data": {"event_id": new_event.id, "event_type": new_event.event_type}
        }
        
        # Return encrypted response for service communication
        if decrypted_payload:
            return encrypt_response_data(response_data)
        
        return APIResponse(**response_data)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create event"
        )


@router.get("/stats", response_model=APIResponse)
async def get_analytics_stats(
    db: AsyncSession = Depends(get_postgres_db),
    decrypted_payload: Optional[Dict[str, Any]] = Depends(get_optional_decrypted_payload)
):
    """Get analytics statistics and optionally call user service for user count"""
    try:
        # Get local analytics stats
        total_events = await get_events_count(db)
        
        # Optionally get user stats from user service via dispatcher
        user_stats = None
        try:
            user_stats = await dispatcher.call_user_service(
                "/api/v1/users/stats/count",
                {}
            )
        except Exception as e:
            # User service call failed, continue without user stats
            pass
        
        response_data = {
            "message": "Analytics statistics retrieved",
            "data": {
                "total_events": total_events,
                "user_stats": user_stats.get("data") if user_stats else None
            }
        }
        
        return APIResponse(**response_data)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analytics stats"
        ) 